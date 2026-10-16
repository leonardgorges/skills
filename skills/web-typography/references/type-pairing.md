# Choosing and pairing typefaces

## Contents
1. Basic stance
2. Dimensions to compare
3. Strategies: concord, contrast, conflict
4. Test procedure
5. Measuring x-height and equalising it
6. German and English coverage check
7. Common pitfalls
8. How to report a pairing judgement

---

## 1. Basic stance

- **Start with one family.** Weights, italics, sizes and space usually give enough hierarchy, and one family can't clash with itself.
- **Every extra family needs a role**, for example display headings, running text, data and code, or UI. If you can't name the role, the second family is decoration.
- **Two families, plus a monospace if needed.** A third needs an explicit reason (⚙; opinions differ, and some designers treat three or more as a sign the system has lost control).
- **The text face matters most.** Readers spend most of their time in running text. Choose the text face for the language, the size and the reading mode first, then choose a display face that suits it, not the other way round.

## 2. Dimensions to compare

| Dimension | What to look at | Why it matters |
| --- | --- | --- |
| Class and period | Renaissance serif, transitional, Didone, slab, grotesque, neo-grotesque, humanist sans, geometric sans, script, blackletter. DIN 16518 and Vox-ATypI are historical schemes; ATypI retired Vox in 2021 † | Faces from the same period or idea often share proportions and rhythm |
| Form principle † | **dynamic** (pen-based, humanist: modulated, open, varied widths), **static** (classicist and grotesque: vertical stress, closed, more uniform widths), **geometric** (constructed from circle and line). This follows Willberg's grouping by form principle | Sharing a principle tends towards harmony; crossing principles creates contrast, which should then be deliberate |
| Skeleton and proportions | letter widths (is "o" round or narrow?), stress axis, aperture (how open are c, e, a?) | The skeleton is what remains at text sizes once the details stop being visible |
| x-height | x-height relative to font size, and relative to cap height | It decides whether two faces look the same size at the same `font-size`, and how much leading they need |
| Contrast | difference between thick and thin strokes | High contrast (Didone) sparkles at display sizes and breaks up at small text sizes and on low-resolution screens |
| Weight and texture | the grey value of a text block at reading size, and the range of weights available | Mixed faces should produce compatible greys where they meet |
| Details | serif shape, terminals, dots (round or square), the italic's construction | Small details carry personality. Conflicting details read as noise |
| Character | formal or casual, warm or technical, historical associations | The face should fit the content and the brand, for example a law firm or a children's app |
| Technical | language coverage, OpenType features (`kern`, `liga`, `onum`, `lnum`, `tnum`, `smcp`, `case`), variable axes (`wght`, `opsz`, `GRAD`), hinting and rendering at small sizes, web licence, file size | A beautiful face without „“, ẞ or tabular figures is unusable for a German financial report |

## 3. Strategies: concord, contrast, conflict

The triad is often attributed to Robin Williams, *The Non-Designer's Design Book* †.

- **Concord (agreement):** one family, or a superfamily whose serif and sans share the same skeleton, spacing and proportions. Examples include IBM Plex, Source Serif / Source Sans, Noto, Merriweather / Merriweather Sans and Fira †. It's the lowest-risk option.
- **Contrast:** the faces differ clearly in one or two dimensions (serif against sans, high against low contrast, condensed against normal width) while **sharing structure** (similar proportions, x-height or form principle). A classic is a humanist serif with a humanist sans, which share a dynamic skeleton but differ in serifs. Assign clear roles, for example display against text.
- **Conflict (avoid):** two faces that are *similar but not the same*, such as two neo-grotesques, or two transitional serifs from different foundries. The difference is too small to read as a decision and too large to read as one face. The result looks like a mistake.

**Rule of thumb:** contrast in role, agreement in structure.

## 4. Test procedure

1. **Real sample text.** Use German *and* English, with long compounds, figures, quotation marks and a heading over two paragraphs. Never judge from the alphabet or from "Hamburgefonstiv" alone.
2. **Target sizes and the real measure.** Set the text face at the body size in the actual column, and the display face at the heading sizes, including the smallest, mobile heading size.
3. **Compare x-heights** at the same `font-size` (section 5). A large difference makes inline mixing look wrong, and makes headings and text look unrelated.
4. **Compare grey values.** Blur your eyes, or apply a CSS `filter: blur(2px)`. Do the heading and the text sit comfortably together, or does one punch a hole?
5. **Check the details** you'll need: italic, bold, figures (old-style or lining, tabular), small caps, German glyphs (section 6).
6. **Look at the hierarchy.** Is the role difference visible at a glance, and is it the *only* strong difference?
7. **Check performance.** Count the font files and their kB, and decide on variable or static. Plan fallback metrics (see measure-and-responsive.md).

## 5. Measuring x-height and equalising it

```js
// In a page where the fonts are loaded (await document.fonts.ready first).
async function fontMetrics(family) {
  await document.fonts.load(`100px "${family}"`);
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `100px "${family}"`;
  const x = ctx.measureText('x').actualBoundingBoxAscent / 100;
  const H = ctx.measureText('H').actualBoundingBoxAscent / 100;
  return { family, xHeight: +x.toFixed(3), capHeight: +H.toFixed(3), xToCap: +(x / H).toFixed(3) };
}
// e.g. Promise.all(['Source Serif 4', 'Source Sans 3'].map(fontMetrics)).then(console.table)
```

- **Typical x-height ratios:** about 0.45–0.50 is moderate (many classical serifs), and about 0.52–0.55 or more is large (many screen-oriented sans faces) †. Differences above about 0.04 are visible side by side.
- **Equalising with `font-size-adjust`** (Chrome 127+, Firefox 118+, Safari 17+): the value is the desired x-height ratio. Set it to the ratio of the primary face, and the other face is scaled to match:

  ```css
  body  { font-family: "Source Serif 4", Georgia, serif; font-size-adjust: from-font; }
  code  { font-family: "JetBrains Mono", monospace; font-size-adjust: 0.48; } /* the body font's x-height ratio */
  ```

- `from-font` takes the ratio from the first available font in the stack. It also makes fallback fonts match while the web font loads.

## 6. German and English coverage check

Paste this into a test page set in each candidate face, in regular, italic and bold:

```
Äpfel, Öl und Übermaß – „Zitat“ mit ‚innen‘ und »Guillemets« › ‹ · STRASSE / STRAẞE
Größe 1–2 %, 10 kg, z. B., 20 × 30 cm, 3,5 °C, 1 000 €, § 12, № 5, … ’s
“English quotes” and ‘single’ — em dash, 1990–2000, 0123456789 (old-style / lining)
fi fl ff ffi ffl ft · Auflage · Schifffahrt · Kaufleute
```

What to check:
- Every glyph is present. A fallback glyph shows up as a different weight or shape.
- The quotation marks are well shaped and spaced.
- ẞ exists, if capital-letter settings need it.
- The figures you need exist, via `font-variant-numeric`.
- The ligatures look right, and can be suppressed at compound boundaries ("Auf|lage", see microtypography.md).

## 7. Common pitfalls

- **A display face used for running text.** High-contrast, very narrow or very wide faces, and decorative faces, tire readers in long text. This includes Didone-style faces such as Playfair Display and wide geometric sans faces at small sizes †.
- **Two faces from the same class but different sources** (two geometric sans, two neo-grotesques). That is conflict, not contrast.
- **Wide faces with long German words.** Wide letters mean fewer characters per line, so German compounds break more often. Check runts and hyphenation at 320 px.
- **Faux styles.** If a weight or italic isn't loaded, the browser fakes it. Load the real files, or set `font-synthesis: none` and decide on purpose.
- **Too many weights.** Use three at most in one view, typically regular, an emphasis weight and a heading weight. More of them reduces the contrast between levels.
- **Ignoring the fallback.** For one to three seconds, readers see the fallback. Choose it to be similar in metrics, and adjust it (`size-adjust`, `font-size-adjust`).

## 8. How to report a pairing judgement

```markdown
**Recommendation:** <pair> (roles: <display / text / UI / code>)

| Dimension | Face A | Face B | Effect |
| --- | --- | --- | --- |
| Class / form principle | … | … | … |
| Proportions, x-height | … | … | … |
| Contrast, texture | … | … | … |
| Coverage, features | … | … | … |

**Why it works / what to watch:** two or three sentences, tied to the content and the reading mode.
**Alternatives:** one safer option (usually a superfamily) and one more expressive option, each with its trade-off.
**Verify:** the sample test from section 6, and the x-height measurement from section 5.
```

Say clearly when a judgement rests on general knowledge of the typeface rather than on a rendered test. Typefaces are sometimes revised, and names can be ambiguous.
