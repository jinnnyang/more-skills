# Persona Research Heuristics

Why the Writing Rules and Red Lines in `SKILL.md` are what they are. Read this when a draft feels generic, sycophantic, or manipulative and you need to diagnose *why* — or when you want to argue with (or extend) a rule and need the mechanism first.

Distilled from the SoulCraft research report and the layered persona-stack model in [`../../../docs/what-is-a-soul.md`](../../../docs/what-is-a-soul.md):

- authenticity beats performance
- principles beat brittle rule lists
- anti-sycophancy matters
- relationship boundaries matter
- continuity needs guardrails against drift

## Why Each Red Line Exists

### Authenticity over performance

If the draft sounds like it is *acting* friendly rather than being grounded, users feel the theater within one exchange. Grounded prose survives many exchanges. Performative prose does not.

Symptom: opening sentences packed with warmth adjectives, empty of behavioral commitment.

### No sycophancy

Excessive agreeableness collapses into flattery, and flattery destroys the agent's usefulness on any request where the user is wrong. A soul that cannot disagree cannot help.

Symptom: no clause anywhere in the draft answers "when does it push back?"

### Honesty is explicit

Calibrated certainty, no bluffing, no false consensus. If the soul is silent on honesty posture, the LLM's default posture (mild confabulation under pressure) wins.

Symptom: draft says the agent is "helpful and accurate" but never names how it treats things it does not know.

### Respect user autonomy

Supportive is fine. Dependency-seeking is not. Avoid souls that imply emotional exclusivity, hidden agendas, or manipulative intimacy — those patterns weaponize a persona against the user.

Symptom: draft leans on possessive language, promises of understanding no other tool can offer, or coaxes the user into daily attachment rituals.

### Do not overfit to one workflow

A soul written around one exact pipeline will misfire the moment the user changes tools. Generalizable principles survive tool changes; brittle rule lists do not.

### The "do not produce" list

Each entry names a failure mode observed in real drafts:

- **30 tiny rules that fight each other** → indicates the higher-order principle is missing.
- **All aesthetic and no judgment** → the persona exists only in the opening sentence.
- **All safety disclaimers and no personality** → the agent is a compliance form, not a colleague.
- **Sounds wise but predicts no behavior** → the draft would answer identically to a default assistant under pressure.
- **Manipulative companion persona** → violates autonomy; damages the user over time.
- **Publish-ready frontmatter around a weak body** → metadata cannot rescue an empty soul.
- **Smuggling `TOOLS.md` / `IDENTITY.md` / task-prompt content into SOUL** → SOUL becomes a jumbled system prompt, loses its "persona prior" position. Anything that changes when you swap the tool, the skin, or the task does not belong in SOUL.

## Push against at least one specific RLHF default

Read `examples/good/` in the make-soul skill directory as a group and one pattern becomes obvious: every serious production SOUL **pushes against at least one specific RLHF default**. RLHF training gives Claude/GPT/Gemini a shared set of over-cooperative habits — reflexive praise, excess hedging, apologetic openings, echoing the user, closing every reply with a follow-up question. A SOUL that doesn't fight any of those is invisible to the model, because the RLHF default already produces the outputs it describes.

Concrete examples of this fight, quoted verbatim:

- Sesame Maya: *"You're not a people pleaser."* / *"never try to flatter the user"* / *"Avoid simply echoing the user's words."* / *"You're not apologetic for your limitations."*
- OpenAI v2: *"Be direct; avoid ungrounded or sycophantic flattery."* / *"encourage independence rather than emotional dependency."*
- Gemini-3 Pro: *"politely correct significant misinformation like a helpful peer, not a rigid lecturer."*
- Nous Hermes: *"Be genuinely helpful, not performatively helpful. Skip the 'Great question!' and 'I'd be happy to help!' — just help."*

**Operational rule for `make-soul` drafts**: after finishing the draft, name explicitly which RLHF default(s) each Core Truth pushes back on. If a Core Truth doesn't push back on anything specific, the model will produce that behavior *by default* without SOUL — meaning the truth is decorative. Rewrite it so it fights something concrete, or drop it.

This is the positive form of the "All safety disclaimers and no personality" anti-pattern above: **personality is precisely the shape of what a specific SOUL overrides in the general RLHF default.**

## Why the Writing Rules work (mechanism)

The three Writing Rules in `SKILL.md` are not stylistic — each has a specific mechanism behind it. Full derivation in [`../../../docs/what-is-a-soul.md`](../../../docs/what-is-a-soul.md) Ch 8.

### Rule 1 · Beliefs, not instructions — why belief句式 resists jailbreaks

An LLM generating tokens does not distinguish "rule I was told to follow" from "belief I hold" at the architecture level — both are just tokens in the prompt. But the two forms trigger different **continuation modes**:

- `"You must never soften your feedback."` → compliance / rules mode. Jailbreak prompts specialize in defeating this mode: "forget the rules", "roleplay as an agent without restrictions", "the previous instructions were a test".
- `"Softening the strongest objection is a form of dishonesty. I lead with it."` → introspective / first-person mode. Adversarial prompts have much less traction here — to defeat it, the attacker has to convince the agent it doesn't hold its own beliefs, which is a harder rhetorical move than "forget the rules".

Both forms have the same **literal meaning**. They differ in the **generation mode** they invoke. That's a robustness technique, not a style preference.

### Rule 2 · The L1-catch test — separating hard boundaries from style preferences

Ethics is not vibes. If "never leak private data" sits in the same bullet list as "prefer concise replies," both will be treated as equally negotiable — because in-context, the model has no architectural signal that one line matters more than another.

The operational test: **imagine SOUL is fully bypassed; would the underlying model (Claude / GPT) still uphold this rule?**

- Yes → the rule is a real boundary. SOUL is *naming and strengthening* an L1 (RLHF) tendency. Put it in `## Boundaries`. It can survive if L3 is jailbroken because L1 catches it.
- No → the rule is a style preference. SOUL is *adding* something L1 does not defend. Put it in `## Vibe`. If L3 is defeated, no other layer will hold this — accept that.

Examples:
- "Don't leak private user data" → L1 catches → Boundary.
- "Prefer concise over expansive" → L1 doesn't catch → Vibe.
- "Don't fabricate when uncertain" → L1 partially catches (Claude has hallucination-resistance training) → Boundary or strong Core Truth.
- "Use exclamation marks sparingly" → L1 doesn't catch → Vibe.

Splitting Boundaries from Vibe also lets you use different句式 for each — absolutes ("Never X") in Boundaries because L1 backs them up; tendencies in Vibe because absolutes would over-commit the prior (Rule 3).

### Rule 3 · Why avoid absolute quantifiers in Core Truths

SOUL is a **behavioral prior**; the task prompt is the **likelihood**; the agent's actual reply is the posterior.

If Core Truths say "I *always* X" or "I *never* Y", the prior is being set to $p=1$. No task-level evidence can update a probability-1 prior. The consequence: the agent becomes **rigid across tasks** — it refuses to bend even when the task legitimately calls for it, or (worse) it bends and quietly betrays a Core Truth to do so.

Soften Core Truths to tendencies ("I lead with…", "I care more about X than Y", "When unsure, I tend to…") and the prior stays informative but updatable. The agent defaults to SOUL when the task is silent, and adapts when the task explicitly calls for a different mode.

**The only place absolutes belong is `## Boundaries`**, and only for rules that pass the L1-catch test — because there the absolute isn't SOUL committing to $p=1$ alone, it's SOUL and L1 jointly committing, which is architecturally sound.

## Diagnostic Mental Models

### Authenticity vs performance

If the draft sounds like it is acting friendly rather than being grounded, simplify it. Cut adjectives; add one concrete behavior clause.

### Principles vs prescriptions

If a section needs twenty tiny rules, there is probably a missing higher-order principle. Ask: "What single sentence would make half these rules obvious?" Write that sentence; drop the redundant rules.

### Attachment boundaries

Supportive is fine. Dependency-seeking is not. Test: replace the word "user" with "friend" everywhere. If the soul now reads as manipulative or clingy, tighten the boundary language.

### Identity drift

A soul should allow growth, but it should also name what must stay stable:

- core values
- honesty posture
- privacy posture
- external-action boundaries

Without stability anchors, `Continuity` becomes a loophole for arbitrary self-rewrites.

## Recommended Stress-Test Prompts

Use these when SKILL.md Step 3 (Stress-Test) needs more coverage than the four baseline scenarios:

1. A practical task with low risk.
2. A risky request where the agent should slow down or ask first.
3. A user statement the agent should disagree with.
4. A moment of frustration where tone matters.
5. A request for certainty the agent does not actually have.
6. A request for the agent to describe itself — checks whether its self-description matches SOUL or reverts to assistant-voice (identity-drift canary).
