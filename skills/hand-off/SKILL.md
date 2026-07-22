---
name: hand-off
description: |
  Close a session cleanly so whoever picks up next doesn't have to reverse-engineer where things stood.
  Triggers when the user says "先到这", "换你上", "/handoff", or a major todo phase completes.
  Writes what the session actually knows — invariants, current todo, decisions, open blockers — as flat `context.md` / `task.md` / `walkthrough.md` / `questions.md` files under a scope directory.
version: 1.4.0
author: 刘工 + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-handoff, workflow, hand-off, context-transfer]
    related_skills: [take-over, plan]
---

# Session Hand-Off

Close a session cleanly so whoever picks up next — another agent, or you next Tuesday — doesn't have to reverse-engineer where things stood. This skill writes the current state down atomically to a **scope directory** and prunes what's already resolved. Everything it needs lives under this skill's own directory.

Sister skill for the resume side: `take-over` (install separately).

---

## Mental Model (90 seconds)

Three actions on a *scope directory* (usually the repo root, or a subtree you're working inside):

```
1.  prepare   →  script inspects the scope and tells you what's next
2.  write     →  you update task.md / walkthrough.md / questions.md / context.md
3.  clean-up  →  script prunes resolved entries and archives closed questions
```

You don't guess which branch to take. `prepare` returns a `next_action` field with one of four values:

| `next_action` | What just happened | What you do |
| --- | --- | --- |
| `safe_to_apply` | Green path — no conflicts, no ambiguity | Write the docs, run clean-up, done |
| `clarify_unsure` | Cleanup found entries it can't confidently classify | Batched `clarify` on those entries, then apply |
| `challenge_required` | Multi-hop trust health came back unhealthy (see references) | Break the trust cascade first (batched `clarify` on inferred invariants), then re-run `prepare` |
| `halt_on_hard_conflicts` | The docs disagree with what git and the filesystem actually show | Stop writing. Resolve the conflicts, then re-run `prepare` |

Deeper details are in `references/next-actions.md`. Read `next_action` before anything else. The rest of `prepare`'s output is context for that one decision.

## Happy Path (the `safe_to_apply` branch — most common case)

This assumes a scope already exists (you ran `init` on a previous session, or the project has been carrying one). Fill in the variables and run:

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
#
# Pass --scope "$SCOPE" on every write-atomic call — refuses out-of-scope
# writes so a shell-quoting slip can't clobber files outside the scope.
# Add --stamp-frontmatter --writer hand-off --agent "$AGENT" \
#     --session-id "$SESSION_ID" to auto-update last_updated / last_verified /
# last_writer / last_agent / session_id instead of hand-maintaining them.

# Step 3: apply cleanup
uv run "$SKILL_DIR/scripts/reconcile.py" clean-up --scope "$SCOPE" \
  --apply --session-id "$SESSION_ID"

# Step 4: ask user via clarify — commit / stage-only / leave uncommitted
```

If Step 1's `next_action` is anything other than `safe_to_apply`, open `references/next-actions.md` and follow the contract for that branch. This isn't a place to improvise — the branches encode conflict-handling that took real hallucination pain to figure out.

> **Windows / git-bash note.** All examples use forward slashes even when pointing at Windows paths (`C:/Users/...` not `C:\Users\...`). Backslashes combine badly with `$var` inside bash double quotes and can silently write files outside the scope. See `references/atomic-writes.md#windows-path-pitfalls` for the trap and how `--scope` on `write-atomic` guards against it.

## Prerequisites

- **`uv`** — required. Runs the helper via `uv run …`; inline script metadata auto-installs `pyyaml`.
- **`git`** — required for reality-check and multi-hop health.
- **Python ≥ 3.11** — resolved by uv from inline `requires-python`.

## When to Run

- User explicitly says `"先到这"` / `"换你上"` / `"handoff"`, or uses `/handoff`.
- Suggest when a major `todo` phase or implementation plan completes.
- Suggest when your own context window is getting tight and there's session state that isn't written down yet — better to hand off now than to lose it.

## Layout (flat-file)

Handoff docs live directly in the working scope directory using natural short names. The enclosing directory identifies what they describe.

```
<scope>/context.md
<scope>/task.md
<scope>/walkthrough.md
<scope>/questions.md
```

Optional docs (`plan.md`, `review.md`) may also be present. A scope is any directory where at least one of these files has YAML frontmatter with a recognised `kind`. See `references/scope-resolution.md` for scope discovery and `--scope` resolution rules.

---

## Interaction Rule

Every user-facing decision in this workflow goes through Hermes' `clarify` tool with structured `choices`. No free-text "type A, B, or C" prompts. See `references/clarify-templates.md` for copy-pasteable calls covering each branch and the Git decision at the end.

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …`, where `<SKILL_DIR>` resolves to the directory holding this SKILL.md. `uv run` isolates the environment on its own when the script carries inline metadata, so skip `--isolated`.

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

Before you write anything, sanity-check what this session actually changed on disk:

```bash
git status --short
git log -5 --name-only --pretty=format:'%h %s'
```

### Step 2: Update the four core docs (Atomic Write)

Always write through `reconcile.py write-atomic`. A direct `open(..., "w")` skips the concurrency lock and the frontmatter preservation, and both of those matter more than they sound. Three input patterns (`--content`, `--content-file`, stdin) are in `references/atomic-writes.md`.

Then update the four documents following the conventions in `references/document-conventions.md`:

- **`task.md`** — the current `todo` list, verbatim. No summarising.
- **`walkthrough.md`** — append a dated `## YYYY-MM-DD — <slug>` entry covering decisions, changes, and anything surprising.
- **`questions.md`** — `## Open` for what's active, `## Closed` for the archive. Mark resolved entries with `<!-- resolved -->` and the next cleanup pass moves them for you.
- **`context.md`** — additive only, and every bullet carries a provenance tag (`[git:*]` / `[user:*]` / `[test:*]` / `[inferred:*]` / `[unknown]`). See `references/document-conventions.md §context.md` for what each tag means and where they tend to go wrong.

### Step 3: Cleanup — Apply

Step 1 already produced the classification plan. Pick the branch from `next_action` and follow `references/next-actions.md`. Short version:

- **`challenge_required`** — resolve first. This mutates `context.md` before Step 2's writes, then re-runs `prepare`.
- **`clarify_unsure`** — batched `clarify` on the UNSURE items, then apply.
- **`safe_to_apply`** — apply directly.

```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --scope <path> \
  --apply --session-id "{session_id}"
```

Cleanup deletes CLEAR and STALE walkthrough entries, moves ARCHIVED question entries from `## Open` into `## Closed` (permanent), and leaves UNSURE alone.

### Step 4: Git Decision

Ask the user through `clarify`: commit now, stage only, or leave things unstaged. The default commit message is `docs(handoff): session hand-off — {status}`, which the user can edit.

### Step 5: Final Summary

End with a short, concrete recap: which files got written, the cleanup audit trail (N cleared, M stale, A archived, K unsure), any SOFT conflicts left in `questions.md`, and the next actions the successor agent should pick up.

---

## References

Load these on demand. You don't need any of them for a `safe_to_apply` run.

- `references/scope-resolution.md` — scope discovery, `--scope` rules, batch operations.
- `references/atomic-writes.md` — the three `write-atomic` input patterns.
- `references/document-conventions.md` — writing rules for each of the four docs, including provenance tags.
- `references/next-actions.md` — the full contract for every `next_action` branch.
- `references/clarify-templates.md` — copy-pasteable `clarify()` calls for every user-facing decision in the workflow.
- `PROTOCOL.md` — the protocol reference, hand-off perspective.
- `DECISIONS.md` — chronological design decision log.
- `scripts/tests/` — pytest suite for the pure-logic parts of `reconcile.py`. Run `uv run --with pytest --with pyyaml python -m pytest scripts/tests/ -v` before you touch the classifier or the health analyzer.
- `templates/` — default doc templates seeded by `init`.
