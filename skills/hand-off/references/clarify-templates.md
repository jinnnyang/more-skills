# `clarify` Templates for hand-off Branches

> Loaded when the agent needs to talk to the user during a hand-off. Every user-facing decision goes through Hermes' `clarify` tool (the AskUserQuestion equivalent) rather than a free-text message that asks for a choice. Standardising the call shape here means different sessions and different agents produce a consistent UX, and users learn what a "hand-off clarify" is going to feel like.
>
> `clarify(question, choices)` takes:
> - `question`: the question, and only the question. Don't enumerate the options inside the string — they belong in `choices`.
> - `choices`: up to 4 entries. A 5th "Other (type your answer)" option is auto-appended.
>
> The templates below are Python-ish pseudocode. Adapt to the actual tool schema of the runtime you're on.

## Priority-order cheat sheet

Pick the template that matches `prepare`'s `next_action`:

| `next_action` | Template |
| --- | --- |
| `halt_on_hard_conflicts` | §1 — per-conflict resolution |
| `challenge_required` | §2 — batched provenance challenge |
| `clarify_unsure` | §3 — batched cleanup review |
| `safe_to_apply` | (no clarify needed; §4 Git decision only) |

Step 4 (Git decision) always runs regardless of branch — see §4.

---

## §1. `halt_on_hard_conflicts`

Reality-check found HARD conflicts. Each conflict must be resolved individually — do NOT batch them into one clarify, because resolution actions vary per conflict type.

### 1.a Concurrency lock owned by a stale session

```python
clarify(
    question=(
        "The hand-off scope at <SCOPE> has a lock held by session "
        "<OTHER_SESSION_ID> from <TIMESTAMP>. "
        "That looks stale. What should we do?"
    ),
    choices=[
        "Release the lock and continue (nobody else is running)",
        "Keep the lock and abort this hand-off",
        "Investigate — pause hand-off, I'll check the other session first",
    ],
)
```

**If user picks "Release":** `uv run <SKILL_DIR>/scripts/reconcile.py unlock --scope <SCOPE>`, then re-run `prepare`.

### 1.b Doc references a deleted file

```python
clarify(
    question=(
        "walkthrough.md mentions `<PATH>` but git shows it was deleted "
        "on <DELETE_COMMIT>. Is the walkthrough entry stale, or was "
        "the path wrong to begin with?"
    ),
    choices=[
        "Walkthrough entry is stale — mark it <!-- resolved --> so cleanup archives it",
        "Path was wrong all along — I'll correct it in walkthrough.md",
        "The file was deleted by mistake — restore it (skip hand-off for now)",
    ],
)
```

### 1.c Generic HARD conflict fallback

When the conflict doesn't fit a known pattern (e.g., unexpected git working tree state):

```python
clarify(
    question=(
        "HARD conflict: <CONFLICT_DESCRIPTION_FROM_PREPARE>. "
        "How should we proceed?"
    ),
    choices=[
        "Fix it now — I'll describe what to change",
        "Skip this conflict — treat as SOFT (log to questions.md) and continue",
        "Abort hand-off — I want to investigate manually",
    ],
)
```

After each resolution, **re-run `prepare`**. Only continue when `next_action` is no longer `halt_on_hard_conflicts`.

---

## §2. `challenge_required` (multi-hop trust health)

`prepare` returned `health.inferred_samples` (up to 3 items). Present them in **one batched clarify** with per-item structured choices — do NOT open three separate clarifies (context-switching cost defeats the challenge).

Two acceptable shapes depending on runtime capabilities:

### 2.a Preferred: one clarify per invariant (batched in the same turn)

Some runtimes support multiple `clarify` calls in a single assistant turn. When available, this is cleaner than a compound question.

```python
# In the SAME turn, issue N (≤ 3) clarify calls back-to-back.
for i, sample in enumerate(health["inferred_samples"], start=1):
    clarify(
        question=(
            f"[Invariant {i}/{N}] context.md says:\n"
            f"    {sample['line']}\n"
            f"(source: {sample['tag']}, {sample['age_days']} days old)\n"
            f"Is this still true?"
        ),
        choices=[
            "Still valid — re-attribute to me as of today",
            "Stale — delete the line",
            "Rewrite — I'll provide the correction",
        ],
    )
```

### 2.b Fallback: one compound clarify with lettered items

When the runtime only supports one clarify at a time, encode the batch in the question body:

```python
clarify(
    question=(
        "Multi-hop trust check flagged these inferred invariants "
        "(context.md, hop count = " + str(health["hop_count"]) + "):\n\n"
        "(A) " + samples[0]["line"] + "\n"
        "(B) " + samples[1]["line"] + "\n"
        "(C) " + samples[2]["line"] + "\n\n"
        "For each, reply with A/B/C followed by keep / stale / rewrite. "
        "Example: 'A keep, B stale, C rewrite: new wording here'."
    ),
    choices=[
        "All still valid — re-attribute all to me as of today",
        "All stale — delete all three",
        "Mixed — I'll type per-item decisions",
    ],
)
```

After the user answers, apply the decisions to `context.md` via `write-atomic`, then **re-run `prepare`**. Do not proceed to Step 2 write until `next_action` moves out of `challenge_required`.

**Anti-pattern:** silently upgrading `[inferred:*]` to `[user:<today>]` "because the user didn't push back". The user must have actively confirmed each item in the current session for that upgrade to be valid.

---

## §3. `clarify_unsure` (cleanup ambiguity)

`prepare`'s `cleanup_plan.unsure` contains one or more entries the classifier couldn't confidently bucket. Also show the auto-classified lists so the user can veto them before apply.

### 3.a Standard batched cleanup review

```python
plan = prepare_output["cleanup_plan"]

question_body = (
    "Cleanup plan review before applying:\n\n"
    f"  Auto-classified (will apply on OK):\n"
    f"    CLEAR (delete): {len(plan['clear'])} entries\n"
    f"    STALE (delete): {len(plan['stale'])} entries\n"
    f"    ARCHIVED (move to Closed): {len(plan['archived'])} entries\n\n"
    f"  UNSURE ({len(plan['unsure'])} entries need your call):\n"
)
for i, item in enumerate(plan["unsure"], start=1):
    question_body += f"    [{i}] {item['header']} — {item['reason']}\n"
question_body += (
    "\nReply with per-item drop/keep decisions, or take a group action."
)

clarify(
    question=question_body,
    choices=[
        "Apply plan as shown — keep all UNSURE items (safest)",
        "Apply plan and drop all UNSURE items too",
        "Show me each UNSURE item as a separate follow-up",
        "Abort cleanup — I want to edit walkthrough.md / questions.md manually first",
    ],
)
```

### 3.b Per-item UNSURE drill-down (when user picks the third option above)

```python
for i, item in enumerate(plan["unsure"], start=1):
    clarify(
        question=(
            f"[UNSURE {i}/{len(unsure)}] {item['header']}\n"
            f"Body preview: {item['preview']}\n"
            f"Classifier's reason for UNSURE: {item['reason']}\n"
            f"Keep or drop?"
        ),
        choices=[
            "Keep — I'll mark it <!-- keep --> in the source",
            "Drop — treat as resolved, will not survive next hand-off",
            "Skip — leave as UNSURE for now, decide next time",
        ],
    )
```

After UNSURE decisions, run `clean-up --apply` — apply preserves UNSURE by default; the user's keep/drop answers translate into `<!-- keep -->` / `<!-- resolved -->` markers you set on the source entries before applying.

---

## §4. Git decision (Step 4, all branches)

Runs regardless of `next_action`. Never auto-commit — always ask.

### 4.a Standard commit prompt

```python
clarify(
    question=(
        "Hand-off docs updated. Git status:\n"
        f"  Modified: {git_modified_count} file(s)\n"
        f"  Untracked: {git_untracked_count} file(s)\n"
        "How should I finalise?"
    ),
    choices=[
        "Commit now — use default message 'docs(handoff): session hand-off — {status}'",
        "Stage only (git add) — I'll write the commit message myself",
        "Leave uncommitted — I want to review the diff before staging",
        "Custom commit message — I'll type it in the follow-up",
    ],
)
```

### 4.b Custom commit message follow-up

Only fire when the user picked the last option above:

```python
clarify(
    question=(
        "What commit message should I use? "
        "(will be committed with `git commit -m '<your text>'`)"
    ),
    choices=[
        "docs(handoff): session hand-off — {status}",  # default
        "docs(handoff): checkpoint before context reset",
        "docs(handoff): phase complete — <phase name>",
    ],
    # user can also type freely via the auto-appended "Other" option
)
```

---

## §5. Anti-patterns (things not to do)

1. **Enumerating options inside `question` and passing empty `choices`.** Hermes' UI can only render selectable rows out of `choices`. Options written into the question text become dead prose — the user reads them but can't click them.
2. **Batching unrelated decisions into one clarify.** "Should I release the lock, commit now, and drop these UNSURE items?" is unreadable, and the user can't answer half of it. One decision per call.
3. **Free-text prompts when the answer space is finite and known.** If you can list the choices ahead of time, list them. Ask via `choices` rather than "please reply with A, B, or C".
4. **Auto-answering on the user's behalf.** If the safe choice really is obvious, skip the clarify and just tell the user what you're about to do. If it needs a decision, the user makes it — not you. That includes the honest cases: "still valid" on a `challenge_required` item, "don't stage" on the Git question — these are decisions, and you don't get to answer them silently just because the odds look good.
5. **Skipping the re-run of `prepare` after resolving a HALT or CHALLENGE.** Reality may have shifted underneath you while the user was answering. Re-run `prepare` and let the branch move on its own, or find out it hasn't.
