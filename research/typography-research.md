# Typography research: foundation for a typesetting skill

Status: research notes, 2026-10-16. This document is the source material that the skill's `SKILL.md` and `references/` files will be distilled from. It is not the skill itself.

**How to read the evidence markers**

- No marker: checked against a source during this research (see the source list at the end).
- **†** Standard typographic literature or practitioner knowledge, not re-checked against a source in this pass. Verify before turning it into a hard rule.
- **⚙** A working parameter proposed for the skill. It's a starting value to tune with evals, not an established typographic canon.

---

## 0. Guiding idea

Typographic rules exist to serve reading. The skill should never apply a rule mechanically. For every adjustment, the agent should be able to say:

1. **What** the problem is (for example "a single word in the last line").
2. **Why** it hurts reading or the page (for example "it leaves a hole in the text texture and makes the paragraph look like it ends twice").
3. **Which fixes** are possible, and what each one costs (for example "a non-breaking space may cause overflow on narrow screens").
4. **Which fix it chose**, and why that's the lesser evil in this context.

Typographic rules often conflict. Fixing a widow by tightening letter spacing can produce an uneven texture. Avoiding a hyphen can produce a ragged hole. So the core skill is weighing trade-offs, not ticking off rules.

Proposed priority order for resolving conflicts **⚙**:
content and meaning → reading flow → accessibility floors (WCAG) → even texture (Grauwert) and page balance → purity of individual rules.

---

## 1. Terminology (DE ↔ EN)

German and English terms don't map one to one, and the web uses "orphan" in a different sense from print. The skill must use these terms precisely.

| Phenomenon | German | English (print) | CSS |
|---|---|---|---|
| First line of a paragraph left alone at the **bottom** of a page or column | **Schusterjunge** (also Waise, Waisenzeile, Findelkind) | orphan | `orphans` |
| Last line of a paragraph left alone at the **top** of a page or column | **Hurenkind** (also Witwe, Witwenzeile) | widow | `widows` |
| A single word (or a fragment) alone in the last line of a paragraph | no established term (the de.wikipedia article names none). "Wortwaise" works as the skill's own term but should be explained when used | runt (in web writing often loosely called an "orphan") | `text-wrap: pretty` (partly) |

Mnemonic from de.wikipedia: "Ein Hurenkind weiß nicht, wo es herkommt, ein Schusterjunge nicht, wo er hingeht." In words: a widow doesn't know where it came from; an orphan doesn't know where it's going.

**Severity:** the Hurenkind (widow) is the worse error, especially when it lands on the back of a leaf, because the reader can't see the context without turning back. Both are worst when the stranded line holds only one word or syllable.

**Other core terms**

| German | English | Meaning |
|---|---|---|
| Ausgangszeile | last line | final line of a paragraph |
| Satzspiegel | type area | the area of the page that carries text |
| Stege (Bund-, Kopf-, Außen-, Fußsteg) | margins (inner, top, outer, bottom) | the space around the type area |
| Zeilenlänge, Satzbreite | measure | line length |
| Durchschuss / Zeilenabstand | leading / line spacing | extra space between lines, or baseline to baseline |
| Laufweite | tracking | uniform letter spacing |
| Unterschneidung | kerning | pair-specific spacing |
| Grauwert | texture, typographic color | overall grey value of a text block |
| Flattersatz / Rausatz | ragged right / tight rag | Rausatz = ragged with a narrow rag zone and hyphenation |
| Blocksatz | justified | aligned to both margins |
| Gießbach / Löcher | rivers / holes | vertical runs of word space in justified text |
| Registerhaltigkeit | register / baseline grid | baselines align across columns and pages |
| Mediävalziffern / Versalziffern | old-style / lining figures | |
| Proportional- / Tabellenziffern | proportional / tabular figures | |
| Kapitälchen | small caps | |
| Versalien | capitals, all caps | |
| Auszeichnung | emphasis | italic, bold, small caps and so on |
| Schriftsippe | superfamily | for example a serif and a sans built on the same skeleton |
| Leserlichkeit / Lesbarkeit † | legibility / readability | legibility of letterforms, versus readability of the arranged text |

---

## 2. Line breaking and short last lines (aims 1 and 2)

### 2.1 Why it matters

- A very short last line punches a hole into the even grey of the text block. It also makes the space between paragraphs look bigger than intended. †
- In headings and short display text, one word alone on a line breaks the text's sense and looks unbalanced.
- An uneven rag (jagged right edge, "staircases", deep holes) disturbs the eye's return sweep to the next line. †

### 2.2 What counts as a problem (proposed checks)

- **Hard:** the last line is a single word, or the fragment of a hyphenated word. ⚙
- **Hard:** the last line is shorter than the next paragraph's first-line indent. The indent and the short line then collide visually. †
- **Soft:** the last line is shorter than about **¼ of the measure**. ⚙ (Tune with evals. Some typographers tolerate shorter lines in ragged text.)
- **Soft, justified text with indents:** a completely full last line hides where the paragraph ends. †
- **Headings:** a single word on the last line, or a break inside a phrase that belongs together ("Zeilenfall nach Sinn", breaking by sense). †

### 2.3 How good line breaking works: greedy versus total-fit

- **Greedy** (the classic browser default): fill each line as far as possible, then break. It's fast, but it decides line by line and can strand a word at the end.
- **Total-fit** (Knuth & Plass 1981, used in TeX): treat every possible break point as a node and every candidate line as a weighted edge. "Badness" measures how much spacing must stretch or shrink. The algorithm picks the cheapest path through the whole paragraph. TeX runs up to three passes: first without hyphenation, then with it, then an emergency pass. InDesign's paragraph composer works on the same principle.
- **Takeaway for the skill:** good breaks come from looking at the whole paragraph. Fixing one line at a time often just moves the problem.

### 2.4 Tools on the web (as of October 2026)

**`text-wrap` / `text-wrap-style`**

| Value | Purpose | Notes |
|---|---|---|
| `wrap` | default, greedy | |
| `balance` | evens out line lengths | Short blocks only. Line limits: Chromium ≤ 6, Firefox ≤ 10 (MDN), WebKit balances all lines. Makes the block narrower than its container, which suits headlines, captions and quotes, not running text. |
| `pretty` | better breaks at some extra cost | **Chromium (since 117)** adjusts only the **last four lines**, aiming at short last lines and hyphenation at the end. **WebKit (since Safari 26)** evaluates the **whole paragraph** and improves short last lines, the rag and hyphenation. It doesn't yet handle rivers. **Firefox: not supported.** Global support about 88 % (caniuse). |
| `stable` | editable text | Earlier lines stay put while typing. |

WebKit's guidance: `pretty` is safe for typical paragraphs. Cost depends on paragraph length, not on how many elements use it. Be careful only with extremely long unbroken text and with text that rewraps continuously during animation.

```css
/* Progressive enhancement: browsers that don't support it fall back to greedy wrapping */
p, li, figcaption, blockquote { text-wrap: pretty; }
h1, h2, h3, .teaser-title   { text-wrap: balance; }
```

**Manual or robust fallbacks (needed for Firefox and for exact control)**

- A **non-breaking space** between the last two words of a paragraph (`&nbsp;` / U+00A0). The risk: on narrow screens a long word pair can no longer break and may overflow. Only bind short pairs, and do it when the page is built or rendered, not by hand inside CMS text. ⚙ Proposed limit: only when the bound pair is ≤ about 15–20 characters.
- **Word groups that must never be split** (in German): number + unit ("20 kg", "50 %"), "S. 12", "Nr. 5", "§ 3", "Abb. 4", dates ("1. Januar"), initials and abbreviations ("z. B.", "d. h.", "u. a."), title + name ("Dr. Meier"). Use a narrow no-break space U+202F (`&#8239;`) inside abbreviations and between number and unit. `&thinsp;` is wrong here because it allows a break.
- **`<span style="white-space: nowrap">`** for phrases in headings that belong together. The risk is overflow if the phrase is longer than the narrowest container.
- **Never** use `<br>` to fix a line break in responsive running text. It only works at one width. In headings, a `<br>` is only acceptable when it marks a sense break that holds at every width, or when it's scoped to a breakpoint.

### 2.5 Hyphenation (Silbentrennung)

- `hyphens: auto` only works with a correct `lang` attribute (`<html lang="de">`). Browser support is broad (about 97 %).
- **German needs hyphenation more than English** because of its long compounds ("Datenschutzgrundverordnung"). On narrow screens, a ragged layout without hyphenation tears big holes, and justified text without hyphenation produces "ugly gaps".
- Fine control:
  - `hyphenate-limit-chars: 10 4 3` sets the minimum word length and the minimum characters before and after the hyphen. Supported in Chrome/Edge 109+ and Firefox 137+, **not in Safari** (Technology Preview only).
  - `hyphenate-limit-lines` and `hyphenate-limit-last` (maximum consecutive hyphenated lines; no hyphen on the last line) are specified in CSS Text 4 but barely implemented. Treat them as hints only. †
  - `&shy;` (soft hyphen, U+00AD) for manual break points in critical words.
- Rules from German typesetting practice:
  - No more than **2–3 hyphenated lines in a row** (sources give 2–3 or 3–4).
  - **No break that distorts the meaning**, even if it's orthographically correct: "Urin-stinkt", "Anal-phabet".
  - Avoid two-letter fragments. TUSTEP, for example, uses a minimum of 3 characters on either side. †
  - No hyphen in the last line of a paragraph, and none at the end of a page or column. †
  - Ragged text needs less hyphenation than justified text. Rausatz (tight rag) uses deliberate, sparing hyphenation.

### 2.6 Justified versus ragged

- **Justified text** needs hyphenation and a long enough measure. A common working minimum is about **40 characters**, attributed to Bringhurst. Otherwise word spaces go uneven and **rivers** appear.
- WCAG 1.4.8 (AAA) advises against full justification because uneven word spaces create "rivers of white". These make reading difficult or impossible for some people with cognitive disabilities, and overly tight spacing makes word boundaries hard to see.
- **Recommendation for the web:** left-aligned ragged text as the default. Justify only with hyphenation, a long measure, and checks at every breakpoint (never on mobile widths). ⚙
- **Centred text:** sparingly. Use it for short display text, not for running text (Butterick).

---

## 3. Measure, leading and page proportions (aim 2)

### 3.1 Line length (measure)

| Source | Recommendation |
|---|---|
| Bringhurst (secondary sources) | 45–75 characters, ideally **66**, for a single column of serif text at reading sizes. Multi-column: 40–50. |
| Butterick, *Practical Typography* | 45–90 characters including spaces. |
| WCAG 2.2, 1.4.8 (AAA) | Width ≤ **80** characters (≤ 40 for CJK), or a mechanism to achieve it. |
| Research (Dyson; Dyson & Haselgrove 2001) | On screen, long lines (around 100 characters) are often read *faster* without losing comprehension, but readers *prefer* 45–72 characters. Results vary with the task; about 55 characters is offered as a compromise. Many studies have methodological weaknesses. |

**Why** †:
- Lines that are too long make the return sweep harder, so readers slip into the wrong line.
- Lines that are too short break up phrases and force more hyphens and a rougher rag.
- For text that's read thoroughly (lineares Lesen, linear reading), lean shorter. For text that's scanned, longer lines are acceptable.

**CSS:** `max-width: 65ch` is only an approximation. `ch` is the width of the digit "0". In most text faces the average character, spaces included, is narrower, so you often get noticeably more characters per line than the number suggests. Measure with real text. ⚙ Proposed default: `max-width: 60ch–70ch` on the text container, then check by counting.

### 3.2 Leading

- Body text: 120–145 % of the type size (Butterick).
- The leading WCAG 1.4.8 (AAA) asks for: at least 1.5 within a paragraph; paragraph spacing at least 1.5 times the line spacing.
- **WCAG 1.4.12 (AA, required):** the layout must survive these user overrides without losing content: line height 1.5×, paragraph spacing 2×, letter spacing 0.12×, word spacing 0.16× the type size. That means no fixed heights on text containers, and truncation always needs a way to reveal the full text.
- **Relationships** †:
  - Longer lines need more leading.
  - A large x-height needs more leading.
  - Large display sizes need relatively *less* leading (around 1.05–1.25).
- Use **unitless** `line-height` (for example `1.5`) so it scales with the type size.

### 3.3 Satzspiegel (type area) and margins

- Classical page construction: diagonal construction on the double page (Villard's figure, which approximates the golden section), or the **9×9 grid (Neunerteilung)**. In the 9×9 grid, inner, top, outer and bottom margins get 1:1:2:2 grid units. The results come close to the golden section.
- Historical margin ratios: 2:3:4:6 (on 2:3 paper) and 3:4:6:8 (on 3:4 paper). The inner margin is often half the outer margin.
- A given construction only works for one paper format.
- **Transfer to the screen** † ⚙: there is no fixed page. The equivalents are:
  - a text column with a capped measure,
  - side margins that grow with the viewport (a minimum of about 16 px on mobile),
  - vertical space that's clearly larger above a heading than below it (proximity),
  - an overall balance of the text's grey value against white space.
- **Baseline grid / Registerhaltigkeit:** in print this matters for multi-column layouts and for show-through on thin paper. On the web it's optional; a consistent rhythm unit is more practical (see 5.5). `text-box-trim` / `text-box` trims the half-leading above and below text so it aligns more precisely. Supported in Chrome 133+, Safari 18.2+ and Firefox 154+.

---

## 4. Schusterjunge and Hurenkind across page and column breaks (aim 3)

### 4.1 Where they occur

- **Print and PDF**, including CSS paged media (Paged.js, WeasyPrint, Prince †), e-book readers, multi-column layouts (`columns`), and paginated or fixed-height components (carousels, cards with `line-clamp`).
- **Continuously scrolling web pages have no page breaks**, so the concepts only apply there to columns, print stylesheets and paginated views.

### 4.2 Related break errors (same logic: content separated from its context) †

- A heading at the bottom of a page or column (keep it with the following text, ideally with at least 2–3 lines).
- A hyphen at the end of a page.
- A figure or table separated from its caption.
- A table row split across a page break.
- Very short final pages of a chapter.

### 4.3 Fixes in print (in rising order of intervention)

1. Paragraph control in the layout software ("Absatzkontrolle", "keep lines together"). In LaTeX: `\widowpenalty` and `\clubpenalty`.
2. Minimal changes to letter and word spacing, hyphenation, or line count. Caution: rules that are too strict produce visible gaps, especially in justified text.
3. Running a facing-page pair one line long or short, together (a spread should stay the same height). †
4. Shifting space around figures or headings. †
5. Changing the text (shortening or lengthening). This is possible, but typographers criticise it, and the skill should only suggest it, never do it silently.

### 4.4 Tools on the web

```css
/* Defaults are already 2. Chrome 25+ and Safari 7+ support them; Firefox does NOT. */
article { orphans: 2; widows: 2; }

@media print {
  p           { orphans: 3; widows: 3; }      /* stricter in print */
  h2, h3      { break-after: avoid; }          /* heading stays with the text */
  figure, tr  { break-inside: avoid; }
}
```

- `orphans` and `widows` work in multi-column layouts and print. Firefox ignores them, so test critical print output in Chromium or WebKit, or render it with a paged-media tool.
- **Detection in a browser** ⚙: line boxes per paragraph can be measured with `Range.getClientRects()`. You then compare the first and last line of each paragraph against column or page boundaries. This is a candidate for a script in `scripts/`.

---

## 5. Responsive typography (aim 4)

### 5.1 Basic principle

Line breaks aren't fixed on the web. **Every fix must hold at every width.** A fix that's correct at 1440 px (a `<br>`, a `nowrap` group, a hand-placed `&nbsp;`) can break the layout at 320 px. Proposed test widths ⚙: 320, 375, 768, 1024 and 1440 px, plus 200 % zoom, with real German and English text including long compounds.

### 5.2 Fluid type sizes with `clamp()`

- Browser zoom scales `rem` and `px`, but **not `vw`**. Pure `vw` sizes, or `clamp()` with a vw-dominated middle value, can fail **WCAG 1.4.4 (resize text to 200 %)**.
- **Rule from Smashing Magazine (2023):** if the **maximum size is ≤ 2.5 × the minimum size**, fluid type passes 1.4.4 in modern browsers. The same applies to step-wise sizes set with media queries: going from 1rem to 3rem fails.
- Build `clamp()` with rem values plus a small vw term, for example `clamp(1rem, 0.93rem + 0.33vw, 1.19rem)`. Calculators such as **Utopia** generate these.
- Test at 500 % zoom and measure the rendered result. DevTools doesn't show zoomed values.
- Never set the root font size (`html`) in px. It overrides the user's font-size preference.

### 5.3 Measure and container

- Cap the measure on the text container (`max-width` in `ch` or `em`), not on the page.
- For components, use container queries and `cqi` units so that type responds to the space it actually has, not to the viewport. †

### 5.4 Long words on narrow screens

- `hyphens: auto` with `lang="de"` is the first choice.
- `overflow-wrap: break-word` (or `anywhere`) is a last-resort safety net against overflow (URLs, codes). It breaks without a hyphen.

### 5.5 Type scale and rhythm

- **Modular scale:** each size is the previous size times a ratio, for example 1.2 (minor third), 1.25 (major third), 1.333 (perfect fourth), √2 or φ. ⚙ Common practice: a smaller ratio on mobile (about 1.2) and a larger one on desktop (about 1.25–1.333). Utopia interpolates between the two.
- **Vertical rhythm:** one base unit (for example the body line height in rem). Spacing and line heights are multiples of it.

### 5.6 Font loading and fallbacks

- `font-size-adjust` aligns the x-height of fallback and mixed fonts (Chrome 127+, Firefox 118+, Safari 17+).
- `@font-face` descriptors `size-adjust`, `ascent-override` and `descent-override` reduce layout shift when the web font swaps in. †

### 5.7 Dark mode †

- Light text on a dark background looks heavier. Consider a slightly lower weight or a variable-font grade axis (`GRAD`), and a little more leading.

---

## 6. Combining typefaces

### 6.1 Basic stance

- **One family is often enough.** Weights, styles, sizes and space create hierarchy. Every additional family needs a clear **role**: running text, display, data or code.
- Heuristic: **at most 2 families**, plus a monospace if needed. A third needs an explicit justification. ⚙ (Opinions differ. One source calls three or more "almost always a system that lost control".)

### 6.2 Dimensions of analysis (what an agent should compare)

| Dimension | What to check |
|---|---|
| Class / historical style | Renaissance serif, transitional, Didone, slab, grotesque, humanist sans, geometric sans and so on. (DIN 16518 and Vox-ATypI are historical schemes. ATypI retired Vox-ATypI in 2021 †) |
| Form principle † | dynamic (pen-based, humanist), static (classicist, grotesque), geometric (constructed). This follows Willberg's grouping by form principle. |
| Skeleton and proportions | letter widths, stress axis, aperture (open versus closed) |
| x-height ratio | x-height relative to cap height and size; it decides whether two faces look the same size at the same `font-size` |
| Stroke contrast and weight | thick/thin contrast; grey value at the same size |
| Details | terminals, serif shapes, shape of the dot, italic style |
| Character and period | designer, era, mood |
| Technical | language coverage (DE: ÄÖÜäöüß, ẞ, „“ ‚‘ »« –), OpenType features (`kern`, `liga`, `onum`, `lnum`, `tnum`, `smcp`), variable axes, web licence, file size |

### 6.3 Strategies

- **Concord (agreement):** the same family or superfamily (for example IBM Plex, Source). This is the lowest-risk option because the skeleton, spacing and proportions are shared.
- **Contrast:** a clear difference in one or two dimensions (for example serif against sans) **while sharing structure** (for example humanist serif with humanist sans, or similar proportions and x-height).
- **Conflict (avoid):** two faces that are *similar but not the same*, such as two grotesques with similar proportions. The difference reads as a mistake, not a decision. †

The concord / contrast / conflict triad is often attributed to Robin Williams, *The Non-Designer's Design Book*. †

### 6.4 Practical tests (the agent can run these)

1. Set the same sample text (German **and** English, with figures and punctuation) in both faces, at the target sizes.
2. Compare the x-height at the same `font-size`. Equalise it with `font-size-adjust` or by adjusting the size.
3. Compare the grey value of the two text blocks at reading size.
4. Check that italics, figures (old-style or lining, tabular) and the German special characters are present and work.
5. Set the faces side by side in the intended hierarchy (heading over body). Is the role difference obvious?
6. When mixing inside a line (for example inline code), x-height and baseline must match visually.

The output should be a recommendation with reasons along the dimensions above, plus a fallback suggestion.

---

## 7. Further essentials (microtypography)

### 7.1 German punctuation and spacing

- **Quotation marks:** „…“ (German low-high style) or »…« (guillemets pointing inward). Switzerland uses «…» (pointing outward) †. Inner quotes use ‚…‘ or ›…‹. Never use straight quotes " " or ' '.
- **Apostrophe:** ’ (U+2019), not ' or ´.
- **Dashes:**
  - Hyphen `-` in compounds, with no spaces ("Hilfe-Seiten").
  - En dash `–` with spaces as a parenthetical dash.
  - En dash without spaces for ranges ("1990–2000") †.
  - The em dash `—` is rare in German, used mainly in tables.
- **Ellipsis:** … (one character). In German, put a space before it when whole words are left out, and none when part of a word is left out. †
- **Spaces:**
  - Narrow no-break space U+202F in "z. B." and between number and unit ("357 022 km²", as a thousands separator too).
  - A normal space between number and unit is never right.
  - "50 %" with a space (DIN 5008 †).
- Multiplication sign ×, not x. One space between sentences, never multiple spaces.

### 7.2 Figures, capitals, small caps

- Old-style figures for running text and lining figures for capital settings, if the font offers both. Tabular figures in tables (`font-variant-numeric: oldstyle-nums | lining-nums tabular-nums`). †
- All caps: track by about **5–12 %** (Butterick). Use them for less than one line of text. Never track lowercase running text. †
- **Tracking depends on size.** Large display sizes often want slightly *negative* tracking, small sizes slightly *positive*, and running text stays near 0. One fixed `letter-spacing` value is wrong somewhere. For variable fonts with an `opsz` axis, use `font-optical-sizing: auto`. (Apple, WWDC 2020 "The Details of UI Typography" †)
- ß in capitals: SS, or the capital ẞ (part of official German orthography since 2017 †).
- Only use real small caps (`font-variant-caps: small-caps` with a font that has `smcp`). No synthesised ones (`font-synthesis: none`).

### 7.3 Ligatures (German rule)

- **No ligature across a compound boundary:** Auf|lage, Schaf|fell. But "Aufl." (the abbreviation) does take the ligature. When in doubt, follow the spoken syllables (Duden).
- On the web: the zero-width non-joiner (U+200C) suppresses a ligature at that point. Alternatively, control ligatures through `font-variant-ligatures`.

### 7.4 Emphasis and paragraphs

- Italic for emphasis inside running text. Bold for navigational signals. Don't combine them. No underlines except links. No faux bold or italic.
- Kerning always on (`font-kerning: normal`).
- Separate paragraphs **either** with an indent (1–4 × the type size) **or** with space (4–10 pt), never both. No indent after a heading. †
- Hanging punctuation (optical margin alignment): `hanging-punctuation` currently only works in Safari †.

### 7.5 Accessibility floors (non-negotiable)

- Contrast: WCAG 1.4.3, at least 4.5:1 for body text †.
- Resize to 200 % (1.4.4), and survive text-spacing overrides (1.4.12).
- Body size on the web: 15–25 px (Butterick). As a working value ⚙, start at 1rem ≈ 16 px or above.

---

## 8. Decision framework: why a typographic decision is right (aim 5)

### 8.1 Reading modes decide the typography †

Willberg and Forssman (*Lesetypografie*) distinguish several kinds of reading. Each calls for different priorities:

| Reading mode | Example | Typographic consequence |
|---|---|---|
| Linear | novel, long essay | calm grey value, comfortable measure, few emphasis styles, strict widow and orphan control |
| Informing (scanning) | news, landing page | clear hierarchy, short paragraphs, entry points |
| Differentiating | textbook, technical text | several clearly distinct levels of emphasis |
| Consulting | encyclopedia, documentation, tables | findability, tabular figures, consistent structure |
| Selecting | learning material | marking and selection aids |
| Activating / staged | advertising, editorial display | expressive type is allowed; rules are relaxed deliberately |

### 8.2 Pattern for reasoning (agent output)

> **Finding:** what is wrong, and where.
> **Effect on reading:** why it matters in *this* reading mode.
> **Options:** 2–3 fixes, each with its cost or risk (responsive behaviour, grey value, meaning).
> **Decision:** the chosen option and the trade-off that justifies it.
> **Check:** how it was verified (widths, zoom, browsers).

### 8.3 Tolerance depends on context ⚙

A widow in a print novel is an error. A short last line in a news teaser is acceptable. In UI text (buttons, labels), readability and robustness come before any break aesthetics.

---

## 9. Implications for the skill (first sketch)

What an agent can **check automatically** (candidates for `scripts/`):

1. **Text linter (DE/EN):**
   - quotation marks and apostrophes,
   - dashes and their spacing,
   - ellipsis,
   - missing no-break spaces (number + unit, "z. B.", "S. 12"),
   - multiple spaces.
2. **CSS audit:**
   - `lang` attribute and `hyphens`,
   - `text-wrap` on text and headings,
   - measure (`max-width`) on text containers,
   - unitless `line-height`,
   - root font size not in px,
   - `clamp()` ratio ≤ 2.5,
   - fixed heights on text containers,
   - `orphans` / `widows` / `break-*` in print styles and multi-column layouts.
3. **Render check (headless browser at several widths):**
   - characters per line,
   - short last lines (single word, or below the ¼-measure threshold),
   - widows and orphans in columns and print/PDF,
   - overflow from no-break groups,
   - a 200 % zoom test.
4. **Typeface pairing report:** measure the x-height ratio, glyph coverage and OpenType features of two font files, and render a side-by-side sample.

What remains **judgement** (the reasoning lives in `SKILL.md` and `references/`): reading mode, conflicting rules, pairing decisions, deliberate rule-breaking in display typography.

Possible reference split ⚙:
- `references/line-breaking.md` (sections 2 and 5.4)
- `references/page-breaks.md` (section 4)
- `references/measure-and-layout.md` (sections 3 and 5)
- `references/type-pairing.md` (section 6)
- `references/microtypography-de-en.md` (section 7)
- `references/browser-support.md` (all the support tables in one place, easy to update)

---

## 10. Open points and caveats

- Browser support was checked against caniuse and MDN in October 2026. It will change, which is why it belongs in one separate file.
- The Bringhurst numbers come from secondary sources. Check them against the book (4th ed., 2013) if you want to quote them exactly.
- Willberg/Forssman (*Lesetypografie*, *Erste Hilfe in Typografie*) and Forssman/de Jong (*Detailtypografie*) are the core German references. Their content isn't freely available online and was only included here from prior knowledge (†). Buying or borrowing *Detailtypografie* is worth it if the skill should be authoritative on German detail rules.
- The ⚙ thresholds (¼ measure, ≤ 15–20 characters per no-break pair, test widths) are starting values for evals.

---

## Sources

**Specifications and accessibility**
- [MDN: text-wrap](https://developer.mozilla.org/en-US/docs/Web/CSS/text-wrap)
- [MDN: widows](https://developer.mozilla.org/en-US/docs/Web/CSS/widows)
- [MDN: hyphenate-limit-chars](https://developer.mozilla.org/en-US/docs/Web/CSS/hyphenate-limit-chars)
- [CSS Text Level 4 (Editor's Draft)](https://drafts.csswg.org/css-text-4/)
- [W3C: Understanding SC 1.4.8 Visual Presentation](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html)
- [W3C: Understanding SC 1.4.12 Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)

**Browser support (caniuse, October 2026)**
- [text-wrap: pretty](https://caniuse.com/mdn-css_properties_text-wrap_pretty)
- [widows / orphans](https://caniuse.com/css-widows-orphans)
- [hyphens](https://caniuse.com/css-hyphens)
- [hyphenate-limit-chars](https://caniuse.com/mdn-css_properties_hyphenate-limit-chars)
- [text-box-trim](https://caniuse.com/css-text-box-trim)
- [font-size-adjust](https://caniuse.com/font-size-adjust)

**Line breaking**
- [WebKit: Better typography with text-wrap pretty](https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/)
- [ppc.land on Safari's text-wrap: pretty](https://ppc.land/safaris-text-wrap-pretty-brings-superior-web-typography/)
- [Knuth & Plass line-breaking Revisited](https://defoe.sourceforge.net/folio/knuth-plass.html)
- [TUGboat: line breaking article](https://TUG.org/TUGboat/tb37-3/tb117wermuth.pdf)

**Responsive and fluid type**
- [Smashing Magazine: Addressing Accessibility Concerns With Using Fluid Type](https://www.smashingmagazine.com/2023/11/addressing-accessibility-concerns-fluid-type/)
- [Adrian Roselli: Responsive Type and Zoom](https://adrianroselli.com/2019/12/responsive-type-and-zoom.html)
- [LogRocket: Fluid vs. responsive typography](https://blog.logrocket.com/fluid-vs-responsive-typography-css-clamp)

**Measure and readability**
- [Butterick: Summary of key rules](https://practicaltypography.com/summary-of-key-rules.html)
- [webtypography.net 2.1.2: Choose a comfortable measure](https://webtypography.net/2.1.2)
- [Clagnut: on measure and ch](https://clagnut.com/blog/2432/)
- [Dyson: line length review (PDF)](https://stu.westga.edu/~ssynan1/literacy/Dyson.pdf)
- [Visible Language: line length and reading from screen](https://journals.uc.edu/index.php/vl/article/view/5671)
- [Wikipedia: Line length](https://www.wikipedia.com/wiki/Line_length)

**German typography**
- [de.wikipedia: Hurenkind und Schusterjunge](https://de.wikipedia.org/wiki/Hurenkind_und_Schusterjunge)
- [de.wikipedia: Satzspiegel](https://de.wikipedia.org/wiki/Satzspiegel)
- [Macwelt: Workshop detailtypografische Regeln](https://www.macwelt.de/article/939993/workshop-detailtypografische-regeln.html)
- [Wikibooks: Hilfe:Typografie](https://de.wikibooks.org/wiki/Hilfe:Typografie)
- [Lehrerfortbildung BW: Trennung (PDF)](https://lehrerfortbildung-bw.de/st_digital/medienkompetenz/gestaltung-typografie/schrlesb/trennung/trennung.pdf)
- [Schule BW: Satzarten (PDF)](https://www.schule-bw.de/faecher-und-schularten/berufliche-schularten/berufliches-gymnasium-oberstufe/bg_tg/gestaltung-und-medientechnik/tg_gmt/GMT/gmt_lpe04_07_satzarten_fj.pdf)
- [TUSTEP documentation (PDF)](https://www.tustep.uni-tuebingen.de/bi/bi94/bi9411l1.pdf)
- [CTAN rmligs (Duden rules on ligatures)](https://ctan.org/tex-archive/support/rmligs)

**Typeface pairing**
- [Typekit: Type Study: Pairing typefaces](https://blog.typekit.com/2012/05/23/type-study-pairing-typefaces/)
- [Google Fonts Knowledge: Pairing within a family/superfamily](https://fonts.google.com/knowledge/choosing_type/pairing_typefaces_within_a_family_superfamily)
- [Made Good Designs: Font pairing guide](https://madegooddesigns.com/font-pairing/)
- [Birkhäuser: Combining Typefaces](https://birkhauser.com/en/book/9783035611137)
- [ZHdK: Übung Schriftmischung (PDF)](https://paul.zhdk.ch/pluginfile.php/214644/mod_page/content/28/CAS-Fundamentals-U%CC%88bung-Schriftmischung.pdf)

**Rhythm and scale**
- [Queensland Health Design System: spacing](https://www.design-system.health.qld.gov.au/styles/spacing/overview)
- [rhythm-sass](https://npmjs.com/package/rhythm-sass)
