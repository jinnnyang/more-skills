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

## 2026-07-16 (rev-2) — MVP simplifications after review

Following an internal review of PROTOCOL v0.1, several sections had drifted from the DECISIONS ①②③④ agreed above. This entry records the corrections and small MVP-focused simplifications. **None of ①②③④ are superseded** — this is alignment work.

### R1 · Walkthrough form: clarify — single file (aligned with ②)

**Context:** §5 layout showed `walkthrough/<date>-<slug>.md` + `INDEX.md`; §8 Step 2b said "NEW file, append-only". This contradicted DECISIONS ② ("single `walkthrough.md`, actively pruned").
**Decision:** Enforce single-file `walkthrough.md` throughout. Removed `walkthrough/` subdirectory and `INDEX.md` from §5. §8 Step 2b now "UPDATE the single living file: append today's entry, prune per §9a, target < 20 KB, do not split".
**Rationale:** ② was correct; the other sections drifted. Per-session files reintroduce a pruning + indexing problem ② already rejected. Long-term audit trail remains in git log + session_search.

### R2 · Frontmatter minimum surface (§6)

**Decision:** MVP frontmatter carries only fields with an actual reader in `hand-off` / `take-over`:
`kind, version, last_updated, last_verified, last_agent, last_writer, session_id (optional), status`.
Added: **`last_writer`** (hand-off | take-over | user | migration) — supports §9 anti-hallucination audit ("did take-over invent this entry?").
Deferred to §13: `project` (implied by cwd), `branch` (needs v2 branch-prefix layout), `next_agent` (no claim protocol yet).
`last_updated` / `last_verified` **must** include ISO-8601 timezone offset to avoid Windows/Unix parse drift.
**Rationale:** every frontmatter field is a chance for an agent to hallucinate a value. Fewer fields = fewer failure modes. Fields can be reintroduced when a reader exists.

### R3 · `open-questions.md` vs `task.md` boundary (§4.1)

**Decision:** `open-questions.md` is exclusively for items requiring a **human** answer. Agent-side blockers (waiting on API, build, tool availability) stay in `task.md` with a `[!]` marker.
**Rationale:** the two were previously ambiguous, causing "blockers" to be dumped into open-questions.md, which then bloated and drifted from actual human decision points.

### R4 · Promote semantics = COPY snapshot (§8 Step 4)

**Decision:** Promoting to `docs/handoff/` is a **copy** (not move). `.hermes/handoff/` continues to be the live working set. Files copied into `docs/handoff/` receive `frozen: true` in frontmatter; skills MUST NOT re-touch frozen files. Re-promoting overwrites the frozen copy.
**Rationale:** the previous wording was silent on move-vs-copy. Copy is the least surprising ("publish a snapshot") and matches the "leave private working memory intact" mental model.

### R5 · plan-mode coexistence check (§7 Step 7)

**Decision:** On take-over, if `.hermes/plans/` exists, report its presence in the summary but **do not auto-merge**. On explicit user request, offer a `clarify` with Ignore / Import plan.md / Show diff. Never write to `.hermes/plans/`.
**Rationale:** independence from plan-mode is a stated design goal, but users who have plan-mode artifacts should get a visible bridge rather than silent orphaning. The bridge is explicit and one-shot; no runtime coupling.

### R6 · Open questions cleanup (§13)

**Decision:** Removed obsolete "does INDEX.md auto-regenerate?" (INDEX.md no longer exists per R1). Added: concurrent hand-off, multi-branch layout, `next_agent` claim protocol, dry-run mode for `hand-off`.
**Rationale:** §13 must reflect the current design surface, not v0.1's.

---

## 2026-07-16 — Post-Review Design Decisions (v0.3)

Following the comprehensive review of PROTOCOL v0.2, several critical reliability, architecture, and user experience issues were addressed and incorporated into the protocol.

### ① Script-assisted Execution to Lower Cognitive Load
**Decision:** Standardize on a script-based helper pattern. Realize complex YAML parsing, Reality Check logic, Smart Cleanup classification, and Conflict Handling calculation in a python script (`skills/_shared/session-handoff/scripts/reconcile.py`) instead of relying solely on pure AI reasoning in the skill text.
**Rationale:** Operating at high context usage (>75%) significantly degrades LLM reasoning capabilities. Offloading deterministic logic to Python ensures reliability and keeps the AI cognitive load minimal.

### ② Atomic Write Protection
**Decision:** All writes to `.hermes/handoff/` and `docs/handoff/` must be atomic: write to a `.tmp` file and rename (POSIX `rename()`) to overwrite the target.
**Rationale:** Prevents torn writes/corrupted files if the agent is interrupted or crashes midway through the hand-off process.

### ③ Metadata-based Tool-Call History Logs
**Decision:** Add a structured `<session-tools-log>` markdown block at the bottom of the active `walkthrough.md`. It must serialize the list of actual tool calls (tool name, timestamp, simplified inputs/outputs) of the current session.
**Rationale:** The LLM tool-call history is in-memory and lost across sessions. Recording it in walkthrough metadata allows the next session's `take-over` flow to verify claims without relying on agent memory.

### ④ Cold-Start (Bootstrap) and Empty State Handling
**Decision:** If `.hermes/handoff/` does not exist during `take-over` or `hand-off`, it is automatically initialized. `take-over` will report: "No previous handoff history found. Initialized empty session." and populate default files from `_shared/session-handoff/templates/`.
**Rationale:** Resolves the first-time-use (FTU) user experience gap.

### ⑤ Pre-empt Plan-Mode Merge Check
**Decision:** Move the `plan-mode` coexistence check *before* the final report to the user in `take-over`.
**Rationale:** If `plan-mode` files are imported, the report must reflect the imported tasks; otherwise, the summary shown to the user becomes immediately stale.

### ⑥ Unified Frontmatter Kind Enum & Context Append-Only
**Decision:** Frontmatter `kind` is strictly restricted to the enum values: `context`, `task`, `walkthrough`, `open-questions`, `plan`, `review`. The field name `kind` is mapped cleanly (no sub-namespaces). `context.md` is strictly additive; corrections are appended at the bottom as dated correction entries.
**Rationale:** Eliminates parser ambiguity and maintains a clean audit trail.

---

*Next: implement `skills/hand-off/SKILL.md` and `skills/take-over/SKILL.md` against PROTOCOL v0.3.*
