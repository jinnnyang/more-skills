# `prepare` Output → `next_action` Branching Guide

> Loaded during hand-off Steps 1 and 3, when you need to figure out what `prepare`'s JSON is telling you to do. Each `next_action` value comes with a specific contract, and cutting corners on one branch is what quietly rots the whole trust chain across sessions.
>
> For the exact `clarify()` call shapes each branch uses, see `clarify-templates.md` in this same directory.

## Priority order (top-down)

Each branch is more permissive than the one above it. Pick the highest one that applies:

```
halt_on_hard_conflicts   ← docs inconsistent (reality-check failed)
challenge_required       ← docs unhealthy (multi-hop trust degradation)
clarify_unsure           ← cleanup ambiguity (per-entry classification unclear)
safe_to_apply            ← green path
```

## `halt_on_hard_conflicts`

**Trigger:** `reality.hard_conflicts` is non-empty. Usual suspects: another session still holds the concurrency lock, the filesystem is missing files that docs reference, or the git working tree is in an unexpected state.

**Contract:**
1. Do not touch Step 2 (write) or Step 3 (apply). The docs are already inconsistent, and any further writing widens the gap.
2. Surface each HARD conflict through `clarify` with structured choices. Typical resolutions:
   - Stale concurrency lock → run `unlock --scope <path>` after the user confirms nobody else is running.
   - Reference to a deleted file → ask via `clarify`: is the file genuinely gone (so the walkthrough entry is stale), or was the path wrong from the start?
3. Once the user resolves each conflict, re-run `prepare`. Only move on when `next_action` is no longer `halt_on_hard_conflicts`.

The reconcile process exits with code 1 on this branch so calling scripts can detect the halt.

## `challenge_required`

**Trigger:** `health == "unhealthy"`, i.e. two or more issues fired at once. The most common signature is a scope that has been handed off three or more times, with `inferred_pct ≥ 40` and `untagged_pct ≥ 50`.

**Contract:**
1. Handle this before Step 2's write. It's the only branch that mutates docs before you write anything else.
2. Take `health.inferred_samples` from `prepare`'s output (up to 3 items).
3. Present them in one batched `clarify` with per-item structured choices:
   - `still valid` → upgrade the tag to `[user:<today>]`. This elevates the provenance without deleting the fact.
   - `stale` → delete the line.
   - `rewrite` → user gives corrected wording, and the new line is tagged `[user:<today>]`.
4. Apply the user's decisions to `context.md` via `write-atomic`.
5. Re-run `prepare`. Only continue when `next_action` has moved on (usually to `safe_to_apply` or `clarify_unsure`).

**Why this branch exists at all.** By the third or fourth hand-off, most of what a scope "knows" is inherited from an earlier agent that inherited it from someone before. If a fact was hallucinated on hop 1, hop 2 quoted it as authority, hop 3 stopped questioning it, and by hop 4 it's just part of the furniture. That's the cascade. The challenge exists to break it: the user sees the top few suspiciously-old inferred invariants and either re-confirms them (turning them into `[user:<today>]` ground-truth) or throws them out. If you auto-answer "still valid" on the user's behalf, or you skip the challenge because the docs "look fine", you're the reason someone downstream will later trust a line that was never true. When the user does push back on a specific item, honor it — that's the signal the whole mechanism was built to catch.

## `clarify_unsure`

**Trigger:** `cleanup_plan.unsure` is non-empty. Cleanup couldn't confidently classify one or more walkthrough / questions entries.

**Contract:**
1. Do Step 2 (write task / walkthrough / questions / context) as normal.
2. Present every UNSURE item in one batched `clarify` with structured choices (keep or drop each entry).
3. Also show `cleanup_plan.clear` / `.stale` / `.archived` so the user can veto individual actions before you apply the batch.
4. Run `clean-up --apply` (Step 3) regardless of what the user picked on UNSURE — apply preserves UNSURE by default. The user's answers just tell you which UNSURE items to explicitly re-mark as `<!-- keep -->` or `<!-- resolved -->` before the next cycle.

## `safe_to_apply`

**Trigger:** No HARD conflicts, no health issues at or above `unhealthy`, no UNSURE items.

**Contract:**
1. Do Step 2 write.
2. Show a one-line summary of what Step 3 will remove (X CLEAR, Y STALE, Z ARCHIVED). No batched `clarify` needed on this branch.
3. Run `clean-up --apply` (Step 3).

Run `clean-up --apply` even on the green path. It produces the `applied: {walkthrough.md: N, questions.md: M, archived_to_closed: A}` audit trail that Step 5's final summary reports back to the user.

## Health verdicts under the hood

`prepare` computes `health.health` ∈ `{fresh, healthy, warning, unhealthy}`:

| Verdict | Meaning | Triggers `challenge_required`? |
| --- | --- | --- |
| `fresh` | No hand-off commits yet (hop 0) | No |
| `healthy` | Zero issues | No |
| `warning` | Exactly one issue | No — guidance mentions the issue as a soft heads-up |
| `unhealthy` | Two or more issues | **Yes** |

Issue rules (see `PROTOCOL.md §11a`):

- `hop_count ≥ 3` AND `inferred_pct ≥ 40` → hallucination-cascade risk
- `hop_count ≥ 3` AND `untagged_pct ≥ 50` → untraceable-source risk
- `stale_invariants_count ≥ 5` (git blame > 30 days) → currency risk
- `soft_conflicts ≥ 3` unresolved in `questions.md` → debt-accumulation risk
