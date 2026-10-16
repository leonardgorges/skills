# Measure, leading, scale and responsive type

## Contents
1. Measure (line length)
2. Leading (line height)
3. Type scale and hierarchy
4. Fluid sizes with `clamp()`
5. Zoom, user settings and WCAG floors
6. Long words on narrow screens
7. Containers and components
8. Tracking by size
9. Font loading and fallback metrics
10. Dark mode
11. Test matrix

---

## 1. Measure (line length)

| Source | Recommendation |
| --- | --- |
| Bringhurst (via secondary sources) | 45–75 characters, about 66 ideal, for a single column at reading sizes; 40–50 in multi-column layouts |
| Butterick, *Practical Typography* | 45–90 characters including spaces |
| WCAG 2.2, SC 1.4.8 (AAA) | ≤ 80 characters (≤ 40 for CJK), or a way for readers to get there |
| Research (Dyson; Dyson & Haselgrove 2001) | On screen, long lines (around 100 characters) are often read faster with the same comprehension, but readers prefer 45–72. About 55 is proposed as a compromise. The results depend on the reading task. |

**Why it matters:**
- If lines are too long, the return sweep to the next line gets unreliable and readers lose their place.
- If lines are too short, phrases are chopped up and you get more hyphens and a rougher rag.

For thorough reading, lean towards 55–70 characters. Scanned material tolerates longer lines.

**In CSS:**
- Cap the measure on the text container, not on the page: `.prose { max-width: 66ch; }`.
- `ch` is the advance width of the digit "0". In most text faces the average character (spaces included) is narrower, so `66ch` usually gives *more* than 66 characters per line. Measure with real text (`inspect_lines.js` reports characters per line), then adjust.
- `em` works too. As a rough guide, 30–35 em is 60–75 characters for many text faces †.
- When the measure is right, the text column is often narrower than the layout. That's correct. Put the leftover space into margins, or into a sidebar for notes and figures, rather than stretching the lines.

## 2. Leading (line height)

- **Body text:** 120–145 % of the size (Butterick). WCAG 1.4.8 (AAA) asks for at least 1.5. **A practical default is 1.5**: lower it slightly for short measures and small x-heights, raise it for long measures and large x-heights †.
- **Headings and display:** 1.05–1.25. Large type needs relatively less leading, because the same ratio would push the lines visibly apart.
- **Always unitless** (`line-height: 1.5`). Unitless values are inherited as a ratio, so children with other font sizes get correct leading. A `px` value breaks when the text size changes.
- **Paragraph spacing:** either a space between paragraphs (about 0.75–1 em, or one line) or a first-line indent of about 1 em. Not both, and no indent directly after a heading †.
- **WCAG 1.4.12 (AA) is a hard floor.** Users must be able to override:
  - line height to 1.5×,
  - paragraph spacing to 2×,
  - letter spacing to 0.12×,
  - word spacing to 0.16× the font size,

  without content being clipped or overlapping. That means no fixed heights on boxes that contain text (titles, buttons, table headers, navigation). Use `min-height` and padding, and make sure truncated text can still be read in full somewhere.

## 3. Type scale and hierarchy

- **A modular scale multiplies each size by the same ratio:** 1.2 (minor third), 1.25 (major third), 1.333 (perfect fourth), 1.414 (√2) or 1.618 (φ).
- **Smaller ratios suit small screens and dense interfaces, larger ratios suit editorial pages.** A common pattern interpolates between them, for example 1.2 at 320 px to 1.25–1.333 at 1440 px. Utopia's calculator generates such a fluid scale.
- **Use few sizes.** Typically 5–7 steps cover an entire site. Build hierarchy with size, weight, space and colour together, not with size alone.
- **Space follows proximity.** Leave clearly more space *above* a heading than below it, so the heading belongs to the text it introduces.
- **Vertical rhythm:** derive spacing from one base unit, usually the body line height in rem, and make margins multiples of it. A strict baseline grid is optional on the web. `text-box: trim-both cap alphabetic` (Chrome 133+, Safari 18.2+, Firefox 154+) trims the extra space above and below text, so its box aligns more precisely.

## 4. Fluid sizes with `clamp()`

**Formula.** The size grows linearly from `Fmin` at viewport `Vmin` to `Fmax` at viewport `Vmax` (all in px):

```
slope     b = (Fmax − Fmin) / (Vmax − Vmin)
intercept a = Fmin − b · Vmin
CSS:  clamp(Fmin/16 rem,  a/16 rem + (b·100) vw,  Fmax/16 rem)
```

Example: 16 px at 320 px, rising to 20 px at 1280 px:

```
b = 4 / 960 = 0.004167      a = 16 − 1.333 = 14.667 px = 0.9167 rem
font-size: clamp(1rem, 0.9167rem + 0.4167vw, 1.25rem);
```

**The zoom rule.** Browser zoom scales `rem` and `px` but **not** `vw`. A size made only of `vw` doesn't grow with zoom. That fails WCAG 1.4.4, which requires text to resize to 200 %.

- Testing in 2023 (Smashing Magazine) found that `clamp()` passes 200 % zoom in modern browsers when **max ≤ 2.5 × min**. The same applies to stepwise sizes set with media queries: going from 1rem to 3rem fails.
- So for very large display headings, either accept a smaller maximum, or start from a larger minimum.
- **Always use rem bounds,** never px, so the reader's font-size setting still applies.
- **Verify by zooming the real page to 200 %,** and to 500 % for headings. DevTools' computed values don't show the zoomed size.

## 5. Zoom, user settings and WCAG floors

- **Root font size:** never set `html { font-size: …px }`. It overrides the reader's default font size. `100%`, or no declaration at all, keeps it. The 62.5 % trick keeps user scaling working, but it redefines what 1rem means. Avoid it in new projects †.
- **Don't block zoom.** A `meta viewport` with `user-scalable=no` or `maximum-scale=1` stops people from zooming on mobile.
- **Floors to meet:**
  - 1.4.3: contrast of at least 4.5 : 1 for body text †.
  - 1.4.4: text resizes to 200 %.
  - 1.4.10: reflow at 320 CSS px without horizontal scrolling †.
  - 1.4.12: text-spacing overrides.
- **Body size on screen:** 15–25 px (Butterick). Start at 16 px or more, and go larger for small x-height faces or long-form reading.

## 6. Long words on narrow screens

At 320 px with 16–18 px type, a line holds only about 30–40 characters. German compounds then take up half a line.

1. **Hyphenation first:** `lang="de"` plus `hyphens: auto`, with `hyphenate-limit-chars` set as a starting value (see line-breaking.md).
2. **For URLs, email addresses and codes:** `overflow-wrap: anywhere`. It breaks only when it has to, without a hyphen.
3. **Avoid `word-break: break-all`.** It breaks *every* word anywhere, even when there's room.
4. **Watch headings.** A large fluid `h1` with a 25-character compound won't fit at 320 px. Lower the minimum size, or add `&shy;` at the compound boundary.

## 7. Containers and components

- Size type for components (cards, sidebars, teasers) by the space they actually get, not by the viewport. Use container queries (`@container`) and container units (`cqi`). A card is narrow in a three-column grid even on a large screen †.
- Give each text container its own measure cap, so the same component works full width and in a sidebar.

## 8. Tracking by size

- **Running text:** leave tracking at 0. Tracked lowercase text is harder to read and looks mannered.
- **Large display sizes:** often slightly negative, about −0.01 to −0.03 em, because the letters drift apart visually as they grow.
- **Small sizes:** slightly positive, +0.01 to +0.03 em, for legibility †.
- **All caps and small caps:** +5 to +12 % (0.05–0.12 em). Capitals are designed to sit next to lowercase letters, so on their own they look cramped.
- **Optical sizes:** variable fonts with an `opsz` axis adjust their design to the size. Keep `font-optical-sizing: auto`.

## 9. Font loading and fallback metrics

- **Fallback metrics:** use `font-display: swap` (or `optional` for body text when layout stability matters most). Match the fallback's metrics to reduce layout shift when the web font arrives. The `@font-face` descriptors `size-adjust`, `ascent-override`, `descent-override` and `line-gap-override` do this †.
- **x-height matching:** `font-size-adjust` (Chrome 127+, Firefox 118+, Safari 17+) scales a font so that its x-height matches a given ratio. `font-size-adjust: from-font` takes the ratio from the first available font. This keeps fallbacks and mixed fonts visually the same size.
- **Load only the weights and styles you use.** Each one is a file. A variable font often replaces four or more static files.

## 10. Dark mode

Light text on a dark background looks bolder and slightly larger †:
- consider a slightly lighter weight (a variable `wght` value, or a `GRAD` axis if the font has one, which changes weight without changing width);
- consider a little more leading;
- avoid pure white text on pure black, which glares.

## 11. Test matrix

| Check | How |
| --- | --- |
| Widths | 320, 375, 768, 1024 and 1440 px, plus the real container widths of components |
| Zoom | 200 % for text (WCAG 1.4.4), and 400 % for reflow at 1280 px (WCAG 1.4.10) † |
| Spacing overrides | Apply line-height 1.5, paragraph spacing 2em, letter-spacing 0.12em, word-spacing 0.16em, and look for clipping |
| Content | Real copy, including the longest German compounds, the longest headings and translated strings (German UI text often runs about 30 % longer than English †) |
| Engines | Chromium, WebKit and Firefox. Firefox has no `pretty`, `widows` or `orphans`, so make sure the page still reads well there |
| Print | The real PDF engine (see page-and-column-breaks.md) |
