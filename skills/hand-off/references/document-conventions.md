# Document Conventions

> Loaded by hand-off Step 2 when the agent is writing content to the four core documents. Covers what each doc must contain, how the cleanup classifier reads it, and the provenance-tag requirement on `context.md`.

## The four core documents

| File | Purpose | Cleanup semantics |
| --- | --- | --- |
| `task.md` | Current in-progress `todo` list (verbatim) | Overwritten every hand-off |
| `walkthrough.md` | Dated log of decisions, changes, surprises | Aggressively pruned by `clean-up` |
| `questions.md` | Open blockers + Closed archive | Resolved entries auto-archived to `## Closed` |
| `context.md` | Long-lived project invariants + constraints | Strictly additive; `prepare` tracks provenance |

## `task.md`

- Persist the current `todo` list **verbatim**. Do NOT summarize away open items, and do NOT reorder.
- Preserve status markers (`pending` / `in_progress` / `completed` / `cancelled`).
- If a task was cancelled and superseded, add the successor task after the cancelled one — don't rewrite history.

## `walkthrough.md`

- Append a dated entry for the current session with the header format:

  ```
  ## YYYY-MM-DD — <slug>
  ```

  Deviating from this format disables the cleanup classifier (see PROTOCOL §9a). The date and em-dash separator are required.

- Content: decisions made & why, files changed (with paths), surprises encountered. **NOT** a transcript replay — the walkthrough is a distilled log, not chat history.

- Explicit classification markers where the classifier's heuristics might misread intent:
  - `<!-- keep -->` on an entry you always want retained.
  - Or use keywords `lesson` / `surprise` / `decision` / `invariant` in the header — these trigger the KEEP heuristic automatically.
  - `<!-- resolved -->` on an entry the next hand-off should CLEAR (walkthrough only — for questions, `<!-- resolved -->` archives rather than clears).

## `questions.md`

Two-section structure with different retention semantics:

```markdown
## Open
### Q1 · Should we use Postgres or MySQL?
<question body>

## Closed
### Q0 · Should we build the frontend in React or Vue? <!-- resolved -->
<archived body — kept permanently>
```

- Entry-level headers use `###` (three hashes). Section headers use `##`.
- Mark resolved entries under `## Open` with `<!-- resolved -->` — the next `clean-up --apply` will **move** them to `## Closed` (permanent history, not deletion).
- Manually placing entries directly under `## Closed` is fine; they'll stay there indefinitely.

## `context.md` (provenance rules)

`context.md` is **strictly additive-only**. It records long-lived invariants that survive multiple hand-offs — architectural rules, environmental facts, decisions that would break the system if broken.

### Walkthrough-to-Context Promotion Rule

Prior to running cleanup, review any walkthrough entries that are planned to be pruned (CLEAR or STALE). If an entry contains a long-term architectural decision or project invariant, reformat it and append it to the bottom of `context.md` so the knowledge is preserved after cleanup deletes the walkthrough entry.

### Provenance tags (required on every bullet)

Prefix each `context.md` bullet with one of the five source tags below. `prepare` uses these tags to compute health and detect hallucination cascade across hops. See `PROTOCOL.md §11a` for the full multi-hop trust model.

| Tag | Example | When to use |
| --- | --- | --- |
| `[git:<short-sha>]` | `[git:a3f2c9] Auth tokens are JWT with 24h expiry.` | Invariant is backed by a specific commit you can point to. |
| `[user:<YYYY-MM-DD>]` | `[user:2026-07-17] DATABASE_URL is read from .env.local` | User confirmed in-session on that date. |
| `[test:<test-name>]` | `[test:test_auth_expiry] JWT expiry is 24 hours.` | An automated test enforces it. |
| `[inferred:<session-id>]` | `[inferred:sess-abc123] API rate limit is ~100 rps.` | Agent's own inference; expect challenge on later hops. |
| `[unknown]` | `[unknown] Redis is deployed as single instance.` | Explicit "we don't know where this came from" — better than untagged. |

### Provenance-tag anti-patterns

- **Do NOT fabricate a `[git:*]` tag by guessing a SHA.** If the source is memory or an unattributed carry-over from a previous hop, `[inferred:*]` or `[unknown]` is the honest choice. Wrong provenance is worse than missing provenance.
- **Do NOT leave bullets untagged.** Untagged lines inflate `untagged_pct` and count against the health verdict. If you truly don't know, use `[unknown]`.
- **Do NOT upgrade tags without evidence.** Only rewrite `[inferred:*]` to `[user:<today>]` after the user has actually confirmed the fact in the current session (typically via the `challenge_required` batched clarify).
