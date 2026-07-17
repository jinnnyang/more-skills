---
name: hand-off
description: |
  Guides the agent through a structured session closing workflow.
  Triggers when the user says "先到这", "换你上", "/handoff", or when context window exceeds 75%.
  Ensures that the current project state (invariants, tasks, walkthrough, and human blockers) is atomically persisted.
version: 1.1.0
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

This skill implements the **hand-off** half of the Session Handoff Protocol. It is self-contained: everything it needs lives under this skill's directory. See `PROTOCOL.md` in this same directory for the protocol reference; see `DECISIONS.md` for the design decision log.

The companion skill `take-over` implements the resume side of the protocol. Each skill is independently installable.

## Prerequisites

- **`uv`** — required. This skill runs its helper Python script via `uv run …` and relies on inline script metadata to auto-install `pyyaml`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log --diff-filter=D`).
- **Python ≥ 3.11** — resolved automatically by uv from the inline `requires-python`.

## When to Run This Skill

- User explicitly requests: `"先到这"`, `"换你上"`, `"handoff"`, or uses `/handoff`.
- Automatically suggested when the context window usage exceeds 75%.
- Suggest when a major `todo` phase or implementation plan is completed.

---

## Hand-Off Execution Workflow

Follow these steps precisely. **All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …`** where `<SKILL_DIR>` is the directory of this SKILL.md file. `uv run` is inherently isolated for scripts with inline metadata — do not pass `--isolated`.

### Step 0: Bootstrap Check
Verify if `.hermes/handoff/` exists (project-scoped, in the current working directory). If not, run:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py init --agent "{agent_name}" --session-id "{session_id}" --writer hand-off
```
*(Substitute `{agent_name}` and `{session_id}` dynamically.)*

### Step 1: Reality Check & Anti-Hallucination
Before editing documents, audit actual mutations. Do NOT trust memory alone.
Run the helper (frontmatter validity + git-status + tools-log ↔ git evidence + `last_verified` staleness):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py check-reality
```
The command returns JSON with `hard_conflicts` and `soft_conflicts`. Resolve HARD conflicts before proceeding.

Additionally cross-check the current session's real mutations:
```bash
git status --short
git log -5 --name-only --pretty=format:'%h %s'
```

### Step 2: Update Core Handoff Documents (Atomic Write Rule)

**All file writes MUST be atomic** (write to `.tmp` first, then rename). Two supported patterns:

- **Small edits (< 4 KB, no complex escaping):** call the helper with `--content`:
  ```bash
  uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath ".hermes/handoff/task.md" --content "…"
  ```
- **Large / multi-line writes (recommended default):** stage content into a temp file first, then let the helper stream it:
  ```bash
  uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath ".hermes/handoff/walkthrough.md" --content-file /path/to/staged.tmp
  ```
  or pipe via stdin:
  ```bash
  cat /path/to/staged.tmp | uv run <SKILL_DIR>/scripts/reconcile.py write-atomic --filepath ".hermes/handoff/walkthrough.md"
  ```

Update the following documents:
- **`task.md`**: Persist the current `todo` list verbatim. Do not omit or summarize open items.
- **`walkthrough.md`**: Update this single living file:
  - Append a dated entry with the header format `## YYYY-MM-DD — <slug>`. Deviating from this format disables the cleanup classifier (see §9a).
  - Content: decisions made & why, files changed (paths), surprises / gotchas. NOT a transcript replay.
  - Use explicit markers when the classification is non-obvious:
    - `<!-- keep -->` on an entry you always want retained (or use keywords `lesson` / `surprise` / `decision` / `invariant` in the header).
    - `<!-- resolved -->` on an entry the next hand-off should CLEAR.
  - Optionally serialize this session's tool calls as JSON inside the `<session-tools-log>` block. **The tools-log is best-effort auxiliary evidence** — see PROTOCOL §9 note about the primary evidence source being `git`.
- **`open-questions.md`**: Add any human-blocking questions discovered during this session. Mark resolved entries with `<!-- resolved -->` so the next cleanup removes them.
- **`context.md`**: Append any new critical invariants learned (strictly additive-only).

### Step 3: Smart Cleanup (two-phase)

**Phase 3a — dry-run classification** (no disk mutation):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --dry-run
```
Returns four buckets: `clear`, `stale`, `kept`, `unsure`.

- If `unsure` is non-empty, present the items to the user as a **single batched `clarify` prompt** with structured choices (keep / drop each).
- Show the user the `clear` and `stale` lists so they can veto individual deletions.

**Phase 3b — apply** (only after user confirmation on any UNSURE items):
```bash
uv run <SKILL_DIR>/scripts/reconcile.py clean-up --apply
```
Removes CLEAR + STALE entries verbatim. UNSURE entries are always preserved. The audit trail (what was removed) is in the JSON output — mirror it into the Step 5 summary.

### Step 4: Promote & Git Decision (Optional)

Handoff docs in `.hermes/handoff/` are private and gitignored by default. Ask the user via `clarify` with structured choices:
- Keep private in `.hermes/handoff/` (default)
- Promote to `docs/handoff/` and git commit now
- Promote to `docs/handoff/` and stage only

If promotion is chosen:
- Copy the handoff documents to `docs/handoff/`, adding `frozen: true` to each YAML frontmatter (via the `write-atomic --content-file` pattern).
- If committing, propose the default commit message `docs(handoff): session hand-off — {status}` via `clarify` and let the user approve or edit it before running `git commit`.

### Step 5: Final Summary Message

Print a concise summary containing:
- Files written (task.md / walkthrough.md / open-questions.md / context.md — only those actually touched).
- Cleanup audit trail: N cleared, M stale, K unsure preserved (with headers).
- SOFT conflicts left over from Step 1 (if any).
- Explicit next actions for the successor agent.

---

## Companion & References

- Companion skill (resume side): `take-over` — each is independently installable; they share protocol semantics but not files.
- `PROTOCOL.md` (this directory) — protocol reference from the hand-off perspective.
- `DECISIONS.md` (this directory) — design decision log (hand-off relevant subset).
- `templates/` (this directory) — default handoff document templates, seeded by `scripts/reconcile.py init`.
