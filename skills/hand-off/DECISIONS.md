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
**Decision:** Private `<scope>/` is `.gitignore`'d — no commit action. On explicit promote → `docs/handoff/`, always ask via `clarify` (structured choices: leave private / promote+commit / promote+stage-only). If commit chosen, offer editable default message `docs(handoff): <slug> — <status>`.
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

### R3 · `questions.md` vs `task.md` boundary (§4.1) (cross-cutting)
**Decision:** `questions.md` is exclusively for items requiring a **human** answer. Agent-side blockers (waiting on API, build, tool availability) stay in `task.md` with a `[!]` marker.
**Rationale:** the two were previously ambiguous, causing "blockers" to be dumped into questions.md, which then bloated and drifted from actual human decision points.

### R4 · Promote semantics = COPY snapshot (§8 Step 4) (hand-off specific)
**Decision:** Promoting to `docs/handoff/` is a **copy** (not move). `<scope>/` continues to be the live working set. Files copied into `docs/handoff/` receive `frozen: true` in frontmatter; skills MUST NOT re-touch frozen files. Re-promoting overwrites the frozen copy.
**Rationale:** the previous wording was silent on move-vs-copy. Copy is the least surprising ("publish a snapshot") and matches the "leave private working memory intact" mental model.

---

## 2026-07-16 — Post-Review Design Decisions (v0.3)

Following the comprehensive review of PROTOCOL v0.2, several critical reliability, architecture, and user experience issues were addressed.

### ① Script-assisted Execution to Lower Cognitive Load (cross-cutting)
**Decision:** Standardize on a script-based helper pattern. Realize complex YAML parsing, Reality Check logic, Smart Cleanup classification, and Conflict Handling calculation in a python script (`scripts/reconcile.py` local to each skill) instead of relying solely on pure AI reasoning in the skill text.
**Rationale:** Operating at high context usage (>75%) significantly degrades LLM reasoning capabilities. Offloading deterministic logic to Python ensures reliability and keeps the AI cognitive load minimal.

### ② Atomic Write Protection (cross-cutting)
**Decision:** All writes to `<scope>/` and `docs/handoff/` must be atomic: write to a `.tmp` file and rename (POSIX `rename()`) to overwrite the target.
**Rationale:** Prevents torn writes/corrupted files if the agent is interrupted or crashes midway through the hand-off process.

### ③ Metadata-based Tool-Call History Logs (hand-off specific)
**Decision:** Add a structured `<session-tools-log>` markdown block at the bottom of the active `walkthrough.md`. It must serialize the list of actual tool calls (tool name, timestamp, simplified inputs/outputs) of the current session.
**Rationale:** The LLM tool-call history is in-memory and lost across sessions. Recording it in walkthrough metadata allows the next session's `take-over` flow to verify claims without relying on agent memory.

### ④ Cold-Start (Bootstrap) and Empty State Handling (cross-cutting)
**Decision:** If `<scope>/` does not exist during `hand-off`, it is automatically initialized. Bootstrap uses templates from this skill's own `templates/` directory.
**Rationale:** Resolves the first-time-use (FTU) user experience gap.

### ⑥ Unified Frontmatter Kind Enum & Context Append-Only (cross-cutting)
**Decision:** Frontmatter `kind` is strictly restricted to the enum values: `context`, `task`, `walkthrough`, `questions`, `plan`, `review`. `context.md` is strictly additive; corrections are appended at the bottom as dated correction entries.
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

## 2026-07-17 (rev-B) — Post-review script hardening

Second round of design-doc-review findings, focused on the scripts and cleanup semantics. `_shared/PROTOCOL.md` / `_shared/DECISIONS.md` are now frozen historical snapshots; further protocol changes land only in each skill's own copy.

### R7 · Frontmatter parser: switch to pyyaml (was: hand-rolled) (cross-cutting)
**Decision:** `reconcile.py` now uses `pyyaml` via uv's inline script metadata (`# /// script … dependencies = ["pyyaml>=6.0"] # ///`). Bare `python` invocations require pyyaml on the ambient interpreter; `uv run` installs it automatically.
**Rationale:** the hand-rolled `line.split(':', 1)` parser choked on quoted values, inline comments, and the `kind` enum requirement from v0.3 ⑥. pyyaml handles all three, plus proper timezone-aware timestamp parsing.
**Rejected:** stdlib-only "just accept the limitations" — v0.3 ⑥'s enum validation cannot be implemented reliably without a real parser.

### R8 · CLI evidence transport: stdin / --content-file (was: --content arg only) (hand-off specific)
**Decision:** `write-atomic` accepts three payload sources in preference order: `--content-file <path>`, stdin (piped), `--content <inline>`. SKILL.md steers agents to `--content-file` for anything non-trivial.
**Rationale:** Windows git-bash caps shell argv at ~32 KB; the previous `--content "…"` API broke on real walkthrough sizes and required aggressive escaping of every quote/newline/`$` in the payload. File-based transport removes all escaping and lifts the size cap.

### R9 · Cross-platform file-reference detection (cross-cutting)
**Decision:** `check-reality`'s "missing file" check now matches Windows (`C:\…` / `C:/…`), POSIX (`/foo/bar`), and MSYS (`/c/foo`) path shapes; MSYS is normalized to Windows before `pathlib.Path.exists()`. Documentation-looking tokens (`/http…`, `/dev/…`, `/tmp/…`, URLs, tokens without a `.ext` filename tail) are filtered out to prevent false HARD conflicts. Content inside fenced code blocks is stripped before scanning.
**Rationale:** the earlier POSIX-only regex was silently a no-op on Windows and produced false positives on Linux (code examples treated as filesystem claims).

### R10 · Explicit lifecycle markers replace free-text grep (hand-off specific)
**Decision:** Smart Cleanup CLEAR/KEEP classification now looks for explicit HTML-comment markers (`<!-- keep -->`, `<!-- resolved -->`) plus a small keyword set in section headers (`lesson`, `surprise`, `decision`, `invariant`). The previous `"resolved" in body.lower()` heuristic is removed.
**Rationale:** free-text grep matched sentences like "not resolved yet" or "resolved before we…" and deleted live entries. HTML comments are unambiguous, invisible in rendered markdown, and machine-checkable.

### R11 · Two-phase Smart Cleanup (dry-run → apply) (hand-off specific)
**Decision:** `reconcile.py clean-up` requires a mutually-exclusive `--dry-run` or `--apply` flag. SKILL.md Step 3 mandates dry-run first, batched `clarify` on UNSURE items, then apply.
**Rationale:** the earlier one-shot mode landed CLEAR/STALE deletions to disk before the user saw the plan, defeating §9a's "err toward UNSURE" intent.

### R12 · SOFT conflict logging by script, not agent (take-over specific — mirrored here for cross-skill awareness)
**Decision:** `check-reality --apply-soft-conflicts` writes SOFT conflicts directly into `questions.md` under `## Soft Conflicts (Reconciled)`. `take-over` no longer needs to construct that section itself.
**Rationale:** consistent with v0.3 ① (script-assisted execution). Removes another surface where the agent could hallucinate the structure.

### R13 · Serializer double-newline fix (S3) (cross-cutting)
**Decision:** `dump_frontmatter` closes the fence with exactly one `\n` and `lstrip("\n")`s the body before concatenation. Previously each round-trip added a blank line at the body top.
**Rationale:** trivial correctness fix; a walkthrough re-serialized N times gained N blank lines under the old serializer.

### R14 · Auxiliary evidence: `<session-tools-log>` demoted (cross-cutting)
**Decision:** The `<session-tools-log>` block is documented and validated as **auxiliary evidence** only. Reality-check uses `git status --short` + `git log -5 --name-only` as the primary evidence source; tools-log entries lacking git presence surface as SOFT conflicts rather than being trusted or rejected on their own.
**Rationale:** the Hermes runtime does not currently expose a reliable structured tool-call history, so agent-constructed tools-log blocks are self-reported and cannot substitute for git evidence (v0.3 ③ was implicitly self-referential).

### R15 · `validate` command added (cross-cutting)
**Decision:** New `reconcile.py validate` subcommand runs frontmatter validation across all handoff docs (kind enum + timezone-aware timestamps + status enum + last_writer enum). `take-over` Step 1 calls it before loading any body content.
**Rationale:** enforces v0.3 ⑥ kind enum without waiting for the fuller `check-reality` pass.

### R16 · CLI does NOT pass `--isolated` to uv (documentation fix)
**Decision:** SKILL.md invocations use `uv run <path> …` (no `--isolated`).
**Rationale:** `uv run` is already isolated for scripts declaring inline `# /// script` metadata; passing `--isolated` produces a warning and no additional effect.


## Rev-C (v0.5-rev-C · 2026-07-17) — Flat file naming + kind-based scope + question archive

### R17 · Filename prefix `HANDOFF-` retired (cross-cutting)
**Decision:** Handoff docs use their natural short names — `context.md`, `task.md`, `walkthrough.md`, `questions.md`, `plan.md`, `review.md` — with no `HANDOFF-` prefix. The enclosing directory identifies the scope.
**Rationale:** User pushback ("为什么每个文件前面都要加一个 HANDOFF ？？？？？... 这几个文件在那个目录就是描述的哪个目录，自解释自包含"). Prefix added no information because the directory is the scope declaration.

### R18 · Kind-based scope discovery (cross-cutting)
**Decision:** A directory qualifies as a handoff scope only when it contains at least one candidate file (`context.md` / `task.md` / `walkthrough.md` / `questions.md` / `plan.md` / `review.md`) whose YAML frontmatter carries a recognised `kind` value. `_peek_kind()` reads the first 1 KB of each candidate for the classification.
**Rationale:** Once filename prefix disappeared, filename-only detection would false-positive on any project shipping a generic `context.md` or `task.md`. Kind detection is O(1) per candidate and unambiguous.

### R19 · `open-questions.md` → `questions.md` with `## Open` / `## Closed` sections (cross-cutting)
**Decision:** The questions doc has two subsections. `## Open` holds active entries; `## Closed` is a permanent archive of resolved entries. Frontmatter `kind` is `questions`.
**Rationale:** "Open questions" was descriptive but the doc was already accumulating implicitly-closed history in prose. Making Open/Closed explicit removes ambiguity and enables auto-archive.

### R20 · `<!-- resolved -->` archives questions, does not delete (hand-off specific)
**Decision:** On `clean-up --apply`, question entries under `## Open` bearing `<!-- resolved -->` are **moved** to `## Closed` (retaining full body), not removed. `apply_cleanup` reports the count as `archived_to_closed`. Walkthrough entries with the same marker continue to be deleted (their function is transient session memory, not history).
**Rationale:** User pick (option A of two): "永久保留，便于历史回顾". Questions carry decision history worth keeping.

### R21 · Scope defined by task range, not directory role (methodological)
**Decision:** Scope selection is neither "one per skill" nor "always repo root". The agent and user negotiate scope per task based on the task's actual range. `list-scopes` enumerates all live scopes neutrally; no scope is canonical.
**Rationale:** User pushback ("这一套方法是有明确范围的，取决于我们讨论的范围、处理任务的范围... 说白了，这个是一套方法，不是死板的程序"). Prior wording ("per-skill / repo root default") baked in policy the protocol shouldn't hold.
**SKILL.md v1.3.0 impact:** Bootstrap Step re-worded to describe scope choice as user-negotiable; example uses no longer imply default location.

### R22 · Rev-B dogfood bugs fixed under rev-C (cross-cutting)
**Decision:** Two bugs surfaced when v0.4 ate its own dogfood on this repo, fixed as part of rev-C:
- `write-atomic --content-file /tmp/…` on Windows git-bash now resolves MSYS paths via `resolve_msys_path` on both `--filepath` and `--content-file`.
- `<session-tools-log>` regex is line-anchored (`re.MULTILINE` + `^` / `$`), so prose mentions of the tag names in walkthrough entries no longer hijack the match.
**Rationale:** Both bugs blocked the rev-B dogfood test; the fix is straightforward once observed, and the smoke suite now regressions both.

### R23 · `_SECTION_RE` extended to `#{2,3}` (cross-cutting)
**Decision:** `split_sections` now matches h2 or h3 headers (`^(#{2,3}\s+.*)$`). Walkthrough classification still checks for date-header format (unchanged behaviour). Questions classification uses `hash_count` to distinguish `##` structural headers (Open/Closed) from `###` entry headers.
**Rationale:** The Open/Closed section design requires two-level headers in `questions.md` (`##` for section, `###` for entry). The old h2-only regex ignored entry-level headers entirely, disabling classification.
