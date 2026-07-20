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

- Persist the current `todo` list verbatim. Don't summarise away open items, and don't reorder.
- Preserve status markers (`pending` / `in_progress` / `completed` / `cancelled`).
- If a task was cancelled and superseded, add the successor task after the cancelled one. Don't rewrite history.

## `walkthrough.md`

- Append a dated entry for the current session with the header format:

  ```
  ## YYYY-MM-DD — <slug>
  ```

  If you deviate from this format, the cleanup classifier can't read the entry and will leave it alone. See PROTOCOL §9a. The date and the em-dash separator are both required.

- Content: decisions and their reasoning, files changed (with paths), surprises encountered. The walkthrough is a distilled log, not chat history — don't replay the transcript.

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
- Mark resolved entries under `## Open` with `<!-- resolved -->`, and the next `clean-up --apply` will move them into `## Closed`. That's permanent history, not deletion.
- Placing entries directly under `## Closed` by hand is fine too; they stay there indefinitely.

## `context.md` (provenance rules)

`context.md` is **strictly additive-only**. It records the long-lived invariants that survive multiple hand-offs: architectural rules, environmental facts, decisions the system genuinely depends on.

### Walkthrough-to-Context promotion rule

Before you run cleanup, look at the walkthrough entries that are about to be pruned (CLEAR or STALE). If any of them state something that's really a long-term architectural decision or a project invariant — the kind of thing that will still be true two hand-offs from now — reformat it and append it to the bottom of `context.md`. Otherwise cleanup will delete the walkthrough entry and take the knowledge with it.

### Provenance tags (required on every bullet)

Every `context.md` bullet is prefixed with one of the five source tags below. `prepare` uses these tags to compute the health verdict and to catch hallucination cascade across hops. Full multi-hop model is in `PROTOCOL.md §11a`.

| Tag | Example | When to use |
| --- | --- | --- |
| `[git:<short-sha>]` | `[git:a3f2c9] Auth tokens are JWT with 24h expiry.` | Invariant is backed by a specific commit you can point to. |
| `[user:<YYYY-MM-DD>]` | `[user:2026-07-17] DATABASE_URL is read from .env.local` | User confirmed in-session on that date. |
| `[test:<test-name>]` | `[test:test_auth_expiry] JWT expiry is 24 hours.` | An automated test enforces it. |
| `[inferred:<session-id>]` | `[inferred:sess-abc123] API rate limit is ~100 rps.` | Agent's own inference; expect challenge on later hops. |
| `[unknown]` | `[unknown] Redis is deployed as single instance.` | Explicit "we don't know where this came from" — better than untagged. |

### Provenance-tag anti-patterns

- **Don't invent a `[git:*]` SHA.** If the fact came from memory or from an unattributed carry-over on an earlier hop, tag it `[inferred:*]` or `[unknown]`. Wrong provenance is worse than missing provenance — one is a signal, the other is a lie the next agent will trust.
- **Don't leave bullets untagged.** Untagged lines inflate `untagged_pct` and drag the health verdict down. If you honestly don't know where a line came from, `[unknown]` is the right answer.
- **Don't upgrade tags without evidence.** `[inferred:*]` becomes `[user:<today>]` only when the user actually confirmed the fact in the current session — usually through the `challenge_required` batched clarify. Silently promoting a tag because "it's probably true" is the exact failure mode the provenance system exists to prevent.
