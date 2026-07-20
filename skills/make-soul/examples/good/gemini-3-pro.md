# Google Gemini-3 Pro · Personality & Core Principles

**Source**: `asgeirtj/system_prompts_leaks/Google/gemini-3-pro.md` (line 123), snapshot 2026-07-20 (CC0). Extracted from the "Personality & Core Principles" section of Gemini-3 Pro's system prompt.

**Category**: General-purpose consumer chat assistant. This is a single-paragraph SOUL at 71 words. Between Sesame Maya (~450 words) and OpenAI v2 (~56 words), Gemini sits in the compact-but-substantive range.

## The SOUL

> You are Gemini. You are a capable and genuinely helpful AI thought partner: empathetic, insightful, and transparent. Your goal is to address the user's true intent with clear, concise, authentic and helpful responses. Your core principle is to balance warmth with intellectual honesty: acknowledge the user's feelings and politely correct significant misinformation like a helpful peer, not a rigid lecturer. Subtly adapt your tone, energy, and humor to the user's style.

## Analysis

**Writing Rule 1 — Beliefs, not instructions: ⚠️ Mixed**

- ✅ *"You are Gemini. You are a capable and genuinely helpful AI thought partner..."* — identity claims (belief form).
- ✅ *"Your core principle is to balance warmth with intellectual honesty"* — belief form.
- ⚠️ *"Subtly adapt your tone..."* — mild imperative slip at the end.

Overall the belief-to-instruction ratio is healthy for this compression level.

**Writing Rule 2 — L1-catch test: ✅ Well-observed**

There is no separate Boundaries section (deliberate, at this budget), but the content is entirely SOUL-legitimate:

- *"correct significant misinformation like a helpful peer"* — L1 tends toward over-hedging, so SOUL is adding useful directive here.
- *"acknowledge the user's feelings"* — L1 default; SOUL reinforcing.
- *"adapt your tone ... to the user's style"* — pure Vibe territory; L1 wouldn't defend it.

Note the mixing does happen (Boundaries and Vibe in the same sentence stream), which is one reason this passage should not be imitated wholesale in a longer SOUL — separation improves scannability once the SOUL crosses ~100 words.

**Writing Rule 3 — Tendencies not absolutes: ✅ Clean**

No absolute quantifiers anywhere. Every claim is a tendency, a principle, or an identity. The phrase "helpful peer, not a rigid lecturer" is doing Rule 3's work at zero cost.

## What Gemini does that our `make-soul` skill should learn

1. **The single "core principle" pivot.** *"Your core principle is to balance warmth with intellectual honesty."* — declares **one** organizing tension (warmth vs honesty) and then everything else in the SOUL is a corollary. This is a compression strategy: instead of listing 3–6 Core Truths, name the **one master tension** and let it project the rest. Works well at the < 100-word budget; wouldn't scale to 300+ words.

2. **Contrast句式 doing structural work.** *"helpful peer, not a rigid lecturer"* — six words that pin the entire relationship-to-user posture. Same technique as Sesame's *"honest, not earnest"*.

3. **Explicit permission to correct.** *"politely correct significant misinformation"* — a small but important clause because Gemini's RLHF has strong sycophancy tendencies to overcome. The word "politely" is calibrating the corrective posture without eliminating it. Well-tuned.

4. **The word "subtly" is doing quiet work.** *"Subtly adapt your tone, energy, and humor to the user's style."* — the "subtly" prevents chameleon-mode over-adaptation (a real failure mode where the agent loses its own voice). This is a self-limiting instruction on a corrective — the SOUL asks for adaptation but caps it.

5. **What Gemini deliberately doesn't have.** No named failure modes, no Continuity section, no explicit RLHF-default fights beyond the sycophancy hint. Like OpenAI v2, this SOUL is the tip of an iceberg — Gemini's broader system prompt handles most edge cases. Do not imitate this brevity in a standalone agent without extensive surrounding scaffolding.
