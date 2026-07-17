---
name: take-over
description: |
  Guides the agent through a structured session resume/take-over workflow.
  Triggers when the session starts or when the user says "continue previous work" or "接着之前的做".
  Discovers prior handoff state at a scope directory (`context.md` / `task.md` / `walkthrough.md` / `questions.md`), performs Git reality reconciliation, and restores task checklists.
version: 1.3.0
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

This skill implements the **take-over** half of the Session Handoff Protocol (v0.5, flat-file layout). It is self-contained: everything it needs lives under this skill's directory. See `PROTOCOL.md` for the protocol reference; see `DECISIONS.md` for the design decision log.

The companion skill `hand-off` implements the closing side of the protocol. Each skill is independently installable.

## Prerequisites

- **`uv`** — required. Runs the helper Python script via `uv run …` and relies on inline script metadata to auto-install `pyyaml`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log`).
- **Python ≥ 3.11** — resolved automatically by uv.

## When to Run This Skill

- At the very beginning of a new agent session.
- When the user explicitly requests: `"接着之前的做"`, `"继续"`, `"continue"`, or `"continue previous work"`.

## Layout (v0.5 flat-file, no prefix)

Handoff documents live **directly** in the working scope directory using their natural short names:

```
<scope>/context.md
<scope>/task.md
<scope>/walkthrough.md
<scope>/questions.md
```

The enclosing directory identifies what the docs describe — no filename prefix. A "scope" is any directory where at least one of these files has YAML frontmatter with a recognised `kind` value.

### Choosing a Scope

**Scope is defined by the task's range, not by directory role.** The agent and user negotiate per task: repo root for cross-cutting reworks; a subtree root when the task is limited to that subtree; separate scopes for truly independent parallel tasks.

Discover live scopes:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

## Scope Resolution

Most commands take an optional `--scope <path>`:

1. `--scope <path>` — used verbatim (explicit wins).
2. No `--scope`, and pwd contains recognised handoff docs — pwd used silently.
3. No `--scope`, pwd has no handoff docs — script emits `WARNING`, prints `ambiguous_scope` JSON, exits with code 3. **Agent MUST `clarify` with the user** before proceeding.

Batch operations (`validate`, `check-reality`, `clean-up`) accept `--all-scopes` for repository-wide analysis.

---

## Take-Over Execution Workflow

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is the directory of this SKILL.md file. Do not pass `--isolated`.

### Step 0: Bootstrap Check — Discover Scopes

```bash
command -v uv && command -v git
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

- **If `list-scopes` finds no scope**, ask the user via `clarify`: initialize a new scope at pwd, initialize at another path, or exit (no prior handoff to resume from).
- **If `list-scopes` finds exactly one scope**, use it as `<path>` for subsequent commands.
- **If `list-scopes` finds multiple scopes**, list them and ask the user via `clarify` which to resume from; pass the choice as `--scope <path>` to every subsequent command.

If initializing (no prior state):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py init --scope <path> --agent "{agent_name}" --session-id "{session_id}" --writer take-over
```
Report: *"No previous handoff history found. Initialized empty session."* Exit the take-over flow and greet the user.

### Step 1: Validate Handoff State

Frontmatter kind-enum + timestamp sanity:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py validate --scope <path>
```

`errors` in the JSON output are HARD conflicts — halt and surface via `clarify` before loading any body content.

Determine freshness by comparing `last_updated` against the latest Git commit time:
```bash
git log -1 --format=%cI
```

### Step 2: Reality Check & Reconciliation

Offload reconciliation to the helper, appending any SOFT conflicts to `questions.md`:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py check-reality --scope <path> --apply-soft-conflicts
```

- Parse the JSON output — `hard_conflicts`, `soft_conflicts`, `applied_soft_conflicts` (count of SOFT entries appended under `## Open` in `questions.md` as `### Soft conflict · …` subsections).
- Handling per §9b of `PROTOCOL.md`:
  - HARD → skip Step 3; jump to Step 5 conflict resolution.
  - SOFT → already logged; continue to Step 3.

### Step 3: Layered Load

To control context usage:

- **L1 (Always Load)**: `context.md`, `task.md`, `questions.md`.
- **L2 (Load on Demand)**: `plan.md` or `review.md` only when the current task references them (heuristic: if `task.md` body contains the literal string `plan.md` or `review.md`).
- **L3 (Reference Only — Do NOT Auto-load)**: `walkthrough.md` is a living memory dump. Do not auto-load; only inspect when deep-diving into a specific past decision. `session_search` is often preferable.

### Step 4: Restore Checklist

Parse `task.md`'s open tasks and populate the agent runtime `todo` list.

**Reordering note**: if Step 6 (plan-mode coexistence) imports `plan.md`, re-run Step 4 against the updated `task.md` before the Step 7 summary.

### Step 5: Conflict Handling

Handle Step 2 discrepancies per tier (§9b of `PROTOCOL.md`):

- **HARD** (e.g. claimed task done but no Git/code evidence): halt loading. Present via `clarify` with options: *Trust Handoff Docs / Trust Git Reality / User Explains*. Non-interactive fallback: after 5-minute wait, write details to `<scope>/conflict_pending.json` via `write-atomic` and abort.
- **SOFT** — already logged as `### Soft conflict · …` entries under `## Open` in `questions.md` by Step 2. Nothing more to do here; the summary will report the count. To close a SOFT entry once addressed, mark it with `<!-- resolved -->` — the next `hand-off` will archive it to `## Closed`.
- **AMBIGUOUS** — the helper escalates these to HARD (fail-safe).

### Step 6: Plan-Mode Coexistence Check

If `.hermes/plans/` exists (plan-mode planning artifacts):

- Do NOT auto-merge.
- Prompt the user via `clarify`:
  - *Ignore (default)*: keep plan-mode and handoff scopes independent.
  - *Import plan.md*: copy plan-mode's `plan.md` to `<scope>/plan.md` (one-shot via `write-atomic`).
  - *Show diff*: compare plan-mode artifacts first.

If import chosen, re-run Step 4 against the updated `task.md`.

### Step 7: Summary Report to User

Print a resume greeting:
```
Scope: <path>
Previous agent: {last_agent}. Last verified: {last_verified_timestamp}.
N soft conflicts logged (see questions.md ## Open § Soft conflict), M hard conflicts resolved.
Done: ...
Now/Next: ...
Blocked on: ...
```

If `list-scopes` returned multiple scopes, mention the others as one-liners so the user can pivot later if they want.

Ask the user where they would like to resume or what task to focus on first.

---

## Companion & References

- Companion skill (closing side): `hand-off` — each is independently installable; they share protocol semantics but not files.
- `PROTOCOL.md` (this directory) — protocol reference from the take-over perspective.
- `DECISIONS.md` (this directory) — design decision log (take-over relevant subset).
- `templates/` (this directory) — default document templates, seeded by `scripts/reconcile.py init`.
