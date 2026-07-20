---
kind: task
version: 1
last_updated: 2026-07-20T09:35:00+00:00
last_verified: 2026-07-20T09:35:00+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: hand-off
session_id: sess-20260720-takeover-lock-lifecycle-bug
status: in-progress
---

# Current Tasks

## Now

- `[ ]` **T1 · Confirm the diagnosis** — reproduce the stale-lock scenario in a fresh scratch scope. Steps: (a) `init` a temp scope with session-id `S1`; (b) run `check-reality --scope <tmp> --session-id S1 --agent A1` (this simulates take-over Step 2 · Reality Check per take-over SKILL.md line 249); (c) verify `.handoff.lock` was written and contains `session_id: S1`; (d) run `prepare --scope <tmp> --session-id S2 --agent A2` (simulates a later hand-off from a different logical session) and confirm it returns `halt_on_hard_conflicts` with `concurrency_lock_conflict`. This locks the failure mode in a reproduction script before touching code.

- `[ ]` **T2 · Decide the fix strategy** — three viable options, ranked in the walkthrough. Pick one via clarify, then land it:
  - **A · Doc-only fix** — take-over SKILL.md gains an explicit release step at end of Step 7 (call `unlock`). Zero code change. Weakest guarantee (still leaks if take-over aborts mid-flow) but 15-minute delivery. Also fine as a stopgap while B is being designed.
  - **B · Read-only preflight (recommended)** — split `check-reality`'s current implicit acquire from its read semantics. Add a `--acquire-lock` flag defaulting to false; `_check_reality_scope` only acquires when the flag is on. Update take-over SKILL.md to call `check-reality` without the flag; update hand-off SKILL.md's `prepare` (which composes check-reality + cleanup planning) to pass `--acquire-lock`. Needs an ADR in DECISIONS.md.
  - **C · Context-manager lock** — make lock acquisition a `with acquired_lock(...)` block scoped to the operation. Cleanest but larger refactor and doesn't fit `check-reality`'s natural shape (which just wants to *not* acquire).

- `[ ]` **T3 · Land the chosen fix** — with test coverage. Even if fix is doc-only (option A), write at minimum a regression test that `check-reality` **without `--acquire-lock`** does not write `.handoff.lock`. This is the P2 test-coverage gap for lock handling that REVIEW-2026-07-20.md line 103 already flags; use this fix as the excuse to close it.

- `[ ]` **T4 · Add an ADR to `skills/take-over/DECISIONS.md`** — Supersedes-form. Reference: the fix chosen in T2, the exact bug reproduction (T1), and note whether it also updates hand-off (see script-parity question in questions.md). Follow `docs/adr-decision-records.md` Ch 7 format.

- `[ ]` **T5 · Verify script parity with hand-off** — take-over's and hand-off's `reconcile.py` currently have different md5 hashes. Investigate: is the divergence intentional (different features), or drift? If they were meant to stay in sync, either the fix must land in both, or they must be unified (out-of-scope this session — file a separate task). Answer question Q1 in `questions.md`.

## Next

- `[ ]` If the fix chosen is B, consider whether other implicit-acquire spots (`cmd_init` at line 651, any indirect callers) should also become explicit. The audit output goes into an appendix of the ADR.
- `[ ]` Optional dogfood: run the fixed take-over end-to-end on a fresh scope and verify a subsequent hand-off in the same shell doesn't hit the same conflict.

## Blocked

- None.

> [!] Marks blockers or agent-side issues (not human blockers).
