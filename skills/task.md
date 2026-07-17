---
kind: task
version: 1
last_updated: 2026-07-17T03:52:00+00:00
last_verified: 2026-07-17T03:52:00+00:00
last_agent: Antigravity
last_writer: hand-off
session_id: b041c687-73d0-47f4-9d8b-bf878a50422e
status: in-progress
---

# Task Checklist — `skills/` scope

Rework of the session-handoff protocol trio (`hand-off` / `take-over` / `_shared/session-handoff`). Scope = `skills/` because every edit lives under that directory.

## Phase: v0.5 flat-file + kind-based scope + Open/Closed questions — 2026-07-17

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
- [ ] Update `skills/hand-off/PROTOCOL.md` (§5 layout: short names + kind detection · §9a: questions archive semantics · §9 evidence rules unchanged)
- [ ] Update `skills/take-over/PROTOCOL.md` (same)
- [ ] Append rev-C decision entries to `skills/hand-off/DECISIONS.md` and `skills/take-over/DECISIONS.md`
- [ ] `git commit -am "session-handoff v0.5-rev-C: flat-file, kind-based scope, question Open/Closed archive"`
- [ ] `git push`

### Deferred

- [ ] D1-D5 · original DEFER items from review cycle 2
- [ ] Live end-to-end integration test on a non-toy repo
- [ ] Pre-commit hook enforcing 3-way byte-identical reconcile script + templates (see questions.md Q2)
- [ ] Short README per skill (hand-off README, take-over README) with quickstart

## Open Blockers

- None. Open questions in `questions.md` are non-blocking.
