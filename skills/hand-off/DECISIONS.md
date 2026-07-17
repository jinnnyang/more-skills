# Design Decisions — `hand-off` skill

> Append-only log. Never rewrite past entries; add a new dated entry that supersedes if needed.
> Each entry records: date, decision id, decision, rationale, alternatives rejected.
> **Scope:** decisions relevant to the `hand-off` half of the session handoff protocol. The companion skill `take-over` maintains its own `DECISIONS.md`. Cross-cutting decisions appear in both.

---

## 2026-07-16 — Initial Design Decisions

### ① Document format (cross-cutting)
**Decision:** YAML frontmatter + Markdown body for all handoff documents.
**Rationale:** Enables cheap L1 pre-scan by take-over — only frontmatter needs parsing to decide whether to load full body. Aligns with SKILL.md format. Robust against agent-authored format drift (`---` fences are a hard boundary).
**Rejected:** Plain Markdown with convention'd `**Status:**` lines — too fragile against whitespace/case drift.

### ② Walkthrough growth control (hand-off specific)
**Decision:** Single `walkthrough.md` file, actively pruned. Not append-only, not audit log.
**Rationale:** Walkthrough is *working memory*, not permanent record. Resolved items must be removable to keep L3 load cost bounded (< 20 KB target). Long-term audit trail already exists in `git log` and `session_search`.
**Rejected:**
- One file per session (`walkthrough/<date>-<slug>.md`) — creates file sprawl, still needs pruning.
- Single-file-with-quarterly-archive — YAGNI for MVP; add later if size becomes a real issue.

### ③ Git commit on hand-off (hand-off specific)
**Decision:** Private `.hermes/handoff/` is `.gitignore`'d — no commit action. On explicit promote → `docs/handoff/`, always ask via `clarify` (structured choices: leave private / promote+commit / promote+stage-only). If commit chosen, offer editable default message `docs(handoff): <slug> — <status>`.
**Rationale:** Default (private, no commit) is zero-friction for 90% of sessions. Promote is a user-initiated action, so an interactive commit prompt is appropriate. Structured choices prevent ambiguous free-text answers.
**Rejected:**
- Auto-commit on promote — user often wants to bundle with unrelated changes or edit the message.
- Never touch git — makes promotion less useful.

---

## Cross-cutting rules established at the same time

### User interaction (§10a) (cross-cutting)
All user-facing prompts from both skills MUST use `AskUserQuestion` (Hermes: `clarify`) with structured `choices`, not free-text messages. Free-text only for genuinely open-ended follow-ups.

### plan-mode relationship (cross-cutting)
`plan-mode` is design inspiration only. No runtime coupling. `hand-off` / `take-over` do not read `.hermes/plans/` and do not require `plan-mode` to be installed.

---

## 2026-07-16 (rev-2) — MVP simplifications after review

Following an internal review of PROTOCOL v0.1, several sections had drifted from the DECISIONS ①②③ agreed above. This entry records the corrections and small MVP-focused simplifications. **None of ①②③ are superseded** — this is alignment work.

### R1 · Walkthrough form: clarify — single file (aligned with ②) (hand-off specific)
**Context:** §5 layout showed `walkthrough/<date>-<slug>.md` + `INDEX.md`; §8 Step 2b said "NEW file, append-only". This contradicted DECISIONS ② ("single `walkthrough.md`, actively pruned").
**Decision:** Enforce single-file `walkthrough.md` throughout. Removed `walkthrough/` subdirectory and `INDEX.md`. §8 Step 2b now "UPDATE the single living file: append today's entry, prune per §9a, target < 20 KB, do not split".
**Rationale:** ② was correct; the other sections drifted. Per-session files reintroduce a pruning + indexing problem ② already rejected. Long-term audit trail remains in git log + session_search.

### R2 · Frontmatter minimum surface (§6) (cross-cutting)
**Decision:** MVP frontmatter carries only fields with an actual reader in `hand-off` / `take-over`:
`kind, version, last_updated, last_verified, last_agent, last_writer, session_id (optional), status`.
Added: **`last_writer`** (hand-off | take-over | user | migration) — supports §9 anti-hallucination audit ("did take-over invent this entry?").
Deferred to §13: `project` (implied by cwd), `branch` (needs v2 branch-prefix layout), `next_agent` (no claim protocol yet).
`last_updated` / `last_verified` **must** include ISO-8601 timezone offset to avoid Windows/Unix parse drift.
**Rationale:** every frontmatter field is a chance for an agent to hallucinate a value. Fewer fields = fewer failure modes. Fields can be reintroduced when a reader exists.

### R3 · `open-questions.md` vs `task.md` boundary (§4.1) (cross-cutting)
**Decision:** `open-questions.md` is exclusively for items requiring a **human** answer. Agent-side blockers (waiting on API, build, tool availability) stay in `task.md` with a `[!]` marker.
**Rationale:** the two were previously ambiguous, causing "blockers" to be dumped into open-questions.md, which then bloated and drifted from actual human decision points.

### R4 · Promote semantics = COPY snapshot (§8 Step 4) (hand-off specific)
**Decision:** Promoting to `docs/handoff/` is a **copy** (not move). `.hermes/handoff/` continues to be the live working set. Files copied into `docs/handoff/` receive `frozen: true` in frontmatter; skills MUST NOT re-touch frozen files. Re-promoting overwrites the frozen copy.
**Rationale:** the previous wording was silent on move-vs-copy. Copy is the least surprising ("publish a snapshot") and matches the "leave private working memory intact" mental model.

---

## 2026-07-16 — Post-Review Design Decisions (v0.3)

Following the comprehensive review of PROTOCOL v0.2, several critical reliability, architecture, and user experience issues were addressed.

### ① Script-assisted Execution to Lower Cognitive Load (cross-cutting)
**Decision:** Standardize on a script-based helper pattern. Realize complex YAML parsing, Reality Check logic, Smart Cleanup classification, and Conflict Handling calculation in a python script (`scripts/reconcile.py` local to each skill) instead of relying solely on pure AI reasoning in the skill text.
**Rationale:** Operating at high context usage (>75%) significantly degrades LLM reasoning capabilities. Offloading deterministic logic to Python ensures reliability and keeps the AI cognitive load minimal.

### ② Atomic Write Protection (cross-cutting)
**Decision:** All writes to `.hermes/handoff/` and `docs/handoff/` must be atomic: write to a `.tmp` file and rename (POSIX `rename()`) to overwrite the target.
**Rationale:** Prevents torn writes/corrupted files if the agent is interrupted or crashes midway through the hand-off process.

### ③ Metadata-based Tool-Call History Logs (hand-off specific)
**Decision:** Add a structured `<session-tools-log>` markdown block at the bottom of the active `walkthrough.md`. It must serialize the list of actual tool calls (tool name, timestamp, simplified inputs/outputs) of the current session.
**Rationale:** The LLM tool-call history is in-memory and lost across sessions. Recording it in walkthrough metadata allows the next session's `take-over` flow to verify claims without relying on agent memory.

### ④ Cold-Start (Bootstrap) and Empty State Handling (cross-cutting)
**Decision:** If `.hermes/handoff/` does not exist during `hand-off`, it is automatically initialized. Bootstrap uses templates from this skill's own `templates/` directory.
**Rationale:** Resolves the first-time-use (FTU) user experience gap.

### ⑥ Unified Frontmatter Kind Enum & Context Append-Only (cross-cutting)
**Decision:** Frontmatter `kind` is strictly restricted to the enum values: `context`, `task`, `walkthrough`, `open-questions`, `plan`, `review`. `context.md` is strictly additive; corrections are appended at the bottom as dated correction entries.
**Rationale:** Eliminates parser ambiguity and maintains a clean audit trail.

---

## 2026-07-17 — Adopted 方案 A: self-contained skill directories

**Decision:** Each skill (`hand-off`, `take-over`) is a **self-contained directory** with its own copy of `PROTOCOL.md`, `DECISIONS.md`, `scripts/reconcile.py`, and `templates/`. No cross-skill file dependency. No shared `_shared/session-handoff/` runtime import.

**Supersedes:** 2026-07-16 "Skill layout" cross-cutting note ("Two peer skills sharing this protocol via `skills/_shared/session-handoff/`").

**Rationale:**
- Every path referenced in a SKILL.md must be **relative to that skill's own directory**. Skill users may install a single skill in isolation (drop the folder into their own repo), and any outside dependency breaks that use case.
- Absolute paths and cross-skill `../_shared/…` references had already accumulated concrete bugs (e.g. `file:///home/twait-halek/...` embedded literals from another user's machine, and `../_shared/` relative references that break when a single skill is copied out).
- Single-directory installability is a stronger correctness property than single-source-of-truth for prose/scripts of this size.

**Rejected alternatives:**
- **Keep `_shared/` runtime references** (previous layout) — violates "every skill directory is independently runnable"; users copying just one skill get broken paths.
- **Hybrid main/shim (one skill hosts, the other references)** — breaks the "peer skills" design intent and still couples one skill to the other's directory tree.
- **Auto-sync via build script or symlink** — Windows symlink permissions are painful, and a build step forces users to install tooling before using a skill. Manual sync (MVP) then a drift-check script (later) is preferred.

**Trade-off accepted:** duplication cost. `reconcile.py` (≈411 lines) is duplicated verbatim; `PROTOCOL.md` is duplicated with view-adjusted section selection; `DECISIONS.md` is split per-skill (this file records hand-off-relevant decisions only). `templates/` are duplicated verbatim.

**Consequences:**
- The `_shared/session-handoff/` folder becomes a **development-time source-of-reference only** — not a skill, not loaded at runtime. Its README makes this explicit.
- Drift management is currently **pure human discipline** (each commit that touches a shared artifact must include the mirrored change). Escalation to a drift-check script is deferred (see PROTOCOL §13).

**Verification (2026-07-17):**
- `skills/hand-off/scripts/reconcile.py` and `skills/take-over/scripts/reconcile.py` byte-identical to the `_shared/` origin at this commit.
- `skills/hand-off/templates/` and `skills/take-over/templates/` byte-identical to the `_shared/` origin at this commit.
- Both `SKILL.md` files now use `<SKILL_DIR>/scripts/reconcile.py` relative references only.

---

*Next: address remaining review findings (Windows path handling, parser hardening, dry-run mode) — see PROTOCOL §13 open questions.*
