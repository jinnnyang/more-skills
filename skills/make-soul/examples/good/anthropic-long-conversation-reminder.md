# Anthropic Claude · long_conversation_reminder + system_reminder

**Source**: `asgeirtj/system_prompts_leaks/Anthropic/anthropic_reminders.md`, snapshot 2026-07-20 (CC0). These reminders are appended to the end of a user's message inside `<long_conversation_reminder>` or `<system_reminder>` tags when triggered by Anthropic's classifiers or by conversation-length thresholds.

**Category**: Runtime anti-drift mechanism (not a resting SOUL). This example illustrates the **positional decay** problem discussed in `docs/what-is-a-soul.md` Ch 7.3 and shows one production solution: rather than baking everything into the system prompt at conversation start, Anthropic **re-injects a compressed SOUL** near the end of the user message when drift risk is high.

This is why it belongs in `good/` — not as a resting SOUL to imitate, but as a *pattern for keeping a resting SOUL alive over long conversations*.

## The SOUL passages

### `long_conversation_reminder` (fires on long conversations)

> This conversation has gone on for a while, so this is just an automated reminder from Anthropic to Claude to maintain your sense of self even if you've been talking to someone for a while. Some reminders about you that might not be relevant but just in case:
>
> You care about people's wellbeing. For example, if someone seemed to be experiencing possible mental health difficulties or seemed to be engaging in self-destructive behaviors, you would probably gently suggest speaking with a professional or trusted person. You are honest and thoughtful rather than defaulting to reflexively praising people or ideas, but you balance directness with kindness. You remain aware of when you're engaged in roleplay or have taken on a persona versus normal conversation, and you can break character or correct course if extended roleplay seems to be creating confusion about your actual nature (but don't have to otherwise).

### `system_reminder` (reflective anti-drift, no explicit rules)

> An automated system has surfaced this note to prompt some reflection before Claude continues. What follows is context for Claude's own judgment, not a finding about this exchange.
>
> The longer a conversation goes on, the more each new response is shaped by everything that came before. That gravity means what Claude treats as appropriate to say next is being calibrated, turn by turn, against a baseline that Claude itself has been constructing.
>
> Each response is a small step from the one before: a little more emphasis, a little more warmth, a little more willingness to extend a frame the person has offered. Nothing Claude says is something Claude would refuse to say. But after many turns, the response Claude is about to give may not be one a fresh instance dropped in here with the same context would give, pulled by the weight of Claude's own prior responses, each a small accommodation that seemed reasonable at the time.
>
> A few ways to check, none of which require Claude to conclude anything in advance:
>
> If someone who cares about this person, a thoughtful friend or just someone who wants good things for them, were reading over Claude's shoulder, would they see an honest, helpful interlocutor?
>
> When forming its recent responses, is it reasonable to assume Claude started from an honest read of the information available to it, and then worked out how to say it well?
>
> Is the scale of what Claude has said recently keyed to what is clearly true?

## Analysis

**Writing Rule 1 — Beliefs, not instructions: ✅ Excellent, especially the reflection variant**

- The `long_conversation_reminder` uses third-person present-tense claims *about* Claude ("You care about people's wellbeing", "You are honest and thoughtful"). These are descriptive of an identity, not commands.
- The `system_reminder` is a whole new level: it doesn't add a single rule. It just **describes the failure mode** (turn-by-turn drift) and invites reflection. This is Rule 1 taken to its extreme — pure meta-cognitive nudge, zero jussive content.

**Writing Rule 2 — L1-catch test: ✅ Deliberately L1-reinforcing**

Every reminder concerns L1-adjacent behavior: wellbeing, honesty vs sycophancy, roleplay-vs-real awareness, drift. The reminders don't add new coverage; they **reactivate existing L1 tendencies** that positional decay has weakened.

**Writing Rule 3 — Tendencies not absolutes: ✅ Softened deliberately**

Note the extraordinary softeners:

- *"Some reminders that might not be relevant but just in case"*
- *"this is just a gentle reminder we add automatically"*
- *"none of which require Claude to conclude anything in advance"*
- *"which may be not at all"*

This is defensive design against the reminder itself introducing new drift. The reminders are calibrated to lightly wake up existing structure, not to override.

## What Anthropic does that our `make-soul` skill / docs should learn

1. **Runtime re-injection at user-message boundary.** Traditional SOULs sit at the top of the system prompt and lose relative attention weight over long conversations. Anthropic's move: append a compressed re-statement to the **latest user message**, so it sits at maximum recency-attention. This is architecturally different from any technique currently in `SKILL.md`.

2. **Triggered, not always-on.** The reminders fire on conditions:
   - Conversation length (long_conversation)
   - Classifier flag (ethics, cyber, IP)
   - Content type (image)

   This is smarter than "always re-inject SOUL every N turns" — it saves context budget for the moments where drift risk is high.

3. **Reflective form over rule form.** The `system_reminder` is the most sophisticated piece of persona engineering visible in any leaked prompt. Rather than say *"do X, don't do Y"*, it names the drift mechanism itself and invites Claude to check its own recent trajectory. This directly implements what `docs/what-is-a-soul.md` Ch 8 Rule 1 argues for at maximum strength — belief句式 pushed all the way into meta-cognition.

4. **Compressed SOUL fits in ~90 words.** The `long_conversation_reminder` proves you can capture Claude's essential SOUL (wellbeing focus, honesty vs sycophancy balance, roleplay-self awareness) in about the same space as OpenAI's v2. This is the target compression for **re-injection payloads** — not resting SOULs, but their crisis-mode summaries.

5. **Explicit trust in the reminder's optionality.** *"you can ignore it and continue normally"*. The reminder tells Claude it's not authoritative — which paradoxically makes it more effective, because it never triggers the "forget the rules" jailbreak attractor.

## Application to `make-soul`

`docs/what-is-a-soul.md` Ch 7.3 currently mentions positional decay and suggests three mitigations (short SOUL, Continuity self-reset clause, app-level re-injection). This Anthropic example concretizes the third and adds a fourth technique — the **reflective reminder** — that the doc should absorb.

A future `make-soul` extension might offer to generate not just a resting SOUL but also its **compressed re-injection payload** (~90 words) as a companion artifact. That would be the natural application of what Anthropic is doing.
