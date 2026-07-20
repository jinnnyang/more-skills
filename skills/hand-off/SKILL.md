---
name: hand-off
description: |
  Guides the agent through a structured session closing workflow.
  Triggers when the user says "先到这", "换你上", "/handoff", or a major todo phase completes.
  Ensures that the current project state (invariants, tasks, walkthrough, and human blockers) is atomically persisted to a **scope directory** as flat-layout `context.md` / `task.md` / `walkthrough.md` / `questions.md` files.
version: 1.4.0
author: 刘工 + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-handoff, workflow, hand-off, context-transfer]
    related_skills: [take-over, plan]
---

# Session Hand-Off

Structured session-closing workflow that atomically persists project state to a **scope directory** so the next agent (or the next you) can pick up without amnesia. Self-contained: everything lives under this skill's directory.

Companion resume-side skill: `take-over` (independently installable).

---

## Mental Model (90 seconds)

A hand-off is **three actions** on a *scope directory* (usually the repo root or a subtree you're working in):

```
1.  prepare   →  script inspects scope, tells you what's next
2.  write     →  you update task.md / walkthrough.md / questions.md / context.md
3.  clean-up  →  script prunes resolved entries + archives closed questions
```

**You never decide the branch yourself** — `prepare` returns a `next_action` field with one of four values:

| `next_action` | What just happened | What you do |
| --- | --- | --- |
| `safe_to_apply` | Green path, no conflicts, no ambiguity | Write docs, run clean-up, done |
| `clarify_unsure` | Cleanup found entries it can't confidently classify | Batched `clarify` on those entries, then apply |
| `challenge_required` | Multi-hop trust health is unhealthy (see references) | Break trust cascade first (batched `clarify` on inferred invariants), re-run `prepare` |
| `halt_on_hard_conflicts` | Docs disagree with git/filesystem reality | STOP writing. Resolve conflicts, then re-run `prepare` |

Deep details live in `references/next-actions.md`. **Read `next_action` first every time**; the rest of `prepare`'s output is context for that decision.

## Happy Path (safe_to_apply branch — the common case)

Assumes scope exists (you already ran `init` or it's an ongoing project). Copy-paste template:

```bash
SKILL_DIR=<absolute path to this skill>
SCOPE=<absolute path to scope>
SESSION_ID="{session_id}"          # from your runtime
AGENT="{agent_name}"

# Step 1: preflight — read next_action from the JSON
uv run "$SKILL_DIR/scripts/reconcile.py" prepare --scope "$SCOPE" \
  --apply-soft-conflicts --session-id "$SESSION_ID" --agent "$AGENT"

# Step 2: write your four docs via write-atomic (see references/atomic-writes.md)
#   task.md         ← current todo verbatim
#   walkthrough.md  ← append `## YYYY-MM-DD — <slug>` entry
#   questions.md    ← updates to Open / Closed sections
#   context.md      ← new invariants, each with a provenance tag

# Step 3: apply cleanup
uv run "$SKILL_DIR/scripts/reconcile.py" clean-up --scope "$SCOPE" \
  --apply --session-id "$SESSION_ID"

# Step 4: ask user via clarify — commit / stage-only / leave uncommitted
```

If Step 1's `next_action` is anything other than `safe_to_apply`, jump to `references/next-actions.md` and follow the contract for that branch. Don't improvise.

## Prerequisites

- **`uv`** — required. Runs the helper via `uv run …`; inline script metadata auto-installs `pyyaml`.
- **`git`** — required for reality-check and multi-hop health.
- **Python ≥ 3.11** — resolved by uv from inline `requires-python`.

## When to Run

- User explicitly says `"先到这"` / `"换你上"` / `"handoff"`, or uses `/handoff`.
- Suggest when a major `todo` phase or implementation plan completes.
- Suggest when the agent judges its own context window is getting tight and continuing would risk losing state that isn't yet persisted here.

## Layout (flat-file)

Handoff docs live directly in the working scope directory using natural short names — the enclosing directory identifies what they describe.

```
<scope>/context.md
<scope>/task.md
<scope>/walkthrough.md
<scope>/questions.md
```

Optional docs (`plan.md`, `review.md`) may also be present. A scope is any directory where at least one of these files has YAML frontmatter with a recognised `kind`. See `references/scope-resolution.md` for scope discovery and `--scope` resolution rules.

---

## Interaction Rule

All user-facing prompts in this workflow use structured choices via `clarify` (Hermes' built-in `AskUserQuestion`). Do NOT free-text branching decisions. See `references/clarify-templates.md` for copy-pasteable `clarify()` calls covering every branch and the Git decision.

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is this SKILL.md's directory. `uv run` is inherently isolated for scripts with inline metadata — do not pass `--isolated`.

---

## Workflow

### Step 0: Bootstrap

```bash
command -v uv && command -v git
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

Decide the scope with the user; if none exists, `init` one. See `references/scope-resolution.md §Bootstrap decision matrix` for the four cases (0 / 1-at-pwd / 1-elsewhere / N scopes).

```bash
uv run <SKILL_DIR>/scripts/reconcile.py init --scope <path> \
  --agent "{agent_name}" --session-id "{session_id}" --writer hand-off
```

### Step 1: Preflight — one composite call

```bash
uv run <SKILL_DIR>/scripts/reconcile.py prepare --scope <path> \
  --apply-soft-conflicts --session-id "{session_id}" --agent "{agent_name}"
```

Read-only preflight (except SOFT conflicts are auto-appended to `questions.md`). Returns:

- `reality` — HARD conflicts (`halt`) + SOFT conflicts (auto-logged).
- `cleanup_plan` — five buckets (`clear` / `stale` / `kept` / `unsure` / `archived`).
- `health` — multi-hop trust signals: `hop_count`, `provenance_distribution`, `inferred_pct`, `untagged_pct`, verdict ∈ `{fresh, healthy, warning, unhealthy}`, `issues`, `inferred_samples`. See `PROTOCOL.md §11a`.
- `next_action` ∈ `{halt_on_hard_conflicts, challenge_required, clarify_unsure, safe_to_apply}` — the branching decision. **Read this first.** Full contract per branch in `references/next-actions.md`.
- `guidance` — `[AGENT GUIDANCE]` string for inline reading.

Cross-check the current session's real mutations before writing anything:

```bash
git status --short
git log -5 --name-only --pretty=format:'%h %s'
```

### Step 2: Update the four core docs (Atomic Write)

Write via `reconcile.py write-atomic` — never bypass with direct `open(..., "w")`. Three input patterns (`--content`, `--content-file`, stdin) in `references/atomic-writes.md`.

Update the four core documents according to their conventions in `references/document-conventions.md`:

- **`task.md`** — persist current `todo` verbatim (no summarizing).
- **`walkthrough.md`** — append dated `## YYYY-MM-DD — <slug>` entry (decisions, changes, surprises).
- **`questions.md`** — `## Open` for active items, `## Closed` for archive. Use `<!-- resolved -->` to auto-archive on next cleanup.
- **`context.md`** — additive-only invariants; **every bullet must carry a provenance tag** (`[git:*]` / `[user:*]` / `[test:*]` / `[inferred:*]` / `[unknown]`). See `references/document-conventions.md §context.md` for tag semantics and anti-patterns.

### Step 3: Cleanup — Apply

Step 1's `prepare` already produced the classification plan. Branch on `next_action` per `references/next-actions.md`. In summary:

- **`challenge_required`** → resolve first (mutates `context.md` before Step 2 write, then re-runs `prepare`).
- **`clarify_unsure`** → batched `clarify` on UNSURE items, then apply.
- **`safe_to_apply`** → apply directly.

```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --scope <path> \
  --apply --session-id "{session_id}"
```

Removes CLEAR + STALE walkthrough entries; moves ARCHIVED question entries from `## Open` to `## Closed` (permanent). UNSURE always preserved.

### Step 4: Git Decision

Ask via `clarify`: commit now / stage only / don't stage. Default commit message: `docs(handoff): session hand-off — {status}` (user can edit).

### Step 5: Final Summary

Print concise summary: files written, cleanup audit trail (N cleared, M stale, A archived, K unsure), leftover SOFT conflicts, explicit next actions for the successor agent.

---

## References (load on demand)

- `references/scope-resolution.md` — scope discovery, `--scope` rules, batch operations.
- `references/atomic-writes.md` — three `write-atomic` input patterns.
- `references/document-conventions.md` — writing rules for each of the four docs (including provenance tags).
- `references/next-actions.md` — full contract for each `next_action` branch.
- `references/clarify-templates.md` — copy-pasteable `clarify()` templates for every user-facing decision in the workflow.
- `PROTOCOL.md` — protocol reference (hand-off perspective).
- `DECISIONS.md` — design decision log (chronological revisions).
- `scripts/tests/` — pytest suite for the pure-logic parts of `reconcile.py`. Run with `uv run --with pytest --with pyyaml python -m pytest scripts/tests/ -v` before touching the classifier / health analyzer.
- `templates/` — default doc templates seeded by `init`.
