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

---

## 2026-07-17 (rev-D) — Dead-code prune (hand-off specific)

Follow-up to a skill-creator optimization pass on `hand-off`. Three items removed because they had no working reader / no reachable trigger.

### R24 · `<session-tools-log>` block fully removed
**Decision:** Delete the `<session-tools-log>` markdown block from `templates/walkthrough.md`, remove all references from `SKILL.md` and `PROTOCOL.md` (§8 Step 1/2b, §9 anti-hallucination §1, §11 MVP reality-check), and drop `_TOOLS_LOG_RE` + its 40-line matcher block from `scripts/reconcile.py::_check_reality_scope`. `apply_soft_conflicts` still exists — only the tools-log producer was removed.
**Rationale:** Rev-B R14 (2026-07-17) already demoted the block to "auxiliary evidence only" because Hermes' runtime does not expose a reliable structured tool-call history — the agent has to hand-serialize it from memory, which is exactly the failure mode reality-check exists to catch. Keeping a self-reported "evidence" surface violated §9.1 ("No claims without evidence"). Primary evidence is now `git status --short` + `git log -5 --name-only`, full stop.
**Rejected:** keep the block as opt-in for runtimes that DO expose tool-call history — YAGNI; when such a runtime appears the feature can be reintroduced with a real reader.
**Take-over side note:** `take-over`'s copies of PROTOCOL/DECISIONS/scripts intentionally retain this feature; the two skills are on independent evolution tracks (see 2026-07-17 "Adopted 方案 A"). Cross-skill drift on this specific point is accepted.

### R25 · `context window > 75%` trigger removed
**Decision:** Delete the "context window exceeds 75%" line from `SKILL.md` description, `SKILL.md` When-to-Run list, `PROTOCOL.md` §8 trigger sentence, and `PROTOCOL.md` §13 open-questions list. Trigger set is now: explicit user invocation (`先到这` / `换你上` / `/handoff`) OR a major `todo` phase completes.
**Rationale:** Hermes does not expose current context-window usage to the agent. The trigger was aspirational — never actually fired. Advertising a trigger the agent can't detect wastes description tokens and misleads users about capability. §13 already flagged this ("Runtime-dependent; may not be portable") — R25 acts on that observation.

### R26 · "Choice Tool Fallback" preamble compressed to one line
**Decision:** Replace the 4-line 中文 "交互与工具回退机制" IMPORTANT block in `SKILL.md` with a single line: *"All user-facing prompts in this workflow use structured choices via `clarify` (Hermes' built-in `AskUserQuestion`). Do NOT free-text branching decisions."*
**Rationale:** The old preamble described a portability contract (fallback to numbered-list + yield-turn) for runtimes lacking `AskUserQuestion`. `hand-off` explicitly targets Hermes (see `Prerequisites`), where `clarify` is guaranteed. The verbose fallback rule was loaded into context on every trigger for a code path that never executes here. Rule §10a in `PROTOCOL.md` still documents the underlying policy for future portability discussions.
**Rejected:** delete the mention entirely — a one-liner is worth retaining so agents don't invent free-text branches by accident.

**Verification (2026-07-17):**
- `uv run scripts/reconcile.py --help` and `list-scopes` still succeed post-prune (imports clean, no dangling refs).
- `grep -rn "session-tools-log\|75%\|Choice Tool Fallback" *.md scripts/*.py templates/*.md` → 0 hits.

---

## 2026-07-17 (rev-E) — Composite `prepare` subcommand (hand-off specific)

### R27 · `prepare` = reality-check + cleanup dry-run in one subprocess
**Decision:** Add a new `reconcile.py prepare` subcommand that internally composes `_check_reality_scope()` + `classify_cleanup()` and returns a single JSON payload with `reality`, `cleanup_plan`, `next_action` ∈ {`halt_on_hard_conflicts`, `clarify_unsure`, `safe_to_apply`}, and an inline `[AGENT GUIDANCE]` string. `SKILL.md` Step 1 now invokes `prepare` instead of `check-reality`; Step 3 reads the plan from Step 1's output instead of re-running `clean-up --dry-run`. The original `check-reality` and `clean-up --dry-run` subcommands remain intact for advanced use.
**Rationale:** On Windows / git-bash each `uv run` costs ~300-500ms of cold start (uv boot + Python interpreter + pyyaml import). A full hand-off flow was spending 2-4 seconds on subprocess startup alone, most of which came from three separate read-only calls (`check-reality` + `clean-up --dry-run` + eventual `clean-up --apply`). Both phases are read-only and share scope resolution + lock semantics — composing them halves the preflight subprocess count and gives the agent one authoritative "what should I do next" decision point instead of two.
**Design constraint:** `prepare` must be **read-only** to `<scope>/` except for the already-agreed `--apply-soft-conflicts` behaviour (which mirrors `check-reality`). The actual cleanup mutation still happens through `clean-up --apply` in Step 3 — that separation is intentional so the agent can pause between the plan and the apply if `next_action == clarify_unsure`.
**Rejected alternatives:**
- Auto-apply cleanup when `next_action == safe_to_apply` inside `prepare` — merges read and write phases and loses the "user sees plan before apply" invariant.
- Deprecate `check-reality` and `clean-up --dry-run` — some workflows (validation-only dry-runs, CI checks) legitimately want just one phase; forcing them through `prepare` would ship irrelevant JSON keys.
- Cache `prepare` output to disk so Step 3 apply can consume it — YAGNI; the plan is regenerated cheaply from the same on-disk state, and stale caches would silently apply wrong plans.
**Verification (2026-07-17):**
- `uv run scripts/reconcile.py prepare --help` lists all flags (`--scope` / `--all-scopes` / `--apply-soft-conflicts` / `--session-id` / `--agent`).
- On a freshly `init`ed temp scope, `prepare` returns `status: ok`, `next_action: safe_to_apply`, and the correct `kept` classification for the template's sample entry.
- Exit code is `1` when any scope produces `halt_on_hard_conflicts` or `status: error`, matching `check-reality`'s exit semantics so callers can chain.

---

## 2026-07-17 (rev-F) — Multi-hop trust health (hand-off specific)

Addresses the "chinese-whispers" failure mode: when a scope has been through multiple hand-offs (session A → B → C → D), each agent inherits the previous agent's `context.md` verbatim. Hallucinations propagate freely because no one questions the source once a fact has been quoted twice. rev-F introduces three composable mechanisms (provenance / health / challenge) that let a later-hop `prepare` detect and interrupt the cascade without changing the semantics of a 1st-hop flow.

### R28 · Provenance tags on `context.md` invariants
**Decision:** Every `context.md` bullet must be prefixed with one of `[git:<short-sha>]` / `[user:<YYYY-MM-DD>]` / `[test:<test-name>]` / `[inferred:<session-id>]` / `[unknown]`. `_extract_provenance_lines()` in `reconcile.py` parses these tags; `_count_invariant_lines()` gives the denominator so `untagged_pct` can be computed. Untagged lines are counted as unattributed and count against health. The template at `templates/context.md` demonstrates the tag format inline.
**Rationale:** The core defect in multi-hop scopes is that hallucinated invariants and human-verified invariants are visually indistinguishable — a wall of unattributed bullet points. A structural tag lets `prepare` compute an inferred/untagged share and lets a downstream agent (or user) filter high-confidence from low-confidence claims. `[unknown]` explicitly captures "we don't know" as a legitimate state, which is better than silent untagged bullets that get indistinguishably counted as unattributed noise.
**Rejected alternatives:**
- Two-file split (`facts.md` + `inferences.md`) — clean but breaks the additive-only invariant of `context.md` and forces migration of existing scopes. Deferred to a hypothetical v0.6.
- YAML sidecar per invariant — heavy, illegible to humans reading the doc.
- Free-form provenance in prose (`"Auth uses JWT (per commit a3f2c9)"`) — not machine-parseable, cannot be scored across hops.

### R29 · `hop_count` from `docs(hand-off):` commits (empty-commit-safe)
**Decision:** `_count_hops()` runs `git log --pretty=format:'%H|%an|%s' -- .` in the scope directory and counts commits whose subject matches `docs\(hand[-]?off\)` (case-insensitive). Because `-- .` is used, git filters out empty commits — ceremonial `--allow-empty` commits do not inflate the hop count. Unique writers are collected from git authors PLUS every `last_writer` / `last_agent` field in the four core doc frontmatters.
**Rationale:** The user needs to know they're on hop N to calibrate scrutiny, but hop count must be robust — otherwise agents will game it by squashing or padding. Anchoring on real commits that touched the scope's files ensures the count reflects actual work. Combining git authors with frontmatter writers catches the case where multiple agents run under the same git identity.
**Rejected alternatives:**
- Count `walkthrough.md` dated headers — cleanup can prune those, so the count decays as history is cleaned. Git history is immutable and reliable.
- Read a `hop_count` field from frontmatter — self-reported, can be lied to, easy to forget to increment.

### R30 · `challenge_required` `next_action` branch + health verdict
**Decision:** `_analyze_multihop_health()` produces a verdict ∈ `{fresh, healthy, warning, unhealthy}` from four rules (hallucination-cascade / untraceable-source / stale / soft-conflict-debt). `_prepare_scope()` maps `unhealthy` to a new `next_action = "challenge_required"` branch. The agent contract for this branch: present top `inferred_samples` (up to 3) via ONE batched `clarify`, apply user choices (`still valid` → re-tag `[user:<today>]`, `stale` → delete, `rewrite` → user-supplied replacement), re-run `prepare` to verify health improved, THEN proceed to Step 2 / Step 3. `challenge_required` takes priority over `clarify_unsure` because forcing UNSURE cleanup on a hallucination-cascading scope compounds the problem. `halt_on_hard_conflicts` still takes top priority because those conflicts leave the docs in an inconsistent state.
**Rationale:** Threshold values (`hop_count ≥ 3` gate + 40% inferred + 50% untagged) are calibrated so hop-1 clean scopes stay `fresh`, hop-2 accumulating scopes stay `healthy`, and only genuinely-degraded multi-hop scopes trigger challenge. This preserves the "zero friction on first hand-off" property while giving the mechanism teeth on the 4th, 5th, Nth hand-off. Two-issue threshold for `unhealthy` (versus one for `warning`) means a single accidentally-crossed threshold produces a soft warning noted in `guidance`, not a full challenge — challenge is reserved for genuinely bad trust states.
**Priority ordering (top-down):** `halt_on_hard_conflicts` (docs inconsistent) > `challenge_required` (docs unhealthy) > `clarify_unsure` (cleanup ambiguity) > `safe_to_apply` (green path). Each is strictly more permissive than the previous.
**Rejected alternatives:**
- Auto-execute challenge without user in the loop (agent decides which invariants are stale) — defeats the purpose. The whole point is to break the trust chain by re-anchoring to the user's ground truth.
- Trigger `challenge_required` for any hop ≥ 3 regardless of provenance stats — noisy on well-tagged scopes; users would learn to ignore it.
- Cache challenge decisions to disk so hop 5 doesn't re-ask what was answered on hop 4 — YAGNI now; if it becomes a real annoyance we add a "last challenged at <hash>" frontmatter later.

**Take-over side note:** The multi-hop health analysis is intentionally hand-off-only for now. `take-over` sees the results indirectly by reading `context.md` at resume time, which naturally exposes the provenance tags. If a symmetric surface is needed on take-over (e.g., "warn the resumer that they're taking over an unhealthy scope"), that's a separate rev.

**Verification (2026-07-17):**
- 1-hop clean scope: `health: healthy`, `next_action: safe_to_apply`, no issues.
- 4-hop scope with 40% `[inferred:*]` + 50% untagged: `health: unhealthy`, `issues: [hallucination-cascade, untraceable-source]`, `next_action: challenge_required`, guidance includes 3 concrete `inferred_samples` for user challenge.
- 4-hop scope with 44% inferred but only 44% untagged (one under threshold): `health: warning`, single-issue, still `safe_to_apply` — verifies threshold discipline.
- Priority ordering: HARD conflicts still bypass health check as designed.

---

## 2026-07-17 (rev-G) — SKILL.md structural slimming

Motivated by P2: SKILL.md had grown to 221 lines as rev-D through rev-F added reality-check semantics, `prepare` composite branching, and rev-F provenance / health / challenge rules. Every trigger of the skill re-injected the whole thing into the agent's context, and the agent doesn't need the detailed spec of `write-atomic` input patterns or per-branch contracts until it actually reaches that step. rev-G applies progressive disclosure: SKILL.md keeps only the trigger conditions + workflow skeleton; the details move to `references/` and are loaded on demand.

### R31 · Progressive disclosure via `references/`
**Decision:** SKILL.md is trimmed to a 138-line skeleton covering prerequisites, when-to-run, layout summary, and the 5-step workflow at the "one paragraph per step" level. Four new files under `references/` carry the details:

- `references/scope-resolution.md` — `list-scopes`, `--scope` priority, bootstrap decision matrix, batch operations.
- `references/atomic-writes.md` — `write-atomic` input patterns (`--content` / `--content-file` / stdin), frontmatter preservation rule.
- `references/document-conventions.md` — per-doc writing conventions including the rev-F provenance-tag spec (with anti-patterns).
- `references/next-actions.md` — full contract per `next_action` branch, health rule table.

Each step in SKILL.md's workflow references the applicable file(s) so the agent knows what to load when it needs the details. `PROTOCOL.md` and `DECISIONS.md` remain untouched — they were already reference-tier from day one.

**Rationale:** The old SKILL.md conflated two audiences: agents that need to know "does hand-off apply here, and what's the shape of the workflow" (short-scan use) versus agents that are in the middle of Step 2 and need to know exactly how `write-atomic` handles a large payload (deep-dive use). The 221-line document served both audiences by re-injecting deep-dive content into every skill load. Progressive disclosure serves each audience separately: SKILL.md is quick to scan and cheap to inject, references load on demand.

**Verification (2026-07-17):**
- `wc -l SKILL.md` → 138 lines (target <150). ✅
- All four `references/*.md` files exist and are referenced from SKILL.md by relative path.
- The five canonical commands (`list-scopes`, `init`, `prepare`, `write-atomic`, `clean-up --apply`) all remain visible in SKILL.md so an agent skimming for command shapes without loading references still gets the executable outline.
- `uv run scripts/reconcile.py --help` still lists all subcommands (`{init, validate, check-reality, clean-up, write-atomic, list-scopes, unlock, prepare}`) unchanged.

**Rejected alternatives:**
- Move the entire workflow to `references/` and leave only trigger conditions in SKILL.md — too aggressive; the agent then needs a reference load even to know "which command is Step 1". Workflow skeleton belongs in SKILL.md.
- Split SKILL.md by revision (`SKILL-rev-E.md`, `SKILL-rev-F.md`) — the file is not a changelog; that's what `DECISIONS.md` is for.
- Fold `PROTOCOL.md` into `references/` — the protocol document is deliberately at the skill root because it describes the whole hand-off / take-over contract, not just this skill's UI. Moving it would obscure that.

