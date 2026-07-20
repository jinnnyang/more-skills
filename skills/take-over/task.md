---
kind: task
version: 1
last_updated: 2026-07-20T09:43:30+00:00
last_verified: 2026-07-20T09:43:30+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: take-over
session_id: sess-20260720-takeover-lock-lifecycle-bug
status: phase-complete
---

# Current Tasks

## Now

- None. Phase complete; see `## Done (this phase)` below and `walkthrough.md § 2026-07-20 (rev-B)`.

## Next

- `[ ]` Audit other implicit-acquire spots. `cmd_init` at reconcile.py line 651 still calls `acquire_lock` unconditionally — expected (init *is* a writer), but confirm no other command inadvertently writes locks on read paths.
- `[ ]` Optional follow-up: run the fixed take-over → hand-off end-to-end on a real scope over a real time gap (not the in-process dogfood) to double-check TTL/skew behaviour under actual clock drift.
- `[ ]` Optional (P2, from `REVIEW-2026-07-20.md`): split the 1700+ line `reconcile.py` into modules — the lock code plus the new tests are natural first extractions.

## Blocked

- None.

## Done (this phase · 2026-07-20)

- `[x]` **T1** · Bug reproduced in a scratch scope (repro script; ran green).
- `[x]` **T2** · Fix strategy chosen: **option B** — `--acquire-lock` opt-in flag. See ADR R35.
- `[x]` **T3** · Fix landed with regression coverage. take-over 7 cases + hand-off 9 cases + e2e dogfood, 42+1 green. Commits `7b0441d`, `096275f`.
- `[x]` **T4** · ADR R35 (fix) + R36 (hand-off parity) landed in `skills/take-over/DECISIONS.md`. SKILL.md bumped 1.4.0 → 1.5.0 and Step 2 gained an `IMPORTANT` callout.
- `[x]` **T5** · Script-parity question (Q1) answered "divergent by design"; fix applied to both `reconcile.py` copies with matching semantics. hand-off's `_prepare_scope` passes `acquire=True` internally so hand-off's own workflow is unchanged from the outside.

> [!] Marks blockers or agent-side issues (not human blockers).
