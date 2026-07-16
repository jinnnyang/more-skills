# Design Decisions — Session Handoff Protocol

> Append-only log. Never rewrite past entries; add a new dated entry that supersedes if needed.
> Each entry records: date, decision id, decision, rationale, alternatives rejected.

---

## 2026-07-16 — Initial Design Decisions

### ① Document format
**Decision:** YAML frontmatter + Markdown body for all handoff documents.
**Rationale:** Enables cheap L1 pre-scan by take-over — only frontmatter needs parsing to decide whether to load full body. Aligns with SKILL.md format. Robust against agent-authored format drift (`---` fences are a hard boundary).
**Rejected:** Plain Markdown with convention'd `**Status:**` lines — too fragile against whitespace/case drift.

### ② Walkthrough growth control
**Decision:** Single `walkthrough.md` file, actively pruned. Not append-only, not audit log.
**Rationale:** Walkthrough is *working memory*, not permanent record. Resolved items must be removable to keep L3 load cost bounded (< 20 KB target). Long-term audit trail already exists in `git log` and `session_search`.
**Rejected:**
- One file per session (`walkthrough/<date>-<slug>.md`) — creates file sprawl, still needs pruning.
- Single-file-with-quarterly-archive — YAGNI for MVP; add later if size becomes a real issue.

### ③ Git commit on hand-off
**Decision:** Private `.hermes/handoff/` is `.gitignore`'d — no commit action. On explicit promote → `docs/handoff/`, always ask via `clarify` (structured choices: leave private / promote+commit / promote+stage-only). If commit chosen, offer editable default message `docs(handoff): <slug> — <status>`.
**Rationale:** Default (private, no commit) is zero-friction for 90% of sessions. Promote is a user-initiated action, so an interactive commit prompt is appropriate. Structured choices prevent ambiguous free-text answers.
**Rejected:**
- Auto-commit on promote — user often wants to bundle with unrelated changes or edit the message.
- Never touch git — makes promotion less useful.

### ④ Take-over conflict handling
**Decision:** Tiered per §9b of PROTOCOL.md.
- **HARD** (doc claims contradicted by code/git, cross-doc contradictions, invariant violations) → HALT via `clarify`.
- **SOFT** (stale `last_verified`, renamed files, pruned session_id) → log to `open-questions.md` with `⚠️ stale`, continue.
- **AMBIGUOUS** → escalate to HARD (fail-safe).
**Rationale:** Consistent with §9a Smart Cleanup philosophy. User only interrupted for highest-signal conflicts.
**Rejected:**
- Halt on any conflict — too disruptive (a 3-day-old timestamp shouldn't stop take-over).
- Auto-log everything — hard conflicts (docs lying) must not slip through silently.
- Tag as "low-confidence" and proceed — dangerous downstream when agent acts on unverified info.

---

## Cross-cutting rules established at the same time

### User interaction (§10a)
All user-facing prompts from both skills MUST use `AskUserQuestion` (Hermes: `clarify`) with structured `choices`, not free-text messages. Free-text only for genuinely open-ended follow-ups.

### plan-mode relationship
`plan-mode` is design inspiration only. No runtime coupling. `hand-off` / `take-over` do not read `.hermes/plans/` and do not require `plan-mode` to be installed.

### Skill layout
Two peer skills — `skills/hand-off/` and `skills/take-over/` — sharing this protocol via `skills/_shared/session-handoff/`. Neither skill owns the protocol; both reference it.

---

*Next entries append here. Do not edit past decisions in place — supersede with a new dated entry.*
