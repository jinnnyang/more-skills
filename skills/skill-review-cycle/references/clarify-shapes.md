# `clarify` shapes for skill-review-cycle

> Loaded whenever the review workflow needs to talk to the user. Every user-facing decision runs through Hermes' `clarify(question, choices)` rather than a free-text enumeration.
>
> The rule to hold onto: options belong in `choices`, and the question alone belongs in `question`. Hermes' UI auto-appends a fifth "Other (type your answer)" option, so up to four in `choices` is enough.

## §1. After Step 2 · present the review + ask for direction

```python
clarify(
    question=(
        "I've written the review report at REVIEW-<DATE>.md. "
        "Ranked P0 through P3. Before landing anything, "
        "I have <N> key judgment call(s) that need your direction. "
        "How do you want to proceed?"
    ),
    choices=[
        "Land the plan as-is — start with P0, one commit at a time",
        "I want to see the report first — pause here so I can read it",
        "Skip some items — I'll tell you which P0/P1 to drop",
        "Rework the plan — I disagree with a priority",
    ],
)
```

Follow with a per-judgment-call `clarify` for each Q in the report's "Key Judgment Calls" section (one call per Q).

## §2. Per judgment call

```python
clarify(
    question=(
        "[Q<n>] <the question, one sentence>\n\n"
        "My recommendation: <A/B/C> — <one-sentence rationale>. "
        "Do you agree, or pick differently?"
    ),
    choices=[
        "<Option A label>",
        "<Option B label>",
        "<Option C label>",
        "Explain the trade-offs more first — I'm not ready to decide",
    ],
)
```

## §3. After each P1 lands · checkpoint

```python
clarify(
    question=(
        "P1<letter> landed as <commit-sha>. Diff summary: <N> files, <+M/-K> lines. "
        "Next up: P1<letter+1> · <one-line description>. Proceed?"
    ),
    choices=[
        "Proceed — do P1<letter+1> now",
        "Pause — I want to eyeball the last commit first",
        "Change direction — skip P1<letter+1>, jump to a different item",
        "Wrap up here — mark remaining items as backlog",
    ],
)
```

## §4. After P0+P1 done · decide about P2/P3

```python
clarify(
    question=(
        "P0/P1 all landed. Remaining backlog:\n"
        "  P2 items: <count> — <one-line themes>\n"
        "  P3 items: <count> — <one-line themes>\n"
        "How far do you want to go?"
    ),
    choices=[
        "Continue — knock out P2 and P3 in one go",
        "P2 only — leave P3 for later",
        "Wrap up — mark P2/P3 as backlog in REVIEW-<date>.md and stop",
        "Save a new skill first — I want to preserve what we learned",
    ],
)
```

## §5. Discovered scope creep — user gate

Only fire if during landing you find an issue that would require touching a sibling skill or an unrelated area:

```python
clarify(
    question=(
        "While landing P1<letter>, I noticed <issue> in <sibling scope / file>. "
        "This is technically out of scope for this review. Handle now, or log it for later?"
    ),
    choices=[
        "Log it and continue — add to REVIEW-<date>.md 'Discovered but out of scope'",
        "Handle it now — this review pass grows to include it",
        "Stop and re-scope — open a fresh review for that area",
    ],
)
```

## Anti-patterns

1. **`clarify` with `question="A) foo B) bar" choices=[]`.** The UI can't lift options out of the question text. They become dead prose the user reads but can't click.
2. **Batching independent decisions into one clarify.** "Should I land P0 and drop P1c and commit as `foo`?" is unreadable, and half of it can't be answered without splitting the question apart anyway. One decision per call.
3. **Auto-answering because the safe choice looks obvious.** If it's obvious enough to auto-answer, it's obvious enough to skip the clarify entirely — just tell the user what you're about to do. If it isn't obvious, the user picks, not you.
4. **Skipping the checkpoint after each P1.** You save four tool calls; you lose the ability to bail out mid-pipeline. That's a bad trade the second something goes wrong.
