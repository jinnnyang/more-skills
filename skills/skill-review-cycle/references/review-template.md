# REVIEW template

> Copy this file into `skills/<target-name>/REVIEW-<YYYY-MM-DD>.md` before you start writing the review. Once you're done, delete this blockquote.
>
> Every bullet you write needs to cite `file:line` or a `commit-sha`. If you can't back it up with a citation, leave it out — a review report that editorialises without evidence is worse than no report at all.

# `<skill-name>` Skill — Review <YYYY-MM-DD>

> Reviewer: `<agent model or human name>`
> Skill version reviewed: `<version from SKILL.md frontmatter>` (with `<clean | N modified + M untracked>` local changes)
> Scope: `skills/<target-name>/` only. Sister skills (`<name>`, `<name>`) are out of scope for this pass.

## Overall Impression

`<3-5 sentence honest read of the skill. Include one thing you like, one thing that concerns you, one thing you're uncertain about. Evidence-backed — cite specific files.>`

---

## Optimization Plan (priority-ordered)

### P0 · `<one-line rationale — usually first-screen ergonomics>`
- `[ ]` `<concrete change #1>`
- `[ ]` `<concrete change #2>`

**Rationale:** `<why this is P0. Cite the pain point with file:line.>`

**Estimated effort:** `<~30 min | ~1 hr | ~2 hr>`

---

### P1 · `<one-line rationale — usually correctness / maintainability>`
- `[ ]` `<concrete change>`
- `[ ]` `<concrete change>`

**Rationale:** `<...>`

**Estimated effort:** `<...>`

---

### P1 · `<second P1 group, if independent>`
`<...>`

---

### P2 · `<nice-to-have polish>`
- `[ ]` `<...>`

**Rationale:** `<...>`

---

### P3 · Housekeeping
- `[ ]` `<...>`

---

## Rejected Alternatives

Things you considered and decided not to recommend. Listing them here proves the decision was deliberate rather than an oversight:

1. **`<alternative name>`** — `<why rejected>`
2. **`<alternative>`** — `<why>`
3. **`<alternative>`** — `<why>`

---

## Do NOT Change

Explicitly out of scope for this review:

- `<file / feature>` — `<why stable>`
- `<file / feature>` — `<why stable>`
- `<file / feature>` — `<why stable>`

---

## Key Judgment Calls (deliver to user via `clarify`)

Two or three concrete decisions that block landing. Each becomes a `clarify` call with `choices`.

### Q1: `<pointed question>`

Options (these go into the `clarify` call's `choices` array, not into the question text):
- Option A — `<one-line description>`
- Option B — `<one-line description>`
- Option C — `<one-line description>`

**My recommendation:** `<A | B | C>` — `<one-sentence reason>`.

### Q2: `<pointed question>`

`<same shape>`

---

## Landing Plan

1. P0 lands as commit 1
2. P1a lands as commit 2 (after P0 pushed and user acks)
3. `<...>`

Each commit gets an `R<n>` entry in `skills/<target-name>/DECISIONS.md`.

---

## Review-cycle summary (fill in as items land)

Landed commits:
- `<sha>` — `<short desc>`
- `<sha>` — `<short desc>`

Deferred to future review:
- `<item>` — `<why deferred>`

Discovered but out of scope (log elsewhere):
- `<item>` — `<where to log>`
