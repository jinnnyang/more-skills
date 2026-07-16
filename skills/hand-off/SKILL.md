---
name: hand-off
description: |
  Guides the agent through a structured session closing workflow.
  Triggers when the user says "先到这", "换你上", "/handoff", or when context window exceeds 75%.
  Ensures that the current project state (invariants, tasks, walkthrough, and human blockers) is atomically persisted.
---

# Session Hand-Off Skill

Provides a structured session-closing workflow to ensure that the current project state is accurately persisted and ready for the next agent or session.

## Overview

This skill implements the hand-off portion of the [Session Handoff Protocol](file:///home/twait-halek/Documents/more-skills/skills/_shared/session-handoff/PROTOCOL.md). It ensures invariants, tasks, walkthrough memory, and open human questions are persisted in `.hermes/handoff/`.

## When to Run This Skill

- User explicitly requests: `"先到这"`, `"换你上"`, `"handoff"`, or uses `/handoff`.
- Automatically suggested when the context window usage exceeds 75%.
- Suggest when a major `todo` phase or implementation plan is completed.

---

## Hand-Off Execution Workflow

Follow these steps precisely:

### Step 0: Bootstrap Check
Verify if `.hermes/handoff/` exists. If not, run:
```bash
python3 skills/_shared/session-handoff/scripts/reconcile.py init --agent "{agent_name}" --session-id "{session_id}" --writer hand-off
```
*(Substitute `{agent_name}` and `{session_id}` dynamically).*

### Step 1: Reality Check & Anti-Hallucination
Before editing documents, audit actual mutations. Do NOT trust memory alone.
Check tool call execution history. Extract the files actually created or modified during this session.
Run git status to confirm:
```bash
git status --short
```

### Step 2: Update Core Handoff Documents (Atomic Write Rule)
All file writes MUST use the Atomic Write Rule (write to `.tmp` first, then rename). You can do this by creating a temp file in the repo or calling the helper:
```bash
python3 skills/_shared/session-handoff/scripts/reconcile.py write-atomic --filepath ".hermes/handoff/{filename}.md" --content "{content}"
```

Update the following documents:
- **`task.md`**: Persist the current `todo` list verbatim. Do not omit or summarize open items.
- **`walkthrough.md`**: Update this single living file:
  - Append a dated entry with decisions, files changed, and surprises.
  - Serialize the actual tool calls from this session as a JSON array inside the `<session-tools-log>` block at the bottom of the file (e.g. `[{"tool": "write_to_file", "target": "/path/to/file", "timestamp": "..."}]`).
- **`open-questions.md`**: Add any human-blocking questions discovered during this session.
- **`context.md`**: Append any new critical invariants learned (strictly additive-only).

### Step 3: Run Smart Cleanup
Prune resolved entries to keep document sizes bounded (walkthrough target < 20 KB). Call the Python cleanup tool:
```bash
python3 skills/_shared/session-handoff/scripts/reconcile.py clean-up
```
- Parse the output JSON.
- If there are `unsure_items`, present them to the user as a single batched confirmation using `AskUserQuestion` / `clarify`.
- Confirm final deletions.

### Step 4: Promote & Git Decision (Optional)
Handoff docs in `.hermes/handoff/` are private and gitignored by default. Ask the user via `AskUserQuestion` / `clarify`:
> *"How would you like to handle this handoff?"*
> 1. Keep private in `.hermes/handoff/` (default)
> 2. Promote to `docs/handoff/` and git commit now
> 3. Promote to `docs/handoff/` and stage only

If promotion is chosen:
- Copy the handoff documents to `docs/handoff/`, appending `frozen: true` to their YAML frontmatter.
- If committing, generate a default commit message: `docs(handoff): session hand-off — {status}` and let the user approve or edit it before committing.

### Step 5: Final Summary Message
Print a concise summary of what was written and highlight explicit next actions/tasks for the successor agent.
