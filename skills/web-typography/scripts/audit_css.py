#!/usr/bin/env python3
"""Static typography audit of CSS and HTML: smells that hurt reading, zoom or line breaking.

Usage:
  audit_css.py PATH [PATH ...]

PATH may be a file or a folder (.css, .html, .htm). CSS is read from .css files,
<style> blocks and style="" attributes. Plain CSS only: for Sass, Less, Tailwind or
CSS-in-JS, run it on the compiled CSS.
Output, one line per candidate:
  path:line:col  warn|info  [rule]  message
Exit code: 0 = no warnings, 1 = at least one warning, 2 = usage error.

Findings are candidates. A declaration may be overridden elsewhere, or a choice
may be deliberate, so confirm each one in context before changing it.
"""
import argparse
import os
import re
import sys

SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.next', '.nuxt', '.svelte-kit', 'vendor', '.venv'}
DECL_AT_RULES = {'page', 'font-face', 'property', 'counter-style', 'font-palette-values', 'viewport',
                 'top-left-corner', 'top-left', 'top-center', 'top-right', 'top-right-corner',
                 'bottom-left-corner', 'bottom-left', 'bottom-center', 'bottom-right', 'bottom-right-corner',
                 'left-top', 'left-middle', 'left-bottom', 'right-top', 'right-middle', 'right-bottom'}
SKIP_AT_RULES = {'keyframes', '-webkit-keyframes', 'font-feature-values'}
GENERIC_FAMILIES = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui', 'ui-serif',
                    'ui-sans-serif', 'ui-monospace', 'ui-rounded', 'math', 'emoji', 'fangsong',
                    '-apple-system', 'blinkmacsystemfont', 'inherit', 'initial', 'unset', 'revert'}

BODY_SEL = re.compile(
    r'(?:^|[\s>+~(])(?:body|p|li|dd|blockquote|article|main|td)(?=$|[\s>+~.:#\[)])'
    r'|\.(?:prose|content|text|copy|article|post|entry|body|lead|intro|description|excerpt|columns)\b', re.I)
HEADING_SEL = re.compile(
    r'(?:^|[\s>+~(])h[1-6](?=$|[\s>+~.:#\[)])|title|heading|headline|eyebrow|label|button|btn|nav|badge|caption|stat',
    re.I)
H_TAG = re.compile(r'(?:^|[\s>+~(])h[1-6](?=$|[\s>+~.:#\[)])', re.I)


class Rule:
    def __init__(self, path, line, selector, context):
        self.path, self.line, self.selector, self.context = path, line, selector, context
        self.decls = []  # (prop, value, line)

    def last(self, *props):
        for prop, value, line in reversed(self.decls):
            if prop in props:
                return value, line
        return None


# ---------------------------------------------------------------- parsing

def strip_comments(css):
    return re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group()), css, flags=re.S)


def parse_css(css, path, line_offset=0):
    css = strip_comments(css)
    rules, stack = [], []
    buf, buf_line = [], None
    line = 1 + line_offset
    quote, depth = None, 0

    def context():
        return tuple(f['prelude'] for f in stack if f['kind'] == 'at')

    def in_skip():
        return any(f['kind'] == 'skip' for f in stack)

    def current_rule():
        for f in reversed(stack):
            if f['kind'] == 'rule':
                return f['rule']
            return None
        return None

    def flush():
        nonlocal buf, buf_line
        text = ''.join(buf).strip()
        if text and not in_skip():
            rule = current_rule()
            if rule is not None and ':' in text:
                prop, _, value = text.partition(':')
                prop = prop.strip().lower()
                value = re.sub(r'\s*!important\s*$', '', value.strip(), flags=re.I)
                if re.match(r'^-{0,2}[a-z][\w-]*$', prop):
                    rule.decls.append((prop, value, buf_line or line))
        buf, buf_line = [], None

    i, n = 0, len(css)
    while i < n:
        ch = css[i]
        if quote:
            buf.append(ch)
            if ch == '\n':
                line += 1
            if ch == '\\' and i + 1 < n:
                buf.append(css[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch == '{' and depth == 0:
            prelude = ' '.join(''.join(buf).split())
            start = buf_line or line
            buf, buf_line = [], None
            low = prelude.lower()
            if in_skip():
                stack.append({'kind': 'skip', 'prelude': prelude})
            elif low.startswith('@'):
                m = re.match(r'@([\w-]+)', low)
                name = m.group(1) if m else ''
                if name in SKIP_AT_RULES:
                    stack.append({'kind': 'skip', 'prelude': prelude})
                elif name in DECL_AT_RULES:
                    rule = Rule(path, start, prelude, context())
                    rules.append(rule)
                    stack.append({'kind': 'rule', 'prelude': prelude, 'rule': rule})
                else:
                    stack.append({'kind': 'at', 'prelude': prelude})
            else:
                parent = current_rule()
                selector = prelude
                if parent is not None:
                    selector = prelude.replace('&', parent.selector) if '&' in prelude else parent.selector + ' ' + prelude
                rule = Rule(path, start, selector, context())
                rules.append(rule)
                stack.append({'kind': 'rule', 'prelude': prelude, 'rule': rule})
            i += 1
            continue
        if ch == ';' and depth == 0:
            flush()
            i += 1
            continue
        if ch == '}' and depth == 0:
            flush()
            if stack:
                stack.pop()
            i += 1
            continue
        if ch == '\n':
            line += 1
        if ch in '"\'':
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        if not buf and ch.isspace():
            i += 1
            continue
        if not buf:
            buf_line = line
        buf.append(ch)
        i += 1
    return rules


def parse_inline_style(body, path, line):
    rule = Rule(path, line, '[style attribute]', ())
    for part in body.split(';'):
        if ':' in part:
            prop, _, value = part.partition(':')
            rule.decls.append((prop.strip().lower(), value.strip(), line))
    return rule


# ---------------------------------------------------------------- value helpers

def to_px(value):
    m = re.match(r'^\s*(-?\d*\.?\d+)\s*(px|rem|em|pt|%)?\s*$', value or '', re.I)
    if not m or not m.group(2):
        return None
    num, unit = float(m.group(1)), m.group(2).lower()
    return {'px': num, 'rem': num * 16, 'em': num * 16, 'pt': num * 4 / 3, '%': num * 0.16}[unit]


def func_args(value, name):
    m = re.search(r'\b%s\(' % name, value, re.I)
    if not m:
        return None
    args, cur, depth, i = [], [], 1, m.end()
    while i < len(value):
        c = value[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                break
        if c == ',' and depth == 1:
            args.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    args.append(''.join(cur).strip())
    return args


def font_shorthand(value):
    """Return (size, line_height) from a `font` shorthand, or (None, None)."""
    m = re.search(r'(\d*\.?\d+(?:px|pt|rem|em|%)|clamp\([^;]*?\))\s*(?:/\s*(\d*\.?\d+(?:px|pt|rem|em|%)?))?', value, re.I)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def parts(selector):
    return [s.strip() for s in selector.split(',') if s.strip()]


def is_body_text(selector):
    return any(BODY_SEL.search(s) and not HEADING_SEL.search(s) for s in parts(selector))


def is_heading(selector):
    return any(H_TAG.search(s) or re.search(r'title|heading|headline', s, re.I) for s in parts(selector))


def is_root(selector):
    return any(s in ('html', ':root') for s in parts(selector))


def first_family(value):
    first = value.split(',')[0].strip().strip('"\'').strip()
    return first if first and first.lower() not in GENERIC_FAMILIES and not first.startswith('var(') else None


# ---------------------------------------------------------------- checks

def check_rule(rule, facts, out):
    sel = rule.selector
    ctx = ' '.join(rule.context).lower()
    in_print = facts['print_file'](rule.path) or bool(re.search(r'\bprint\b', ctx))
    wide_only = 'min-width' in ctx or 'min-inline-size' in ctx or bool(re.search(r'width\s*>=?', ctx))

    def emit(level, name, msg, line=None):
        out.append((rule.path, line or rule.line, level, name, '%s: %s' % (sel, msg)))

    font = rule.last('font')
    fs = rule.last('font-size')
    lh = rule.last('line-height')
    if font:
        size, height = font_shorthand(font[0])
        if size and not fs:
            fs = (size, font[1])
        if height and not lh:
            lh = (height, font[1])

    # alignment
    ta = rule.last('text-align')
    if ta and ta[0].strip().lower() == 'justify':
        hy = rule.last('hyphens', '-webkit-hyphens')
        if not (hy and 'auto' in hy[0].lower()):
            if facts['hyphens_auto']:
                emit('info', 'justify-check-hyphens',
                     'justified; hyphens: auto is set elsewhere (%s), confirm it reaches this text' % facts['hyphens_auto'][0], ta[1])
            else:
                emit('warn', 'justify-without-hyphens',
                     'justified text without hyphens: auto gets uneven word gaps and rivers, especially in German and in narrow columns', ta[1])
        if not wide_only and not in_print:
            emit('warn', 'justify-on-narrow-screens',
                 'justification also applies at phone widths, where few words per line make gaps uneven; use ragged right or limit it to a min-width media query', ta[1])
    if ta and ta[0].strip().lower() == 'center' and is_body_text(sel):
        emit('info', 'centered-running-text', 'centred running text makes every line start somewhere else; keep centring for short display text', ta[1])

    # font size
    if fs:
        value, line = fs
        low = value.lower()
        if 'clamp(' in low:
            args = func_args(low, 'clamp')
            if args and len(args) == 3:
                lo, hi = to_px(args[0]), to_px(args[2])
                if re.search(r'\d\s*(v(w|h|min|max|i|b)|cq\w+)\b', args[0]):
                    emit('warn', 'clamp-viewport-minimum', 'the clamp() minimum uses viewport units, so it does not grow with zoom', line)
                if lo and hi and hi / lo > 2.5:
                    emit('warn', 'clamp-zoom-ratio',
                         'max/min = %.2f, above 2.5: text may not reach 200 %% under browser zoom (WCAG 1.4.4); raise the minimum or lower the maximum' % (hi / lo), line)
                if re.search(r'\dpx\b', args[0] + ' ' + args[2]):
                    emit('info', 'clamp-px-bounds', "px bounds ignore the reader's font-size setting; use rem", line)
        elif re.search(r'\d\s*(v(w|h|min|max)|cq(i|w|b|h|min|max))\b', low) and not re.search(r'\d\s*(rem|em|px|%|ch|ex)\b', low):
            emit('warn', 'viewport-only-font-size',
                 "viewport units alone don't grow with browser zoom (WCAG 1.4.4); use clamp(<min>rem, <a>rem + <b>vw, <max>rem)", line)
        if is_root(sel) and re.match(r'^\s*\d*\.?\d+px\s*$', low):
            emit('warn', 'root-font-size-px', "a px root size overrides the reader's default font size; use 100% or leave it unset", line)
        if is_body_text(sel) and not in_print and not low.strip().endswith('%'):
            px = to_px(low)
            if px is not None and px < 15:
                emit('info', 'small-body-text', 'running text at about %.0f px; 16 px or more reads better on screen' % px, line)

    # leading
    if lh:
        value, line = lh
        v = value.strip().lower()
        if re.match(r'^\d*\.?\d+px$', v):
            emit('warn', 'line-height-px', "fixed px leading doesn't follow the text size; use a unitless value", line)
        elif re.match(r'^\d*\.?\d+(r?em|%)$', v):
            emit('info', 'line-height-units', 'prefer unitless line-height: it inherits as a ratio, so nested text keeps correct leading', line)
        elif re.match(r'^\d*\.?\d+$', v) and is_body_text(sel):
            limit = 1.2 if in_print else 1.3
            if float(v) < limit:
                emit('warn', 'tight-leading', 'line-height %s on running text; about 1.4-1.6 reads more comfortably (WCAG 1.4.8 AAA asks for 1.5)' % v, line)

    # tracking and case
    ls = rule.last('letter-spacing')
    tt = rule.last('text-transform')
    uppercase = bool(tt and 'uppercase' in tt[0].lower())
    if ls and is_body_text(sel) and not uppercase:
        val = ls[0].strip().lower()
        if val not in ('0', 'normal', '0em', '0px', '0rem') and not val.startswith('-'):
            emit('info', 'tracked-running-text',
                 'letter-spacing on running text makes word shapes harder to recognise; keep it at 0 and track capitals instead', ls[1])
    if uppercase and not ls:
        emit('info', 'caps-without-tracking', 'all caps without letter-spacing look cramped; add about 0.05-0.12em', tt[1])

    # clipping
    height = rule.last('height', 'block-size')
    overflow = rule.last('overflow', 'overflow-y', 'overflow-block')
    if height and re.match(r'^\d*\.?\d+(px|r?em|lh|ex|ch)$', height[0].strip().lower()):
        if (overflow and re.search(r'hidden|clip', overflow[0], re.I)) or rule.last('text-overflow'):
            emit('warn', 'fixed-height-text',
                 'fixed height with hidden overflow clips text when copy is longer or readers enlarge spacing (WCAG 1.4.12); use min-height, or line-clamp plus a way to read the full text', height[1])

    # breaking
    wb = rule.last('word-break')
    if wb and 'break-all' in wb[0].lower():
        emit('warn', 'word-break-all', 'break-all splits every word anywhere, even when there is room; use overflow-wrap: anywhere', wb[1])
    for prop in ('orphans', 'widows'):
        d = rule.last(prop)
        if d and d[0].strip() == '1':
            emit('warn', 'single-line-fragments', '%s: 1 allows a single line stranded at a column or page edge; use 2, or 3 in print' % prop, d[1])
    for prop, value, line in rule.decls:
        if prop.startswith('page-break-'):
            emit('info', 'legacy-page-break', '%s is legacy; use break-%s' % (prop, prop[len('page-break-'):]), line)
    tw = rule.last('text-wrap', 'text-wrap-style')
    if tw and 'balance' in tw[0].lower() and is_body_text(sel):
        emit('info', 'balance-on-running-text', 'balance evens all lines and narrows the block; for paragraphs, pretty avoids short last lines without that', tw[1])
    hy = rule.last('hyphens')
    if hy and 'auto' in hy[0].lower() and is_heading(sel):
        emit('info', 'hyphenated-headings', 'automatic hyphenation is conspicuous in large headings; prefer hyphens: manual with &shy; where needed', hy[1])
    cc = rule.last('column-count', 'columns')
    if cc:
        m = re.match(r'^\s*(\d+)\b', cc[0])
        if m and int(m.group(1)) >= 3:
            emit('info', 'narrow-columns', '%s columns: check characters per column (40-50) and that hyphenation is on' % m.group(1), cc[1])
    tsa = rule.last('-webkit-text-size-adjust', 'text-size-adjust')
    if tsa and tsa[0].strip().lower() == 'none':
        emit('warn', 'text-size-adjust-none', 'text-size-adjust: none can stop text from scaling on mobile; use 100% or remove it', tsa[1])


def check_globals(rules, html_files, css_seen, facts, out):
    decls = [(r, p, v, ln) for r in rules for p, v, ln in r.decls]
    anchor = rules[0].path if rules else (html_files[0][0] if html_files else '')

    def emit(level, name, msg):
        out.append((anchor, 1, level, name, msg))

    if not css_seen:
        return
    if not any(p in ('text-wrap', 'text-wrap-style') for _, p, _, _ in decls):
        emit('info', 'no-text-wrap', 'no text-wrap found: text-wrap: pretty on paragraphs and balance on headings reduce runts and ragged headings')
    has_measure = any(p in ('max-width', 'max-inline-size', 'width', 'inline-size') and re.search(r'\d\s*(ch|r?em)\b', v)
                      for _, p, v, _ in decls) or any(re.search(r'--[\w-]*measure', p) for _, p, _, _ in decls)
    if not has_measure:
        emit('info', 'no-measure-cap', 'no max-width in ch or em found: check characters per line (45-75 for running text)')
    multicol = [r for r, p, v, _ in decls if p in ('column-count', 'columns', 'column-width')]
    controls = any(p in ('orphans', 'widows') or (p == 'break-inside' and 'avoid' in v) for _, p, v, _ in decls)
    if multicol and not controls:
        emit('info', 'multicol-without-break-control',
             'multi-column text without orphans/widows or break-inside: avoid; defaults are 2 in Chromium and WebKit, Firefox has no widow control')
    printish = [r for r in rules if facts['print_file'](r.path) or re.search(r'\bprint\b', ' '.join(r.context).lower())]
    if printish:
        if not any(r.selector.lower().startswith('@page') for r in rules):
            emit('info', 'print-no-page-rule', 'print styles without @page: page size and margins are left to the browser defaults')
        keeps = any(is_heading(r.selector) and (('break-after', 'avoid') in [(p, v.strip().lower()) for p, v, _ in r.decls]
                                                or any(p == 'page-break-after' and 'avoid' in v for p, v, _ in r.decls))
                    for r in rules)
        if not keeps:
            emit('info', 'print-headings-not-kept', 'no break-after: avoid on headings: a heading can end up alone at the bottom of a page')
    small_caps = any((p == 'font-variant' and 'small-caps' in v) or (p == 'font-variant-caps' and 'small' in v) for _, p, v, _ in decls)
    if small_caps and not any(p.startswith('font-synthesis') and 'none' in v for _, p, v, _ in decls):
        emit('info', 'small-caps-synthesis', 'small caps without font-synthesis: none: browsers fake missing small caps with shrunken capitals')
    families = []
    for _, p, v, _ in decls:
        if p in ('font-family', 'font'):
            fam = first_family(v if p == 'font-family' else re.sub(r'^.*?\d\S*\s+', '', v, count=1))
            if fam and fam not in families:
                families.append(fam)
    if len(families) > 2:
        emit('info', 'many-font-families', '%d primary font families (%s): each needs a clear role; two plus a monospace is usually enough'
             % (len(families), ', '.join(families)))
    facts['families'] = families


def check_html(path, raw, facts, out):
    m = re.search(r'<html\b[^>]*>', raw, re.I)
    if m and not re.search(r'\blang\s*=', m.group(), re.I):
        line = raw.count('\n', 0, m.start()) + 1
        extra = ' (hyphens: auto is set, but cannot work without it)' if facts['hyphens_auto'] else ''
        out.append((path, line, 'warn', 'missing-lang',
                    '<html> has no lang: hyphenation, language-aware quotes and screen readers need it%s' % extra))
    for m in re.finditer(r'<meta\b[^>]*name\s*=\s*["\']viewport["\'][^>]*>', raw, re.I):
        content = m.group().lower()
        mx = re.search(r'maximum-scale\s*=\s*([\d.]+)', content)
        if re.search(r'user-scalable\s*=\s*(no|0)\b', content) or (mx and float(mx.group(1)) < 2):
            out.append((path, raw.count('\n', 0, m.start()) + 1, 'warn', 'zoom-blocked',
                        'the viewport meta tag blocks pinch zoom (user-scalable=no or maximum-scale < 2); WCAG 1.4.4'))
    t = re.search(r'<table\b', raw, re.I)
    if t and not facts['tabular_nums']:
        out.append((path, raw.count('\n', 0, t.start()) + 1, 'info', 'table-without-tabular-figures',
                    'tables but no font-variant-numeric: tabular-nums anywhere: proportional figures make columns of numbers ragged'))
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p\s*>', raw, re.I | re.S):
        if re.search(r'<br\b', m.group(1), re.I):
            out.append((path, raw.count('\n', 0, m.start()) + 1, 'info', 'br-in-paragraph',
                        '<br> inside a paragraph fixes a line break for one width only; check whether it is a real line break (address, poem) or a layout patch'))


# ---------------------------------------------------------------- driver

def iter_paths(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in ('.css', '.html', '.htm'):
                        yield os.path.join(root, f)
        elif os.path.isfile(p):
            yield p
        else:
            print('audit_css: no such file or folder: %s' % p, file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('paths', nargs='+')
    args = ap.parse_args(argv)

    rules, html_files, css_seen = [], [], False
    for path in iter_paths(args.paths):
        with open(path, encoding='utf-8', errors='replace') as fh:
            raw = fh.read()
        if path.lower().endswith('.css'):
            rules += parse_css(raw, path)
            css_seen = True
        else:
            html_files.append((path, raw))
            for m in re.finditer(r'<style\b[^>]*>(.*?)</style\s*>', raw, re.S | re.I):
                rules += parse_css(m.group(1), path, line_offset=raw.count('\n', 0, m.start(1)))
                css_seen = True
            for m in re.finditer(r'\bstyle\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', raw, re.I):
                body = m.group(1) if m.group(1) is not None else m.group(2)
                rules.append(parse_inline_style(body, path, raw.count('\n', 0, m.start()) + 1))

    facts = {
        'hyphens_auto': ['%s:%d' % (r.path, ln) for r in rules for p, v, ln in r.decls
                         if p in ('hyphens', '-webkit-hyphens') and 'auto' in v.lower()],
        'print_file': lambda p: 'print' in os.path.basename(p).lower(),
        'tabular_nums': any((p == 'font-variant-numeric' and 'tabular' in v) or (p == 'font-feature-settings' and 'tnum' in v)
                            for r in rules for p, v, _ in r.decls),
    }
    out = []
    for rule in rules:
        check_rule(rule, facts, out)
    for path, raw in html_files:
        check_html(path, raw, facts, out)
    check_globals(rules, html_files, css_seen, facts, out)

    any_warn = False
    for path, line, level, name, msg in sorted(out, key=lambda o: (o[0], o[1])):
        any_warn = any_warn or level == 'warn'
        print('%s:%d:1  %s  [%s]  %s' % (path, line, level, name, msg))
    print('# %d candidate(s); %d rule(s) parsed; font families: %s'
          % (len(out), len(rules), ', '.join(facts.get('families', [])) or 'none found'), file=sys.stderr)
    return 1 if any_warn else 0


if __name__ == '__main__':
    sys.exit(main())
