---
kind: walkthrough
version: 1
last_updated: '2026-07-20T03:06:22+00:00'
last_verified: 2026-07-20 02:58:15+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: hand-off
session_id: sess-20260720-make-soul-refactor
status: in-progress
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

---

<session-tools-log>
[]
</session-tools-log>
