---
name: hand-off
description: |
  Guides the agent through a structured session closing workflow.
  Triggers when the user says "先到这", "换你上", "/handoff", or when context window exceeds 75%.
  Ensures that the current project state (invariants, tasks, walkthrough, and human blockers) is atomically persisted to a **scope directory** as flat-layout `context.md` / `task.md` / `walkthrough.md` / `questions.md` files.
version: 1.3.0
author: 刘工 + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-handoff, workflow, hand-off, context-transfer]
    related_skills: [take-over, plan]
---

# Session Hand-Off Skill

Provides a structured session-closing workflow to ensure that the current project state is accurately persisted and ready for the next agent or session.

## Overview

This skill implements the **hand-off** half of the Session Handoff Protocol (v0.5, flat-file layout). It is self-contained: everything it needs lives under this skill's directory. See `PROTOCOL.md` (in this same directory) for the protocol reference; see `DECISIONS.md` for the design decision log.

The companion skill `take-over` implements the resume side of the protocol. Each skill is independently installable.

## Prerequisites

- **`uv`** — required. This skill runs its helper Python script via `uv run …` and relies on inline script metadata to auto-install `pyyaml`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log --diff-filter=D`).
- **Python ≥ 3.11** — resolved automatically by uv from the inline `requires-python`.

## When to Run This Skill

- User explicitly requests: `"先到这"`, `"换你上"`, `"handoff"`, or uses `/handoff`.
- Automatically suggested when the context window usage exceeds 75%.
- Suggest when a major `todo` phase or implementation plan is completed.

## Layout (v0.5 flat-file, no prefix)

Handoff documents live **directly** in the working scope directory using their natural short names:

```
<scope>/context.md
<scope>/task.md
<scope>/walkthrough.md
<scope>/questions.md
```

The enclosing directory identifies what the docs describe — no filename prefix required. Optional docs (`plan.md`, `review.md`) may also be present.

A "scope" is any directory where at least one of these files has YAML frontmatter with a recognised `kind` value (`context` / `task` / `walkthrough` / `questions` / `plan` / `review`). Kind-based detection avoids false positives from arbitrary `context.md` / `task.md` files in generic projects.

### Choosing a Scope

**Scope is defined by the task's range, not by directory role.** Neither "one per skill" nor "always repo root" is a rule — the agent and user negotiate per task:

- Refactor spanning the entire repo → scope at the repo root is appropriate.
- Rework limited to a subtree (`skills/`, a package dir, a feature module) → scope at that subtree's root.
- Multiple truly independent parallel tasks → separate scopes at each task's natural root.

Discover live scopes at any time:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

`list-scopes` enumerates every live scope neutrally. Present the list to the user via `clarify` when scope choice is not obvious.

## Scope Resolution

All commands except `write-atomic` and `list-scopes` take an optional `--scope <path>`:

1. `--scope <path>` — used verbatim (explicit wins).
2. No `--scope`, and pwd contains recognised handoff docs (kind-frontmatter match) — pwd used silently.
3. No `--scope`, pwd has no recognised handoff docs — script emits `WARNING`, prints `ambiguous_scope` JSON, and exits with code 3. **Agent MUST `clarify` with the user** before proceeding — either `init --scope <pwd>` to create a new scope, or specify an existing scope's path.

Batch operations (`validate`, `check-reality`, `clean-up`) also accept `--all-scopes` to apply across every scope discovered under pwd. `init` and `write-atomic` are single-target only.

---

## Hand-Off Execution Workflow

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is the directory of this SKILL.md file. `uv run` is inherently isolated for scripts with inline metadata — do not pass `--isolated`.

### Step 0: Bootstrap Check

Preview the scope landscape and confirm the target with the user:

```bash
command -v uv && command -v git
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

- **If `list-scopes` finds no scope under pwd**, ask the user via `clarify` whether to init a new scope at pwd or specify an existing scope path.
- **If `list-scopes` finds exactly one scope at pwd**, silent use.
- **If `list-scopes` finds multiple scopes**, print them, ask the user to pick with `clarify`, and pass the choice as `--scope <path>` to subsequent commands.

Init only if the chosen scope has no docs yet:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py init --scope <path> --agent "{agent_name}" --session-id "{session_id}" --writer hand-off
```

### Step 1: Reality Check & Anti-Hallucination

Before editing documents, audit actual mutations. Do NOT trust memory alone.

```bash
uv run <SKILL_DIR>/scripts/reconcile.py check-reality --scope <path>
```

The command returns JSON with `hard_conflicts` and `soft_conflicts`. Resolve HARD conflicts before proceeding. Cross-check the current session's real mutations:

```bash
git status --short
git log -5 --name-only --pretty=format:'%h %s'
```

### Step 2: Update Core Handoff Documents (Atomic Write Rule)

**All file writes MUST be atomic** (write to `.tmp` first, then rename). Two supported patterns:

- **Small edits (< 4 KB, no complex escaping):** call the helper with `--content`:
  ```bash
  uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath "<scope>/task.md" --content "…"
  ```
- **Large / multi-line writes (recommended default):** stage content into a temp file, then stream it:
  ```bash
  uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath "<scope>/walkthrough.md" --content-file /tmp/staged.md
  ```
  MSYS paths (`/tmp/…`, `/c/…`) are auto-resolved on Windows. Or pipe via stdin:
  ```bash
  cat /tmp/staged.md | uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath "<scope>/walkthrough.md"
  ```

Update the four core documents:

- **`task.md`**: persist the current `todo` list verbatim. Don't omit or summarize open items.
- **`walkthrough.md`**: append a dated entry with the header `## YYYY-MM-DD — <slug>`. Deviating from this format disables the cleanup classifier (see PROTOCOL §9a).
  - Content: decisions made & why, files changed (paths), surprises. NOT a transcript replay.
  - Use explicit markers where classification is non-obvious:
    - `<!-- keep -->` on an entry you always want retained (or use keywords `lesson` / `surprise` / `decision` / `invariant` in the header).
    - `<!-- resolved -->` on an entry the next hand-off should CLEAR (walkthrough only — for questions, `<!-- resolved -->` archives rather than clears).
  - Optionally serialize this session's tool calls as JSON inside the `<session-tools-log>` block. **The tools-log is best-effort auxiliary evidence** — see PROTOCOL §9 note about `git` being primary.
- **`questions.md`**: two sections. `## Open` for active questions/blockers; `## Closed` for archived history. Mark resolved entries under `## Open` with `<!-- resolved -->` — the next `clean-up --apply` will **move** them to `## Closed` (permanent history, not deletion). Entry format: `### <Question ID> · <title>` at the `###` level under either section.
- **`context.md`**: append any new critical invariants learned (strictly additive-only).

### Step 3: Smart Cleanup (two-phase)

**Phase 3a — dry-run classification** (no disk mutation):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --scope <path> --dry-run
```
Returns five buckets: `clear`, `stale`, `kept`, `unsure`, `archived`.

- **`clear`** / **`stale`**: walkthrough entries marked for deletion.
- **`archived`**: `questions.md` entries under `## Open` bearing `<!-- resolved -->` — they will move to `## Closed` on apply (never deleted).
- **`kept`**: preserved (either explicit `<!-- keep -->`, placeholder body, or already under `## Closed`).
- **`unsure`**: needs human decision.

- If `unsure` is non-empty, present items to the user as a **single batched `clarify` prompt** with structured choices (keep / drop each).
- Show the user the `clear`, `stale`, and `archived` lists so they can veto individual actions.

**Phase 3b — apply** (only after user confirmation on any UNSURE items):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --scope <path> --apply
```
Removes CLEAR + STALE walkthrough entries. Moves ARCHIVED question entries from `## Open` to `## Closed` (permanent). UNSURE entries are always preserved. Mirror the JSON audit trail into the Step 5 summary.

### Step 4: Git Decision

Under v0.5 there is no separate "promote from `.hermes/handoff/`" step — handoff docs are just files in the working tree. Ask the user via `clarify`:

- Commit now
- Stage only (user will commit)
- Don't stage — leave for a later commit

Propose the default commit message `docs(handoff): session hand-off — {status}` via `clarify` and let the user approve or edit it before running `git commit`.

### Step 5: Final Summary Message

Print a concise summary containing:

- Files written (which docs were actually touched at which scope).
- Cleanup audit trail: N cleared, M stale, A archived-to-Closed, K unsure preserved (with headers).
- SOFT conflicts left over from Step 1 (if any).
- Explicit next actions for the successor agent.

---

## Companion & References

- Companion skill (resume side): `take-over` — each is independently installable; they share protocol semantics but not files.
- `PROTOCOL.md` (this directory) — protocol reference from the hand-off perspective (v0.5).
- `DECISIONS.md` (this directory) — design decision log (hand-off relevant subset).
- `templates/` (this directory) — default handoff document templates, seeded by `scripts/reconcile.py init`.
