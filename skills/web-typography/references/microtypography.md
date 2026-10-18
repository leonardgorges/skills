# Microtypography (German and English)

## Contents
1. Quotation marks and apostrophes
2. Dashes and hyphens
3. Spaces: no-break, narrow, and where they go
4. Numbers, units, signs
5. Figures, capitals, small caps
6. Ligatures
7. Emphasis and paragraphs
8. Hanging punctuation
9. CSS features at a glance
10. Glossary (German and English)
11. Language tags and regional variants

Rules marked † come from standard German typesetting literature (Duden, Forssman & de Jong *Detailtypografie*, Willberg & Forssman) and were not re-checked against a source for this skill.

---

## 1. Quotation marks and apostrophes

| | German (Germany, Austria) | German (Switzerland) † | English (US) | English (UK) † |
| --- | --- | --- | --- | --- |
| Double | „Text“ (U+201E, U+201C) or »Text« (U+00BB, U+00AB) | «Text» (U+00AB, U+00BB) | “Text” (U+201C, U+201D) | ‘Text’ is common for the outer level |
| Single (inner) | ‚Text‘ (U+201A, U+2018) or ›Text‹ | ‹Text› | ‘Text’ | “Text” for the inner level |
| Apostrophe | ’ (U+2019): geht’s, Hans’ Buch | ’ | ’: it’s, ’90s | ’ |

- **Never use straight quotes** " or ' in running text. They are typewriter substitutes. The exceptions are code, and the inch and foot marks ″ ′ (or straight " ' in technical context).
- German guillemets point **inwards** (»…«). Swiss ones point **outwards** («…»). Swiss German sets them without spaces †; French adds spaces.
- Watch for the "99 at the top" mistake: “Text” is English. German uses „ at the bottom and “ at the top.
- The `q` element and `quotes: auto` give language-correct quotes based on `lang`:

  ```css
  :lang(de) { quotes: "„" "“" "‚" "‘"; }
  ```

## 2. Dashes and hyphens

| Character | Name (DE / EN) | Use | Spacing |
| --- | --- | --- | --- |
| - U+002D | Bindestrich / hyphen | compounds ("E-Mail", "Hilfe-Seiten"), word breaks | none |
| – U+2013 | Halbgeviertstrich / en dash | German: **Gedankenstrich** (a parenthetical dash) | spaces on both sides: "Text – Einschub – Text" |
| – U+2013 | Bis-Strich / en dash | ranges: "1990–2000", "Mo–Fr", "S. 12–14" | none in German † |
| – U+2013 | Streckenstrich / en dash | routes: "Berlin–Hamburg" | none † |
| – U+2013 | Gegenstrich / en dash | match-ups: "Schalke – Dortmund" | spaces † |
| — U+2014 | Geviertstrich / em dash | English (US) dash: "text—aside—text"; rare in German (tables †) | none (US); UK uses a spaced en dash instead † |
| − U+2212 | Minuszeichen / minus | negative numbers, arithmetic: "−5 °C" | as in mathematics |
| ‑ U+2011 | geschützter Bindestrich / non-breaking hyphen | a hyphen that must not break: "E‑Mail-Adresse" at a critical point | none |

- Don't mix "von … –": write "von 9 bis 17 Uhr" or "9–17 Uhr", never "von 9–17 Uhr" †.
- A dash shouldn't start a line. Bind it to the preceding word with U+00A0 †.

## 3. Spaces: no-break, narrow, and where they go

| Character | HTML | Breaks? | Use |
| --- | --- | --- | --- |
| U+0020 space | ` ` | yes | normal word space |
| U+00A0 no-break space | `&nbsp;` | **no** | "S. 12", "Dr. Meier", "§ 3", the last two words of a paragraph |
| U+202F narrow no-break space | `&#8239;` | **no** | "z. B.", "d. h.", number and unit "10 kg", thousands "10 000", "50 %" |
| U+2009 thin space | `&thinsp;` | **yes** | Avoid it for groups that must stay together. It can break. |
| U+00AD soft hyphen | `&shy;` | break point | manual hyphenation |
| U+200B zero-width space | `&#8203;` | break point without a hyphen | long URLs or paths where a hyphen would mislead |
| U+200C zero-width non-joiner | `&zwnj;` | no | suppresses a ligature (section 6) |

- Use one space between sentences, never two.
- In HTML, sequences of spaces collapse anyway. In plain text and Markdown sources, still use one space.

## 4. Numbers, units, signs

| Topic | German | English |
| --- | --- | --- |
| Decimal and thousands separators | 3,5; 10 000 with U+202F (from 5 digits on, 4 digits optional †); avoid "10.000" in running text † | 3.5; 10,000 |
| Number and unit | 10 kg, 20 °C, 5 MB, 90° (an angle takes no space †) | 10 kg (SI), 20 °C |
| Percent | 50 % (DIN 5008 †) | 50% |
| Currency | 12,50 € or EUR 12,50 † | €12.50, $12.50 |
| Dimensions | 20 × 30 cm (U+00D7, not x) | 20 × 30 cm |
| Paragraph sign | § 12, §§ 12–14 (U+00A0) | § 12 |
| Dates | 16.10.2026, 16. Oktober 2026 (U+00A0 after the day) | October 16, 2026; 16 October 2026 |
| Times | 9:30 Uhr, 9.30 Uhr † | 9:30 a.m. |
| Ordinals | 1., 2. | 1st, 2nd (no superscript needed) |

## 5. Figures, capitals, small caps

- **Figures** †:
  - old-style figures (`onum`) blend into running text;
  - lining figures (`lnum`) suit capitals and headings;
  - tabular figures (`tnum`) belong in tables, prices and anything that updates live or is compared in columns;
  - proportional figures (`pnum`) suit running text.

  ```css
  .prose  { font-variant-numeric: oldstyle-nums proportional-nums; } /* only if the font has them */
  table, .price, .counter { font-variant-numeric: lining-nums tabular-nums; }
  ```
- **All caps:** only for short texts (less than a line). Track by 5–12 % (`letter-spacing: 0.05em–0.12em`). Use the `case` feature for case-sensitive punctuation such as hyphens and brackets, if the font has it (`font-feature-settings: "case"`).
- **ß in capitals:** STRASSE, or the capital ẞ (U+1E9E, part of official orthography since 2017 †). `text-transform: uppercase` produces "SS" in browsers.
- **Small caps:** only real ones (`font-variant-caps: small-caps` with a font that has `smcp`). Use `font-synthesis: none` (or `font-synthesis-small-caps: none`) to stop the browser from faking them by shrinking capitals. Fakes look too thin.
- **Tracking:** none in running lowercase text; slightly negative for large display sizes; slightly positive for very small sizes.

## 6. Ligatures

- **The German rule (Duden):** no ligature across a compound boundary. Auf|lage (no fl), Schaf|fell (no ff), Kauf|leute. A ligature is fine inside a morpheme: "Schiff", "Aufl." (the abbreviation). When in doubt, follow the spoken syllables: kniff|lig.
- **On the web,** standard ligatures (`liga`) are on by default. A browser doesn't know German morphology, so it sets "Auflage" with an fl ligature. For high-quality German text:
  - suppress ligatures at known compound boundaries with `&zwnj;` (U+200C): `Auf&zwnj;lage`; or
  - turn off `liga` for the text and keep only safe contextual alternates: `font-variant-ligatures: no-common-ligatures`. This is the safe default for German if you can't post-process the text †.
- Discretionary ligatures (`dlig`, such as "ct" or "st") are display effects only.

## 7. Emphasis and paragraphs

- **Italic** is for emphasis inside running text ("integrated" emphasis that doesn't break the texture). **Bold** is for navigational signals that should be found while scanning. Don't combine them, and don't use underlining except for links.
- **One emphasis style per level.** Too many kinds of emphasis cancel each other out.
- **Paragraphs:** either a first-line indent (about 1 em, at most 1–4 × the size) or space between paragraphs. Not both. No indent directly after a heading or other break †.
- **Kerning:** always on (`font-kerning: normal`, which browsers do by default for most text).
- **Alignment:** see line-breaking.md, section 9.

## 8. Hanging punctuation

Optical margin alignment (optischer Randausgleich) lets quotation marks, hyphens and punctuation hang slightly into the margin, so the edge looks straight.

- `hanging-punctuation: first allow-end last` is currently supported only in Safari †. Treat it as progressive enhancement.
- For pull quotes, a negative `text-indent` on the opening quotation mark achieves the hang in every browser:

  ```css
  blockquote p:first-child::before { content: open-quote; margin-left: -0.45em; }
  ```

## 9. CSS features at a glance

| Need | CSS |
| --- | --- |
| Language-aware hyphenation and quotes | `lang` attribute, `hyphens: auto`, `quotes: auto` |
| Kerning | `font-kerning: normal` |
| Figures | `font-variant-numeric: oldstyle-nums / lining-nums / tabular-nums / proportional-nums / slashed-zero` |
| Small caps | `font-variant-caps: small-caps / all-small-caps` + `font-synthesis: none` |
| Ligatures | `font-variant-ligatures: common-ligatures / no-common-ligatures / discretionary-ligatures` |
| Low-level OpenType | `font-feature-settings: "case", "ss01"` (last resort; overrides the above) |
| Optical sizes | `font-optical-sizing: auto` |
| x-height matching | `font-size-adjust: from-font` or a number |
| Hanging punctuation | `hanging-punctuation` (Safari only) |

## 10. Glossary (German and English)

| German | English | Meaning |
| --- | --- | --- |
| Ausgangszeile | last line | a paragraph's final line |
| Schusterjunge | orphan | first line of a paragraph alone at the bottom of a column or page |
| Hurenkind | widow | last line of a paragraph alone at the top of a column or page |
| (Wortwaise) | runt | single word or fragment on a paragraph's last line |
| Satzspiegel | type area | the text block on the page |
| Bund-, Kopf-, Außen-, Fußsteg | inner, top, outer, bottom margin | page margins |
| Zeilenlänge, Satzbreite | measure | line length |
| Zeilenabstand, Durchschuss | leading | baseline-to-baseline distance, or the extra space between lines |
| Laufweite | tracking | uniform letter spacing |
| Unterschneidung | kerning | spacing adjustment for specific letter pairs |
| Grauwert | texture, typographic colour | evenness of a text block's grey |
| Flattersatz / Rausatz | ragged / tight rag | left-aligned; Rausatz has a narrow rag zone and moderate hyphenation |
| Blocksatz | justified | aligned to both edges |
| Gießbach, Löcher | rivers, holes | vertical runs of white in justified text |
| Registerhaltigkeit | register | baselines align across columns and pages |
| Mediävalziffern / Versalziffern | old-style / lining figures | |
| Tabellenziffern | tabular figures | fixed-width digits |
| Kapitälchen | small caps | |
| Versalien | capitals, caps | |
| Auszeichnung | emphasis | |
| Schriftschnitt | style, weight | for example regular, italic, bold |
| Schriftsippe | superfamily | serif and sans built on the same design |
| Leserlichkeit / Lesbarkeit | legibility / readability | how well letterforms can be told apart, versus how well arranged text reads |
| Optischer Randausgleich | optical margin alignment | hanging punctuation |

## 11. Language tags and regional variants

**Why it matters:** `lang` decides the hyphenation dictionary, the marks `quotes: auto` and `<q>` produce, and the screen reader's voice. A wrong tag is worse than it looks. With `lang="en"` on German text, the browser hyphenates German words with English patterns (or not at all), and screen readers read German with English pronunciation.

- **Check the tag against the text,** not just whether it exists. `check_text.py` reports `lang-mismatch` when the text clearly reads as another language.
- **Region:**
  - `de-DE`, `de-AT` and plain `de` share the conventions in sections 1–4.
  - `de-CH` differs, see below.
  - `en-GB` and `en-US` differ in spelling and quotation style. Match the tag to the copy.
- **Passages in another language** get their own tag: `<span lang="en">…</span>`. This is the case for a quotation, a title or a term. The quotation marks around such a passage usually follow the *surrounding* language †, so put the tag on an element inside the marks: `„<span lang="en">The harbour never sleeps</span>“`. If you use `<q>`, note that its marks follow the `q` element's own language, so set `lang` on a span inside it rather than on the `q`.

**Swiss German (`de-CH`)** †

| Topic | Convention |
| --- | --- |
| Quotation marks | «…» outside, ‹…› inside, without spaces |
| ß | not used: always ss ("Strasse", "gross"). Never convert ss to ß in Swiss text |
| Amounts | `Fr. 120.–` or `CHF 120.–` for round amounts, `Fr. 12.50` with a decimal point |
| Thousands | apostrophe: `18’450` (typographically U+2019; plain ' is common). Don't convert it to `18.450` |
| Vocabulary | Swiss words such as "innert", "Velo" or "parkieren" are correct; never "correct" them |
