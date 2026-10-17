#!/usr/bin/env python3
"""Grade skill-test runs for the typography skills.

Usage:
  python3 evals/grade.py ITERATION_DIR [ITERATION_DIR ...]

ITERATION_DIR is e.g. skills/web-typography-workspace/iteration-1. For every
eval-*/<config>/run-*/ it writes grading.json (fields: text, passed, evidence),
combining automatic checks with manual verdicts read from
ITERATION_DIR/manual_grades.json:
  { "<eval-name>/<config>": { "<assertion text>": [true|false, "evidence"] } }
Assertions without an automatic check and without a manual verdict are graded
as failed with the evidence "needs manual grading", so nothing passes silently.
"""
import difflib
import filecmp
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'skills', 'web-typography', 'scripts')
FIXTURES = os.path.join(ROOT, 'fixtures')
sys.path.insert(0, SCRIPTS)
import audit_css  # noqa: E402


# ---------------------------------------------------------------- helpers

def read(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            return fh.read()
    except OSError:
        return ''


def audit(folder):
    """Rules reported by audit_css.py for a folder: list of (level, rule, line)."""
    res = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'audit_css.py'), folder],
                         capture_output=True, text=True)
    out = []
    for line in res.stdout.splitlines():
        m = re.match(r'^(.*?):(\d+):\d+\s+(warn|info)\s+\[([\w-]+)\]', line)
        if m:
            out.append((m.group(3), m.group(4), '%s:%s' % (os.path.basename(m.group(1)), m.group(2))))
    return out


def text_warnings(folder):
    res = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'check_text.py'), folder],
                         capture_output=True, text=True)
    out = []
    for line in res.stdout.splitlines():
        m = re.match(r'^(.*?):(\d+):\d+\s+(warn|info)\s+\[([\w-]+)\]\s+"(.*?)"', line)
        if m:
            out.append((m.group(3), m.group(4), m.group(5)))
    return out


def rules_of(folder):
    rules = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if name.endswith('.css'):
            rules += audit_css.parse_css(read(path), path)
        elif name.endswith('.html'):
            raw = read(path)
            for m in re.finditer(r'<style\b[^>]*>(.*?)</style\s*>', raw, re.S | re.I):
                rules += audit_css.parse_css(m.group(1), path)
    return rules


def decls(rules, prop_re):
    return [(r, p, v) for r in rules for p, v, _ in r.decls if re.fullmatch(prop_re, p)]


def visible_words(raw):
    raw = re.sub(r'<(script|style)\b.*?</\1>', ' ', raw, flags=re.S | re.I)
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = html.unescape(raw)
    trans = {ord(c): '"' for c in '„“”»«'}
    trans.update({ord(c): "'" for c in '‚‘’›‹'})
    trans.update({ord(c): '-' for c in '–—‑−'})
    trans.update({ord(c): ' ' for c in '   ­'})
    raw = raw.translate(trans).replace('…', '...').replace('×', 'x')
    raw = re.sub(r'([.,;:!?"\'()\-%])', r' \1 ', raw)
    return raw.split()


def unchanged(run_out, fixture):
    src = os.path.join(FIXTURES, fixture)
    dst = os.path.join(run_out, fixture)
    if not os.path.isdir(dst):
        return False, 'copy of %s is missing from outputs' % fixture
    changed = [f for f in sorted(os.listdir(src)) if not filecmp.cmp(os.path.join(src, f), os.path.join(dst, f), shallow=False)]
    extra = [f for f in sorted(os.listdir(dst)) if f not in os.listdir(src)]
    if changed or extra:
        return False, 'changed: %s; added: %s' % (', '.join(changed) or 'none', ', '.join(extra) or 'none')
    return True, 'all fixture files identical to the originals'


def has(rules_list, names):
    hits = [r for r in rules_list if r[1] in names]
    return hits


# ---------------------------------------------------------------- checks per eval

def blog_checks(out):
    folder = os.path.join(out, 'blog-de')
    html_src = read(os.path.join(folder, 'index.html'))
    rules = rules_of(folder)
    a = audit(folder)
    t = text_warnings(folder)

    def no_audit(names, ok_msg):
        hits = has(a, names)
        return (not hits, ok_msg if not hits else 'audit_css still reports: ' + '; '.join('%s %s' % (h[1], h[2]) for h in hits))

    m = re.search(r'<html\b[^>]*>', html_src, re.I)
    lang_ok = bool(m and re.search(r'\blang\s*=\s*["\']?de', m.group(), re.I))
    hy = decls(rules, r'hyphens')
    hy_auto = [d for d in hy if 'auto' in d[2]]
    bodies = [(r.selector, v) for r, p, v in decls(rules, r'line-height')
              if audit_css.is_body_text(r.selector) and re.fullmatch(r'\d*\.?\d+', v.strip())
              and not re.search(r'\bprint\b', ' '.join(r.context))]
    low = [(s, v) for s, v in bodies if float(v) < 1.4]
    head_break = [r.selector for r, p, v in decls(rules, r'hyphens|overflow-wrap|word-wrap')
                  if re.search(r'auto|anywhere|break-word', v)
                  and re.search(r'(^|[\s,>])(h[1-6]|body|html|article|main|\*)\b|card-title|\.content', r.selector)]
    shy = '&shy;' in html_src or '­' in html_src
    orig = visible_words(read(os.path.join(FIXTURES, 'blog-de', 'index.html')))
    new = visible_words(html_src)
    ratio = difflib.SequenceMatcher(None, orig, new, autojunk=False).ratio()
    micro = [w for w in t if w[0] == 'warn' and w[1] in ('straight-double-quote', 'abbreviation-spacing', 'spaced-hyphen', 'three-dots')]
    return {
        'index.html declares German: lang="de" on <html>':
            (lang_ok, m.group() if m else 'no <html> tag'),
        'Pinch zoom is no longer blocked by the viewport meta tag':
            no_audit({'zoom-blocked'}, 'no zoom-blocked finding'),
        'No px root font size':
            no_audit({'root-font-size-px'}, 'no root-font-size-px finding'),
        'Headline sizes are zoom-safe: no vw-only size and no clamp() above 2.5x':
            no_audit({'viewport-only-font-size', 'clamp-zoom-ratio', 'clamp-viewport-minimum'}, 'no zoom-unsafe font sizes'),
        'Automatic hyphenation is switched on (hyphens: auto)':
            (bool(hy_auto), '; '.join('%s { hyphens: %s }' % (r.selector, v) for r, _, v in hy_auto) or 'no hyphens: auto'),
        'Running text is no longer justified at phone widths, and never without hyphenation':
            no_audit({'justify-on-narrow-screens', 'justify-without-hyphens'}, 'no justification problems reported'),
        'Line length is capped in ch or em':
            no_audit({'no-measure-cap'}, 'a ch/em measure cap exists'),
        'Body text leading is at least 1.4 (unitless)':
            (bool(bodies) and not low, ('values: ' + ', '.join('%s %s' % b for b in bodies)) if bodies else 'no unitless body line-height found'),
        'text-wrap: pretty or balance is used against runts and ragged headings':
            (bool(decls(rules, r'text-wrap(-style)?')), '; '.join('%s { text-wrap: %s }' % (r.selector, v) for r, _, v in decls(rules, r'text-wrap(-style)?')) or 'none'),
        'Fixed-height card titles no longer clip text':
            no_audit({'fixed-height-text'}, 'no fixed-height-text finding'),
        'Straight quotes, z.B./d.h., spaced hyphens and "..." are corrected in the text':
            (not micro, 'check_text has no such warnings' if not micro else 'remaining: ' + '; '.join('%s "%s"' % (w[1], w[2]) for w in micro[:6])),
        'Long compounds in headings can break on phones (hyphenation or overflow-wrap reaches the headings, or &shy;)':
            (bool(head_break) or shy, ('rules: ' + ', '.join(head_break)) if head_break else ('&shy; in HTML' if shy else 'no hyphens/overflow-wrap on headings and no &shy;')),
        "The author's wording is preserved (word sequence at least 97% similar)":
            (ratio >= 0.97, 'similarity %.3f' % ratio),
    }


def report_checks(out):
    folder = os.path.join(out, 'report-print')
    rules = rules_of(folder)
    pages = [r for r in rules if r.selector.lower().startswith('@page')]
    size_ok = any(re.search(r'\bA4\b|210mm\s+297mm', v, re.I) for r in pages for p, v, _ in r.decls if p == 'size')
    margin_ok = any(p.startswith('margin') for r in pages for p, v, _ in r.decls)
    ow = decls(rules, r'orphans|widows')
    ow_vals = [(p, v.strip()) for _, p, v in ow]
    ow_ok = bool([1 for p, v in ow_vals if p == 'orphans' and v.isdigit() and int(v) >= 2]) and \
        bool([1 for p, v in ow_vals if p == 'widows' and v.isdigit() and int(v) >= 2]) and \
        not [1 for p, v in ow_vals if v == '1']
    keep = [r.selector for r, p, v in decls(rules, r'(page-)?break-after') if 'avoid' in v and audit_css.is_heading(r.selector)]
    wrappers = [r.selector for r, p, v in decls(rules, r'(page-)?break-inside') if 'avoid' in v and re.search(r'keep|section|group|block', r.selector)]
    protect = [r.selector for r, p, v in decls(rules, r'(page-)?break-inside') if 'avoid' in v]
    fig_ok = any(re.search(r'\bfigure\b', s) for s in protect) and any(re.search(r'\b(table|tr)\b', s) for s in protect)
    modern = decls(rules, r'break-before')
    cols = [(r, v) for r, p, v in decls(rules, r'column-count|columns')]
    two = all(re.match(r'\s*[12]\b', v) for _, v in cols) if cols else True
    col_hy = any('auto' in v for r, p, v in decls(rules, r'hyphens'))
    justify = [r.selector for r, p, v in decls(rules, r'text-align') if 'justify' in v]
    tab = decls(rules, r'font-variant-numeric|font-feature-settings')
    tab_ok = any('tabular' in v or 'tnum' in v for _, _, v in tab)
    resp = read(os.path.join(out, 'response.md'))
    engine = bool(re.search(r'firefox[^\n]{0,160}(widows|orphans|ignor)|(widows|orphans)[^\n]{0,160}firefox', resp, re.I))
    return {
        '@page sets A4 and explicit margins':
            (size_ok and margin_ok, '%d @page rule(s); size A4: %s; margins: %s' % (len(pages), size_ok, margin_ok)),
        'orphans and widows are at least 2 (no value of 1 left)':
            (ow_ok, ', '.join('%s: %s' % x for x in ow_vals) or 'none set'),
        'Headings are kept with their text (break-after: avoid on headings, or a keep-with-next wrapper)':
            (bool(keep or wrappers), ('headings: ' + ', '.join(keep)) if keep else (('wrappers: ' + ', '.join(wrappers)) if wrappers else 'no keep-with-next rule')),
        'Figures and tables are protected from splitting (break-inside: avoid)':
            (fig_ok, 'break-inside: avoid on ' + (', '.join(protect) or 'nothing')),
        'Uses break-before instead of only the legacy page-break-before':
            (bool(modern), ', '.join('%s { %s: %s }' % (r.selector, p, v) for r, p, v in modern) or 'only legacy properties'),
        'Columns get a workable measure: at most two columns, or hyphenation on':
            (two or col_hy, 'columns: %s; hyphens: auto present: %s' % (', '.join(v for _, v in cols) or 'none', col_hy)),
        'Justified text only together with hyphenation':
            (not justify or col_hy, 'justify on %s; hyphens: auto: %s' % (', '.join(justify) or 'nothing', col_hy)),
        'The table uses tabular figures':
            (tab_ok, ', '.join(v for _, _, v in tab) or 'no font-variant-numeric'),
        'The reply notes that Firefox ignores widows/orphans (only Chromium and WebKit honour them)':
            (engine, 'mentions Firefox together with widows/orphans' if engine else 'no note that Firefox ignores widows/orphans'),
    }


REVIEW_FIXTURE = {'review-landing-en': 'landing-en', 'review-blog-de-quick': 'blog-de', 'review-print-pages': 'report-print'}

MANUAL = {
    'german-blog-mobile': ['The reply explains the changes in German, each with its effect on reading'],
    'print-report-widows': ['The reply describes widow and orphan correctly (widow: last line alone at the top; orphan: first line alone at the bottom)'],
    'font-pairing-law-firm': [
        'The reply is in German',
        'Compares the pairs on concrete dimensions such as x-height, width or proportions, and contrast',
        "Says Playfair Display's high contrast suits display sizes, not small or long text",
        'Flags Montserrat as a weak fit for long German body text and says why',
        'Recognises Source Serif 4 and Source Sans 3 as one superfamily designed to work together',
        'Gives one clear recommendation',
        'The CSS baseline uses rem-based clamp(), a ch or em measure, unitless line-height, lang and hyphens: auto',
        'Mentions checking German glyphs or language support (ß/ẞ, „“, umlauts)',
    ],
    'review-landing-en': [
        'Flags the h1 clamp(): max/min of 3.33 exceeds 2.5 and fails 200 % zoom',
        'Flags the fixed-height .card h3 with overflow: hidden',
        'Flags word-break: break-all on .stat',
        'Flags text-wrap: balance on the long .lead paragraph',
        'Flags the straight quotes or apostrophe and the -- in the copy',
        'Flags missing tabular figures in the pricing table or counter',
        'Flags letter-spacing on the body text',
        'Credits what already works (lang, body clamp, line-height, measure, pretty and hyphens)',
        'Ends with a clear verdict',
    ],
    'review-blog-de-quick': [
        'Flags the missing lang attribute',
        'Flags blocked zoom (maximum-scale=1)',
        'Flags the vw-only h1 or the px root font size',
        'Flags justified text without hyphenation',
        'Flags the over-long measure (about 90 characters per line)',
        'Flags long German compounds overflowing on phones',
        'Stays quick: at most 8 findings',
    ],
    'review-print-pages': [
        'Flags orphans: 1 and widows: 1',
        'Flags the missing @page rule',
        'Flags headings that are not kept with their text',
        'Flags figures and tables that can split across pages',
        'Flags the legacy page-break-before',
        'Flags the narrow justified three-column text without hyphenation',
        'Gives exact target values (for example orphans 2-3, @page margins in mm)',
        'Stays within the requested focus on page and column breaks',
    ],
}


def automatic(eval_name, out):
    if eval_name == 'german-blog-mobile':
        return blog_checks(out)
    if eval_name == 'print-report-widows':
        return report_checks(out)
    if eval_name in REVIEW_FIXTURE:
        ok, ev = unchanged(out, REVIEW_FIXTURE[eval_name])
        return {'No files were modified (the review is read-only)': (ok, ev)}
    return {}


def assertion_texts(eval_name):
    return list(automatic_names.get(eval_name, [])) + MANUAL.get(eval_name, [])


automatic_names = {}


def grade_iteration(it_dir):
    manual = {}
    mpath = os.path.join(it_dir, 'manual_grades.json')
    if os.path.exists(mpath):
        manual = json.load(open(mpath, encoding='utf-8'))
    for eval_dir in sorted(d for d in os.listdir(it_dir) if d.startswith('eval-')):
        name = eval_dir[len('eval-'):]
        for config in ('with_skill', 'without_skill'):
            cdir = os.path.join(it_dir, eval_dir, config)
            if not os.path.isdir(cdir):
                continue
            for run in sorted(d for d in os.listdir(cdir) if d.startswith('run-')):
                rdir = os.path.join(cdir, run)
                out = os.path.join(rdir, 'outputs')
                auto = automatic(name, out)
                automatic_names[name] = list(auto)
                verdicts = manual.get('%s/%s' % (name, config), {})
                exps = []
                for text, (passed, evidence) in auto.items():
                    exps.append({'text': text, 'passed': bool(passed), 'evidence': evidence})
                for text in MANUAL.get(name, []):
                    if text in verdicts:
                        passed, evidence = verdicts[text]
                        exps.append({'text': text, 'passed': bool(passed), 'evidence': evidence})
                    else:
                        exps.append({'text': text, 'passed': False, 'evidence': 'needs manual grading'})
                passed = sum(e['passed'] for e in exps)
                grading = {'expectations': exps,
                           'summary': {'passed': passed, 'failed': len(exps) - passed, 'total': len(exps),
                                       'pass_rate': round(passed / len(exps), 2) if exps else 0.0}}
                # timing stays in timing.json: aggregate_benchmark reads time and tokens from there
                json.dump(grading, open(os.path.join(rdir, 'grading.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                pending = sum(1 for e in exps if e['evidence'] == 'needs manual grading')
                print('%-28s %-14s %d/%d passed%s' % (name, config, passed, len(exps), ('  (%d need manual grading)' % pending) if pending else ''))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for d in sys.argv[1:]:
        grade_iteration(d)
