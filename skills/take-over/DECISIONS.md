# Design Decisions — `take-over` skill

> Append-only log. Never rewrite past entries; add a new dated entry that supersedes if needed.
> Each entry records: date, decision id, decision, rationale, alternatives rejected.
> **Scope:** decisions relevant to the `take-over` half of the session handoff protocol. The companion skill `hand-off` maintains its own `DECISIONS.md`. Cross-cutting decisions appear in both.

---

## 2026-07-16 — Initial Design Decisions

### ① Document format (cross-cutting)
**Decision:** YAML frontmatter + Markdown body for all handoff documents.
**Rationale:** Enables cheap L1 pre-scan by take-over — only frontmatter needs parsing to decide whether to load full body. Aligns with SKILL.md format. Robust against agent-authored format drift (`---` fences are a hard boundary).
**Rejected:** Plain Markdown with convention'd `**Status:**` lines — too fragile against whitespace/case drift.

### ④ Take-over conflict handling (take-over specific)
**Decision:** Tiered per §9b of PROTOCOL.md.
- **HARD** (doc claims contradicted by code/git, cross-doc contradictions, invariant violations) → HALT via `clarify`.
- **SOFT** (stale `last_verified`, renamed files, pruned session_id) → log to `open-questions.md` with `⚠️ stale` under `## Soft Conflicts (Reconciled)` section, continue.
- **AMBIGUOUS** → escalate to HARD (fail-safe).
**Rationale:** Consistent with hand-off's Smart Cleanup philosophy (§9a in hand-off's PROTOCOL). User only interrupted for highest-signal conflicts.
**Rejected:**
- Halt on any conflict — too disruptive (a 3-day-old timestamp shouldn't stop take-over).
- Auto-log everything — hard conflicts (docs lying) must not slip through silently.
- Tag as "low-confidence" and proceed — dangerous downstream when agent acts on unverified info.

---

## Cross-cutting rules established at the same time

### User interaction (§10a) (cross-cutting)
All user-facing prompts from both skills MUST use `AskUserQuestion` (Hermes: `clarify`) with structured `choices`, not free-text messages. Free-text only for genuinely open-ended follow-ups.

### plan-mode relationship (cross-cutting)
`plan-mode` is design inspiration only. No runtime coupling. `hand-off` / `take-over` do not read `.hermes/plans/` and do not require `plan-mode` to be installed. For take-over: if `.hermes/plans/` is present, the coexistence flow (§7 Step 6) offers a one-shot, opt-in import via `clarify`.

---

## 2026-07-16 (rev-2) — MVP simplifications after review

Following an internal review of PROTOCOL v0.1. **None of ①④ are superseded** — this is alignment work.

### R2 · Frontmatter minimum surface (§6) (cross-cutting)
**Decision:** MVP frontmatter carries only fields with an actual reader in `hand-off` / `take-over`:
`kind, version, last_updated, last_verified, last_agent, last_writer, session_id (optional), status`.
Added: **`last_writer`** (hand-off | take-over | user | migration) — supports §9 anti-hallucination audit ("did take-over invent this entry?").
Deferred to §13: `project` (implied by cwd), `branch` (needs v2 branch-prefix layout), `next_agent` (no claim protocol yet).
`last_updated` / `last_verified` **must** include ISO-8601 timezone offset to avoid Windows/Unix parse drift.
**Rationale:** every frontmatter field is a chance for an agent to hallucinate a value. Fewer fields = fewer failure modes. Fields can be reintroduced when a reader exists.

### R3 · `open-questions.md` vs `task.md` boundary (§4.1) (cross-cutting)
**Decision:** `open-questions.md` is exclusively for items requiring a **human** answer. Agent-side blockers (waiting on API, build, tool availability) stay in `task.md` with a `[!]` marker.
**Rationale:** the two were previously ambiguous. take-over's SOFT-conflict logging must land in the correct file — human questions and stale reconciliations go into `open-questions.md`; automated retry blockers go into `task.md`.

### R5 · plan-mode coexistence check (§7 Step 6) (take-over specific)
**Decision:** On take-over, if `.hermes/plans/` exists, report its presence in the summary but **do not auto-merge**. On explicit user request via `clarify`, offer Ignore / Import plan.md / Show diff. Never write to `.hermes/plans/`.
**Rationale:** independence from plan-mode is a stated design goal, but users who have plan-mode artifacts should get a visible bridge rather than silent orphaning. The bridge is explicit and one-shot; no runtime coupling.

### R6 · Open questions cleanup (§13) (bookkeeping)
**Decision:** Removed obsolete "does INDEX.md auto-regenerate?" (INDEX.md no longer exists per hand-off's R1). Added: concurrent take-over, multi-branch layout, `next_agent` claim protocol, dry-run mode for `take-over`, drift-detection tooling between self-contained skills.
**Rationale:** §13 must reflect the current design surface, not v0.1's.

---

## 2026-07-16 — Post-Review Design Decisions (v0.3)

Following the comprehensive review of PROTOCOL v0.2.

### ① Script-assisted Execution to Lower Cognitive Load (cross-cutting)
**Decision:** Standardize on a script-based helper pattern. Realize complex YAML parsing, Reality Check logic, and Conflict Handling calculation in a python script (`scripts/reconcile.py` local to each skill) instead of relying solely on pure AI reasoning in the skill text.
**Rationale:** Operating at high context usage (>75%) significantly degrades LLM reasoning capabilities. Offloading deterministic logic to Python ensures reliability and keeps the AI cognitive load minimal.

### ③ Atomic Write Protection (cross-cutting)
**Decision:** All writes to `.hermes/handoff/` and `docs/handoff/` must be atomic: write to a `.tmp` file and rename (POSIX `rename()`) to overwrite the target. take-over writes to `.hermes/handoff/` only when logging SOFT conflicts or initializing empty files.
**Rationale:** Prevents torn writes/corrupted files if the agent is interrupted or crashes midway through take-over.

### ④ Cold-Start (Bootstrap) and Empty State Handling (cross-cutting)
**Decision:** If `.hermes/handoff/` does not exist during `take-over`, it is automatically initialized. `take-over` will report: "No previous handoff history found. Initialized empty session." and populate default files from this skill's `templates/` directory.
**Rationale:** Resolves the first-time-use (FTU) user experience gap.

### ⑤ Pre-empt Plan-Mode Merge Check (take-over specific)
**Decision:** Position the `plan-mode` coexistence check (§7 Step 6) *before* the final report to the user in `take-over` (§7 Step 7).
**Rationale:** If `plan-mode` files are imported, the report must reflect the imported tasks; otherwise, the summary shown to the user becomes immediately stale.

### ⑥ Unified Frontmatter Kind Enum & Context Append-Only (cross-cutting)
**Decision:** Frontmatter `kind` is strictly restricted to the enum values: `context`, `task`, `walkthrough`, `open-questions`, `plan`, `review`. `context.md` is strictly additive; take-over must not rewrite past entries.
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

**Trade-off accepted:** duplication cost. `reconcile.py` (≈411 lines) is duplicated verbatim; `PROTOCOL.md` is duplicated with view-adjusted section selection; `DECISIONS.md` is split per-skill (this file records take-over-relevant decisions only). `templates/` are duplicated verbatim.

**Consequences:**
- The `_shared/session-handoff/` folder becomes a **development-time source-of-reference only** — not a skill, not loaded at runtime. Its README makes this explicit.
- Drift management is currently **pure human discipline** (each commit that touches a shared artifact must include the mirrored change). Escalation to a drift-check script is deferred (see PROTOCOL §13).

**Verification (2026-07-17):**
- `skills/hand-off/scripts/reconcile.py` and `skills/take-over/scripts/reconcile.py` byte-identical to the `_shared/` origin at this commit.
- `skills/hand-off/templates/` and `skills/take-over/templates/` byte-identical to the `_shared/` origin at this commit.
- Both `SKILL.md` files now use `<SKILL_DIR>/scripts/reconcile.py` relative references only.

---

## 2026-07-17 (rev-B) — Post-review script hardening

Second round of design-doc-review findings, focused on the scripts and take-over reconciliation semantics. `_shared/PROTOCOL.md` / `_shared/DECISIONS.md` are now frozen historical snapshots; further protocol changes land only in each skill's own copy.

### R7 · Frontmatter parser: switch to pyyaml (cross-cutting)
**Decision:** `reconcile.py` now uses `pyyaml` via uv's inline script metadata. Bare `python` invocations require pyyaml on the ambient interpreter; `uv run` installs it automatically.
**Rationale:** the hand-rolled parser choked on quoted values, inline comments, and the `kind` enum requirement from v0.3 ⑥.
**Impact on take-over:** frontmatter validation (`reconcile.py validate`) now enforces the kind enum reliably before Step 3 loads any body content.

### R8 · CLI evidence transport: stdin / --content-file (cross-cutting)
**Decision:** `write-atomic` accepts `--content-file <path>`, stdin, or `--content <inline>` — SKILL.md steers agents to file-based transport.
**Rationale:** Windows argv size cap made the previous `--content "…"` API break on real handoff-file sizes.
**Impact on take-over:** the `conflict_pending.json` write on non-interactive HARD-conflict timeout now uses `--content-file`.

### R9 · Cross-platform file-reference detection (cross-cutting)
**Decision:** `check-reality`'s "missing file" check handles Windows / POSIX / MSYS paths and filters out documentation-looking tokens (URLs, `/tmp/…` examples, tokens without a `.ext` tail).
**Rationale:** the previous POSIX-only regex was silently a no-op on Windows and produced false HARD conflicts on Linux.

### R10 · Explicit lifecycle markers replace free-text grep (referenced by take-over via mirrored templates)
**Decision:** Smart Cleanup CLEAR/KEEP classification uses `<!-- keep -->` / `<!-- resolved -->` HTML markers, not free-text `"resolved"` grep.
**Rationale:** free-text matched sentences like "not resolved yet" and deleted live entries.
**Impact on take-over:** open-questions.md sections created by `take-over` (SOFT conflicts) will be preserved automatically because the `## Soft Conflicts (Reconciled)` heading is exempted from cleanup and its entries are dated but not marked resolved.

### R11 · Two-phase Smart Cleanup (dry-run → apply) (hand-off specific, mirrored for awareness)
**Decision:** `clean-up` requires `--dry-run` or `--apply`; dry-run first, then apply after user confirmation.
**Rationale:** consistent with §9a "err toward UNSURE"; the previous one-shot mode landed deletions before the user saw the plan.

### R12 · SOFT conflict logging by script, not agent (take-over specific)
**Decision:** `check-reality --apply-soft-conflicts` writes SOFT conflicts directly into `open-questions.md` under `## Soft Conflicts (Reconciled)` with UTC timestamp and `⚠️` marker. `take-over` Step 2 uses this flag; Step 5 no longer constructs the section itself.
**Rationale:** consistent with v0.3 ① (script-assisted execution). Removes another surface where the agent could hallucinate the section shape or drift from the format take-over's next run expects.

### R13 · Serializer double-newline fix (cross-cutting)
**Decision:** `dump_frontmatter` avoids the previous serializer's double-newline bug on body concatenation.
**Rationale:** trivial correctness fix; matters more for take-over than hand-off because take-over re-serializes on every SOFT-conflict apply.

### R14 · Auxiliary evidence: `<session-tools-log>` demoted (cross-cutting)
**Decision:** `<session-tools-log>` is auxiliary evidence only. `git status --short` + `git log -5 --name-only` are the primary evidence source for take-over's reconciliation; tools-log entries lacking git presence surface as SOFT conflicts.
**Rationale:** the Hermes runtime does not currently expose a reliable structured tool-call history, so agent-constructed tools-log blocks cannot substitute for git evidence.

### R15 · `validate` command added (take-over specific — new Step 1 sub-check)
**Decision:** New `reconcile.py validate` subcommand runs frontmatter validation across all handoff docs. `take-over` Step 1 calls it before loading any body content and treats parse errors as HARD conflicts.
**Rationale:** enforces v0.3 ⑥ kind enum + timezone-aware timestamps + status/writer enum without waiting for the fuller `check-reality` pass. Any doc that fails validation halts loading immediately, preventing garbage-in propagation to the runtime `todo`.

### R16 · CLI does NOT pass `--isolated` to uv (documentation fix)
**Decision:** SKILL.md invocations use `uv run <path> …` (no `--isolated`).
**Rationale:** `uv run` is already isolated for scripts declaring inline `# /// script` metadata; passing `--isolated` produces a warning and no additional effect.

### R17 · Step ordering: re-restore todo after plan-mode import (take-over specific)
**Decision:** SKILL.md Step 4 (Restore Checklist) is re-run at the end of Step 6 (Plan-Mode Coexistence) if the user chose "Import plan.md". The final Step 7 summary reflects the reconciled task list.
**Rationale:** DECISIONS 2026-07-16 v0.3 ⑤ ("Pre-empt Plan-Mode Merge Check") intended the report to be up-to-date, but Step 4's original position (before Step 6) meant an imported plan.md's tasks never made it into `todo`.

