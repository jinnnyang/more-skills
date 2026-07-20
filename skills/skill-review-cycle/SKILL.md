---
name: skill-review-cycle
description: Run a structured, evidence-based review pass on an existing skill and land the resulting optimizations in bounded, reversible commits. Use when the user asks to "review", "audit", "refactor", or "clean up" a skill, when a skill has accumulated large uncommitted changes that need a coherent landing plan, or when the user wants a second opinion on a skill's design before merging further work.
---

# Skill Review Cycle

A meta-skill for reviewing and improving other skills. Codifies the flow used to
review `skills/hand-off/` on 2026-07-20 so future reviews follow a consistent,
evidence-first path instead of ad-hoc "reads three files, gives seven
opinions".

## When to use

Load this skill when any of the following is true:

- The user asks to "review", "audit", "critique", "refactor", or "clean up" an existing skill.
- A skill under `skills/<name>/` has substantial uncommitted changes that need a landing plan.
- The user wants a structured second opinion on whether a skill is over-engineered, under-tested, or off-target.
- You are about to make non-trivial changes to a skill and want a written baseline before you touch anything.

Do **not** load this skill for:

- Creating a brand-new skill from scratch — use `skill-creator` instead.
- Fixing a single obvious bug — just patch it.
- Renaming a skill or moving files around — a mechanical operation, not a review.

## Core principles

1. **Evidence before opinion.** Read every file in the target skill (and its uncommitted diff) before you form a single P0/P1/P2 recommendation. No opinion without direct citation of file + line.
2. **User picks the direction, agent executes.** The review report ends with 2-4 concrete decision questions delivered via `clarify` — never free-text choice enumeration in prose. You do not decide priorities on your own once the report is written.
3. **Atomic, reversible commits.** Each priority band (P0, P1a, P1b, ...) lands as an independent commit with its own scope, message, and verifiable diff. If we hate P1c, we revert P1c alone — the P0 win survives.
4. **Close the loop in writing.** Every review produces a `REVIEW-<date>.md` in the target skill. Every optimization landed ticks a `[x]` in that report. Every landed change gets an `R<n>` entry in the target skill's `DECISIONS.md`.
5. **Bounded scope.** MVP is optimization of the current skill only. If review uncovers issues in *another* skill, note it as "out of scope, log as issue for that skill's next review" — do not scope-creep.

## Workflow (7 steps)

### Step 1 · Enumerate + baseline (read-only)

Before touching anything, know what you're reviewing. Run these in parallel:

```bash
cd skills/<target-name> && find . -type f | sort
git status -- skills/<target-name>/    # uncommitted changes?
git log --oneline -20 -- skills/<target-name>/    # recent history
git diff --stat -- skills/<target-name>/   # size of pending changes
```

Then read **every file** — SKILL.md, PROTOCOL.md (if present), DECISIONS.md, all `references/`, all `templates/`, all `scripts/`. **Read the uncommitted diff too**, because it usually contains the latest thinking that hasn't hit main yet.

**Do not skip files** because they "look boring". A 40-line `templates/task.md` can encode a critical design decision.

### Step 2 · Write the review report

Create `skills/<target-name>/REVIEW-<YYYY-MM-DD>.md`. Use the template in `references/review-template.md`. Required sections:

- **Overall Impression** — 3-5 sentences, evidence-backed.
- **Optimization Plan** — P0 / P1 / P2 / P3 buckets. Each item has:
  - Symptom (with file + line citation)
  - Root cause
  - Concrete change proposal
  - Estimated effort ("~30 min", "~2 hr")
- **Rejected Alternatives** — 2-5 items you *considered* and decided NOT to recommend. This proves you thought about them rather than missed them.
- **Do NOT Change** — 3-8 items explicitly out of scope, so you don't accidentally refactor them during landing.
- **Key Judgment Calls** — 1-3 decision questions to ask the user before landing anything (e.g., "keep feature X or feature-flag it?", "should the report itself land as a doc or stay in-chat?").

**Priority rule of thumb:**

| Band | Trigger |
|---|---|
| P0 | New users can't understand the skill without loading references first. First-screen ergonomics. |
| P1 | Correctness / maintainability at risk (missing tests, terminology drift, hallucination surface). |
| P2 | Nice-to-have polish that raises floor of quality but no user is blocked. |
| P3 | Housekeeping (`.gitattributes`, minor wording, dead-file cleanup). |

### Step 3 · Ask the user to pick a direction

Deliver the Key Judgment Calls via `clarify(question, choices)`. See `references/clarify-shapes.md` for the exact shape.

**Do not proceed to Step 4 until you have direction on:**
- Are we keeping / feature-flagging / removing risky new features?
- Should the REVIEW report itself land as a doc, or stay ephemeral?
- Are there items where you disagree with the P0/P1/P2 ranking?

### Step 4 · Land P0 as one commit, then push

Do P0 first — it's usually the highest-leverage, cheapest change (first-screen ergonomics). Land it as an atomic commit + push. This proves the pipeline works before you spend hours on P1.

Commit message format:

```
<type>(<skill>): <one-line summary>

- Bullet 1: what changed and why
- Bullet 2: cross-reference to REVIEW-<date>.md item
- Verification: <how to verify, if applicable>
```

Common types: `chore` (terminology / cleanup), `docs` (reference additions), `test` (new test coverage), `refactor` (code reshape without behavior change), `feat` (new capability — rare in a review cycle).

### Step 5 · Land P1 items — pause between each for user checkpoint

P1 items are almost always independent. Do them **one at a time**, land + push after each, then update the user with a "P1a done, next up P1b — proceed?" checkpoint.

**Anti-pattern:** batching P1a + P1b + P1c into one mega-commit. If one breaks, all three revert. Users hate that. Cost of one extra commit is minimal.

For each P1:
1. Tick `[x]` in REVIEW-<date>.md
2. Add an `R<n>` entry in the target skill's DECISIONS.md (or create DECISIONS.md if missing)
3. Commit + push
4. Report back with commit SHA and brief "here's what happened" summary

### Step 6 · P2 and P3 are optional — user decides

By the time P0 + P1 are done, the user has invested significant time. Ask:

```
clarify(
    question=(
        "P0/P1 all landed. Remaining backlog:\n"
        "  P2 items: <count>\n"
        "  P3 items: <count>\n"
        "Continue, pause, or wrap up?"
    ),
    choices=[
        "Continue — knock out P2 and P3 in one go",
        "P2 only — leave P3 for later",
        "Wrap up — mark P2/P3 as backlog in REVIEW-<date>.md and stop",
    ],
)
```

### Step 7 · Close the loop

Regardless of how far you got:

1. Tick every landed item `[x]` in REVIEW-<date>.md; use `[/]` for partial, `[-]` for explicitly deferred.
2. Add a final "Review-cycle summary" section to REVIEW-<date>.md with the commit SHA chain.
3. Add a corresponding "## <date> — Review-cycle changes (<version>)" section to DECISIONS.md that references those commits and summarises each R<n> entry.
4. Commit + push the closeout.
5. Offer to save any new discoveries as their own skill (or update this one) — see the "Meta-learning" section below.

## Files in this skill

- `SKILL.md` — this file.
- `references/review-template.md` — starter markdown for the REVIEW report.
- `references/clarify-shapes.md` — exact `clarify(...)` invocations for each user-facing decision point.
- `references/priority-heuristics.md` — how to decide P0 vs P1 vs P2 when in doubt.

## Interaction rule

All user-facing decisions in this workflow go through Hermes' `clarify` tool (structured choices). Never enumerate options in prose and expect the user to pick — the choices go in the `choices` array. See `references/clarify-shapes.md`.

## Meta-learning

If during a review you discover a new anti-pattern or heuristic (e.g. "always check for terminology drift on skills > 6 months old"), update this skill's `references/priority-heuristics.md` immediately — don't wait for the next review. Skills that don't self-maintain rot.
