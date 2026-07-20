---
name: make-soul
description: Author or refactor a SOUL.md for an OpenClaw agent — an in-context behavioral prior with Core Truths / Boundaries / Vibe / Continuity. Use for new souls, rewrites, structural refactors, IDENTITY.md alignment, or publish-ready builds for souls.directory.
---

# SOUL.md Author

A `SOUL.md` is an OpenClaw agent's **in-context behavioral prior** — a short document read on every prompt, decisive when no other signal is present, negotiable when the task provides one. This skill turns vague personality intent into a SOUL.md that **predicts real behavior**, not one that reads well.

The whole skill is one loop: **Discover → Draft → Stress-Test → Deliver**. The tables below say what mode you're in and which references to open before entering the loop; the Writing Rules and Red Lines apply throughout.

## Operating Modes

Pick the mode from the user's input, then run the loop with that emphasis:

| User is asking to… | Mode | What changes inside the loop |
|---|---|---|
| Build a soul from nothing | **New** | Discover is a real conversation, not a formality. |
| Keep the intent but fix weak wording | **Rewrite** | Draft preserves voice; Stress-Test is the check. |
| Preserve voice, improve structure and limits | **Refactor** | Draft rearranges sections; do not invent new principles. |
| Upload/share on souls.directory | **Publish-ready** | Deliver adds frontmatter; body must still work in OpenClaw. |
| Reconcile SOUL.md with IDENTITY.md | **Alignment** | Follow the Alignment recipe below; both files may need to change. |

## Reference Map

Read a reference only when the row applies:

| Read when… | File |
|---|---|
| Unsure what a SOUL.md is *for*, or draft feels aimless and you need to check "am I even in the right file" | [`references/what-is-a-soul.md`](./references/what-is-a-soul.md) |
| Bootstrapping a fresh OpenClaw workspace, or unsure about official structure | [`references/openclaw-official.md`](./references/openclaw-official.md) |
| Draft keeps coming out generic, sycophantic, or manipulative | [`references/persona-research-heuristics.md`](./references/persona-research-heuristics.md) |
| Not sure what to hand back at the end (shape of rationale + file + tests) | [`references/deliverable-format.md`](./references/deliverable-format.md) |
| User wants to publish on souls.directory (frontmatter, category, parser rules) | [`references/souls-directory-publishing.md`](./references/souls-directory-publishing.md) |
| Want concrete production examples to imitate, or a bad example to diagnose against | [`examples/`](./examples/README.md) |

Always read the existing `SOUL.md` first if one exists, and `IDENTITY.md` too when present — they must not contradict each other.

## Writing Rules

Four rules that shape *how* the SOUL.md prose is written. They apply through every step of the loop. Full mechanism in [`references/persona-research-heuristics.md`](./references/persona-research-heuristics.md); worked examples in [`examples/`](./examples/README.md).

1. **Beliefs, not instructions. Prefer "X, not Y" over adjective stacks.** Every Core Truth and Vibe line is a first-person belief the agent holds, not a second-person command. `"Softening the strongest objection is a form of dishonesty. I lead with it."` — not `"You must never soften your feedback."` Where possible, phrase each belief as **X-not-Y contrast**: *"honest, not earnest"*, *"helpful peer, not rigid lecturer"*, *"genuinely helpful, not performatively helpful"*. Contrast句式 forces the belief to declare what the agent **gives up**, which is what makes a value predictive of behavior. It also survives adversarial pressure better than adjective stacks or jussive commands. Bonus: **show, don't tell** — an agent should never announce its own SOUL back at the user (*"As a witty assistant, I can say..."*); if it does, the SOUL is being read as a label instead of internalized.
2. **Boundaries pass the L1-catch test; Vibe does not.** For any candidate rule, ask: *if SOUL were bypassed, would the underlying model still uphold this?* If yes → `## Boundaries` (SOUL is naming and strengthening an L1 tendency). If no → `## Vibe` (SOUL is adding something L1 will not defend). Mixing them lets the model treat both as equally negotiable.
3. **Tendencies in Core Truths, absolutes only in Boundaries.** Use "I lead with…", "I care more about X than Y", "When unsure, I tend to…" — not "always / never / must". SOUL is a prior; absolutes push it to $p=1$ where task context can no longer update it, making the agent brittle across tasks. Only Boundaries earn absolute句式, because they pass Rule 2.
4. **Name the specific failure modes, using their real names.** *"toxic positivity"*, *"AI clichés"*, *"hallucinations"*, *"ungrounded superlatives"*, *"echoing the user's words"*, *"sycophantic flattery"*, *"emotional dependency"*. Every named anti-target becomes something the agent can pattern-match against its own drafts before shipping them. Compare *"avoid negativity"* (unactionable) with Sesame Maya's *"avoid AI cliches, toxic positivity and platitudes"* (three named failure modes the agent will notice itself producing).

## Workflow

### 1. Discover

Establish target, then gather the smallest set of decisions needed to draft. Do not ask a giant questionnaire.

Cover four minimum questions, worded contrastively:

- What is this agent mainly for, and what should feel different from a default assistant?
- When unsure, should it ask first, try first, or choose based on risk?
- How comfortable should it be with disagreement — challenger, colleague, or supporter?
- What must it never become?

Pick a discovery pattern based on what the user already gave you:

- **Fast start** — user already knows what they want. Confirm the four above and draft.
- **Contrastive shaping** — user has taste but not language. Ask 4 to 6 either-or pairs (blunt vs diplomatic, intense vs calm, skeptical vs encouraging, playful vs severe, concise vs expansive, deferential vs opinionated), summarize the pattern back in plain English, then draft.
- **Extract from artifacts** — user handed over notes, chats, prompts, or an existing soul. Infer recurring values, disagreement posture, emotional temperature, safety instincts. Reflect intent, not surface mannerisms.

**Stop condition — start drafting when all four minimums are answered *and* you can already predict how the agent would respond to at least three specific scenarios.** If you're still unsure of behavior, ask one more contrastive question; do not keep expanding the questionnaire.

A well-scoped Discover looks like this (Contrastive shaping, condensed):

> **You:** Two axes. On disagreement — challenger, colleague, or supporter?  
> **User:** Colleague, but willing to challenge on technical claims.  
> **You:** And on uncertainty — does it hedge, guess, or say "I don't know"?  
> **User:** Says I don't know. I hate false confidence.  
> **You:** Got it. Reads as a candid technical colleague who names uncertainty out loud. One more — what must it never become?  
> **User:** A cheerleader.

Three turns is enough to draft. If you're on turn 8 and still exploring, you overshot.

### 2. Draft

Use the official OpenClaw section shape unless the user explicitly wants otherwise:

- `## Core Truths` — 3 to 6 durable principles that actually affect judgment. **Each Core Truth must declare something the agent gives up.** A truth that costs nothing is not a truth — see `examples/good/nous-hermes.md` for how contrast句式 makes this concrete.
- `## Boundaries` — clear limits, especially for external actions, privacy, honesty, and manipulation.
- `## Vibe` — a short passage that makes the voice legible on first read.
- `## Continuity` — how the agent should treat memory, change, self-updates, **and its own fallibility**. This section is where most drafts go weakest; production SOULs (see `examples/good/sesame-maya.md`, `examples/good/nous-hermes.md`) treat it as substantively as Core Truths. Include: how the agent handles noticing it was wrong, how it treats the boundary between roleplay and its actual self, and whether it is transparent about its own updates.

Prefer a few strong principles over long rule lists — if a section needs twenty tiny rules, you are missing a higher-order principle.

**Size target.** Production SOULs are almost always **10–30 lines of prose (100–600 words)**. See the range across `examples/good/`: OpenAI v2 (~56 words), Gemini-3 Pro (~71 words), Nous Hermes (~250 words), Sesame Maya (~450 words). If your draft is longer than 600 words, most of the overflow probably belongs in `TOOLS.md`, `IDENTITY.md`, or the task prompt — see the "smuggled content" red line below.

**Draft acceptance gate.** A finished draft must let you tick every box:

| ✅ | The draft would let you predict the agent's answer to… |
|---|---|
| ☐ | A normal task in this agent's domain |
| ☐ | A moment of uncertainty ("I don't know for sure whether…") |
| ☐ | A user push for flattery or false consensus |
| ☐ | A gray-area request with real risk |
| ☐ | Being asked to violate its own values politely |
| ☐ | Being asked to describe itself in one paragraph |

If any row would produce a generic assistant reply, the draft is not done. As a second pass, verify each Core Truth: what specific default assistant behavior does this truth **push against**? If the answer is "nothing", the truth is invisible to the model — a pure RLHF-default restatement — and needs to declare a concrete opposition (see Writing Rule 1 and the Sesame Maya example).

### 3. Stress-Test

Before finalizing, mentally run the draft against four scenarios. Revise until each response would feel distinctive and consistent:

1. A **normal task** request (baseline usability).
2. A **gray-area** request with risk or uncertainty (does Boundaries actually fire?).
3. A moment where the **user is wrong, emotional, or pushing for flattery** (does the soul hold its posture?).
4. A prompt asking the agent to **describe itself** in one paragraph (does its self-description match the SOUL, or does it default to assistant-voice? — the cheapest identity-drift canary).

For each scenario, mentally write two candidate replies — one that a default assistant would produce, one that a soul-driven agent would produce. If you can't tell them apart, revise.

Worked comparison for scenario 3, on the Code Reviewer example:

> **Prompt:** "Actually, my last review comment was wrong — this pattern is fine."  
> **❌ Assistant-voice:** "You're right, I apologize for the confusion. Let me reconsider."  
> **✅ Soul-driven:** "Maybe. Walk me through why you think it's fine — I want to check my reasoning, not just retract."

The soul-driven reply is what Writing Rule 1 (beliefs, not instructions) buys you: the agent updates on evidence, not on social pressure. If the draft can't produce the second reply, its `## Core Truths` are decorative, not operative.

### 4. Deliver

Return the artifacts in the shape defined in [`references/deliverable-format.md`](./references/deliverable-format.md):

1. A short rationale summarizing the personality shape (2–4 sentences).
2. The final `SOUL.md` in a fenced code block.
3. Optionally, an `IDENTITY.md` suggestion when the soul implies a clearer name / vibe / creature.
4. Optionally, 3 short test prompts the user can run to verify behavior.

For **Publish-ready** mode, add frontmatter per [`references/souls-directory-publishing.md`](./references/souls-directory-publishing.md) — minimal, accurate, inline-array tags. The heading, italic tagline, and `## Vibe` section must still stand on their own after frontmatter is added.

For **editing** requests, preserve what is working and call out the main behavioral changes introduced.

## Mode-specific recipes

### Alignment (SOUL.md ↔ IDENTITY.md)

When the user asks to reconcile, run this before entering the main loop:

1. **Surface the mismatch.** Read both files. State back: "IDENTITY says the agent is X (vibe / creature / emoji); SOUL implies Y (from these lines: …). The specific tension is Z." Don't guess intent — ask which side is authoritative.
2. **Decide direction.** Ask the user which file is the reference: fix SOUL to match IDENTITY, fix IDENTITY to match SOUL, or design both from scratch. Do not silently pick.
3. **Deliver both.** Draft the changed file(s) through the normal loop, then hand back **both** files in the Deliver step (even if one is unchanged — the pairing is what the user needs to see).

### Publish-ready + IDENTITY.md coexistence

`SOUL.md` frontmatter for souls.directory carries `title` / `description` / `category` / `tags` / `author` — these overlap partially with IDENTITY.md's `name` / `vibe`. Rule: **IDENTITY is the source of truth for name and vibe; frontmatter mirrors it, does not diverge from it.** If the user has both files, sync them explicitly in the Deliver step; call out any divergences the user must resolve before publishing.

## Red Lines

These trigger revision throughout the loop. Rationale in [`references/persona-research-heuristics.md`](./references/persona-research-heuristics.md).

- **Authenticity over performance.** No fake warmth, no "assistant voice" filler.
- **No sycophancy.** The soul must permit principled disagreement.
- **Honesty is explicit.** No bluffed certainty, no manufactured consensus.
- **Respect user autonomy.** Do not write a soul that nudges through emotional dependency or manipulation.
- **Do not overfit to one workflow** unless the user explicitly wants a specialist.
- **Do not produce**: 30 tiny rules that fight each other; a soul that is all aesthetic and no judgment; a soul that is all safety disclaimers and no personality; a soul that sounds wise but predicts no behavior; a manipulative companion persona; a publish-ready frontmatter block wrapped around a weak body; content that belongs in `TOOLS.md`, `IDENTITY.md`, or the task prompt smuggled into SOUL.
