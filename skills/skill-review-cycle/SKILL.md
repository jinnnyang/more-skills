---
name: skill-review-cycle
description: Run a structured, evidence-based review pass on an existing skill and land the resulting optimizations in bounded, reversible commits. Use when the user asks to "review", "audit", "refactor", or "clean up" a skill, when a skill has accumulated large uncommitted changes that need a coherent landing plan, or when the user wants a second opinion on a skill's design before merging further work.
---

# Skill Review Cycle

A meta-skill for reviewing and improving other skills. The workflow here is the one that got used on `skills/hand-off/` on 2026-07-20 — evidence-first, priority-banded, one commit per band — written down so the next review doesn't devolve into "read three files, hand back seven opinions".

## When to use

Load this skill when any of these apply:

- The user asks to review, audit, critique, refactor, or clean up an existing skill.
- A skill under `skills/<name>/` has accumulated substantial uncommitted changes and needs a coherent landing plan.
- The user wants a structured second opinion on whether a skill is over-engineered, under-tested, or off-target.
- You're about to make non-trivial changes to a skill and want a written baseline captured before you touch anything.

Don't load it for these:

- Creating a brand-new skill from scratch. Use `skill-creator` for that.
- Fixing a single obvious bug. Just patch it.
- Renaming a skill or moving files around. That's a mechanical operation, not a review.

## Core principles

1. **Evidence before opinion.** Read every file in the target skill (and its uncommitted diff) before you form a single P0 / P1 / P2 recommendation. No claim goes into the report without a `file:line` citation behind it.
2. **User picks the direction, agent executes.** Every review report ends with two to four decision questions delivered through `clarify`, not through free-text prose the user has to answer manually. Once the report is written, you stop deciding priorities on your own.
3. **Atomic, reversible commits.** Each priority band (P0, P1a, P1b, and so on) lands as its own commit with its own scope, message, and diff. If P1c turns out badly, P1c reverts alone and the P0 win survives.
4. **Close the loop in writing.** Every review produces `REVIEW-<date>.md` in the target skill. Every landed optimization gets ticked `[x]` in that report. Every landed change gets an `R<n>` entry in the target skill's `DECISIONS.md`.
5. **Bounded scope.** MVP is the current skill only. If the review turns up problems in a sibling skill, log them as "out of scope, log against that skill's next review" and stop there. Scope creep is what turns a two-hour review into a two-day one.

## Workflow (7 steps)

### Step 1 · Enumerate + baseline (read-only)

Before touching anything, know what you're reviewing. Run these in parallel:

```bash
cd skills/<target-name> && find . -type f | sort
git status -- skills/<target-name>/    # uncommitted changes?
git log --oneline -20 -- skills/<target-name>/    # recent history
git diff --stat -- skills/<target-name>/   # size of pending changes
```

Then read every file. SKILL.md, PROTOCOL.md (if present), DECISIONS.md, everything under `references/`, `templates/`, and `scripts/`. Read the uncommitted diff too — that's often where the latest thinking lives before it hits main.

Don't skip files that "look boring". A 40-line `templates/task.md` can encode a design decision that half the workflow depends on.

### Step 2 · Write the review report

Create `skills/<target-name>/REVIEW-<YYYY-MM-DD>.md` from the template in `references/review-template.md`. Required sections:

- **Overall Impression** — three to five sentences, evidence-backed.
- **Optimization Plan** — P0 / P1 / P2 / P3 buckets. Each item spells out its symptom (with `file:line` citation), root cause, concrete change proposal, and estimated effort ("~30 min", "~2 hr").
- **Rejected Alternatives** — two to five items you considered and decided not to recommend. This proves the decision to leave them out was deliberate, not oversight.
- **Do NOT Change** — three to eight items explicitly out of scope, so you don't accidentally refactor them mid-landing.
- **Key Judgment Calls** — one to three decisions to ask the user before landing anything (for example: keep feature X or feature-flag it? Should the review report itself land as a doc, or stay ephemeral?).

**Priority rule of thumb:**

| Band | Trigger |
|---|---|
| P0 | New users can't understand the skill without loading references first. First-screen ergonomics. |
| P1 | Correctness or maintainability at risk (missing tests, terminology drift, hallucination surface). |
| P2 | Nice-to-have polish that raises the floor without unblocking anyone. |
| P3 | Housekeeping (`.gitattributes`, minor wording, dead-file cleanup). |

### Step 3 · Ask the user to pick a direction

Deliver the Key Judgment Calls through `clarify(question, choices)`. See `references/clarify-shapes.md` for the exact shape.

Don't move to Step 4 until you have direction on:

- Any risky new features — keep, feature-flag, or remove?
- Should the review report itself land as a doc, or stay ephemeral?
- Any items where the user disagrees with the P0 / P1 / P2 ranking you assigned?

### Step 4 · Land P0 as one commit, then push

Do P0 first. It's almost always the highest-leverage, cheapest change (first-screen ergonomics), and landing it as an atomic commit + push proves the pipeline works before you invest hours in P1.

Commit message format:

```
<type>(<skill>): <one-line summary>

- Bullet 1: what changed and why
- Bullet 2: cross-reference to REVIEW-<date>.md item
- Verification: <how to verify, if applicable>
```

Common types: `chore` (terminology / cleanup), `docs` (reference additions), `test` (new test coverage), `refactor` (code reshape without behavior change), `feat` (new capability, rare in a review cycle).

### Step 5 · Land P1 items with a user checkpoint between each

P1 items are almost always independent. Do them one at a time. Land and push each on its own, then check in with the user: "P1a done at `<sha>`, next up P1b — proceed?"

Batching P1a + P1b + P1c into one mega-commit is the classic anti-pattern here. If one breaks, all three revert together, and users hate that outcome. The cost of one extra commit is minimal; the cost of a bad mega-revert is not.

For each P1:

1. Tick `[x]` in REVIEW-<date>.md.
2. Add an `R<n>` entry in the target skill's DECISIONS.md (create the file if it doesn't exist yet).
3. Commit + push.
4. Report back with the commit SHA and a brief "here's what happened" summary.

### Step 6 · P2 and P3 are optional — user decides

By the time P0 and P1 are done, the user has already invested real time. Ask before committing to more:

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

Whatever depth you got to, close out with:

1. Tick every landed item `[x]` in REVIEW-<date>.md. Use `[/]` for partially landed items and `[-]` for anything explicitly deferred.
2. Add a "Review-cycle summary" section to REVIEW-<date>.md with the commit SHA chain.
3. Add a corresponding `## <date> — Review-cycle changes (<version>)` section to DECISIONS.md that references those commits and summarises each `R<n>` entry.
4. Commit and push the closeout.
5. Offer to save any new discoveries as their own skill (or fold them into this one). See the Meta-learning note below.

## Files in this skill

- `SKILL.md` — this file.
- `references/review-template.md` — starter markdown for the REVIEW report.
- `references/clarify-shapes.md` — exact `clarify(...)` invocations for each user-facing decision point.
- `references/priority-heuristics.md` — how to decide P0 vs P1 vs P2 when it's not obvious.

## Interaction rule

Every user-facing decision in this workflow goes through Hermes' `clarify` tool with structured `choices`. Don't enumerate options inside the question string and expect the user to type back an answer — those options belong in the `choices` array. See `references/clarify-shapes.md` for the concrete shapes.

## Meta-learning

If during a review you spot a new anti-pattern or heuristic (something like "check for terminology drift on any skill older than six months"), update `references/priority-heuristics.md` right away, before you finish the current review. A skill that doesn't self-maintain rots — that's true of the skill you're reviewing, and it's just as true of this one.
