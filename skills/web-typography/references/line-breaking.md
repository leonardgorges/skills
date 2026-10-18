# Line breaking, runts and hyphenation

## Contents
1. What counts as a runt
2. Why breaks go wrong: greedy versus total-fit
3. `text-wrap` by engine
4. The fix ladder in detail
5. No-break groups (German and English)
6. Binding the last words in a build step
7. Headings: breaking by sense
8. Hyphenation
9. Justified versus ragged text

---

## 1. What counts as a runt

| Case | Severity | Why |
| --- | --- | --- |
| Last line is a single word | hard | A lone word reads as an afterthought and leaves a hole in the texture. |
| Last line is the second half of a hyphenated word | hard | The reader has to reassemble the word across lines just as the paragraph ends. |
| Last line is shorter than the next paragraph's first-line indent | hard | The indent and the short line collide, and the paragraph break becomes ambiguous. |
| Last line is shorter than about ¼ of the measure | soft (tunable) | It's visible as a gap, but many typographers tolerate it in ragged text. |
| Justified text with indents and a completely full last line | soft | The end of the paragraph becomes invisible. |
| Heading with one word on its own line | hard in headings | It breaks the sense and the visual balance. |
| Heading line break inside a sense unit (article + noun, number + unit, a name) | hard in headings | The reader parses the wrong grouping first. |

Runts only matter in paragraphs of two or more lines. Judge them at the widths people actually use, which on the web means checking several.

## 2. Why breaks go wrong: greedy versus total-fit

- **Greedy** wrapping (the classic browser default) fills each line as far as it can, then breaks. It's fast, but each decision is local. A paragraph can end with one word even though a slightly different break three lines earlier would have avoided it.
- **Total-fit** wrapping (Knuth & Plass 1981, used in TeX and similar to InDesign's paragraph composer) treats every possible break as a node and every candidate line as a weighted edge. "Badness" measures how far spacing must stretch or shrink. It then picks the cheapest path through the whole paragraph.
- **Consequence:** good breaks come from looking at the whole paragraph. Patching one line often moves the problem to the next paragraph or to another width. Prefer whole-paragraph tools (`text-wrap: pretty`) and system-level changes (measure, size) over patching individual lines.

## 3. `text-wrap` by engine (as of October 2026)

| Value | Chromium (Chrome, Edge, Opera, Samsung) | WebKit (Safari) | Gecko (Firefox) |
| --- | --- | --- | --- |
| `balance` | yes; blocks of ≤ 6 lines | yes; all lines | yes; blocks of ≤ 10 lines |
| `pretty` | since 117; adjusts only the **last four lines** (short last line, hyphen at the end) | since Safari 26; evaluates the **whole paragraph** (short last line, rag, fewer hyphens) | not supported |
| `stable` | yes | yes | yes |

- **`pretty` is safe for normal running text.** Its cost depends on paragraph length, not on how many elements use it. Only very long unbroken text, or text that rewraps continuously during an animation, needs care.
- **`balance`** makes all lines roughly equal. That usually leaves the block narrower than its container. Use it for headings, captions, pull quotes and card titles. On long paragraphs it produces ragged block widths; use `pretty` there.
- **`pretty` and justified text:** in Chromium, `pretty` shortens some lines to avoid a runt, and justification then stretches those lines, so word gaps can get *wider*. Measured in a test: 8 of 14 lines with gaps over 2× without `pretty`, 11 of 14 with it, at 375 px. Measure both before keeping it on justified paragraphs.
- Use `stable` for `contenteditable` and live-editing views, so earlier lines don't jump while someone types.
- **Firefox ignores `pretty`.** Treat it as progressive enhancement. Where a runt would be serious (headlines, short intros), add a fallback from section 4.

```css
p, li, dd, figcaption, blockquote { text-wrap: pretty; }
h1, h2, h3, h4, .card-title, .lead-short { text-wrap: balance; }
[contenteditable] { text-wrap: stable; }
```

## 4. The fix ladder in detail

Prefer earlier steps. They are cheaper, hold at every width, and don't touch the content.

1. **Use the platform.** `text-wrap: pretty` or `balance`, as above. No cost in supporting browsers.
2. **Make hyphenation work.** A missing or wrong `lang` silently disables `hyphens: auto` and leaves long German compounds unbroken. That is the most common cause of runts and holes in German text. See section 8.
3. **Adjust the system.** If runts are frequent, look at the measure and size first. A measure that's too narrow for the language, or a size jump at a breakpoint, causes runts everywhere. One system change fixes them all; local patches only move them.
4. **Bind locally.**
   - A no-break space between the last two words, when the pair is short.
   - `white-space: nowrap` on a short sense group in a heading.

   Cost: the bound pair can no longer break. A long pair overflows or forces an ugly break earlier at narrow widths. Proposed limit: bind only if the pair is ≤ 15 characters (tunable), and never bind in UI strings that get translated.
5. **Suggest a copy edit.** Rephrasing can fix any break, but it's the author's call. Offer it with the reason; never apply it silently.

Avoid `<br>` in running text. It fixes one width and creates a broken line at every other. In headings, a `<br>` is acceptable only for a deliberate sense break that holds at every width. If it only suits wide layouts, hide it at narrow widths:

```css
@media (max-width: 40em) { h1 br.wide-only { display: none; } }
```

## 5. No-break groups (German and English)

Two characters do most of the work:

- `&nbsp;` (U+00A0) is a no-break space at normal width.
- `&#8239;` (U+202F) is a **narrow** no-break space.

`&thinsp;` (U+2009) is narrow but **allows** a break, so it's wrong for these groups.

| Group | German | English | Character |
| --- | --- | --- | --- |
| Number and unit | `10 kg`, `20 °C`, `5 MB` | `10 kg` | U+202F (or U+00A0) |
| Percent | `50 %` (DIN 5008 †) | `50%` (no space) | U+202F in German |
| Abbreviation with internal space | `z. B.`, `d. h.`, `u. a.`, `i. d. R.` | `e.g.` (no space) | U+202F inside |
| Page, number and figure references | `S. 12`, `Nr. 5`, `Abb. 3`, `Kap. 2`, `§ 3` | `p. 12`, `No. 5`, `Fig. 3` | U+00A0 |
| Dates | `1. Januar 2026` (at least between day and month) | `January 1` | U+00A0 |
| Titles and initials | `Dr. Meier`, `H. Schmidt` | `Dr. Smith`, `J. R. Tolkien` | U+00A0 |
| A dash shouldn't start a line † | `Wort – Einschub` binds the dash to the preceding word | same | U+00A0 before the dash |
| Thousands separator | `10 000` | `10,000` | U+202F in German |

U+202F is present in most current text fonts. If a font lacks it, the browser takes the character from a fallback font, which is usually invisible but worth a glance †.

## 6. Binding the last words in a build step

Apply this in templates, a Markdown or HTML post-processor, or at render time on the server. Don't apply it by hand in CMS content, where nobody can see or maintain the invisible characters. Run it on the last text node of each block element, not on raw HTML strings.

```js
// Bind the last two words of a block with a no-break space when the pair is short.
// maxPair is a tunable limit: longer pairs risk overflow on narrow screens.
function bindLastWords(text, maxPair = 15) {
  const m = text.match(/(\S+)[ \t]+(\S+)\s*$/);
  if (!m) return text;
  if (m[1].length + 1 + m[2].length > maxPair) return text;
  return text.slice(0, m.index) + m[1] + ' ' + m[2];
}
```

Don't run this in client-side JavaScript after load. The visible rewrap causes layout shift, and `text-wrap: pretty` does the job better where it's supported.

## 7. Headings: breaking by sense

- A heading should break where a reader would pause: between phrases, not inside "der | Verein" or "10 | Tipps" †.
- Avoid ending a heading line on an article or a short preposition ("der", "die", "im", "für", "the", "of", "to") †.
- **Tools, in order:**
  1. `text-wrap: balance`.
  2. A short `nowrap` span around a group that must stay together.
  3. A `br.wide-only` that is hidden at narrow widths.
  4. As a last resort, `&shy;` in a long compound where the right break point matters.
- **Hyphenation in headings:** prefer `hyphens: manual` with `&shy;` where needed. Automatic hyphenation in large display type is conspicuous †.
- Check every heading at the narrowest width. Large fluid headings are the main source of single-word lines on mobile.

## 8. Hyphenation

- `hyphens: auto` only works when the language is known. Set `lang` on `<html>`, and on any element in a different language (`<span lang="en">`). Browser support is broad (about 97 %), and Chrome downloads its hyphenation dictionaries per language.
- German needs hyphenation more than English because of long compounds such as "Datenschutzgrundverordnung" or "Auftragsverarbeitungsvertrag". On a narrow screen, ragged text without hyphenation tears deep holes. Justified text without hyphenation gets wide gaps and rivers.
- **Limits:**
  - `hyphenate-limit-chars: <word> <before> <after>`, for example `6 3 3` as a German starting value (⚙). Supported in Chrome/Edge 109+ and Firefox 137+, not in Safari.
  - `hyphenate-limit-lines` and `hyphenate-limit-last` (maximum consecutive hyphenated lines; no hyphen on the last line) are specified in CSS Text 4 but barely implemented †. Check these visually.
- `&shy;` (U+00AD) marks a manual break point. Use it for product names, coined words, and compounds the dictionary splits badly.
- **Never hyphenate** code, URLs, email addresses or identifiers. Use `hyphens: none`, and `overflow-wrap: anywhere` if they must break.
- **German setting rules:**
  - No more than **2–3 hyphenated lines in a row**.
  - No break that distorts the meaning, even when it's orthographically correct: "Urin-stinkt", "Anal-phabet".
  - Prefer breaking compounds at their boundaries: "Daten-schutz-grund-verordnung".
  - No single letters, and preferably at least 3 characters on each side (TUSTEP uses 3).
  - No hyphen in a paragraph's last line, and none at the end of a page or column †.

## 9. Justified versus ragged text

- **Justified text** spreads leftover space across word gaps. It needs hyphenation and a measure of about 40 characters or more. Otherwise gaps vary from line to line and line up into **rivers** of white.
- **Accessibility:** WCAG 1.4.8 (AAA) advises against full justification. Uneven gaps and rivers can make reading very hard for some people with cognitive disabilities, and tight spacing blurs word boundaries.
- **Web default:** ragged right (`text-align: start`). Justify only with `hyphens: auto`, a measure of at least 40 characters, and checks at every breakpoint. Never justify at phone widths. If a brand insists, limit it to wide screens:

  ```css
  @media (min-width: 48em) { .prose--justified { text-align: justify; hyphens: auto; } }
  ```
- **Rag quality:** a good rag alternates gently. Watch for "staircases" (lines getting steadily shorter or longer) and for single deep notches. Rausatz (tight rag: ragged with moderate hyphenation) is the classic compromise.
- **Centred text:** only for short display text such as titles, quotes or short captions. Never for running text: the ragged left edge forces the eye to hunt for each line start.
