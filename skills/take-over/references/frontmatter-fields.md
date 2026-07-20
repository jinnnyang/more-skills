# Handoff Frontmatter — Field Reference

> Enum values and format rules for the YAML frontmatter block at the top of every handoff document (`context.md` / `task.md` / `walkthrough.md` / `questions.md` / `plan.md` / `review.md`).
>
> Enforced by `scripts/reconcile.py validate`. Any value outside the enums below is a HARD conflict and will block take-over's Step 1.

## Required fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `kind` | ✅ | enum | See §"kind enum" below. Must match the file's semantic role. |
| `version` | ✅ | integer | Schema version. Currently `1`. |
| `last_updated` | ✅ | ISO-8601 string | **Must include timezone offset** (e.g. `2026-07-20T14:30:00+08:00` or `…Z`). Naive datetimes are rejected. |
| `last_verified` | ✅ | ISO-8601 string \| `SKIPPED` | When reality-check last ran. Use the literal `SKIPPED` if you deliberately skipped verification. Timezone-aware if a real timestamp. |
| `last_agent` | ✅ | string | Free-form identifier of the agent that last wrote the file, e.g. `claude-sonnet-4 via Hermes/devops`. |
| `last_writer` | ✅ | enum | See §"last_writer enum" below. |
| `status` | ✅ | enum | See §"status enum" below. |

## Optional fields

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | Hermes session ID, if the runtime exposes it. Included so `walkthrough.md` entries can be traced via `session_search`. |

Everything else in the frontmatter is rejected (frontmatter root is a mapping; unknown top-level keys are tolerated by the validator but discouraged — reserve them for future protocol revisions).

---

## Enum: `kind`

Must be **exactly one** of:

```
context
task
walkthrough
questions
plan
review
```

The value must match the file's semantic role — a file named `task.md` with `kind: context` is a HARD conflict.

## Enum: `status`

Must be **exactly one** of:

```
in-progress       ← default for new/active work
blocked           ← waiting on a human answer or external dependency
phase-complete    ← this phase done, but doc still relevant
archived          ← work finished / abandoned; kept for history
```

> ⚠️ **`complete` is NOT a valid value.** Use `phase-complete` (still-referenceable milestone) or `archived` (fully retired). The word "complete" alone is ambiguous about whether the document is still live.

## Enum: `last_writer`

Must be **exactly one** of:

```
hand-off       ← file was last written by the hand-off skill's flow
take-over      ← file was last written by the take-over skill (e.g. SOFT conflict logging, init seeding, acceptance-review remediation)
user           ← the human user hand-edited it
migration      ← written by scripts/reconcile.py init from a template — treat as "seeded, not yet meaningfully populated"
```

`last_writer: migration` on **every** doc in a scope is a signal that the scope was only initialized and never actually handed off. The acceptance-review step (`review-handoff`) treats this as a REJECT-level issue unless the caller passes `--allow-fresh`.

---

## Timestamp format examples

Valid:

```
last_updated: 2026-07-20T14:30:00+08:00
last_updated: 2026-07-20T06:30:00Z
last_updated: 2026-07-20T06:30:00+00:00
```

Invalid (naive → rejected):

```
last_updated: 2026-07-20T14:30:00           # missing timezone
last_updated: 2026-07-20                    # date only, no time
last_updated: "20/07/2026 14:30"            # non-ISO-8601
```

The `SKIPPED` sentinel is only valid for `last_verified`, not for `last_updated`.

---

## Cross-references

- `PROTOCOL.md` §6 — canonical frontmatter block description.
- `DECISIONS.md` 2026-07-16 v0.3 ⑥ — kind enum rationale.
- `DECISIONS.md` 2026-07-16 rev-2 R2 — MVP frontmatter minimum surface.
- `scripts/reconcile.py` `VALID_KINDS` / `VALID_STATUS` / `VALID_WRITERS` — source of truth for the validator.
