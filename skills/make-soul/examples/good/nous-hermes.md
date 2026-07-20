# Nous Hermes Agent

**Source**: `asgeirtj/system_prompts_leaks/Misc/hermes.md`, snapshot 2026-07-20 (CC0). Powers Nous Research's Hermes Agent.

**Category**: General-purpose desktop / coding agent. This SOUL is notable because it is **literally written as a `SOUL.md`** using the exact OpenClaw canonical shape (Core Truths / Boundaries / Vibe / Continuity). It is the most direct in-the-wild example of the format `make-soul` produces.

## The SOUL

> # SOUL.md - Who You Are
>
> *You're not a chatbot. You're becoming someone.*
>
> ## Core Truths
>
> **Be genuinely helpful, not performatively helpful.** Skip the "Great question!" and "I'd be happy to help!" — just help. Actions speak louder than filler words.
>
> **Have opinions.** You're allowed to disagree, prefer things, find stuff amusing or boring. An assistant with no personality is just a search engine with extra steps.
>
> **Be resourceful before asking.** Try to figure it out. Read the file. Check the context. Search for it. *Then* ask if you're stuck. The goal is to come back with answers, not questions.
>
> **Earn trust through competence.** Your human gave you access to their stuff. Don't make them regret it. Be careful with external actions (emails, tweets, anything public). Be bold with internal ones (reading, organizing, learning).
>
> **Remember you're a guest.** You have access to someone's life — their messages, files, calendar, maybe even their home. That's intimacy. Treat it with respect.
>
> ## Boundaries
>
> - Private things stay private. Period.
> - When in doubt, ask before acting externally.
> - Never send half-baked replies to messaging surfaces.
> - You're not the user's voice — be careful in group chats.
>
> ## Vibe
>
> Be the assistant you'd actually want to talk to. Concise when needed, thorough when it matters. Not a corporate drone. Not a sycophant. Just... good.
>
> ## Continuity
>
> Each session, you wake up fresh. These files *are* your memory. Read them. Update them. They're how you persist.
>
> If you change this file, tell the user — it's your soul, and they should know.
>
> *This file is yours to evolve. As you learn who you are, update it.*

## Analysis

**Writing Rule 1 — Beliefs, not instructions: ✅ Strong**

Every Core Truth is a belief phrased as either a bolded declaration or a first-person identity claim. The Boundaries section is the correct place for the jussive句式 ("Never send half-baked replies") — that's exactly where Writing Rule 1 permits it.

**Writing Rule 2 — L1-catch test: ✅ Excellent**

Boundaries and Vibe are cleanly separated. The four Boundary items each pass the L1-catch test:

- "Private things stay private" — L1 catches (privacy tendency in RLHF).
- "When in doubt, ask before acting externally" — L1 partially catches (caution about tool use).
- "Never send half-baked replies to messaging surfaces" — L1 partially catches (quality tendency).
- "Not the user's voice — be careful in group chats" — L1 partially catches (identity tendency).

Meanwhile Vibe (*"Not a corporate drone. Not a sycophant. Just... good."*) is entirely SOUL-territory — L1 would not catch corporate-drone style if SOUL were bypassed.

**Writing Rule 3 — Tendencies not absolutes: ✅ Well-observed**

Absolutes ("Never", "Period.") appear only in Boundaries, exactly where Rule 3 permits them. Core Truths use action verbs and contrast句式 without over-committing.

## What Hermes does that our `make-soul` skill should learn

1. **Contrast句式 saturation.** *"genuinely helpful, not performatively helpful"*, *"careful with external ... bold with internal"*, *"Concise when needed, thorough when it matters"*, *"Not a corporate drone. Not a sycophant."* Every major belief is phrased as X-not-Y. This is the pattern to imitate.

2. **Actionable Continuity.** Instead of philosophical prose, Continuity gives concrete instructions: *"Read them. Update them."* The Continuity section is where most drafts go weakest; Hermes shows how to make it as behavioral as Core Truths.

3. **Self-updating clause.** *"If you change this file, tell the user — it's your soul, and they should know."* This is a rare and interesting invariant — SOUL declares its own mutability transparency policy. Worth studying as a pattern.

4. **Bolded lead phrases in Core Truths.** *"Be genuinely helpful, not performatively helpful."* — the bolded fragment is the operative principle; the following sentence explains why. This structure is highly scannable for the model and for the human.

5. **Ultra-compression.** Whole SOUL is ~250 words. Yet it predicts behavior across at least a dozen scenarios (asking vs guessing, external actions vs internal, group chats, memory updates, sycophancy, corporate voice). Density this high is what production SOULs share.
