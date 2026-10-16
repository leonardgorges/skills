# Widows, orphans and page layout: multi-column, print and CSS-generated PDFs

## Contents
1. Terms and severity
2. Where fragmentation happens
3. CSS break controls
4. Multi-column specifics
5. Print stylesheets and `@page`
6. Page margins (Satzspiegel) for A4 and Letter
7. PDF engines differ
8. Detecting strays in a rendered page
9. Fix ladder

---

## 1. Terms and severity

| German | English | What | CSS |
| --- | --- | --- | --- |
| Schusterjunge (Waise) | orphan | first line of a paragraph alone at the **bottom** of a column or page | `orphans` |
| Hurenkind (Witwe) | widow | last line of a paragraph alone at the **top** of the next column or page | `widows` |

A German mnemonic: "Ein Hurenkind weiß nicht, wo es herkommt, ein Schusterjunge nicht, wo er hingeht." The widow doesn't know where it came from; the orphan doesn't know where it's going.

- **The widow (Hurenkind) is the worse error.** The reader starts a new page or column with a fragment and has to look back for context, which in print may mean turning the page.
- **The orphan (Schusterjunge)** sits at the end of a column. It's less disruptive, but it's very visible with indented paragraphs.
- Both are worst when the stranded line holds a single word or syllable.

**Related errors with the same cause** (content separated from its context) †:
- a heading at the bottom of a column or page, with its text on the next one;
- a hyphenated word split across a page break;
- a figure or table separated from its caption;
- a table row split across pages;
- a very short final page of a chapter or section.

## 2. Where fragmentation happens

Fragmentation means content split across columns, pages or regions:

- **Multi-column layouts** (`columns`, `column-count`, `column-width`).
- **Print**, including the browser's print dialog and print-to-PDF.
- **CSS-generated PDFs**: Puppeteer or Playwright `page.pdf()`, Paged.js, WeasyPrint, Prince.
- **Paginated views**: e-book readers, `overflow` with CSS scroll-snap paging, fixed-height cards with `line-clamp` (where a "widow" becomes a clipped first line).

A normal scrolling web page has no page breaks, so widows and orphans can't occur there.

## 3. CSS break controls

```css
p, li { orphans: 2; widows: 2; }   /* the default: a single line never strands */

@media print {
  p, li { orphans: 3; widows: 3; } /* stricter for printed documents */
  h1, h2, h3, h4 { break-after: avoid; break-inside: avoid; }
  figure, table, tr, blockquote, pre { break-inside: avoid; }
  .chapter { break-before: page; }
}
```

- `orphans` and `widows` take integers (default 2). Supported in Chrome 25+ and Safari 7+. **Firefox does not support them.**
- `break-before` and `break-after` take `auto | avoid | page | column | avoid-page | avoid-column | left | right | recto | verso`. `break-inside` takes `auto | avoid | avoid-page | avoid-column`.
- The legacy `page-break-before`, `page-break-after` and `page-break-inside` still work as aliases. Prefer the `break-*` names.
- **Keeping a heading with its text.** `break-after: avoid` isn't honoured equally everywhere †. The robust pattern wraps the heading and the start of its section together:

  ```css
  .keep-with-next { break-inside: avoid; } /* wrapper around h2 + first paragraph */
  ```

  Only do this for short groups. A tall unbreakable block leaves a large empty gap at the bottom of the previous page.

## 4. Multi-column specifics

- **Measure per column:** about 40–50 characters. Narrower columns need hyphenation, especially in German. Without it the rag gets very rough, and justified columns get rivers.
- **Columns on screens:** multi-column running text only works when a whole column fits in the viewport. Otherwise readers scroll down, then back up to the next column †. For screens, multi-column suits short items (lists, link collections, cards); long-form reading belongs in print.
- **Balancing:**
  - `column-fill: balance` (the default in continuous media) evens out column heights.
  - `column-fill: auto` fills columns one after another, which is needed for fixed-height columns.
  - In print, the last page's columns may balance differently from what you see on screen.
- `column-span: all` makes headings and figures cross all columns. Combine it with `break-after: avoid`.
- `orphans` and `widows` apply in columns in Chromium and WebKit. Because Firefox ignores them, `break-inside: avoid` on short blocks (list items, short paragraphs, figures) is the cross-browser safety net.

## 5. Print stylesheets and `@page`

```css
@page {
  size: A4;                 /* or: letter; or explicit: 210mm 297mm */
  margin: 25mm 20mm 30mm;   /* see section 6 for proportions */
}
@page :first { margin-top: 40mm; }

@media print {
  html { font-size: 10.5pt; }     /* pt is fine in print */
  nav, .no-print, video { display: none; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.85em; } /* use sparingly */
  img, svg { max-width: 100%; }
  * { print-color-adjust: exact; } /* only where colour carries meaning */
}
```

- **Running headers and page numbers** use margin boxes:

  ```css
  @page { @bottom-center { content: counter(page) " / " counter(pages); } }
  ```

  Paged.js, WeasyPrint and Prince support them. Chromium added margin boxes in recent versions; verify this in the version you use †.
- **Font size in print:** 9–12 pt for running text. Leading follows the same logic as on screen.
- **Mirrored margins** for duplex printing: use `@page :left` and `@page :right` (section 6).

## 6. Page margins (Satzspiegel) for A4 and Letter

**Classical construction, the 9 × 9 grid (Neunerteilung).** Divide the page into 9 × 9 units. The inner, top, outer and bottom margins get 1 : 1 : 2 : 2 units, so the type area is 6 × 6 units. Results are close to the golden section and to Villard's diagonal construction.

For A4 (210 × 297 mm), one unit is 23.3 mm horizontally and 33 mm vertically:

| | Inner | Top | Outer | Bottom | Type area |
| --- | --- | --- | --- | --- | --- |
| A4, 9 × 9, duplex | 23.3 mm | 33 mm | 46.7 mm | 66 mm | 140 × 198 mm |
| A4, 9 × 9, single-sided (symmetric sides) | 35 mm | 33 mm | 35 mm | 66 mm | 140 × 198 mm |

```css
@page        { size: A4; margin: 33mm 35mm 66mm; }  /* single-sided screen PDF */
@page :right { margin-left: 23.3mm; margin-right: 46.7mm; } /* duplex: recto */
@page :left  { margin-left: 46.7mm; margin-right: 23.3mm; } /* duplex: verso */
```

**Historical margin ratios** (inner : top : outer : bottom) are 2 : 3 : 4 : 6 on 2 : 3 paper and 3 : 4 : 6 : 8 on 3 : 4 paper. With a 10 mm base, 2 : 3 : 4 : 6 gives 20 / 30 / 40 / 60 mm on A4. Any such construction fits only the format it was made for.

**For reports and business documents,** classical book margins are generous. Keep the proportions rather than the absolute sizes †:
- the bottom margin the largest;
- top and inner the smallest;
- the inner margin large enough for binding when the document will be printed and bound.

**Register (Registerhaltigkeit) in print** †. Make the type area's height a whole number of lines, so the last line sits exactly on the bottom margin and facing pages and columns line up. Example: 11 pt text on 15 pt leading is 5.29 mm per line, so a 198 mm type area holds 37.4 lines. Round it to 37 lines, which is 195.8 mm, and add the difference to the bottom margin.

## 7. PDF engines differ

| Engine | `widows` / `orphans` | `break-*` | `@page` size and margins | Margin boxes, counters |
| --- | --- | --- | --- | --- |
| Chromium (Chrome print, Puppeteer, Playwright) | yes | yes | yes | recent versions †, verify |
| WebKit (Safari print) | yes | yes | partial † | † |
| Firefox print | **no** | yes | yes | no † |
| Paged.js (polyfill running in Chromium) | yes | yes | yes | yes |
| WeasyPrint | yes † | yes | yes | yes |
| Prince | yes | yes | yes | yes, the most complete |

Always test in the engine that actually produces the PDF. A print preview in a different browser proves nothing about it.

## 8. Detecting strays in a rendered page

`scripts/inspect_lines.js` measures line boxes in the live page and reports paragraphs that leave a single line at the top or bottom of a column (`column-stray`), plus runts and characters per line. The principle: every word's `Range.getClientRects()` gives its line box. Consecutive lines that move *up* mean a new column began. A fragment with fewer lines than the minimum is a stray.

**Print and PDF.** The DOM can't tell where print pages break. Use one of these:
1. **Paged.js.** It lays pages out as DOM (`.pagedjs_page`). Split paragraphs carry `data-split-from` / `data-split-to`. Count each piece's lines with the same method.
2. **Render the PDF and look at it.** Check the first and last line of every page.
3. **Emulate a column.** Temporarily give the content the type area's width and height as a multi-column box with `column-fill: auto`, then run `inspect_lines.js`. This is an approximation.

## 9. Fix ladder

Prefer the earlier, gentler steps:

1. **CSS break control.** `orphans` and `widows` of 2–3, `break-after: avoid` on headings, `break-inside: avoid` on figures and short blocks.
2. **Space.** Adjust the space around figures and headings, or let a figure float to the next page or column.
3. **Line count.** Run a facing-page pair one line long or short, *together*, so the spread stays level †. In CSS this means a local `max-height` or `margin` change on that page's content (Paged.js) or a `break-before` at a better point.
4. **Spacing.** Tiny tracking or word-spacing changes on one paragraph. Keep them invisible (around ±1 % letter-spacing); visible differences in texture are worse than the widow.
5. **The text.** Shortening or lengthening is the author's decision. Suggest it with the exact location, and never apply it silently.
