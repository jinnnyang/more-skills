---
kind: questions
version: 1
last_updated: '2026-07-17T03:52:59+00:00'
last_verified: 2026-07-17 02:45:00+00:00
last_agent: hermes-agent-devops
last_writer: hand-off
session_id: 2026-07-17-v05-adoption
status: in-progress
---

# Questions — `skills/` scope

> [!NOTE]
> Two sections:
> - `## Open` — active questions awaiting input.
> - `## Closed` — archived, permanent, for historical reference.
>
> `<!-- resolved -->` on an Open question → next hand-off archives it to `## Closed`.

## Open

### Q1 · Recover original review items S2 and S5

The review-cycle-2 close-out lists SUGGEST items S1, S3, S4, S6, S7 as closed but leaves S2 and S5 unaccounted for. The original review document was consumed as context; specific item content wasn't preserved verbatim in DECISIONS.md.

**Ask:** if the reviewer (刘工) still has the original 4-tier review report, please attach it so the next hand-off can either close S2/S5 or explicitly DEFER them. If unrecoverable, treat S2/S5 as DEFER and archive this question.

### Q2 · Introduce CI enforcement for 3-way byte-identical sync?

The manual sync discipline for `scripts/reconcile.py` and `templates/*.md` (three byte-identical copies) currently relies on the author remembering to `diff -q` before each commit. A pre-commit hook plus a CI check would remove this footgun.

**Ask:** priority?
- (a) Now — write the hook + CI check as the next task.
- (b) After first real drift is observed.
- (c) Never — trust the manual discipline.

## Closed

### Q3 · `/tmp` MSYS path bug + greedy tools-log regex

<!-- resolved -->
Both dogfood-caught bugs fixed in v0.5-rev-C. Regression smoke tests added inline in the smoke suite. See `walkthrough.md` entry `Rev-C script bugfixes carried in`.

### Q4 · `HANDOFF-` filename prefix

<!-- resolved -->
Removed in rev-C after user feedback. Files now use their natural short names; enclosing directory identifies the scope. Kind-based scope discovery replaces filename-based detection.

### Q5 · Should the questions file use `open-questions.md` or split Open/Closed inside a single `questions.md`?

<!-- resolved -->
User picked (A): single `questions.md` with `## Open` + `## Closed` sections. Resolved questions archive into `## Closed` (permanent history), never delete. Implemented in rev-C.

### Q6 · Scope: per-skill directory, repo root, or task-defined?

<!-- resolved -->
User answer: scope is defined by the task's range, not by any directory role. `list-scopes` enumerates neutrally; agent + user negotiate per task. For the current session-handoff rework, scope = `skills/`.
