# Browser support for typographic CSS

**Checked:** October 2026, against caniuse.com and MDN. Support changes. If today's date is many months later, recheck any feature whose support decides a recommendation.

| Feature | Chromium (Chrome, Edge) | Safari (macOS, iOS) | Firefox | Notes |
| --- | --- | --- | --- | --- |
| `text-wrap: balance` | yes (≤ 6 lines) | yes (all lines) | yes (≤ 10 lines) | Baseline since March 2024 |
| `text-wrap: pretty` | 117+ (adjusts the last 4 lines) | 26+ (whole paragraph) | **no** | about 88 % global |
| `widows` / `orphans` | 25+ | 7+ | **no** | apply in multicol and print |
| `break-before` / `break-after` / `break-inside` | yes | yes | yes | how well `avoid` is honoured varies by context † |
| `hyphens: auto` | 88+ (all desktop platforms) | 5.1+ | 6+ | needs a correct `lang`; about 97 % |
| `hyphenate-limit-chars` | 109+ | **no** (Technology Preview only) | 137+ | about 78 % |
| `hyphenate-limit-lines` / `-last` / `-zone` | † barely | † (`-webkit-` partial) | † | specified in CSS Text 4; don't rely on them |
| `text-box` / `text-box-trim` | 133+ | 18.2+ | 154+ | about 87 % |
| `font-size-adjust` | 127+ | 17+ | 118+ | about 90 % |
| `hanging-punctuation` | no † | yes † | no † | Safari only |
| `font-optical-sizing` | yes | yes | yes | needs a variable font with an `opsz` axis |
| Container queries and `cqi` | yes | yes | yes | Baseline since 2023 † |
| `@page` size and margins | yes | partial † | yes | |
| `@page` margin boxes (running heads, page numbers) | recent versions † | † | no † | Paged.js, WeasyPrint and Prince support them |

## What this means in practice

- **Firefox** is the gap for paragraph quality and fragmentation (`pretty`, `widows`, `orphans`). Design so the text still reads well without them: hyphenation, a sensible measure, `break-inside: avoid` on short blocks.
- **Safari** lacks `hyphenate-limit-chars`. Its default hyphenation limits apply there.
- **Chromium's `pretty`** fixes short last lines but doesn't rebalance whole paragraphs. Safari's goes further.
