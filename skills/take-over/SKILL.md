---
name: take-over
description: |
  Guides the agent through a structured session resume/take-over workflow.
  Triggers when the session starts or when the user says "continue previous work" or "接着之前的做".
  Discovers prior handoff state, performs Git reality reconciliation, and restores task checklists.
---

# Session Take-Over Skill

Provides a structured session-resuming workflow to seamlessly pick up the project state left by the previous session.

## Overview

This skill implements the take-over portion of the [Session Handoff Protocol](file:///home/twait-halek/Documents/more-skills/skills/_shared/session-handoff/PROTOCOL.md). It scans for handoff files, performs reality checks against the filesystem and Git history, restores the active tasks list, and prepares the workspace for resuming work.

## When to Run This Skill

- At the very beginning of a new agent session.
- When the user explicitly requests: `"接着之前的做"`, `"继续"`, `"continue"`, or `"continue previous work"`.

---

## Take-Over Execution Workflow

Follow these steps precisely:

### Step 0: Bootstrap Check
Check if `.hermes/handoff/` exists. If the directory is missing:
1. Run initialization:
   ```bash
   python3 skills/_shared/session-handoff/scripts/reconcile.py init --agent "{agent_name}" --session-id "{session_id}" --writer take-over
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
python3 skills/_shared/session-handoff/scripts/reconcile.py check-reality
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
