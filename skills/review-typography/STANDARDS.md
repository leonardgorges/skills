# Typography review standards: values and patterns

These are the exact values to cite in findings. They mirror `web-typography/references/`, so update both together. Values marked ⚙ are starting thresholds, meant to be tuned. Values marked † come from standard literature and were not re-checked.

## Contents
1. Values
2. Smells to search for
3. Browser support summary (October 2026)
4. Terms

---

## 1. Values

### Measure and leading

| Item | Target | Flag when |
| --- | --- | --- |
| Running text, single column | 45–75 characters per line (about 66 ideal) | the median is outside 45–80, measured at 1024 or 1440 px |
| Multi-column text | 40–50 characters per line | below 35, or justified without hyphenation |
| Justified text | at least 40 characters, with `hyphens: auto` | justified on phones, or without hyphenation |
| Body leading | 1.4–1.6, unitless | below 1.3, or a px value |
| Heading leading | 1.05–1.25 | above 1.4 on large sizes, or below 1.0 |
| Paragraph separation | an indent of about 1 em **or** a space, not both | both, or an indent right after a heading † |
| Body size (screen) | at least 16 px (Butterick: 15–25 px) | below 15 px ⚙ |
| Body size (print) | 9–12 pt | below 8 pt |

### Scaling and accessibility

| Item | Target | Source |
| --- | --- | --- |
| Root font size | not set in px (`100%` or unset) | so the reader's setting applies |
| Fluid size | `clamp(min rem, rem + vw, max rem)` with **max ≤ 2.5 × min** | WCAG 1.4.4; Smashing Magazine, 2023 |
| vw-only size | never | doesn't grow with zoom (WCAG 1.4.4) |
| Zoom | never `user-scalable=no` or `maximum-scale` below 2 | WCAG 1.4.4 |
| Text spacing | survives line height 1.5×, paragraph spacing 2×, letter spacing 0.12×, word spacing 0.16× | WCAG 1.4.12 (AA) |
| Line width (AAA) | at most 80 characters, no full justification, leading of at least 1.5 | WCAG 1.4.8 |
| Text contrast | at least 4.5 : 1, or 3 : 1 for large text † | WCAG 1.4.3 |

### Line breaks and hyphenation

| Item | Value |
| --- | --- |
| Runt (hard) | the last line is one word, or a hyphenated fragment, or shorter than the next paragraph's indent |
| Runt (soft) ⚙ | the last line is shorter than 25 % of the text width |
| Heading break | a single word on its own line; a break inside a sense unit (article and noun, number and unit, a name) |
| No-break pair limit ⚙ | bind the last two words only if the pair is 15 characters or fewer |
| `hyphenate-limit-chars` ⚙ | `6 3 3` (German starting value) |
| Consecutive hyphenated lines | at most 2–3 |
| Never hyphenate | code, URLs, email addresses, identifiers, display headings (use `hyphens: manual`) † |

### Fragmentation (columns, print, PDF)

| Item | Value |
| --- | --- |
| `orphans` / `widows` | 2 minimum; 3 for printed documents; **1 is a finding** |
| Headings | `break-after: avoid`, or a keep-with-next wrapper (`break-inside: avoid` around the heading and its first paragraph) |
| Figures, tables, rows, short blocks | `break-inside: avoid` |
| Legacy properties | `page-break-*` should become `break-*` |
| Page margins (A4, 9 × 9 grid) | inner 23.3 mm, top 33 mm, outer 46.7 mm, bottom 66 mm; single-sided 35 / 33 / 35 / 66 mm |
| Columns on screen | only when a whole column fits the viewport height † |

### Typefaces

| Item | Value |
| --- | --- |
| Families | at most 2, plus a monospace; a third needs a stated role ⚙ |
| Pairing | concord (same family or superfamily) or contrast with shared structure; **conflict** (similar but not the same) is a finding |
| Weights in one view | at most about 3 † |
| Inline mixing | x-heights matched (a difference above about 0.04 of the font size is visible †); `font-size-adjust` |
| German coverage | ä ö ü ß ẞ „ “ ‚ ‘ » « – … and U+202F present in every style used |

### Microtypography

| Item | German | English |
| --- | --- | --- |
| Quotation marks | „…“ ‚…‘ or »…« ›…‹ (Switzerland «…» †) | “…” ‘…’ |
| Apostrophe | ’ | ’ |
| Dash | spaced en dash ( – ) | unspaced em dash (US) or spaced en dash (UK) † |
| Ranges | unspaced en dash: 1990–2000, Mo–Fr | unspaced en dash |
| Ellipsis | … (one character) | … |
| Abbreviation spacing | `z. B.` with U+202F | e.g. |
| Number and unit | `10 kg` with U+202F; `50 %` † | `10 kg`; `50%` |
| Thousands | `10 000` (U+202F) | `10,000` |
| References | `S. 12`, `§ 3`, `Abb. 4` with U+00A0 | `p. 12`, `Fig. 4` |
| Multiplication | `20 × 30` (U+00D7) | `20 × 30` |
| Figures | tabular in tables, prices and counters; old-style optional in running text | same |
| Capitals | tracked 5–12 %; ẞ or SS | tracked 5–12 % |
| Ligatures | none across compound boundaries (Auf\|lage) | standard |
| Swiss German (de-CH) † | «…» ‹…›, no ß (ss), `Fr. 120.–`, thousands `18’450`; never "correct" these to German conventions | — |
| Language tag | matches the content and region; foreign passages get their own `lang`; a wrong tag (`lang="en"` on German text) is a finding | same |

## 2. Smells to search for

Use these when the sibling skill's scripts aren't available (`grep -nE` or `rg`). Every hit is a candidate to confirm in context.

**HTML**
- `<html` without `lang=`: missing language. This breaks hyphenation, quotes and screen readers.
- `lang="en"` (or any tag) on text in another language: compare the tag with the text. A wrong tag breaks hyphenation, quotes and screen readers just like a missing one.
- `user-scalable *= *(no|0)|maximum-scale *= *1(\.0)?\b`: zoom blocked.
- `<br` inside a `<p>`: a manual break patch that only holds at one width.

**CSS**
- `text-align: *justify`: check for hyphenation, the measure, and narrow screens.
- `font-size: *[0-9.]+v(w|h|min|max) *[;}]`: vw-only size.
- `clamp\(`: compute max ÷ min; above 2.5 is a finding.
- `font-size: *[0-9.]+px` inside an `html` or `:root` rule: px root size.
- `line-height: *[0-9.]+px`: fixed leading.
- `letter-spacing` on `body`, `p` or `li` rules: tracked running text.
- `text-transform: *uppercase`: check the rule has letter-spacing.
- `height: *[0-9.]+(px|r?em)` together with `overflow: *hidden` in one rule: clipping under text-spacing overrides.
- `word-break: *break-all`: use `overflow-wrap: anywhere` instead.
- `(orphans|widows): *1\b`: permits stranded lines.
- `page-break-(before|after|inside)`: legacy properties.
- `column-count|columns:`: check the per-column measure, hyphenation and break control.
- `@media print` with no `@page` rule anywhere: page size and margins left to the browser.

**Text (HTML, Markdown)**
- `"[^"<>]{2,}"` outside code: straight quotation marks.
- `\b(z|d|u)\.(B|h|a)\.` (German): missing narrow no-break space in abbreviations.
- `[0-9](kg|km|cm|mm|MB|GB|°C)\b` and, in German text, `[0-9]%`: number and unit spacing.
- ` - `, `--`, `\.\.\.`: dash and ellipsis characters.

## 3. Browser support summary (October 2026)

| Feature | Chromium | Safari | Firefox |
| --- | --- | --- | --- |
| `text-wrap: balance` | yes (≤ 6 lines) | yes | yes (≤ 10 lines) |
| `text-wrap: pretty` | 117+ (last 4 lines) | 26+ (whole paragraph) | no |
| `widows` / `orphans` | yes | yes | no |
| `hyphens: auto` | yes | yes | yes |
| `hyphenate-limit-chars` | 109+ | no | 137+ |
| `font-size-adjust` | 127+ | 17+ | 118+ |
| `text-box-trim` | 133+ | 18.2+ | 154+ |
| `hanging-punctuation` | no † | yes † | no † |

If the date is much later than October 2026, recheck before citing a version.

## 4. Terms

| German | English | CSS |
| --- | --- | --- |
| Schusterjunge | orphan: first line alone at the bottom of a column or page | `orphans` |
| Hurenkind | widow: last line alone at the top of a column or page (the worse error) | `widows` |
| (Wortwaise) | runt: single word on a paragraph's last line | `text-wrap: pretty` |
| Satzspiegel | type area and margins | `@page` |
| Grauwert | texture, typographic colour | |
