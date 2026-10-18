#!/usr/bin/env python3
"""Find microtypography candidates in HTML, Markdown or plain text (German and English).

Usage:
  check_text.py PATH [PATH ...] [--lang de|en|auto] [--max-per-rule N]

PATH may be a file or a folder (searched for .html, .htm, .md, .markdown, .txt).
Output, one line per candidate:
  path:line:col  warn|info  [rule]  "context"  ->  suggestion  (reason)
Exit code: 0 = no warnings, 1 = at least one warning, 2 = usage error.

Every hit is a candidate. Code samples, ISO dates, product names or deliberate
styling can be false positives, so look at the context before changing text.
Skipped: script, style, pre, code, kbd, samp, textarea, svg, math, HTML comments,
Markdown code (fenced and inline), link targets, URLs and email addresses.
In the context column, [NBSP] is U+00A0, [NNBSP] is U+202F, [THIN] is U+2009.
"""
import argparse
import bisect
import html
import os
import re
import sys

EXTENSIONS = {'.html': 'html', '.htm': 'html', '.md': 'md', '.markdown': 'md', '.txt': 'txt'}
SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.next', '.nuxt', '.svelte-kit', 'vendor', '.venv'}
INLINE_TAGS = {
    'a', 'abbr', 'b', 'bdi', 'bdo', 'cite', 'data', 'del', 'dfn', 'em', 'font', 'i', 'ins',
    'label', 'mark', 'q', 's', 'small', 'span', 'strong', 'sub', 'sup', 'time', 'u', 'var', 'wbr',
}
INLINE_SKIP = {'code', 'kbd', 'samp'}
OBJ = '￼'  # stands in for skipped inline content so words don't merge

NBSP, NNBSP, THIN = ' ', ' ', ' '
SPACE_CLASS = '[    ]'

DE_WORDS = {'und', 'der', 'die', 'das', 'ist', 'nicht', 'mit', 'sich', 'auf', 'für', 'ein',
            'eine', 'zu', 'den', 'von', 'im', 'wird', 'sind', 'auch', 'oder', 'dass', 'werden'}
EN_WORDS = {'the', 'and', 'is', 'not', 'with', 'of', 'to', 'for', 'that', 'this', 'are', 'be',
            'or', 'on', 'it', 'as', 'by', 'from', 'you', 'your', 'will'}

DE_ABBREVIATIONS = ['z. B.', 'd. h.', 'u. a.', 'u. U.', 'v. a.', 'z. T.', 'o. Ä.', 'u. Ä.', 'i. d. R.',
                    's. o.', 's. u.', 'u. v. m.', 'm. E.', 'z. Hd.', 'i. A.', 'i. V.', 'o. g.',
                    'z. Zt.', 'v. Chr.', 'n. Chr.']
UNITS = ['kWh', 'MWh', 'kW', 'MW', 'GW', 'Wh', 'kg', 'mg', 'km', 'cm', 'mm', 'µm', 'ml', 'min', 'ms',
         'MB', 'GB', 'TB', 'kB', 'KB', 'Mbit', 'Gbit', 'kHz', 'MHz', 'GHz', 'Hz', '°C', '°F',
         'EUR', 'CHF', 'USD', '€', '%', '‰', 'px', 'pt', 'dpi', 'g', 'm', 'h']
TECH_UNITS = {'px', 'pt', 'dpi'}
SPLIT_SAFE = {NBSP, NNBSP}


# ---------------------------------------------------------------- extraction

def build_pattern(kind):
    parts = []
    if kind == 'md':
        parts += [
            ('frontmatter', r'\A---[ \t]*\n.*?\n---[ \t]*\n'),
            ('fence', r'^[ \t]*(?P<fq>```|~~~)[^\n]*\n.*?^[ \t]*(?P=fq)[^\n]*$'),
            ('inlinecode', r'`[^`\n]+`'),
            ('linkdest', r'(?<=\])\([^)\n]*\)'),
            ('refdef', r'^[ \t]*\[[^\]\n]+\]:[^\n]*$'),
        ]
    if kind in ('html', 'md'):
        parts += [
            ('comment', r'<!--.*?-->'),
            ('skipel', r'<(?P<st>script|style|pre|code|kbd|samp|textarea|svg|math)\b[^>]*>.*?</(?P=st)\s*>'),
            ('tag', r'</?(?P<tn>[a-zA-Z][\w:-]*)\b[^>]*>'),
            ('decl', r'<![^>]*>'),
            ('entity', r'&(?:#\d+|#[xX][0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);'),
        ]
    parts += [
        ('url', r'\b(?:https?://|www\.)[^\s<>"\')\]]+'),
        ('email', r'\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b'),
    ]
    names = [name for name, _ in parts]
    regex = '|'.join('(?P<%s>%s)' % (name, rx) for name, rx in parts)
    return re.compile(regex, re.S | re.M | re.I), names


def extract(raw, kind):
    """Return (text, offsets): visible text and, for each character, its offset in raw."""
    pattern, names = build_pattern(kind)
    out, offsets = [], []

    def emit(s, at):
        for ch in s:
            out.append(ch)
            offsets.append(at)

    pos = 0
    for m in pattern.finditer(raw):
        for i in range(pos, m.start()):
            out.append(raw[i])
            offsets.append(i)
        pos = m.end()
        name = next(n for n in names if m.group(n) is not None)
        if name in ('frontmatter', 'comment', 'decl', 'linkdest'):
            continue
        if name in ('fence', 'refdef'):
            emit('\n', m.start())
        elif name in ('inlinecode', 'url', 'email'):
            emit(OBJ, m.start())
        elif name == 'skipel':
            emit(OBJ if m.group('st').lower() in INLINE_SKIP else '\n', m.start())
        elif name == 'tag':
            if m.group('tn').lower() not in INLINE_TAGS:
                emit('\n', m.start())
        elif name == 'entity':
            emit(html.unescape(m.group()), m.start())
    for i in range(pos, len(raw)):
        out.append(raw[i])
        offsets.append(i)
    return ''.join(out), offsets


def _base(lang):
    return lang.split('-')[0]


def _swiss(lang):
    return lang in ('de-ch', 'de-li')


def declared_lang(raw):
    """(tag, offset) of <html lang=...>, or (None, None)."""
    m = re.search(r'<html\b[^>]*\blang\s*=\s*["\']?([a-zA-Z]{2,3}(?:-[a-zA-Z]{2})?)', raw, re.I)
    return (m.group(1).lower(), m.start()) if m else (None, None)


def content_lang(text):
    """'de' or 'en' when the text clearly reads as one of them, else None."""
    words = re.findall(r'[a-zäöüß]+', text.lower())
    de = sum(w in DE_WORDS for w in words)
    en = sum(w in EN_WORDS for w in words)
    if de >= 8 and de > 2 * en:
        return 'de'
    if en >= 8 and en > 2 * de:
        return 'en'
    return None


def detect_lang(raw, kind, text):
    if kind == 'html':
        tag, _ = declared_lang(raw)
        if tag:
            guess = content_lang(text)
            return tag if not guess or _base(tag) == guess else guess  # a wrong tag is reported separately
    return content_lang(text) or 'en'


# ---------------------------------------------------------------- rules

def is_open_position(text, i):
    prev = text[i - 1] if i > 0 else ' '
    return prev.isspace() or prev in '([{/–—-' + OBJ


def rule_quotes(text, lang):
    if _swiss(lang):
        open_d, close_d, open_s, close_s = '«', '»', '‹', '›'
    elif _base(lang) == 'de':
        open_d, close_d, open_s, close_s = '„', '“', '‚', '‘'
    else:
        open_d, close_d, open_s, close_s = '“', '”', '‘', '’'
    for m in re.finditer('"', text):
        i = m.start()
        prev = text[i - 1] if i > 0 else ' '
        if prev.isdigit():
            yield i, i + 1, 'info', 'inch-mark', 'use ″ (U+2033) for inches, or write "Zoll"/"in"', 'a straight quote after a number is usually a typewriter inch mark'
            continue
        sugg = open_d if is_open_position(text, i) else close_d
        yield i, i + 1, 'warn', 'straight-double-quote', sugg, 'straight quotes are typewriter substitutes'
    for m in re.finditer("'", text):
        i = m.start()
        prev = text[i - 1] if i > 0 else ' '
        nxt = text[i + 1] if i + 1 < len(text) else ' '
        if prev.isalpha() and nxt.isalpha():
            yield i, i + 1, 'warn', 'straight-apostrophe', '’ (U+2019)', 'the apostrophe is a raised comma, not a straight tick'
        elif is_open_position(text, i):
            sugg = '’ (apostrophe, as in ’90s or ’s)' if nxt.isdigit() else open_s + ' (opening single quote) or ’ (apostrophe)'
            yield i, i + 1, 'warn', 'straight-single-quote', sugg, 'straight quotes are typewriter substitutes'
        else:
            yield i, i + 1, 'warn', 'straight-single-quote', '’ (apostrophe, as in Hans’) or ' + close_s + ' (closing single quote)', 'straight quotes are typewriter substitutes'
    if _swiss(lang):
        for m in re.finditer('[„“”‚]', text):
            sugg = '«' if m.group() == '„' else ('‹' if m.group() == '‚' else '«/»')
            yield m.start(), m.end(), 'warn', 'quote-style-swiss', sugg, 'Swiss German uses guillemets «…» ‹…›'
        for m in re.finditer('ß', text):
            yield m.start(), m.end(), 'info', 'eszett-in-swiss', 'ss', 'Swiss German writes ss, never ß'
        for m in re.finditer('—', text):
            yield m.start(), m.end(), 'info', 'em-dash-in-german', ' – (spaced en dash)', 'German uses the spaced en dash as Gedankenstrich'
    elif _base(lang) == 'de':
        for m in re.finditer('[“‘]', text):
            i = m.start()
            nxt = text[i + 1] if i + 1 < len(text) else ' '
            if is_open_position(text, i) and (nxt.isalnum() or nxt in '…‚'):
                sugg = '„' if m.group() == '“' else '‚'
                yield i, i + 1, 'warn', 'english-quote-in-german', sugg, 'German opening quotes sit on the baseline („…“)'
        for m in re.finditer('[”’](?=[\s.,;:!?)]|$)', text):
            i = m.start()
            if m.group() == '’':
                continue  # apostrophe at word end (Hans’), fine
            yield i, i + 1, 'warn', 'english-quote-in-german', '“', 'German closing double quote is “ (66 shape), not ”'
        for m in re.finditer('—', text):
            yield m.start(), m.end(), 'info', 'em-dash-in-german', ' – (spaced en dash)', 'German uses the spaced en dash as Gedankenstrich'
    else:
        for m in re.finditer('[„‚]', text):
            yield m.start(), m.end(), 'info', 'german-quote-in-english', '“ or ‘', 'low opening quotes are German style'


def rule_dashes(text, lang):
    for m in re.finditer(r'(?<=\S) - (?=\S)', text):
        yield m.start() + 1, m.start() + 2, 'warn', 'spaced-hyphen', '– (en dash with spaces)', 'a hyphen joins words; a dash separates them'
    for m in re.finditer(r'(?<!-)--(?!-)', text):
        yield m.start(), m.end(), 'warn', 'double-hyphen', '– (en dash)' + ('' if _base(lang) == 'de' else ' or — (em dash)'), 'two hyphens are a typewriter substitute for a dash'
    for m in re.finditer(r'(?<![\d.,/\-])(\d{1,4})-(\d{1,4})(?![\d\-/]|[.,]\d)', text):
        yield m.start(), m.end(), 'info', 'hyphen-range', m.group(1) + '–' + m.group(2), 'ranges take an en dash (bis-Strich), unspaced'
    days = r'(?:Mo|Di|Mi|Do|Fr|Sa|So)' if _base(lang) == 'de' else r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)'
    for m in re.finditer(r'\b(%s)-(%s)\b' % (days, days), text):
        yield m.start(), m.end(), 'info', 'hyphen-range', m.group(1) + '–' + m.group(2), 'ranges take an en dash, unspaced'
    if _base(lang) == 'de':
        for m in re.finditer(r'(?<=\d) – (?=\d)', text):
            yield m.start(), m.end(), 'info', 'spaced-range-dash', '– without spaces (1990–2000)', 'German sets the bis-Strich without spaces'


def rule_ellipsis(text, lang):
    for m in re.finditer(r'\.\.\.|\. \. \.', text):
        yield m.start(), m.end(), 'warn', 'three-dots', '… (U+2026)', 'the ellipsis character has the right spacing and never breaks apart'


def rule_spacing(text, lang, kind):
    # space before punctuation
    for m in re.finditer(r'(?<=[^\s' + OBJ + r']) (?=[,.;:!?](?:\s|$))', text):
        yield m.start(), m.end(), 'warn', 'space-before-punctuation', 'remove the space', 'German and English set no space before , . ; : ! ?'
    if kind == 'txt':
        for m in re.finditer(r'(?<=\S) {2,}(?=\S)', text):
            yield m.start(), m.end(), 'info', 'multiple-spaces', 'one space', 'one word space between words and sentences'
    for m in re.finditer(THIN, text):
        yield m.start(), m.end(), 'info', 'thin-space-breaks', 'U+202F (narrow no-break space) if the parts must stay together', 'U+2009 allows a line break'


def rule_abbreviations(text, lang):
    if _base(lang) != 'de':
        return
    for abbr in DE_ABBREVIATIONS:
        parts = [p.rstrip('.') for p in abbr.split(' ')]
        first = parts[0]
        rx = r'(?<![\wÄÖÜäöü])[%s%s]' % (first[0].lower(), first[0].upper()) + re.escape(first[1:]) + r'\.'
        for p in parts[1:]:
            rx += r'(%s?)' % SPACE_CLASS + re.escape(p) + r'\.'
        for m in re.finditer(rx, text):
            seps = m.groups()
            if all(s in SPLIT_SAFE for s in seps):
                continue
            bad = 'no space' if any(s == '' for s in seps) else 'a breaking space'
            yield m.start(), m.end(), 'warn', 'abbreviation-spacing', abbr.replace(' ', '[NNBSP]'), 'has %s; use a narrow no-break space (U+202F) so it reads as one unit and never splits' % bad


def rule_units(text, lang):
    units = '|'.join(re.escape(u) for u in UNITS)
    rx = r'(?<![\w.,])(\d+(?:[.,]\d+)?)(?P<sp>%s?)(?P<u>%s)(?![\w])' % (SPACE_CLASS, units)
    for m in re.finditer(rx, text):
        sp, unit = m.group('sp'), m.group('u')
        if sp in SPLIT_SAFE:
            continue
        if unit in ('%', '‰') and _base(lang) != 'de':
            if sp == '':
                continue
            yield m.start(), m.end(), 'info', 'percent-spacing', m.group(1) + unit, 'English usually sets percent without a space'
            continue
        level = 'info' if unit in TECH_UNITS or (unit in ('%', '‰')) else 'warn'
        if sp == '':
            note = 'DIN 5008 sets a space before %' if unit in ('%', '‰') else 'number and unit are separated by a space'
            yield m.start(), m.end(), level, 'number-unit-spacing', m.group(1) + '[NNBSP]' + unit, note + '; make it a narrow no-break space (U+202F)'
        else:
            yield m.start(), m.end(), level, 'number-unit-spacing', m.group(1) + '[NNBSP]' + unit, 'a breaking space lets the unit wrap onto the next line'


def rule_references(text, lang):
    refs = r'(?:S|Nr|Abb|Tab|Kap|Bd|Aufl|Fn|Anm)' if _base(lang) == 'de' else r'(?:p|pp|No|Vol|Fig|Ch|Sec)'
    for m in re.finditer(r'\b(%s)\.(?P<sp>[  ]?)(?=\d)' % refs, text):
        level = 'warn' if m.group('sp') == '' else 'info'
        yield m.start(), m.end() + 1, level, 'reference-spacing', m.group(1) + '.[NBSP]…', 'keep the abbreviation with its number (no-break space)'
    for m in re.finditer(r'§(?P<sp>[  ]?)(?=\d)', text):
        level = 'warn' if m.group('sp') == '' else 'info'
        yield m.start(), m.end() + 1, level, 'reference-spacing', '§[NBSP]…', 'keep § with its number (no-break space)'
    for m in re.finditer(r'\b(Dr|Prof|Mr|Mrs|Ms)\. (?=[A-ZÄÖÜ])', text):
        yield m.start(), m.end(), 'info', 'title-spacing', m.group(1) + '.[NBSP]', 'keep the title with the name'


def rule_times(text, lang):
    for m in re.finditer(r'(?<![\w.])(\d+(?:[.,]\d+)?)( ?)[xX]( ?)(?=\d)', text):
        if m.group(1) == '0' and m.group(2) == '':
            continue  # 0x… hex notation
        yield m.start(), m.end() + 1, 'info', 'multiplication-sign', m.group(1) + ' × …', 'use the multiplication sign (U+00D7), not the letter x'


def rule_thousands(text, lang):
    if _base(lang) != 'de' or _swiss(lang):
        return  # Swiss German groups thousands with an apostrophe (18’450)
    for m in re.finditer(r'(?<![\d.,])\d{1,3}(?:\.\d{3})+(?!\d|[.,]\d)', text):
        grouped = m.group().replace('.', '[NNBSP]')
        yield m.start(), m.end(), 'info', 'thousands-separator', grouped, 'in running text a narrow no-break space groups digits without looking like a decimal point (a dot is acceptable in tables)'


RULES = [rule_quotes, rule_dashes, rule_ellipsis, rule_abbreviations, rule_units, rule_references,
         rule_times, rule_thousands]


# ---------------------------------------------------------------- reporting

def visible(s):
    s = re.sub(r'[ \t\r\n]+', ' ', s)
    return s.replace(NBSP, '[NBSP]').replace(NNBSP, '[NNBSP]').replace(THIN, '[THIN]').replace(OBJ, '…')


def check_file(path, forced_lang, max_per_rule):
    kind = EXTENSIONS.get(os.path.splitext(path)[1].lower())
    if not kind:
        return []
    with open(path, encoding='utf-8', errors='replace') as fh:
        raw = fh.read()
    text, offsets = extract(raw, kind)
    lang = forced_lang if forced_lang != 'auto' else detect_lang(raw, kind, text)
    line_starts = [0] + [m.end() for m in re.finditer('\n', raw)]

    findings = []
    for rule in RULES:
        findings.extend(rule(text, lang))
    findings.extend(rule_spacing(text, lang, kind))

    # drop thin-space hits already covered by a more specific finding
    specific = [(s, e) for s, e, _, r, _, _ in findings if r != 'thin-space-breaks']
    findings = [f for f in findings
                if f[3] != 'thin-space-breaks' or not any(s <= f[0] < e for s, e in specific)]

    results, per_rule = [], {}
    if kind == 'html':
        tag, at = declared_lang(raw)
        guess = content_lang(text)
        if tag and guess and _base(tag) != guess:
            line = bisect.bisect_right(line_starts, at)
            results.append((path, line, at - line_starts[line - 1] + 1, 'warn', 'lang-mismatch',
                            'lang="%s"' % tag, 'lang="%s" (with region if it matters, e.g. de-CH)' % guess,
                            'the text reads as %s; hyphenation, quotation marks and screen readers follow lang' % guess))
    for start, end, level, rule, sugg, reason in sorted(findings, key=lambda f: f[0]):
        per_rule[rule] = per_rule.get(rule, 0) + 1
        if per_rule[rule] > max_per_rule:
            continue
        orig = offsets[start] if start < len(offsets) else len(raw) - 1
        line = bisect.bisect_right(line_starts, orig)
        col = orig - line_starts[line - 1] + 1
        context = visible(text[max(0, start - 18):min(len(text), end + 18)]).strip()
        results.append((path, line, col, level, rule, context, sugg, reason))
    hidden = {r: n - max_per_rule for r, n in per_rule.items() if n > max_per_rule}
    return results, hidden, lang


def iter_paths(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in EXTENSIONS:
                        yield os.path.join(root, f)
        elif os.path.isfile(p):
            yield p
        else:
            print('check_text: no such file or folder: %s' % p, file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--lang', default='auto', choices=['auto', 'de', 'de-ch', 'en'])
    ap.add_argument('--max-per-rule', type=int, default=25)
    args = ap.parse_args(argv)

    any_warn, total, files = False, 0, 0
    for path in iter_paths(args.paths):
        res = check_file(path, args.lang, args.max_per_rule)
        if not res:
            continue
        results, hidden, lang = res
        files += 1
        for path_, line, col, level, rule, context, sugg, reason in results:
            total += 1
            any_warn = any_warn or level == 'warn'
            print('%s:%d:%d  %s  [%s]  "%s"  ->  %s  (%s)' % (path_, line, col, level, rule, context, sugg, reason))
        for rule, n in sorted(hidden.items()):
            print('%s  info  [%s]  ... %d more of this rule not shown (raise --max-per-rule)' % (path, rule, n))
        print('# %s: language %s' % (path, lang), file=sys.stderr)
    print('# %d candidate(s) in %d file(s)' % (total, files), file=sys.stderr)
    return 1 if any_warn else 0


if __name__ == '__main__':
    sys.exit(main())
