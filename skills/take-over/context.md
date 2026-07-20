---
kind: context
version: 1
last_updated: 2026-07-20T09:43:30+00:00
last_verified: 2026-07-20T09:43:30+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: take-over
session_id: sess-20260720-takeover-lock-lifecycle-bug
status: phase-complete
---

# Project Invariants & Context

> [!NOTE]
> Additive-only. Add corrections as new dated entries at the bottom.

## Project Description

- **Target**: `skills/take-over/` in this repo (`more-skills`). Also `skills/hand-off/scripts/reconcile.py` — the two skills share the same script file (physically distinct copies, currently different `md5sum`, but the lock/acquire logic is the same shape). Verify parity before landing changes.
- **Trigger**: A concrete bug found while running `hand-off` at the end of the previous session, session `sess-20260720-make-soul-corpus-opt` on `skills/make-soul/`. The `prepare` call returned `halt_on_hard_conflicts` because a stale lock existed — the lock had been acquired by an earlier `take-over` in the same wall-clock session but never released. See walkthrough for full timeline.
- **Scope of the fix**: contained to lock lifecycle in `take-over`'s reconcile.py + a corresponding SKILL.md doc/step update. Not a protocol rewrite.
- **Not in scope**: reconcile.py's other pending debts (test coverage, splitting the 1773-line file, R24 threshold calibration). These are already tracked in `REVIEW-2026-07-20.md` and are P2 or deferred.

## Repo & Version-Control Facts  [git:2026-07-20]

- Repo root: `C:\Users\jinnn\Documents\more-skills` — origin `https://github.com/jinnnyang/more-skills.git`.
- The Hermes profile skill path `C:\Users\jinnn\AppData\Local\hermes\profiles\devops\skills\software-development\take-over` **is a junction pointing to** `skills/take-over` in this repo. Edits are edits to the tracked file.
- The `hand-off` skill's reconcile.py currently has md5 `7540fa72b30c10e89abd5fc12a41ff76`; `take-over`'s has md5 `2fd7af2c47f2d2f7774be71b3a00519e` — **they differ**. Check whether the divergence is intentional before patching both. If they were meant to be a single source, this is a separate cleanup task.
- Latest three commits on `more` branch: `df1200d` (handoff docs), `cccff14` (gitignore .handoff.lock), `823bbfb` (make-soul feat). None of them touch take-over.

## Invariants & Rules

- **`.handoff.lock` is a runtime file, not source.**  [user:2026-07-20]  It sits in the scope directory and must never be committed. `.gitignore` already excludes it (`cccff14`). Do not accidentally re-track it.
- **Lock TTL is 7200 seconds (2 h).**  [inferred:reconcile.py line 269]  A lock older than TTL is treated as "not a conflict" — writes will simply override it. Any tightening (e.g. shortening TTL) needs an ADR because it changes user-visible behaviour on multi-hour dev sessions.
- **`--session-id` presence toggles acquire vs check.**  [inferred:reconcile.py lines 754-757]  In `_check_reality_scope`, passing `--session-id` triggers `acquire_lock` (writes to disk); omitting it triggers `check_lock_conflict` (read-only). This is subtle and undocumented. The bug is directly downstream of this branch.
- **`release_lock` is only called from `cmd_clean_up`.**  [inferred:reconcile.py grep for release_lock, line 1208]  It is the *only* code path that releases a lock. If a command acquires but is not paired with `cmd_clean_up` under the same session, the lock leaks until TTL.
- **DECISIONS.md is Supersedes-append-only.**  [user:2026-07-20]  Never edit a landed ADR in place. If a fix changes an earlier decision (e.g. "acquire on read-only preflight"), add a new ADR that supersedes it. See `docs/adr-decision-records.md` Ch 7.
- **`context.md` is additive-only.**  [inferred:SKILL.md convention]  Do not rewrite entries above. Add corrections in a new dated block.

## Environment & Build

- `uv`, `git`, and Python ≥ 3.11 must be available (all present on this host).
- Tests: no test file exists yet for reconcile.py's lock logic. This session may want to add one — see task.md T4.
- Manual test harness pattern: see the ad-hoc verify script pattern used at the end of the prior session (`hermes-verify-gitignore-handoff-lock.sh` under Temp). That style — a temp bash script under `$TEMP` with `hermes-verify-` prefix — is the current lightweight verification convention.

## Invariant Corrections Log

- **2026-07-20 (rev-B)** — Invariant on line 35 ("`--session-id` presence toggles acquire vs check") is **superseded** by the new contract: `check-reality` acquires **only** when `--acquire-lock` is passed. `--session-id` alone is now purely identity metadata, not a mode switch. Landed in commits `7b0441d` (take-over) and `096275f` (hand-off), documented in `DECISIONS.md` R35 / R36. The original line stays above as historical record of the bug's shape.
- **2026-07-20 (rev-B)** — Invariant on line 36 ("`release_lock` is only called from `cmd_clean_up`") still holds *literally*, but the acquire side is now gated by explicit opt-in, so the leak surface it warned about is closed. No behavioural change to `release_lock` itself.
- **2026-07-20 (rev-B)** — `skills/take-over/scripts/reconcile.py` md5 changed (new fix). `skills/hand-off/scripts/reconcile.py` md5 also changed (parity fix). Q1 in `questions.md` answered: divergence is intentional; both files carry the same lock semantics but are physically independent copies. No plan to unify.
