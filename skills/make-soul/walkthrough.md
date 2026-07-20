---
kind: walkthrough
version: 1
last_updated: '2026-07-20T09:06:46+00:00'
last_verified: '2026-07-20T09:05:00+00:00'
last_agent: Hermes Agent (ark-code-latest)
last_writer: hand-off
session_id: sess-20260720-make-soul-corpus-opt
status: phase-complete
---

# Living Work Memory & Walkthrough

> [!NOTE]
> Walkthrough is editable working memory, pruned when items resolve.
> Keep decision reasons, files changed, and surprises. Do NOT write full transcript replays.
>
> **Entry header format**: `## YYYY-MM-DD — <slug>` (required for the cleanup classifier).
>
> **Lifecycle markers** (used by `hand-off`'s Smart Cleanup):
> - `<!-- keep -->` in entry body OR any of the keywords `lesson` / `surprise` / `decision` / `invariant` in the header → KEEP forever.
> - `<!-- resolved -->` in entry header or body → CLEAR on next hand-off.
> - No marker + age > 30 days + not referenced from `task.md` / `context.md` → STALE.
> - Anything else → UNSURE (batched confirmation before deletion).

## History of Active Entries

## 2026-07-20 — Plan B restructure of make-soul (decision)

- Decision: restructure `SKILL.md` around four verbs — Discover → Draft → Stress-Test → Deliver — instead of the original 6-step workflow + parallel Discovery Patterns section.
- Rationale: original 192-line `SKILL.md` had two overlapping structures (`Required Workflow` vs `Discovery Patterns`) and two overlapping constraint lists (`Writing Rules` vs `Anti-Patterns`). Both pairs merged.
- Files changed:
  - `SKILL.md` — full rewrite, 192 → 109 lines. Frontmatter renamed `soul-md-creator` → `make-soul`. New Operating Modes table (5 rows) and Reference Map table (4 rows) at top.
  - `references/persona-research-heuristics.md` — rewritten, 60 → 91 lines. Now serves as the "why each Red Line exists" rationale doc.
  - `references/deliverable-format.md` — NEW, 70 lines. Canonical output shape with a worked Code Reviewer example.
  - `references/openclaw-official.md`, `references/souls-directory-publishing.md` — unchanged; verified they are pure external-facts pages with zero duplication.
- Surprise: the two `openclaw-official.md` / `souls-directory-publishing.md` files were the cleanest part of the upstream skill — no edits needed at all.
- Verification: uv+pyyaml frontmatter parse OK; all `./references/*` cross-links resolve; total footprint 423 lines (was 405).
- <!-- keep -->

## 2026-07-20 — Deep optimization + production-corpus pass (decision, lesson)

Two consecutive optimization rounds folded into one feat commit (`823bbfb`) plus one housekeeping commit (`cccff14`).

**Round 1 — Concept-first optimization**

- Motivation: user asked what SOUL actually *is* — the skill had a workflow but no conceptual foundation. Answering the question surfaced enough theory to write a proper backbone.
- Two new documents from the same source material:
  - `references/what-is-a-soul.md` (108 lines) — skill-internal operational cut: persona stack L0–L5, belief-vs-instruction句式, L1-catch test, three writing rules.
  - `docs/what-is-a-soul.md` (repo root, 759 lines with corpus additions) — independent learning document, 12 chapters + 3 appendices. Reads without skill context.
- `SKILL.md` upgraded 109 → 161 lines: Writing Rules section ahead of the loop, Discover stop condition + dialogue demo, Draft acceptance-gate table, Stress-Test scenario 4 (self-description drift canary) + pass/fail comparison, Alignment recipe, Publish+IDENTITY coexistence rule.
- `persona-research-heuristics.md` grew 91 → 144 lines: mechanism sections for each writing rule; smuggled-content red line.

**Round 2 — Production corpus grounding**

- Source: `asgeirtj/system_prompts_leaks` (CC0), snapshot 2026-07-20. Extracted SOUL portions only; tool/format/policy scaffolding stripped.
- Six extracts under new `examples/` directory:
  - `good/sesame-maya.md` — voice companion, ~450 words, textbook-level named failure modes + contrast句式 + self-fallibility.
  - `good/nous-hermes.md` — canonical SOUL.md shape used verbatim; ~250 words.
  - `good/openai-4o-v2.md` — extreme compression, ~56 words. Also demonstrates that jussive句式 has real-world defenders (with attendant jailbreak risk).
  - `good/gemini-3-pro.md` — single-paragraph pattern, ~71 words, single-tension organizing principle ("warmth vs intellectual honesty").
  - `good/anthropic-long-conversation-reminder.md` — runtime three-layer anti-drift mechanism; direct evidence for `docs/what-is-a-soul.md` Ch 7.3.
  - `bad/grok-companion.md` — violates all three writing rules; used as concrete diagnostic reference.
- `SKILL.md` upgrades: `examples/` in Reference Map; Writing Rule 1 extended with "X, not Y" preference + show-don't-tell clause; new Writing Rule 4 (name specific failure modes); Draft section adds "each Core Truth must declare something the agent gives up" + Continuity fallibility requirement + Size Target with production data points; acceptance gate now checks what each Truth pushes against.
- `persona-research-heuristics.md`: new section "Push against at least one specific RLHF default" — every serious production SOUL fights an over-cooperative habit; four verbatim quotes as evidence.
- `docs/what-is-a-soul.md` Ch 7.3 gets Anthropic three-layer reminder case study; Ch 12 adds 拓展主题 placeholder for Multi-Soul / re-injection payload / SOUL versioning.

**Surprises**

- Sesame Maya's SOUL is longer and more complete than any of the frontier-lab SOULs. The compression discipline visible in OpenAI/Gemini isn't universal — Sesame chose density instead.
- Anthropic's `system_reminder` (Level 3) is the most sophisticated single piece of persona engineering in the corpus — pure meta-cognitive nudge, zero rules. It's the extreme case of Writing Rule 1.
- Grok Companion violated all three writing rules so cleanly that it works better as a teaching example than any rewrite exercise would.

**Housekeeping surprise**

- `.handoff.lock` was untracked but not gitignored — hand-off's own runtime lock was missing from the exclude list. Added in `cccff14`. Worth checking whether other skill runtime files have the same gap.

**Lessons for future SOUL work**

- Named failure modes ("hallucinations", "sycophancy", "toxic positivity", "echoing") beat generic negations ("avoid negativity"). Every production SOUL uses named modes.
- Contrast句式 ("honest, not earnest") is the single highest-leverage technique — it forces value declarations to include what's given up.
- Every serious SOUL pushes against at least one specific RLHF default. A SOUL that doesn't fight anything is decorative.
- Size range for production SOULs is 10–30 lines / 100–600 words. Longer usually means smuggled non-SOUL content.

<!-- keep -->

---

<session-tools-log>
[]
</session-tools-log>
