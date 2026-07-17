---
kind: task
version: 1
last_updated: 2026-07-17T07:00:00+00:00
last_verified: 2026-07-17T07:00:00+00:00
last_agent: ark-code-latest via Hermes/devops
last_writer: hand-off
session_id: rev-D-close-out-20260717T145717
status: phase-complete
---

# Task Checklist — `skills/` scope

Rework of the session-handoff protocol trio (`hand-off` / `take-over` / `_shared/session-handoff`). Scope = `skills/` because every edit lives under that directory.

## Phase: v0.5 flat-file + kind-based scope + Open/Closed questions — 2026-07-17

**Status:** phase-complete (rev-D close-out).

### Done

- [x] `reconcile.py` v0.5 rewrite: `--scope`, `list-scopes`, `--all-scopes`, MSYS `write-atomic --content-file`, line-anchored tools-log regex
- [x] Rev-C additions: strip `HANDOFF-` filename prefix; rename `open-questions.md` → `questions.md`; kind-based scope discovery (no file-prefix policy); `<!-- resolved -->` on questions **archives** to `## Closed` (not delete)
- [x] Section regex extended to `#{2,3}` so `### Q1 …` entries under `## Open` are classified
- [x] Templates: `open-questions.md` renamed and restructured to `## Open` + `## Closed`
- [x] `apply_soft_conflicts` writes SOFT conflicts as `### Soft conflict · …` entries under `## Open` (removes legacy `## Soft Conflicts (Reconciled)`)
- [x] 3-way sync (`_shared/`, `hand-off/`, `take-over/`) byte-identical
- [x] Smoke tests: init/validate/check-reality/clean-up (archive semantics)/write-atomic/list-scopes all green
- [x] Migrate content from rev-B `.hermes/handoff/` + intermediate rev-B/C `HANDOFF-*.md` × 12 → single `skills/` scope × 4

### Not-done — this session

- [x] Update `skills/hand-off/SKILL.md` for v0.5-rev-C (short filenames + kind-based scope + Q archive semantics + scope-neutral wording)
- [x] Update `skills/take-over/SKILL.md` (same)
- [x] Update `skills/hand-off/PROTOCOL.md` (§5 layout: short names + kind detection · §9a: questions archive semantics · §9 evidence rules unchanged) — completed at commit 0c56a9a; rev-D C3 fix inline
- [x] Update `skills/take-over/PROTOCOL.md` (same) — completed at commit 0c56a9a; rev-D C1+C2+C3 fixes inline
- [x] Append rev-C decision entries to `skills/hand-off/DECISIONS.md` and `skills/take-over/DECISIONS.md`
- [x] `git commit -am "session-handoff v0.5-rev-C: flat-file, kind-based scope, question Open/Closed archive"` — commit 0c56a9a
- [x] `git push`

### rev-D (2026-07-17 close-out)

- [x] CRITICAL fix C1: repair take-over/PROTOCOL.md §7 fence structure
- [x] CRITICAL fix C2: unify SOFT-conflict landing to `## Open` § `### Soft conflict · …` in take-over/PROTOCOL.md
- [x] CRITICAL fix C3: remove `--isolated` from hand-off & take-over PROTOCOL.md
- [x] W2: delete `skills/_shared/session-handoff/scripts/`, retire 3-way sync to 2-way, update `skills/_shared/session-handoff/README.md`
- [x] questions.md: resolve Q1 (S2/S5 → DEFER, content unrecoverable) and Q2 (3-way sync retired, 2-way manual, no hook)

### Deferred

- [ ] D1-D5 · original DEFER items from review cycle 2 (S2/S5 content lost per Q1 resolution — no action item recoverable)
- [ ] Live end-to-end integration test on a non-toy repo
- [x] ~~Pre-commit hook enforcing 3-way byte-identical reconcile script + templates~~ — DROPPED per Q2 rev-D resolution (3-way sync retired; 2-way manual discipline judged sufficient)
- [ ] Short README per skill (hand-off README, take-over README) with quickstart
- [ ] WORTH findings W1/W3/W4/W5/W6/W7 from rev-D design-doc review (documented in walkthrough rev-D entry; each subtree will pick up during its own independent-development scope)

## Open Blockers

- None. Open questions in `questions.md` are non-blocking.
