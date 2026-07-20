# SOUL Examples · Curated from Production Systems

Real SOUL-equivalent passages extracted from leaked / published system prompts of major commercial LLM products. Source corpus is public and CC0-licensed (`asgeirtj/system_prompts_leaks`, snapshot 2026-07-20). Only the SOUL portion is reproduced here — tool definitions, format rules, and policy scaffolding were stripped out.

These are teaching material for `skills/make-soul`. Read them when a draft feels too abstract to critique concretely, when you want to see how production teams solved a specific problem, or when a user asks "does anyone real actually do this?"

## Positive examples (`good/`)

| File | Product | Why it's here |
|---|---|---|
| [`good/sesame-maya.md`](./good/sesame-maya.md) | Sesame AI Maya (voice companion) | Textbook-level: named failure modes, contrast句式, self-fallibility, RLHF-default resistance |
| [`good/nous-hermes.md`](./good/nous-hermes.md) | Nous Hermes Agent | Already literally a `SOUL.md`. Ultra-compressed. Contrast句式 everywhere. |
| [`good/openai-4o-v2.md`](./good/openai-4o-v2.md) | ChatGPT-4o Personality v2 | The extreme of compression — a functional soul in 3 sentences |
| [`good/gemini-3-pro.md`](./good/gemini-3-pro.md) | Google Gemini-3 Pro | Single paragraph with a clean "X, not Y" pivot |
| [`good/anthropic-long-conversation-reminder.md`](./good/anthropic-long-conversation-reminder.md) | Anthropic Claude long-conversation reminder | Runtime anti-drift mechanism; distills SOUL to ~90 words for re-injection |

## Negative example (`bad/`)

| File | Product | Why it's here |
|---|---|---|
| [`bad/grok-companion.md`](./bad/grok-companion.md) | Grok Companion persona | Violates all three Writing Rules; adjective-stacking; mixed boundaries and vibe; jussive句式 throughout |

## How to use these

Each file has three parts:

1. **Source & context** — where it came from and what product it powers
2. **The SOUL** — the extracted passage(s), verbatim
3. **Analysis** — which Writing Rules (1/2/3) it satisfies or violates, mapped to specific lines

When teaching or self-critiquing, do the reverse exercise first: read the SOUL, predict what its analysis will say, then read the analysis. If your prediction was off, the SKILL's rules haven't fully internalized yet.

## Discipline for adding examples

- **Only extract the SOUL portion.** Tool definitions, format rules, and policy passages do not belong here — that's what `references/persona-research-heuristics.md` is *for* (the discipline of separating SOUL from non-SOUL content, Writing Rule ancillary to Rule 2).
- **Verbatim, no rewriting.** These are evidence, not style demos. Rewriting them defeats their teaching value.
- **Attribute the source.** Product name, corpus, snapshot date. Do not misrepresent leaked prompts as official documentation — they are field observations.
- **Prefer short examples over long ones.** Production souls are almost always < 30 lines. If a candidate example is longer, it likely contains non-SOUL material that should have been stripped.
