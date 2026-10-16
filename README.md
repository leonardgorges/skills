# typography-skill

Agent skills for web typography in German and English, covering HTML/CSS, multi-column layouts, print stylesheets and CSS-generated PDFs.

**Status:** draft, under construction.

## Skills

| Skill | Purpose | Triggering |
| --- | --- | --- |
| [`web-typography`](skills/web-typography/SKILL.md) | Applies and explains typographic decisions: line breaks and runts, hyphenation, measure and leading, widows and orphans across columns and pages, responsive and fluid type, typeface pairing, German and English microtypography. | Automatic, whenever Claude works on web text |
| [`review-typography`](skills/review-typography/SKILL.md) | A strict review with a fixed report: severity, before and after, why, and a verdict. | Manual only: `/review-typography` |

## Layout

```
research/                      source research the skills are distilled from
skills/web-typography/         core skill: SKILL.md, references/, scripts/, evals/
skills/review-typography/      review skill: SKILL.md, STANDARDS.md, evals/
fixtures/                      test pages with deliberate typography problems
```

Some numbers appear in both skills, such as thresholds and browser support. They live in `skills/web-typography/references/` and in `skills/review-typography/STANDARDS.md`, so update both together.

## Install (Claude Code)

Install only after testing. Once installed, the skills are active in every session, including the baseline runs of the tests.

```bash
ln -s "$PWD/skills/web-typography" ~/.claude/skills/web-typography
ln -s "$PWD/skills/review-typography" ~/.claude/skills/review-typography
```
