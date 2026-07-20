---
kind: walkthrough
version: 1
last_updated: '2026-07-20T09:35:00+00:00'
last_verified: '2026-07-20T09:35:00+00:00'
last_agent: Hermes Agent (ark-code-latest)
last_writer: hand-off
session_id: sess-20260720-takeover-lock-lifecycle-bug
status: in-progress
---

# Living Work Memory & Walkthrough

> [!NOTE]
> Walkthrough is editable working memory, pruned when items resolve.
> Keep decision reasons, files changed, and surprises. Do NOT write full transcript replays.
>
> **Entry header format**: `## YYYY-MM-DD — <slug>` (required for the cleanup classifier).
>
> **Lifecycle markers** (used by `hand-off`'s Smart Cleanup):
> - `<!-- keep -->` in entry body OR any of the keywords `lesson` / `surprise` / `decision` / `invariant` in the header → KEEP forever.
> - `<!-- resolved -->` in entry header or body → CLEAR on next hand-off.
> - No marker + age > 30 days + not referenced from `task.md` / `context.md` → STALE.
> - Anything else → UNSURE (batched confirmation before deletion).

## History of Active Entries

## 2026-07-20 — take-over lock lifecycle bug found via make-soul session (bug, decision, invariant)

**Discovered during the closing hand-off of session `sess-20260720-make-soul-corpus-opt`** on `skills/make-soul/`. hand-off's `prepare` call returned `halt_on_hard_conflicts` with a `concurrency_lock_conflict` message pointing at an earlier session ID (`take-over-1784533804`). Force-unlock resolved that specific instance; this task tracks the underlying bug so the next user isn't ambushed.

### Timeline of the bug's manifestation

- `~07:50Z` — chat session starts. User invokes `take-over` skill. take-over runs Step 2 · Reality Check via `check-reality --apply-soft-conflicts --session-id take-over-1784533804 --agent "Hermes Agent"`. This call **wrote** `.handoff.lock` (see mechanism below).
- take-over finished Steps 3–7 successfully, produced the resume greeting, and handed control to normal chat. **No release of the lock in any code path called by take-over.**
- Session continued for ~1h15m of normal work (make-soul optimization + commits).
- `~09:04Z` — user invokes `hand-off` skill. hand-off's `prepare` call uses a fresh session-id `sess-20260720-make-soul-corpus-opt` — different from the lock's session-id — so `check_lock_conflict` treats it as a hostile lock. Age was only ~74 minutes, well under the 2-hour TTL, so TTL bypass did not fire. Reported as HARD conflict.
- Recovery: manual `reconcile.py unlock`, task.md path-reference fixes, prepare re-run → `safe_to_apply`, hand-off completed cleanly (commit `df1200d`).

### Mechanism (root cause, three-layer)

**Layer 1 — `_check_reality_scope` at reconcile.py lines 745-763** silently promotes a read-only op to a write op when `--session-id` is present:

```python
# reconcile.py line 754-757 (take-over copy, md5 2fd7af2c…)
if session_id:
    lock_err = acquire_lock(scope, session_id, agent)
else:
    lock_err = check_lock_conflict(scope, session_id)
```

The branch is on session-id presence, not on caller intent. take-over's SKILL.md always passes `--session-id` (to identify who's checking), so it always trips `acquire_lock`.

**Layer 2 — `acquire_lock` at lines 281-301** writes `.handoff.lock` via `O_CREAT | O_EXCL` — no rollback, no owning context. Once written, the caller inherits release responsibility.

**Layer 3 — `release_lock` is only invoked at line 1208** inside `cmd_clean_up` (a hand-off-only command). take-over never calls `clean-up`, so the lock take-over acquired is never released by take-over. It only clears if a subsequent `hand-off` completes cleanup in the same session-id, or when TTL (7200s) expires.

This is not a race condition or a concurrency issue — it's a **lifecycle contract that assumes take-over and hand-off run back-to-back inside the same shell**. That's a wrong assumption. Users pause between them for arbitrary durations.

### Why take-over's §0a stale-lock fallback didn't save us

take-over `SKILL.md` line 276 does document the case:

> If the hard conflict is a stale lock file (`concurrency_lock_conflict`), prompt the user: "A stale session lock was found. Would you like to force release the lock?"

But that fallback only fires **when take-over starts and finds someone else's lock**. It does not cover **take-over's own leaked locks** haunting a later hand-off. Direction of the fallback is wrong for this failure mode.

### Fix landscape (three options)

Ranked by delivery cost / robustness:

- **A · Doc-only** — take-over SKILL.md Step 7 adds an explicit `unlock` step at the end. Cost: 15 min. Fragile if take-over aborts mid-flow. Legitimate as a stopgap.
- **B · Read-only preflight `--acquire-lock` flag (recommended)** — `_check_reality_scope` gets a flag defaulting to false. take-over's SKILL.md is updated to call `check-reality` without the flag; hand-off's `prepare` (which composes check-reality + cleanup) passes the flag. Cost: ~1 hour (code change + test + ADR + doc updates). Correct semantics: reads don't take write-locks.
- **C · Context-manager lock (`with acquired_lock(...)`)** — biggest refactor, doesn't fit check-reality's shape. Rejected in this walkthrough as over-engineered for this bug.

Author (Hermes Agent) recommends **B**. It fixes the class of bug, not the instance.

### Surprises

- The bug is a straight-line consequence of one small design choice (session-id-triggers-acquire) but it's invisible in individual code review because the acquire is inside a function whose name suggests it's a check. The fix is essentially "make the write-y-ness of `_check_reality_scope` explicit at the call site". Naming discipline would have prevented this.
- `REVIEW-2026-07-20.md` line 103 already flagged "no tests yet for lock handling" — this bug is exactly the shape that gap invites. A test that "check-reality without --acquire-lock leaves the filesystem clean" would have caught the class from day one.
- `hand-off` and `take-over` have divergent `reconcile.py` copies (different md5). Not obvious from the outside. Whatever fix lands, needs to answer: parity or independent evolution?

### Files that will change under option B

- `skills/take-over/scripts/reconcile.py` — add `--acquire-lock` flag; branch on it inside `_check_reality_scope`.
- `skills/take-over/SKILL.md` — Step 2 command example updated (no flag); optional new note in the Prerequisites / semantics section.
- `skills/take-over/DECISIONS.md` — new ADR describing the semantic split. Supersedes any earlier ADR that assumed check-reality would acquire (none found on grep, but check).
- `skills/take-over/scripts/tests/` — new test file (or extension of existing pytest suite) covering the flag semantics.
- `skills/hand-off/` — analogous updates once parity question is resolved.

<!-- keep -->

---

<session-tools-log>
[]
</session-tools-log>
