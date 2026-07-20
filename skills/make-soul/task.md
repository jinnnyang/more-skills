---
kind: task
version: 1
last_updated: 2026-07-20T09:05:00+00:00
last_verified: 2026-07-20T09:05:00+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: hand-off
session_id: sess-20260720-make-soul-corpus-opt
status: phase-complete
---

# Current Tasks

## Done — Plan B Restructure (2026-07-20 · earlier session)

- `[x]` **T1** Rewrite `SKILL.md` around Discover → Draft → Stress-Test → Deliver — 109 lines
- `[x]` **T2** Update `references/persona-research-heuristics.md` — absorbed rationale for Red Lines; 91 lines
- `[x]` **T3** Create `references/deliverable-format.md` — canonical output shape with worked example; 70 lines
- `[x]` **T4** Light pass on `openclaw-official.md` and `souls-directory-publishing.md` — no-op; both are pure external-facts pages
- `[x]` **T5** Self-review — frontmatter valid, all cross-links resolve, sizes within targets
- `[x]` **T6** Presented diff summary to user; approved for hand-off
- `[x]` **T7** Commit skills/make-soul/ to parent repo — verified already committed as `483a0fe`; nothing new needed
- `[x]` **T8** Exercise the refactored skill on a real SOUL.md creation task — superseded by the deep-optimization pass below

## Done — Deep Optimization Pass (2026-07-20 · current session)

- `[x]` **DO1** Create `skills/make-soul/references/what-is-a-soul.md` — 108 lines, operational reference: persona stack, prior-not-program framing, three writing rules
- `[x]` **DO2** Create `docs/what-is-a-soul.md` at repo root — 719 lines, 12 chapters + 3 appendices, independent-reading learning document
- `[x]` **DO3** Update `docs/README.md` — new index row, new reading path "if you write agent personas", updated tree, maintenance discipline
- `[x]` **DO4** Update `SKILL.md` — added Writing Rules section, Discover stop condition + dialogue demo, Draft acceptance-gate table, Stress-Test scenario 4 + pass/fail comparison, Alignment three-step recipe, Publish+IDENTITY coexistence rule (109 → 157 lines)
- `[x]` **DO5** Update `references/persona-research-heuristics.md` — mechanism sections for all three Writing Rules, "smuggled non-SOUL content" red line (91 → 129 lines)

## Done — Production Corpus Analysis Pass (2026-07-20 · current session cont.)

Extracted SOUL portions from the leaked-system-prompts corpus (`asgeirtj/system_prompts_leaks`, CC0) and folded the findings back into the skill.

- `[x]` **PC1** Create `skills/make-soul/examples/` with 5 positive + 1 negative extracts, each with source attribution + Writing-Rules analysis:
  - `examples/good/sesame-maya.md` — voice companion (~450 words), textbook-level
  - `examples/good/nous-hermes.md` — already-formatted SOUL.md, canonical shape
  - `examples/good/openai-4o-v2.md` — extreme compression (~56 words)
  - `examples/good/gemini-3-pro.md` — compact single-paragraph pattern (~71 words)
  - `examples/good/anthropic-long-conversation-reminder.md` — runtime anti-drift mechanism
  - `examples/bad/grok-companion.md` — violates all three Writing Rules; used as diagnostic reference
  - `examples/README.md` — index + usage discipline
- `[x]` **PC2** Update `SKILL.md`:
  - Reference Map row for `examples/`
  - Writing Rule 1 upgraded — now includes "X, not Y" contrast preference + show-don't-tell clause
  - New Writing Rule 4 — "Name the specific failure modes, using their real names"
  - §Draft — each Core Truth must declare something the agent gives up; Continuity elevated with fallibility requirement
  - §Draft — new "Size target" paragraph (10–30 lines, 100–600 words, with production data points)
  - Acceptance gate — second-pass check on what RLHF default each truth pushes against
- `[x]` **PC3** Update `references/persona-research-heuristics.md` — new section "Push against at least one specific RLHF default", with verbatim quotes from four production souls
- `[x]` **PC4** Update `docs/what-is-a-soul.md`:
  - Ch 7.3 expanded with Anthropic 3-layer reminder case study (4 transferable lessons + resting-SOUL vs re-injection-payload distinction)
  - Ch 12 gets "拓展主题" section — Multi-Soul, re-injection payload design, SOUL versioning
  - Ch 12 step 2 now points to `examples/good/` and `examples/bad/` for practice material

- `[x]` **PC5** Commit everything as one logical commit — `823bbfb feat(make-soul): deep optimization + production-corpus pass` (13 files, +1480/-39)
- `[x]` **PC6** Housekeeping — `cccff14 chore: gitignore .handoff.lock runtime lock file`

## Now

- None. Both optimization passes complete and committed. Session handed off.

## Next

- `[ ]` Optional dogfood: write a fresh SOUL.md using the upgraded skill on a real agent use-case. Verify Writing Rule 4 (named failure modes) actually shows up in the draft.
- `[ ]` Optional corpus expansion: add 1–2 more positive examples (e.g. Perplexity's tone block, OpenAI personality presets) to broaden coverage. Diminishing returns after ~5 total, but worth doing before the corpus snapshot goes stale.

## Blocked

- None.

> [!] Marks blockers or agent-side issues (not human blockers).
