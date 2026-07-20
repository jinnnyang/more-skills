# `prepare` Output → `next_action` Branching Guide

> Loaded by hand-off Step 1/3 when the agent needs to decide how to react to `prepare`'s JSON output. Each `next_action` value has a strict contract; violating it leaks trust or produces inconsistent docs.
>
> For the exact `clarify()` call shape used in each branch, see `clarify-templates.md` in this same directory.

## Priority order (top-down)

Each branch is strictly more permissive than the previous. Pick the highest one that fires.

```
halt_on_hard_conflicts   ← docs inconsistent (reality-check failed)
challenge_required       ← docs unhealthy (multi-hop trust degradation)
clarify_unsure           ← cleanup ambiguity (per-entry classification unclear)
safe_to_apply            ← green path
```

## `halt_on_hard_conflicts`

**Trigger:** `reality.hard_conflicts` is non-empty. Common causes: concurrency lock owned by another session, filesystem missing files the docs reference, git working tree in an unexpected state.

**Contract:**
1. Do NOT touch Step 2 (write) or Step 3 (apply). Docs are in an inconsistent state; further writes make it worse.
2. Surface each HARD conflict via `clarify` with structured choices. Common resolutions:
   - Concurrency lock stale → `unlock --scope <path>` after user confirms nobody else is running.
   - Reference to a deleted file → `clarify`: is the file actually gone (walkthrough entry is stale) or was the path wrong all along?
3. After the user resolves each conflict, re-run `prepare`. Only continue when `next_action` is not `halt_on_hard_conflicts`.

The reconcile process exits with code 1 in this branch so calling scripts can detect the halt.

## `challenge_required`

**Trigger:** `health == "unhealthy"` — two or more issues fired. Typical multi-hop signature: `hop_count ≥ 3`, `inferred_pct ≥ 40`, `untagged_pct ≥ 50`.

**Contract:**
1. **Before Step 2 write.** This is the only branch that mutates docs before Step 2.
2. Take `health.inferred_samples` from `prepare`'s output (up to 3 items).
3. Present them in ONE batched `clarify` with per-item structured choices:
   - `still valid` → upgrade the tag to `[user:<today>]` (elevates provenance without deleting the fact).
   - `stale` → delete the line.
   - `rewrite` → user provides corrected wording; new line is tagged `[user:<today>]`.
4. Apply the user's decisions to `context.md` via `write-atomic`.
5. Re-run `prepare`. Only continue when `next_action` has moved out of `challenge_required` (usually to `safe_to_apply` or `clarify_unsure`).

**Why this matters:** the whole point of the challenge is to break single-directional trust inheritance. Skipping it (or auto-answering "still valid" on the agent's behalf) defeats the mechanism and lets the hallucination cascade continue. If the user pushes back on any single item, honor it — the user is the ground-truth anchor.

## `clarify_unsure`

**Trigger:** `cleanup_plan.unsure` is non-empty. Cleanup couldn't confidently classify one or more walkthrough / questions entries.

**Contract:**
1. Perform Step 2 (write task / walkthrough / questions / context) as normal.
2. Present all UNSURE items as a **single batched** `clarify` prompt with structured choices (keep vs drop each entry).
3. Also show `cleanup_plan.clear` / `.stale` / `.archived` lists so the user can veto individual actions before the batch apply.
4. Regardless of user decisions on UNSURE, run `clean-up --apply` (Step 3) — apply preserves UNSURE by default. The user's answers guide which UNSURE items to explicitly re-mark as `<!-- keep -->` / `<!-- resolved -->` for the next cycle.

## `safe_to_apply`

**Trigger:** No HARD conflicts, no health issues at or above `unhealthy`, no UNSURE items.

**Contract:**
1. Perform Step 2 write.
2. Show a one-line summary of what Step 3 will remove (X CLEAR, Y STALE, Z ARCHIVED) — no batched `clarify` needed.
3. Run `clean-up --apply` (Step 3).

Even in this branch, still run `clean-up --apply` — it produces the audit trail (`applied: {walkthrough.md: N, questions.md: M, archived_to_closed: A}`) that the Step 5 final summary reports back to the user.

## Health verdicts under the hood

`prepare` computes `health.health` ∈ `{fresh, healthy, warning, unhealthy}`:

| Verdict | Meaning | Triggers `challenge_required`? |
| --- | --- | --- |
| `fresh` | No hand-off commits yet (hop 0) | No |
| `healthy` | Zero issues | No |
| `warning` | Exactly one issue | No (guidance mentions the issue as a soft heads-up) |
| `unhealthy` | Two or more issues | **Yes** |

Issue rules (see `PROTOCOL.md §11a`):

- `hop_count ≥ 3` AND `inferred_pct ≥ 40` → hallucination-cascade risk
- `hop_count ≥ 3` AND `untagged_pct ≥ 50` → untraceable-source risk
- `stale_invariants_count ≥ 5` (git blame > 30 days) → currency risk
- `soft_conflicts ≥ 3` unresolved in `questions.md` → debt-accumulation risk
