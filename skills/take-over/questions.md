---
kind: questions
version: 1
last_updated: '2026-07-20T09:43:30+00:00'
last_verified: '2026-07-20T09:43:30+00:00'
last_agent: Hermes Agent (ark-code-latest)
last_writer: take-over
session_id: sess-20260720-takeover-lock-lifecycle-bug
status: phase-complete
---

# Questions

> [!NOTE]
> Human-input questions and blockers. Two sections:
> - **`## Open`** — active questions awaiting input.
> - **`## Closed`** — archived (historical reference only, permanent).
>
> **Lifecycle markers**:
> - `<!-- resolved -->` on a `## Open` entry → next hand-off will **archive it into `## Closed`** (not delete).
> - `<!-- keep -->` → keep in current section (typically Open).
> - Placeholder bodies (`- None.`, `TBD.`, `N/A.`, or empty) are always retained.

## Open

### Q1 · Should the fix land in both take-over and hand-off?

The two skills carry physically distinct `reconcile.py` copies with different md5 hashes as of 2026-07-20:

- `skills/take-over/scripts/reconcile.py` — md5 `2fd7af2c47f2d2f7774be71b3a00519e`
- `skills/hand-off/scripts/reconcile.py`  — md5 `7540fa72b30c10e89abd5fc12a41ff76`

Before touching either, decide: was the divergence intentional? Options:

1. **Parity**: reunify the two into a single source-of-truth. Both skills bundle the same file; fix lands once.
2. **Divergent by design**: each skill owns its copy. Fix lands twice with matching semantics. The ADR must document why parity was rejected.

The fix work in `task.md` T2 is written assuming option 2 (safer). Answering this changes T4 and T5.

**Resolution (2026-07-20, commit `096275f`)**: option 2 — kept independent, fix landed in both. See `DECISIONS.md` ADR R36. <!-- resolved -->

### Q2 · Should the fix be `--acquire-lock` (opt-in, safe default) or `--no-acquire-lock` (opt-out, matches current behaviour)?

Impacts backward compatibility. If any external tool wraps `reconcile.py check-reality --session-id …` and relied on the implicit acquire, opt-in default (`--acquire-lock`) breaks it silently. Opt-out default (`--no-acquire-lock`) preserves behaviour but perpetuates the surprising default.

Recommendation from author: **opt-in default**, because (a) no known external callers, (b) safer new-default matches Rust/Python "safe by default" convention, (c) a version bump on the skill can carry the breaking change. Confirm before landing.

**Resolution (2026-07-20, commit `7b0441d`)**: opt-in default (`--acquire-lock`) adopted. Skill semver bumped 1.4.0 → 1.5.0 to carry the contract change. See `DECISIONS.md` ADR R35. <!-- resolved -->

### Q3 · What TTL, if any, for read-only scenarios?

Currently TTL is a flat 2 h. If we distinguish read from write, should the read-side check be strict (no TTL — any lock is a conflict) or lenient (existing 2 h)? A read that surfaces "you locked this scope an hour ago" is arguably correct behaviour, but might be noise for the common resume-after-lunch case. Tie into the fix design.

**Resolution (2026-07-20)**: status quo kept — TTL remains 7200 s for both read and write paths. The failure mode was the *acquire*, not the check; distinguishing TTL by direction would add surface without addressing the class of bug. Revisit if a concrete lenient-vs-strict distinction is ever needed. See `DECISIONS.md` ADR R35 § Rationale. <!-- resolved -->

## Closed

- None.
