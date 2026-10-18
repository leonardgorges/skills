# skills

Agent skills for Claude Code and Codex, in the open [Agent Skills](https://agentskills.io/specification) format. The first set covers web typography in German and English: HTML/CSS, multi-column layouts, print stylesheets and CSS-generated PDFs.

**Status:** draft, under construction. Tested with Claude Code; Codex support follows the format and the Codex docs, but hasn't been tested in Codex yet.

## Skills

| Skill | Purpose | Triggering |
| --- | --- | --- |
| [`web-typography`](skills/web-typography/SKILL.md) | Applies and explains typographic decisions: line breaks and runts, hyphenation, measure and leading, widows and orphans across columns and pages, responsive and fluid type, typeface pairing, German and English microtypography. | Automatic, whenever the agent works on web text |
| [`review-typography`](skills/review-typography/SKILL.md) | A strict review with a fixed report: severity, before and after, why, and a verdict. | Manual only: `/review-typography` in Claude Code, `$review-typography` in Codex |

## Layout

```
research/                      source research the skills are distilled from
skills/web-typography/         core skill: SKILL.md, references/, scripts/, evals/
skills/review-typography/      review skill: SKILL.md, STANDARDS.md, agents/openai.yaml, evals/
fixtures/                      test pages with deliberate typography problems
evals/grade.py                 grading script for the test rounds
```

Some numbers appear in both skills, such as thresholds and browser support. They live in `skills/web-typography/references/` and in `skills/review-typography/STANDARDS.md`, so update both together.

## Install

Install both skills next to each other: the review skill uses the core skill's scripts from its sibling folder. Install only after testing; once installed, the skills are active in every session.

**Claude Code** reads `~/.claude/skills/`:

```bash
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/web-typography" ~/.claude/skills/web-typography
ln -s "$PWD/skills/review-typography" ~/.claude/skills/review-typography
```

**Codex** reads `~/.agents/skills/` (or `.agents/skills/` inside a repository):

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/web-typography" ~/.agents/skills/web-typography
ln -s "$PWD/skills/review-typography" ~/.agents/skills/review-typography
```

## What differs between the two tools

| | Claude Code | Codex |
| --- | --- | --- |
| Review runs only when asked | `disable-model-invocation: true` in SKILL.md | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |
| Calling the reviewer | `/review-typography path quick` | `$review-typography path quick` |
| Arguments | appended to the skill automatically | part of your message |

Each tool ignores the other's setting, so one folder works in both. The scripts need only Python 3.9 or later.
