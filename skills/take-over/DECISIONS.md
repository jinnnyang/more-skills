# Design Decisions — `take-over` skill

> Append-only log. Never rewrite past entries; add a new dated entry that supersedes if needed.
> Each entry records: date, decision id, decision, rationale, alternatives rejected.
> **Scope:** decisions relevant to the `take-over` half of the session handoff protocol. The companion skill `hand-off` maintains its own `DECISIONS.md`. Cross-cutting decisions appear in both.

---

## Meta · Why this skill maintains an ADR log

`DECISIONS.md` is an **Architecture Decision Record (ADR) log** — the same discipline used in long-lived open-source projects (Kubernetes, Rust, Apache) transplanted to a single skill. See `references/adr-and-decisions.md` for the full principles + practices reference.

### Version conventions (three axes)

This skill lives at the intersection of three independent version stories. All three appear in the repo; don't conflate them:

| Axis | Where it lives | What it counts | Current value |
|---|---|---|---|
| **Skill package semver** | `SKILL.md` frontmatter `version:` | User-visible changes to this skill's CLI/UX/behaviour. Bumps on any user-observable change. | `1.4.0` (may bump to `1.4.1` on close-out of the 2026-07-20 review-cycle) |
| **Protocol revision** | `PROTOCOL.md` top header | The shared handoff protocol between `take-over` and `hand-off`. Bumps when the wire format, doc set, or flow shape changes. | `v0.5 (rev-C, 2026-07-17)` |
| **Decision-batch date headers** | `DECISIONS.md` `## <date> — <title>` sections | Chronological group of ADRs that landed together. Reference by date, not by count. | `2026-07-20 — Review-cycle changes (v1.4.1)` |

Rules of thumb:
- A change that only rewords SKILL.md text is a skill-semver patch bump; protocol version untouched.
- A change to the frontmatter fields or the doc set (`context.md` / `task.md` / …) is a protocol version bump *and* a skill-semver bump.
- Cross-cutting decisions (both `take-over` and `hand-off`) get `(cross-cutting)` scope tag and must appear in both skills' DECISIONS.md with identical text.

Three reasons this particular skill needs an ADR log more than most:

1. **The design surface is subtle and easy to re-litigate.** Every field in the frontmatter, every step in the take-over flow, every conflict tier was chosen against 2–4 alternatives with real trade-offs. Without a written record, the next author (human or agent) will inevitably propose "why not just ..." for options that were already rejected months ago, wasting context on rediscovery.

2. **The two peer skills (`take-over` / `hand-off`) share protocol semantics but not files** (see 2026-07-17 · self-contained decision). Drift between them is a real risk. The DECISIONS log is the primary artifact that prevents silent divergence — a decision tagged *(cross-cutting)* must land in both skills' logs verbatim.

3. **Agents editing agents amplify hallucination risk.** An LLM asked to "modify take-over" without seeing prior rationale will confidently rewrite invariants that were carefully chosen. Making rejected alternatives explicit is cheap immunization: the agent sees "we tried X, here's why it broke" before it re-proposes X.

### Editing rules (enforced by convention, not tooling)

- **Never rewrite a past entry.** Corrections/supersessions add a new dated entry that names the entry it replaces (`Supersedes: 2026-07-16 ①`).
- **Cross-cutting decisions must appear in both skills' logs** with identical `Decision` / `Rationale` text (Rejected alternatives may vary if one side has extra concerns).
- **Every entry must include Rejected Alternatives** — a decision without alternatives is a description, not a decision. If genuinely no alternatives were considered, say so explicitly (rare, and a signal to think harder).
- **Consult before changing anything referenced by an entry's decision id.** Section titles like "④ Take-over conflict handling" carry stable ids exactly so `SKILL.md` and `PROTOCOL.md` can reference them.
- **When in doubt whether a change deserves an entry**: if a reviewer would ask "why is it this way instead of the obvious alternative?", write the entry.

See `references/adr-and-decisions.md` for the full playbook — when to write an entry, entry anatomy, common failure modes, and worked examples from this skill's own history.

---

## 2026-07-16 — Initial Design Decisions

### ① Document format (cross-cutting)
**Decision:** YAML frontmatter + Markdown body for all handoff documents.
**Rationale:** Enables cheap L1 pre-scan by take-over — only frontmatter needs parsing to decide whether to load full body. Aligns with SKILL.md format. Robust against agent-authored format drift (`---` fences are a hard boundary).
**Rejected:** Plain Markdown with convention'd `**Status:**` lines — too fragile against whitespace/case drift.

### ④ Take-over conflict handling (take-over specific)
**Decision:** Tiered per §9b of PROTOCOL.md.
- **HARD** (doc claims contradicted by code/git, cross-doc contradictions, invariant violations) → HALT via `clarify`.
- **SOFT** (stale `last_verified`, renamed files, pruned session_id) → log to `questions.md` with `⚠️ stale` under `## Soft Conflicts (Reconciled)` section, continue.
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

### R3 · `questions.md` vs `task.md` boundary (§4.1) (cross-cutting)
**Decision:** `questions.md` is exclusively for items requiring a **human** answer. Agent-side blockers (waiting on API, build, tool availability) stay in `task.md` with a `[!]` marker.
**Rationale:** the two were previously ambiguous. take-over's SOFT-conflict logging must land in the correct file — human questions and stale reconciliations go into `questions.md`; automated retry blockers go into `task.md`.

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
**Decision:** All writes to `<scope>/` and `docs/handoff/` must be atomic: write to a `.tmp` file and rename (POSIX `rename()`) to overwrite the target. take-over writes to `<scope>/` only when logging SOFT conflicts or initializing empty files.
**Rationale:** Prevents torn writes/corrupted files if the agent is interrupted or crashes midway through take-over.

### ④ Cold-Start (Bootstrap) and Empty State Handling (cross-cutting)
**Decision:** If `<scope>/` does not exist during `take-over`, it is automatically initialized. `take-over` will report: "No previous handoff history found. Initialized empty session." and populate default files from this skill's `templates/` directory.
**Rationale:** Resolves the first-time-use (FTU) user experience gap.

### ⑤ Pre-empt Plan-Mode Merge Check (take-over specific)
**Decision:** Position the `plan-mode` coexistence check (§7 Step 6) *before* the final report to the user in `take-over` (§7 Step 7).
**Rationale:** If `plan-mode` files are imported, the report must reflect the imported tasks; otherwise, the summary shown to the user becomes immediately stale.

### ⑥ Unified Frontmatter Kind Enum & Context Append-Only (cross-cutting)
**Decision:** Frontmatter `kind` is strictly restricted to the enum values: `context`, `task`, `walkthrough`, `questions`, `plan`, `review`. `context.md` is strictly additive; take-over must not rewrite past entries.
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
**Impact on take-over:** questions.md sections created by `take-over` (SOFT conflicts) will be preserved automatically because the `## Soft Conflicts (Reconciled)` heading is exempted from cleanup and its entries are dated but not marked resolved.

### R11 · Two-phase Smart Cleanup (dry-run → apply) (hand-off specific, mirrored for awareness)
**Decision:** `clean-up` requires `--dry-run` or `--apply`; dry-run first, then apply after user confirmation.
**Rationale:** consistent with §9a "err toward UNSURE"; the previous one-shot mode landed deletions before the user saw the plan.

### R12 · SOFT conflict logging by script, not agent (take-over specific)
**Decision:** `check-reality --apply-soft-conflicts` writes SOFT conflicts directly into `questions.md` under `## Soft Conflicts (Reconciled)` with UTC timestamp and `⚠️` marker. `take-over` Step 2 uses this flag; Step 5 no longer constructs the section itself.
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

### R17b · Step ordering: re-restore todo after plan-mode import (take-over specific)

> **Renumbered from `R17` to `R17b` on 2026-07-20** — the original `R17` id collided with the rev-C entry below (also numbered `R17`, describing filename-prefix retirement). Kept both entries; distinguished by suffix. All prior references to "R17" in this file that meant "step-ordering fix" now read as "R17b" (only one call site, in this entry's own body).

**Decision:** SKILL.md Step 4 (Restore Checklist) is re-run at the end of Step 6 (Plan-Mode Coexistence) if the user chose "Import plan.md". The final Step 7 summary reflects the reconciled task list.
**Rationale:** DECISIONS 2026-07-16 v0.3 ⑤ ("Pre-empt Plan-Mode Merge Check") intended the report to be up-to-date, but Step 4's original position (before Step 6) meant an imported plan.md's tasks never made it into `todo`.


## Rev-C (v0.5-rev-C · 2026-07-17) — Flat file naming + kind-based scope + question archive

### R17a · Filename prefix `HANDOFF-` retired (cross-cutting)

> Numbered `R17` in the original 2026-07-17 rev-C batch; retitled to `R17a` on 2026-07-20 to disambiguate from the older `R17b` above (step-ordering fix from the 2026-07-17 rev-B batch). The two entries were authored on the same day by different revisions and both landed under `R17` before the collision was noticed.

**Decision (mirrored from hand-off/DECISIONS.md R17):** Handoff docs use natural short names; no `HANDOFF-` prefix. The enclosing directory identifies the scope.
**Take-over impact:** Step 3 layered load references `context.md` / `task.md` / `questions.md` (was `HANDOFF-*.md`). No behavioural change; only naming.

### R18 · Kind-based scope discovery (cross-cutting)
**Decision (mirrored):** Scope detection reads YAML `kind` frontmatter from the six candidate filenames.
**Take-over impact:** Step 0 `list-scopes` output is now scope-safe against arbitrary `context.md`/`task.md` files that lack handoff frontmatter — take-over won't propose bogus resume targets.

### R19 · `questions.md` with `## Open` / `## Closed` sections
**Decision (mirrored):** Frontmatter `kind: questions`. Doc structured as `## Open` + `## Closed`. `apply_soft_conflicts` now writes SOFT conflicts as `### Soft conflict · <type> · <timestamp>` entries under `## Open`.
**Take-over impact:** Step 5 SOFT conflict flow unchanged in spirit; entries are now individually resolvable via `<!-- resolved -->` (which the next `hand-off` will archive, not delete).

### R20 · Resolved questions archive to `## Closed` (hand-off specific, take-over aware)
**Decision (mirrored):** On next `hand-off clean-up`, `<!-- resolved -->` questions move to `## Closed`, preserving history.
**Take-over impact:** L1 load reads `questions.md` including the Closed section, so take-over sees historical decisions when resuming.

### R21 · Scope defined by task range, not directory role (methodological)
**Decision (mirrored):** No canonical scope location. Agent + user negotiate per task via `list-scopes` and `clarify`.
**Take-over impact:** Step 0 was rewritten to describe scope discovery + user-selection explicitly. Prior wording implied a fixed `.hermes/handoff/` location.

### R22 · Rev-B dogfood bugs fixed (cross-cutting)
**Decision (mirrored):** MSYS `/tmp/...` path resolution + line-anchored `<session-tools-log>` regex.
**Take-over impact:** `check-reality` no longer false-positives SOFT conflicts on walkthroughs that mention `<session-tools-log>` in prose (bug caught by rev-B dogfood).

### R23 · `_SECTION_RE` extended to `#{2,3}` (cross-cutting)
**Decision (mirrored):** Section splitting now covers h2 + h3 so questions' `### <ID> · <title>` entries are classifiable.
**Take-over impact:** none direct — take-over does not classify; only load. `apply_soft_conflicts` gains ability to append `### Soft conflict …` entries cleanly under `## Open`.

---

## 2026-07-20 — Acceptance Review + FTU polish (v1.4.0)

Driven by the first real dogfood run of take-over (see the `REVIEW-2026-07-20-dogfood.md` report — originally filed as `调用记录-20260720.md`, renamed 2026-07-20 R34). All decisions land in this single revision because they share the same entry point (SKILL.md's Step 0 / bootstrap) and reworking them separately would churn the same passage repeatedly.

### R24 · Handoff Acceptance Review (take-over specific — new Step 1.5)
**Decision:** New `reconcile.py review-handoff` subcommand + new SKILL.md Step 1.5. Before Step 2 (reality check), take-over verifies the previous session's docs are actually *usable*:
- template-token residue (`{{TIMESTAMP}}` etc.)
- `context.md § Project Description` non-placeholder
- `task.md` has at least one non-template checklist item
- cross-references (`plan.md` / `review.md`) resolve
- `context.md` path-looking tokens exist under scope or repo root (WARN)
- all-migration writers → REJECT (unless `--allow-fresh`)

Verdict is `pass | reject | fresh_init`. `reject` blocks Step 2 and offers three options via §0a: **Reject** (exit, bounce back to previous session), **Remediate** (take-over fixes issues in place, up to 3 passes), **Force continue** (log overrides to `questions.md § Open`).

**Rationale:** the previous flow blindly accepted whatever hand-off left behind. If hand-off produced empty or self-contradictory docs, take-over would burn context on nothing and the user would only notice after the summary. The review is a pure static check (no test execution) so its cost is bounded.

**Severity calibration:** slightly-stricter-than-conservative — empty descriptions and empty task lists are REJECT (not WARN) because they defeat the entire purpose of hand-off; description-code path mismatches are WARN (not REJECT) because absolute or illustrative paths produce too many false positives in practice.

**Remediation scope allowed:** take-over may write to `context.md § Project Description` (originally template stub, therefore not violating additive-only) and `task.md § Now`. It must not rewrite `walkthrough.md`, must not touch `## Closed` in `questions.md`, and must not silently invent content for `plan.md` / `review.md` cross-references (those escalate back to the user).

**Rejected alternatives:**
- Only warn, never reject — leaves the "empty seed passed off as real handoff" bug unfixable.
- Reject-only (no remediation branch) — forces every low-signal fix into a full hand-off round trip; too heavy for FTU.
- Merge with existing `validate` — different concern (validate = frontmatter syntax; review-handoff = body semantics + cross-doc integrity). Keeping them separate makes CLI failure modes legible.

### R25 · Initial Context Seeding (take-over specific — new Step 0.5)
**Decision:** After `init` on the empty-scope branch, take-over MUST seed `context.md § Project Description` and `task.md § Now` from the user's triggering message before greeting. Runs `review-handoff --allow-fresh` afterward to confirm the seed passes acceptance review.

**Rationale:** previously, `init` produced 4 skeleton files and greeted the user, leaving the actual context for the *next* hand-off to write. In practice the very first user message contains everything needed — Project Description + first task — and skipping the seed means the first hand-off has no material to hand off. New agents on the receiving end then had nothing to take over.

**Rejected:** relying on the agent's own judgement to seed after greeting — this depends on how proactive the specific agent is. Making it a documented step levels the floor.

### R26 · Yield-Turn Fallback Protocol (§0a) formalised (cross-cutting behavioural spec)
**Decision:** The "no `clarify` tool → numbered-list yield" fallback is now a top-level §0a section with 5 explicit rules: preamble ≤ 3 lines, no tokens after the list, legal numeric reply is authoritative (no re-confirm), illegal reply loops, and the "no tool" state must be confirmed by search rather than guessed.

**Rationale:** the previous single-paragraph `[!IMPORTANT]` block left three concrete ambiguities (see `REVIEW-2026-07-20-dogfood.md` § "clarify 回退协议"). Different agents behaved inconsistently — some re-confirmed after a numeric reply, some kept generating explanations after the list.

**Rejected:** leaving the rules per-branch inline — same 5 rules repeat at 5+ branch points, duplication is worse than a single hoisted section.

### R27 · Explicit "when to run take-over" trigger list
**Decision:** SKILL.md now names the three triggering conditions explicitly: skill-invocation marker, Chinese/English resume keywords, or auto-load + non-empty scope discovered. Absence of all three → silent exit in Step 0.

**Rationale:** the previous "if the user's initial prompt was a normal, unrelated instruction, exit silently" left the judgement to the agent's intuition. Different runtimes (some invoke take-over via hook, some via user typing) produced different behaviours.

**Rejected:** universal auto-run — too invasive; universal opt-in — misses the hook use case.

### R28 · Case-B branch simplification (empty vs non-empty pwd)
**Decision:** When `list-scopes` returns zero:
- pwd fully empty → the original three-way prompt.
- pwd non-empty but no handoff docs (the FTU case) → simplified two-way prompt with option 1 recommended.
- No resume signal at all → silent exit (see R27).

**Rationale:** the FTU case — user just made a directory, copied some files in, and asked to start — accounted for a disproportionate share of "wait, why is take-over asking me a three-way question when the answer is obvious" complaints. Detecting a working directory (non-empty) is a cheap heuristic that removes one unneeded question.

**Rejected:** auto-init in the FTU case — still needs one confirmation because the wrong scope is a permanent cost.

### R29 · Windows / MSYS path convention documented
**Decision:** SKILL.md Prerequisites gains a "Path convention on Windows / MSYS" subsection stating that `uv run <path>` requires a native `C:\...` path, not `/c/...`. The script itself internally accepts both via `resolve_msys_path`, but the path handed to `uv run` bypasses that translation.

**Rationale:** the hand-off skill hit this bug immediately after v0.5 rollout on Windows (see `REVIEW-2026-07-20-dogfood.md` § "Windows 路径 shell 语法陷阱"). Documenting once at the top costs less than agents re-deriving the fix per session.

### R30 · Frontmatter enum knowledge propagation
**Decision:** New file `references/frontmatter-fields.md` documents `kind` / `status` / `last_writer` enums + timestamp format. Templates now include a top-of-file `<!-- Frontmatter enums ... -->` comment listing valid values. SKILL.md init-branch greeting explicitly names the `status` enum.

**Rationale:** the enum values (particularly `status`: `in-progress|blocked|phase-complete|archived`, notably NOT `complete`) were previously only visible inside `reconcile.py`'s constants. Agents editing frontmatter would guess reasonable values (`complete`, `done`, `in_progress` underscore-style) and hit validation errors on next take-over. Publishing the enum in three places (reference doc, template comment, greeting) creates redundancy where the cost of a wrong guess is high.

### R31 · Cross-skill visibility: greeting names hand-off
**Decision:** Step 0.5 greeting and Step 7 summary both end with a line naming the companion `hand-off` skill and its trigger phrases (`先到这` / `handoff` / `continue later`).

**Rationale:** take-over and hand-off are peer skills that don't currently reveal each other's existence. Users who used take-over once had no signal that hand-off was the way to save progress next time. This is not a runtime coupling — it's UX-level cross-linking, one line of text.

**Rejected:** auto-installing hand-off — too invasive, and each skill remains independently installable per the 2026-07-17 self-contained decision.

---

## 2026-07-20 — Review-cycle changes (v1.4.1)

Follow-up landing from `REVIEW-2026-07-20.md`. All items in this section are UX/legibility polish, not protocol changes. No `SKILL.md` frontmatter version bump (still 1.4.0 for now; may bump to 1.4.1 at close-out).

### R32 · SKILL.md first-screen humanize + 90-second mental model (take-over specific)
**Decision:** Rewrote the SKILL.md `description:` frontmatter (previously AI product copy: "Guides the agent through a structured session resume/take-over workflow…") into a plain-voice one-liner. Added a **90-second mental model** section right after the H1, before Overview: one-liner opener, three-action flow (Discover → Verify → Restore + summarise), explicit "skip ahead if you know the model" pointer. Also lightly humanized §0a's opening paragraph and Step 1.5's `pass/fresh_init/reject` bullets, and unified `<>` vs `{}` placeholder brackets in Step 0 / Step 2 / Step 7 code fences.

**Rationale:** `skills_list()` shows the `description` string before the agent decides whether to load the skill, so its tone lands earlier than SKILL.md L1. The old description was 3 sentences of institutional voice — same failure mode caught in `hand-off` on the same day (commit `590a61c`). The 90-second block gives the agent a mental model before it has to wade through Prerequisites + Windows path notes + When-to-Run + Layout + Scope Resolution + §0a. `skill-review-cycle`'s `references/prose-voice.md` explicitly calls the frontmatter description out as a P0 signal.

**Rejected:**
- Rewrite SKILL.md body wholesale — the 7-step workflow is genuinely 7 steps; brute-shortening loses branch logic.
- Move Prerequisites below the mental model — planned but demoted to `[-]` because the mental model already tells impatient readers to skip ahead, and physically reordering the sections churns diff for marginal benefit.
- Leave the description untouched, only add the mental model — misses the `skills_list()` first-impression fix.

**Impact:** First-load ergonomics parity with `hand-off` post-humanize. No behavioural change; workflow steps unchanged.

### R33 · DECISIONS.md R17 collision + version-label reconciliation (bookkeeping)
**Decision:** Renumbered the duplicate `R17` ids in `DECISIONS.md`:
- Old `R17` at line 191 (2026-07-17 rev-B, "Step ordering: re-restore todo after plan-mode import") → **`R17b`**.
- Old `R17` at line 198 (2026-07-17 rev-C, "Filename prefix HANDOFF- retired") → **`R17a`**.

Suffix (`a` / `b`) preserves chronological order — the rev-C entry landed later but describes a naming rule, while rev-B's entry describes a step-ordering fix. Both entries carry a short "renumbered on 2026-07-20" note explaining the rename.

Additionally added a **§Version conventions** table to `DECISIONS.md` Meta section, documenting the three independent version axes: skill semver (`SKILL.md` frontmatter, `1.4.0`), protocol rev (`PROTOCOL.md` top header, `v0.5 rev-C`), and decision-batch date headers. Bumped `PROTOCOL.md`'s Status line from `v0.3 (2026-07-17 rev-A)` to `v0.5 (2026-07-17 rev-C)` to match the current protocol shape (flat-file layout + kind-based scope + question archive).

**Rationale:** Duplicate ADR ids are the exact anti-pattern called out by `references/adr-and-decisions.md` §6.2. The old `R17` id was silently ambiguous — anything citing "R17" in SKILL.md/PROTOCOL.md/commit messages had no unique referent. Version labels had drifted three ways (`1.4.0` in SKILL.md, `v0.3` in PROTOCOL.md, `v0.5` inside SKILL.md § Overview) making it impossible to answer "what protocol version does this skill implement?" at a glance.

**Rejected:**
- Renumber both R17 entries as `R32`/`R33` — breaks chronological order in the file and forces every "R17" reference to be tracked and rewritten. Suffix-disambiguation is cheaper.
- Delete one of the two R17 entries — they document different decisions; both are still valid.
- Drop the `PROTOCOL.md` version header entirely — the header is useful when comparing take-over vs hand-off drift; keep it, just make it accurate.
- Auto-derive the protocol version from git tags — no tags yet, and this repo is a skill collection not a release train.

**Impact:** Any future ADR cross-references become unambiguous. `SKILL.md § Overview`'s "(v0.5, flat-file layout)" phrasing now agrees with `PROTOCOL.md` top header. Skill semver stays at `1.4.0`; may bump to `1.4.1` at review-cycle close-out per the new §Version conventions rule.

### R34 · Preserve dogfood report as `REVIEW-2026-07-20-dogfood.md` (bookkeeping)
**Decision:** The 108-line Chinese dogfood report that motivated the R24–R31 batch (originally landed as `调用记录-20260720.md`, untracked) was renamed to `REVIEW-2026-07-20-dogfood.md` and committed. Added a short English header explaining its role and relationship to the sibling `REVIEW-2026-07-20.md` (later `skill-review-cycle` pass). Chinese body preserved verbatim; not translated. All three call sites in `DECISIONS.md` R24-header / R26 / R29 updated to point at the new filename.

**Rationale:** The dogfood report is the only artifact tying R24–R31 to concrete user-observed pain (Windows path bug, clarify-fallback ambiguities, empty seed on init). Left untracked, one `git clean` erases the receipts and the R24–R31 rationale becomes ungrounded. `references/adr-and-decisions.md` §6.5 explicitly warns against ADRs whose evidence lives outside the repo.

**Rejected:**
- Extract findings into `references/dogfood-lessons.md` short-form and delete the original — loses the primary source; the distilled version would just be prose rewriting of R24–R31 which the ADRs already carry.
- Delete outright — same problem plus permanently loses the specific numeric/example callouts (e.g. the "list-scopes → JSON output structure" observation) that the ADRs cite abstractly.
- Translate to English — the original captures the reporter's voice (刘工) and technical vocabulary; translation risks distortion for zero benefit.

**Impact:** No behavioural change. Future reviewers can trace R24–R31 back to the first-hand observation. Filename now sorts next to `REVIEW-2026-07-20.md` in `ls`, making the two-report structure discoverable.

### Review-cycle close-out (2026-07-20)

The 2026-07-20 `skill-review-cycle` pass covered SKILL.md first-screen ergonomics, ADR-id collision fixes, and version-label reconciliation. Three commits landed on branch `more`:

- **`4d60311`** — R32 · SKILL.md first-screen humanize + 90-second mental model
- **`e89918c`** — R33 · DECISIONS.md R17 collision + version-label reconciliation
- **`186d7c5`** — R34 · Landed dogfood report as `REVIEW-2026-07-20-dogfood.md`

Deferred to a future review by explicit user decision (Step 6 checkpoint): P1c residual (~15 min of §0a interior lines), P2 (reconcile.py tests + file split), P3 (references list ordering + PROTOCOL §13 stale open question). See `REVIEW-2026-07-20.md § Review-cycle summary` for the full backlog.

Skill semver stays at **1.4.0** — no user-observable behaviour changed, only prose and bookkeeping. Bump to 1.4.1 is not required per the §Version conventions rules.

---

## 2026-07-20 (rev-C) — Lock lifecycle contract: `check-reality` is read-only by default

### R35 · `--acquire-lock` flag on `check-reality` (take-over specific; hand-off mirrored)

**Supersedes:** the implicit contract in R7 / earlier lock code that `_check_reality_scope` acquires `.handoff.lock` whenever `--session-id` is present. No prior ADR names this behaviour explicitly, but the reconcile.py branch at lines 754-757 encoded it since lock introduction. This ADR retires that branch shape.

**Decision:** `reconcile.py check-reality` now takes an optional `--acquire-lock` flag. Semantics:

- **Flag absent (default)** → strictly read-only. `check_lock_conflict` is called; `.handoff.lock` is never written, regardless of whether `--session-id` was supplied. Existing locks are still detected and surface as HARD `concurrency_lock_conflict`.
- **Flag present** → old behaviour. `acquire_lock` is called; a `.handoff.lock` matching the session-id is written iff no conflicting lock exists.

Corresponding SKILL.md change: Step 2 · Reality Check gets an `IMPORTANT` callout instructing take-over **never** to pass `--acquire-lock`. hand-off's `prepare` (which composes check-reality + cleanup planning) is the intended caller of the opt-in path.

Companion regression tests land at `skills/take-over/scripts/tests/test_lock_lifecycle.py` (7 cases: default-no-write, opt-in-writes, existing-lock-still-detected, same-session-reacquire-noop, CLI parser exposes flag, CLI default-no-write end-to-end, CLI opt-in-writes end-to-end).

**Rationale:** The 2026-07-20 make-soul session hit HARD `concurrency_lock_conflict` on hand-off because the take-over that opened the same shell session had silently acquired a lock during its Step 2 · Reality Check (`--session-id` present → implicit `acquire_lock`) and never released it. `release_lock` is only invoked from `cmd_clean_up`, which is a hand-off-only command; take-over has no code path that releases what it took. The lock leaked until the 7200s TTL expired, ambushing hand-off ~74 minutes later.

The root failure is a naming/lifecycle contract mismatch: `_check_reality_scope`'s name promises a read; its body performed a write conditional on an argument (`--session-id`) that every take-over call always supplies. Options considered were the three ranked in `walkthrough.md § 2026-07-20 § Fix landscape`:

- **A · Doc-only fix** — add an `unlock` step at end of take-over Step 7. Rejected: fragile against mid-flow abort; leaves the surprising branch shape in code where the next reader will re-trip it.
- **B · Read-only preflight flag** — this decision. Cost: ~1 hour (code + tests + ADR + doc). Fixes the class, not the instance.
- **C · Context-manager lock** — `with acquired_lock(...)` scoped around callers. Rejected: `check-reality`'s natural shape doesn't want to acquire at all, so wrapping the acquire in a scope doesn't fit the caller.

Answering Q2 (opt-in vs opt-out default) from `questions.md`: **opt-in default** was chosen. No known external callers rely on the old implicit-acquire, the "safe by default" convention argues for reads to be reads, and the flag name makes caller intent explicit. Q1 (parity with hand-off) is answered in a paired R36 landing note below. Q3 (read-side TTL) is left at status quo — read-only checks continue to honour the 7200s TTL, because the failure mode is the acquire, not the check.

**Rejected:**
- Rename `_check_reality_scope` to `_check_or_acquire_reality_scope` — a naming clarity fix without a semantic fix would still leave every take-over caller silently acquiring. The flag is load-bearing.
- Default the flag to `True` for backward compatibility — perpetuates the exact surprising default that caused the bug and forces every read-only caller to remember `--no-acquire-lock`. Rust/Python "safe by default" wins.
- Make take-over release its own lock at end of Step 7 (option A) as well as landing the flag — belt-and-braces sounds good but if the flag is enforced by SKILL.md guidance, the belt is enough; adding a redundant release path adds a new class of bug (release-during-abort races).
- Extend `check_lock_conflict` to also honour a "self-lock-is-ok" fast path so take-over's lock wouldn't conflict with its own later reads — misidentifies the problem. The problem is the *existence* of the lock past take-over's exit, not the conflict semantics.

**Impact:** Behaviour change is user-visible for anyone driving `reconcile.py check-reality --session-id …` outside the two skills. In-repo callers are (a) take-over's SKILL.md Step 2 — now safe as-is, (b) hand-off's `_prepare_scope` — see R36 for parity work. External callers (if any) that relied on the side-effect must add `--acquire-lock`. Skill semver bumps 1.4.0 → **1.5.0** (contract change on a public helper command).

### R36 · Parity with hand-off's `reconcile.py`

**Decision:** Answering `questions.md` Q1 — the two `reconcile.py` copies are **kept independent** (their md5 hashes diverged before this bug), and the same fix is applied twice with matching semantics. hand-off's `_prepare_scope` will pass the flag internally (it *is* the "intending to write" caller), so hand-off users see no CLI change; but `skills/hand-off/scripts/reconcile.py` gets the same `--acquire-lock` flag on its `check-reality` subcommand for parity, and hand-off's `prepare` invokes `_check_reality_scope` with `acquire=True`.

**Rationale:** Unifying the two files into a shared source is a bigger refactor (touches skill packaging, install layout, both templates), out of scope for a lock-lifecycle bugfix. Divergent-by-design is the current de-facto state; making the fix land in both preserves that state without escalating. The parity work + a shared regression test lives under `skills/hand-off/scripts/tests/`, mirroring the take-over side.

**Rejected:**
- Unify the two copies into `skills/_shared/reconcile.py` — retired by R14 (2026-07-17 "Adopted 方案 A: self-contained skill directories"); reversing that under a bugfix would be scope creep.
- Land the fix only in take-over — bug's symptom appears in hand-off's `prepare`; if `prepare` still runs its inner check-reality with the old semantics, the class of leak persists.

**Impact:** hand-off `check-reality` CLI gains the same opt-in flag (no default behaviour change for hand-off's own workflows because `prepare` passes it internally). Regression coverage duplicated to hand-off's test suite.

---

