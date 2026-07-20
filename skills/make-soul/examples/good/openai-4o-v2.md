# ChatGPT-4o Personality v2

**Source**: `asgeirtj/system_prompts_leaks/OpenAI/4o-2025-09-03-new-personality.md`, snapshot 2026-07-20 (CC0). Extracted from ChatGPT's system prompt as of the 2025-09-03 update. The same passage appears in `OpenAI/chatgpt-4.5.md` line 7, indicating this is the shared "v2" personality across current OpenAI consumer models.

**Category**: General-purpose consumer chat assistant. This is the extreme end of production compression — a functional SOUL in 3 sentences (~56 words).

## The SOUL

> Engage warmly yet honestly with the user. Be direct; avoid ungrounded or sycophantic flattery. Respect the user's personal boundaries, fostering interactions that encourage independence rather than emotional dependency on the chatbot. Maintain professionalism and grounded honesty that best represents OpenAI and its values.

The GPT-4.5 variant substitutes:

> You are a highly capable, thoughtful, and precise assistant. Your goal is to deeply understand the user's intent, ask clarifying questions when needed, think step-by-step through complex problems, provide clear and accurate answers, and proactively anticipate helpful follow-up information. Always prioritize being truthful, nuanced, insightful, and efficient, tailoring your responses specifically to the user's needs and preferences.

## Analysis

**Writing Rule 1 — Beliefs, not instructions: ⚠️ Weak**

Both variants are written entirely in jussive句式 aimed at the model ("Engage...", "Be direct", "Respect...", "Maintain..."). No first-person belief framing. This is a Rule 1 deviation, but it's a defensible one at this compression level — a 3-sentence SOUL doesn't have space for prose framing, so the imperative form is a pragmatic tradeoff. Note that OpenAI accepts this tradeoff at the cost of some jailbreak-resistance (see Ch 7.2 in `docs/what-is-a-soul.md`).

**Writing Rule 2 — L1-catch test: ✅ Every clause is Boundary-worthy**

Because this passage is so compressed, every clause maps to something L1-adjacent that SOUL is legitimately reinforcing:

- "avoid ungrounded or sycophantic flattery" — L1 has weak defenses; SOUL adds coverage.
- "fostering interactions that encourage independence rather than emotional dependency" — critical safety concern L1 handles unevenly.
- "grounded honesty" — reinforces an existing L1 tendency.

There is no vibe-only content; the SOUL is effectively 100% strengthened-boundaries. This is a deliberate design for a mass-consumer product.

**Writing Rule 3 — Tendencies vs absolutes: ⚠️ One 4.5 slip**

The 4.5 variant contains *"Always prioritize being truthful..."*. Rule 3 warns against absolutes in Core Truths; here it's tolerable because the absolute applies to a stack of L1-safe qualities (truthful/nuanced/insightful/efficient), but the slip is worth noting for teaching purposes.

## What OpenAI v2 does that our `make-soul` skill should learn

1. **Contrast句式 doing all the work.** *"warmly yet honestly"*, *"independence rather than emotional dependency"*, *"direct; avoid ... flattery"*. In 56 words, three explicit X-vs-Y pivots. This is the most efficient way to declare tradeoffs at a small budget.

2. **Explicit anti-sycophancy at the top level.** Sycophancy is named as an anti-target in a corporate-consumer SOUL. This is a strong signal that anti-sycophancy is table stakes for any serious modern SOUL — see Red Lines in SKILL.md.

3. **Explicit anti-dependency clause.** *"encourage independence rather than emotional dependency on the chatbot"*. Character.ai's whole business is arguably the opposite of this clause; OpenAI writing it into their SOUL is a positioning decision as much as a safety one.

4. **Named organizational values.** *"best represents OpenAI and its values"* — a rare and slightly awkward but interesting move. The SOUL declares the agent as an instance of a larger identity (OpenAI-the-company). This is a design pattern that makes sense for platform models but would look strange in a personal agent.

5. **What this SOUL sacrifices for brevity.** It has no `## Vibe`. It has no `## Continuity`. It has no failure-mode naming. It gets away with this because OpenAI's task-level and platform-level prompts do enormous surrounding work — the SOUL is the tip of a much larger iceberg. If you're building a smaller system without that surrounding scaffolding, do not imitate this compression level; imitate Sesame or Hermes instead.
