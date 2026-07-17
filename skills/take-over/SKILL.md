---
name: take-over
description: |
  Guides the agent through a structured session resume/take-over workflow.
  Triggers when the session starts or when the user says "continue previous work" or "接着之前的做".
  Discovers prior handoff state, performs Git reality reconciliation, and restores task checklists.
version: 1.0.0
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

- **`uv`** — required. This skill runs its helper Python script via `uv run --isolated python …`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log`).

## When to Run This Skill

- At the very beginning of a new agent session.
- When the user explicitly requests: `"接着之前的做"`, `"继续"`, `"continue"`, or `"continue previous work"`.

---

## Take-Over Execution Workflow

Follow these steps precisely. **All Python invocations use `uv run --isolated python <SKILL_DIR>/scripts/reconcile.py …`** where `<SKILL_DIR>` is the directory of this SKILL.md file.

### Step 0: Bootstrap Check
Check if `.hermes/handoff/` exists (project-scoped, in the current working directory). If the directory is missing:
1. Run initialization:
   ```bash
   uv run --isolated python <SKILL_DIR>/scripts/reconcile.py init --agent "{agent_name}" --session-id "{session_id}" --writer take-over
   ```
2. Report: *"No previous handoff history found. Initialized empty session."*
3. Exit take-over flow and proceed to greet the user.

### Step 1: Discover Handoff State
Scan `.hermes/handoff/` (and `docs/handoff/` if present) for the document set.
Read the YAML frontmatter of each file first.
Determine freshness: Compare the `last_updated` timestamps against the latest Git commit time:
```bash
git log -1 --format=%cI
```

### Step 2: Reality Check & Reconciliation
Offload reconciliation checks to the Python helper script:
```bash
uv run --isolated python <SKILL_DIR>/scripts/reconcile.py check-reality
```
- Parse the output JSON which details detected discrepancies, verifying:
  - Git status uncommitted modifications vs. walkthrough notes.
  - Latest commits matching claims.
  - File existence sanity checks.
  - Walkthrough `<session-tools-log>` metadata validation.

### Step 3: Layered Load
To control context usage, follow the layered load rules:
- **L1 (Always Load)**: Read the contents of `context.md`, `task.md`, and `open-questions.md`.
- **L2 (Load on Demand)**: Load `plan.md` or `review.md` only when entering tasks that reference them.
- **L3 (Reference Only - Do NOT Auto-load)**: `walkthrough.md` must not be loaded automatically. Only inspect it or query past session logs via `session_search` when deep-diving into specific past decisions.

### Step 4: Restore Checklist
Parse `task.md`'s open tasks checklist and populate the agent runtime `todo` list.

### Step 5: Conflict Handling
Handle discrepancies identified in Step 2 according to their tiers:
- **HARD Conflicts** (e.g., claimed task done but no Git/code evidence):
  - Halt loading. Present the conflicts to the user via `AskUserQuestion` / `clarify` with options: *Trust Handoff Docs / Trust Git Reality / User Explains*.
  - *Non-interactive Timeout*: If running in non-interactive/CI mode, wait 5 minutes; if no response, write details to `conflict_pending.json` and abort execution.
- **SOFT Conflicts** (e.g., `last_verified` is older than 7 days, files renamed/moved but intact):
  - Log details to `open-questions.md` under a structured `## Soft Conflicts (Reconciled)` section with UTC timestamp. Continue loading.
- **AMBIGUOUS Conflicts**: Escalate to HARD (fail-safe).

### Step 6: Plan-Mode Coexistence Check
If `.hermes/plans/` exists (plan-mode planning artifacts):
- Do NOT auto-merge.
- Prompt the user via `AskUserQuestion` / `clarify` with structured choices:
  - *Ignore (default)*: Keep plan-mode and handoff directories independent.
  - *Import plan.md*: Copy plan-mode's `plan.md` to `.hermes/handoff/plan.md` (one-shot copy).
  - *Show diff*: Compare plan-mode artifacts first.

### Step 7: Summary Report to User
Print a resume greeting:
```
Previous agent: {last_agent}. Last verified: {last_verified_timestamp}.
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
