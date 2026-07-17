---
name: take-over
description: |
  Guides the agent through a structured session resume/take-over workflow.
  Triggers when the session starts or when the user says "continue previous work" or "接着之前的做".
  Discovers prior handoff state, performs Git reality reconciliation, and restores task checklists.
version: 1.1.0
author: 刘工 + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-handoff, workflow, take-over, context-restore]
    related_skills: [hand-off, plan]
---

# Session Take-Over Skill

Provides a structured session-resuming workflow to seamlessly pick up the project state left by the previous session.

## Overview

This skill implements the **take-over** half of the Session Handoff Protocol. It is self-contained: everything it needs lives under this skill's directory. See `PROTOCOL.md` in this same directory for the protocol reference; see `DECISIONS.md` for the design decision log.

The companion skill `hand-off` implements the closing side of the protocol. Each skill is independently installable.

## Prerequisites

- **`uv`** — required. This skill runs its helper Python script via `uv run …` and relies on inline script metadata to auto-install `pyyaml`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log`).
- **Python ≥ 3.11** — resolved automatically by uv from the inline `requires-python`.

## When to Run This Skill

- At the very beginning of a new agent session.
- When the user explicitly requests: `"接着之前的做"`, `"继续"`, `"continue"`, or `"continue previous work"`.

---

## Take-Over Execution Workflow

Follow these steps precisely. **All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …`** where `<SKILL_DIR>` is the directory of this SKILL.md file. `uv run` is inherently isolated for scripts with inline metadata — do not pass `--isolated`.

### Step 0: Bootstrap Check
Check if `.hermes/handoff/` exists (project-scoped, in the current working directory). If the directory is missing:
1. Run initialization:
   ```bash
   uv run <SKILL_DIR>/scripts/reconcile.py init --agent "{agent_name}" --session-id "{session_id}" --writer take-over
   ```
2. Report: *"No previous handoff history found. Initialized empty session."*
3. Exit take-over flow and proceed to greet the user.

### Step 1: Discover Handoff State
Scan `.hermes/handoff/` (and `docs/handoff/` if present) for the document set.
Validate frontmatter first (kind enum + timestamp sanity):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py validate
```
`errors` in the JSON output are HARD conflicts — halt and surface via `clarify` before loading any body content.

Determine freshness: compare `last_updated` against the latest Git commit time:
```bash
git log -1 --format=%cI
```

### Step 2: Reality Check & Reconciliation
Offload reconciliation to the helper (and immediately record any SOFT conflicts):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py check-reality --apply-soft-conflicts
```
- Parse the JSON output. It contains `hard_conflicts`, `soft_conflicts`, and `applied_soft_conflicts` (count written to `open-questions.md` under `## Soft Conflicts (Reconciled)`).
- Handling per §9b of `PROTOCOL.md`:
  - HARD → skip Step 3; jump directly to Step 5 conflict resolution.
  - SOFT → already logged to `open-questions.md`; continue to Step 3.

### Step 3: Layered Load
To control context usage, follow the layered load rules:
- **L1 (Always Load)**: Read the contents of `context.md`, `task.md`, and `open-questions.md`.
- **L2 (Load on Demand)**: Load `plan.md` or `review.md` only when entering tasks that reference them. Heuristic: if `task.md` body contains the literal string `plan.md` or `review.md`, load them at Step 3 too.
- **L3 (Reference Only - Do NOT Auto-load)**: `walkthrough.md` must not be loaded automatically. Only inspect it or query past session logs via `session_search` when deep-diving into specific past decisions.

### Step 4: Restore Checklist
Parse `task.md`'s open tasks checklist and populate the agent runtime `todo` list.

**Reordering note**: if Step 6 (plan-mode coexistence) imports `plan.md`, re-run Step 4 against the updated `task.md` before Step 7 reports.

### Step 5: Conflict Handling
Handle discrepancies identified in Step 2 according to their tiers (§9b of `PROTOCOL.md`):
- **HARD Conflicts** (e.g., claimed task done but no Git/code evidence):
  - Halt loading. Present the conflicts to the user via `clarify` with options: *Trust Handoff Docs / Trust Git Reality / User Explains*.
  - *Non-interactive Timeout*: If running in non-interactive/CI mode, wait 5 minutes; if no response, write details to `.hermes/handoff/conflict_pending.json` via `write-atomic` and abort execution.
- **SOFT Conflicts** — already logged by Step 2. Nothing more to do here; the take-over summary will report the count.
- **AMBIGUOUS Conflicts** — the helper escalates these to HARD (fail-safe).

### Step 6: Plan-Mode Coexistence Check
If `.hermes/plans/` exists (plan-mode planning artifacts):
- Do NOT auto-merge.
- Prompt the user via `clarify` with structured choices:
  - *Ignore (default)*: Keep plan-mode and handoff directories independent.
  - *Import plan.md*: Copy plan-mode's `plan.md` to `.hermes/handoff/plan.md` (one-shot copy via `write-atomic`).
  - *Show diff*: Compare plan-mode artifacts first.

If import chosen, re-run Step 4 against the updated `task.md` so the final report reflects any newly imported tasks.

### Step 7: Summary Report to User
Print a resume greeting:
```
Previous agent: {last_agent}. Last verified: {last_verified_timestamp}.
N soft conflicts logged, M hard conflicts resolved.
Done: ...
Now/Next: ...
Blocked on: ...
```
Ask the user where they would like to resume or what task to focus on first.

---

## Companion & References

- Companion skill (closing side): `hand-off` — each is independently installable; they share protocol semantics but not files.
- `PROTOCOL.md` (this directory) — protocol reference from the take-over perspective.
- `DECISIONS.md` (this directory) — design decision log (take-over relevant subset).
- `templates/` (this directory) — default handoff document templates, seeded by `scripts/reconcile.py init`.
