# Session Handoff Protocol — hand-off perspective

> **Status:** v0.3 (2026-07-17 rev-A) — Adopted self-contained skill layout (方案 A).
> **Scope:** Protocol reference for the **hand-off** side of the session handoff workflow. The companion skill `take-over` maintains its own copy of this protocol from the resume side; the two skills are independently installable and do not share files.
> **Location:** This file is part of the self-contained `skills/hand-off/` directory. See `DECISIONS.md` in the same directory for the design decision log.

---

## 1. Problem

Any non-trivial project passes through multiple agents (Claude / Hermes / OpenCode / humans) and multiple sessions. Today there is **no protocol for transferring project state** between them. The status quo relies on:

- `memory` — too coarse, cross-project noise, not project-scoped state.
- `session_search` — searches past chatter, no structured "current status".
- `.hermes/plans/` (from `plan-mode`) — write-only, no load path, no reconciliation.
- Ad-hoc `NOTES.md` / `TODO.md` files — no convention, silently drifts from reality.

The recurring symptoms:
- New agent burns 30% of context re-discovering what's done.
- New agent trusts stale documentation and re-does completed work, or worse, undoes it.
- Previous agent's undocumented decisions surface as bugs later.
- `todo` state is lost across sessions.

## 2. Goal

Establish a **protocol + pair of independent skills** so that a session boundary is a well-defined handoff, not a memory-hole.

Non-goals:
- Replacing `plan-mode`, `memory`, `todo`, or `session_search` — this skill **bridges** them.
- Full-fidelity conversation replay — that's what `session_search` is for.
- Cross-repo state — scoped to one working directory / project.

## 3. Relationship to Existing Primitives

| Primitive | Role | Handoff protocol's use |
|---|---|---|
| `memory` | Cross-project user preferences | Untouched. Project-specific state does **not** go here. |
| `todo` | Session-local task list | Persisted into `task.md` on hand-off; restored on take-over. |
| `session_search` | FTS over past sessions | `walkthrough.md` records `session_id`; agents fetch prose via `session_search` on demand. |
| `skill_manage` | Reusable procedures | This PROTOCOL + `hand-off` / `take-over` skills. Project-temporary state stays in handoff docs. |

`plan-mode` is **design inspiration only** — it demonstrated that a "planning-only" workflow works. `hand-off` / `take-over` do not read or write `.hermes/plans/`, do not depend on `plan-mode` being installed, and do not require the user to have run it. Independence is a design goal.

**Key rule:** duplicate nothing. Every document is either the source of truth for its concern, or a pointer to one.

## 4. Document Set

Four **core** documents (always considered), two **optional** (only when produced). This section describes what `hand-off` **writes**.

### 4.1 Core

| File | Answers | Lifecycle | Size |
|---|---|---|---|
| `context.md` | *What must never break* — invariants, env, credentials location, "don't touch X because Y" | **Strictly Additive-only** (grows monotonically; corrections appended at the bottom with dated entries) | Small (< 2 KB target) |
| `task.md` | *What's happening now + next up* — persisted `todo` state | Overwritten each hand-off | Small |
| `walkthrough.md` | *What happened, why, and any surprises* — living work-memory, pruned when items resolve | **Editable** (add on hand-off, prune resolved items) | Bounded (target < 20 KB) |
| `questions.md` | *What's blocked pending human input* — **only** items requiring a **human** answer. Agent-side blockers (waiting on API/build/tool) stay in `task.md` with `[!]` marker. | Overwritten; entries removed when resolved | Small |

### 4.2 Optional (create only when relevant)

| File | Answers | Lifecycle |
|---|---|---|
| `plan.md` | *Future intent* — the next-phase roadmap, self-contained | Overwritten |
| `review.md` | *Known bugs / TODOs in the code itself* | Entries removed when fixed |

**Discipline:** never write empty stubs to satisfy the template. If nothing changed on `plan.md` this session, don't touch it.

## 5. Directory Layout

Handoff documents live directly in the working scope directory using their natural short names. They are ordinary files in the working tree and are Git-tracked by default:

```
<scope>/                            # Standard directory in the working tree (Git-tracked)
    context.md                      # Invariants, additive-only
    task.md                         # active checklist
    walkthrough.md                  # single living file, pruned on hand-off (see §9a)
    questions.md                    # ## Open + ## Closed
    plan.md                         # optional
    review.md                       # optional
```

There is no separate `.hermes/handoff/` private scratch directory and no `docs/handoff/` promotion path. Keeping files directly in the working tree ensures simplicity and direct tracking.

**Kind-based scope detection.** A directory qualifies as a scope only when at least one candidate file has YAML frontmatter carrying a recognised `kind` value (`context` / `task` / `walkthrough` / `questions` / `plan` / `review`). This prevents false positives from unrelated generic `context.md` / `task.md` files elsewhere in a project. See §5a for scope resolution.

**Why single `walkthrough.md` (not `walkthrough/*.md`):** per DECISIONS ②, walkthrough is *working memory*, not audit log. A single file makes L3 load cost bounded by pruning discipline (§9a) — long-term audit trail already lives in `git log` and `session_search`. Per-session files created a pruning + indexing problem and were explicitly rejected.

## 5a. Scope Resolution

Scope is defined by **the task's range**, not by directory role. Neither "one per skill" nor "always repo root" is a rule — the agent and user negotiate per task. `reconcile.py list-scopes` enumerates all live scopes neutrally.

Resolution rules for every command that takes `--scope`:

1. **Explicit** — `--scope <path>` wins verbatim.
2. **Implicit at pwd** — if pwd contains recognised handoff docs (kind-frontmatter match), pwd is used silently.
3. **Ambiguous** — otherwise the script emits `WARNING` on stderr, prints `ambiguous_scope` JSON, and exits with code 3. Agent MUST `clarify` with the user before proceeding.

Batch commands (`validate`, `check-reality`, `clean-up`) also accept `--all-scopes` to iterate over every discovered scope.

### Multi-branch caveat (deferred)

Git worktree / branch-parallel work is a real problem but out of scope for MVP. If it becomes an issue, prefix with branch under a per-branch scope (e.g. `<scope>/<branch>/context.md`). Ignore for now.


## 6. Document Format

**YAML frontmatter + Markdown body**, matching how SKILL.md itself is structured.

```yaml
---
kind: context | task | walkthrough | questions | plan | review   # MUST be one of these exact values
version: 1
last_updated: 2026-07-17T14:20:00+08:00     # MUST include timezone offset (avoid Windows/Unix parse drift)
last_verified: 2026-07-17T14:20:00+08:00    # when reality-check last ran; use `SKIPPED` if skipped
last_agent: claude-sonnet-4 via Hermes/devops
last_writer: hand-off | take-over | user | migration — for audit / anti-hallucination
session_id: <hermes-session-id>             # optional; include only if runtime exposes it
status: in-progress | blocked | phase-complete | archived
---
```

# <human-readable title>

<markdown body>

The frontmatter is what makes take-over's **L1 scan** cheap: an agent can slurp all frontmatter and know the shape of everything before deciding what to load.

**MVP frontmatter is intentionally minimal.** Fields deferred (see §13): `project` (implied by cwd), `branch` (v2, requires branch-prefix layout), `next_agent` (no claim protocol yet). Do not invent extra fields — every field must have a reader in `hand-off` or `take-over`.

## 8. The Hand-Off Flow

Triggered by: user says "先到这" / "换你上" / `/handoff`; auto-suggested when context > 75% or when a `todo` phase completes.

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is this skill's directory. `uv run` is already isolated for scripts with inline `# /// script` metadata — do not pass `--isolated`.

```
Step 0  Bootstrap Check
        - If `<scope>/` is missing, initialize the directory structure first.

Step 1  Reality check (anti-hallucination)
        - Offload to `reconcile.py check-reality` to compute actual mutations:
          * `git status --porcelain`         → what's uncommitted? (PRIMARY EVIDENCE)
          * `git log -5 --name-only`         → recent commits (PRIMARY EVIDENCE)
          * Cross-reference walkthrough's optional `<session-tools-log>` block.
          * Diff against what task.md claims is in-progress.

Step 2  Update core docs (Atomic Write Rule: write to `.tmp` first, then rename)
        a) task.md      ← dump current `todo` verbatim; do not "summarize" open items away.
        b) walkthrough.md ← UPDATE the single living file.
           - APPEND today's entry with header format `## YYYY-MM-DD — <slug>`.
             The classifier in §9a REQUIRES this format; deviation disables
             stale-detection for that entry.
           - Entry content:
               * Decisions made & why (rationale)
               * Files changed (paths)
               * Surprises / gotchas discovered
               * session_id back-reference
               * NOT a transcript replay — decisions + deltas + surprises only
               * `<session-tools-log>` metadata: Serialize the list of actual tool calls of this session.
           - PRUNE resolved / obsolete entries per §9a (Smart Cleanup).
           - Target size < 20 KB. If exceeded, tighten pruning; do NOT split into per-session files.
        c) questions.md ← add any blockers found this session.
        d) context.md   ← only if a new invariant was learned. Additive-only; append new invariants to the bottom.
        e) plan.md / review.md ← only if produced/updated this session.

Step 3  Update frontmatter
        - Bump last_updated everywhere touched.
        - Set last_verified to now.
        - Set last_agent, session_id.
        - Set status appropriately (in-progress / blocked / phase-complete).

Step 4  Commit decision
        Handoff files live directly in the working tree. Ask via AskUserQuestion (clarify) with structured choices:
          "How to handle this handoff?"
            - Leave uncommitted (user will commit later)
            - Commit now with default message
            - Stage but don't commit
        
        If "commit now" chosen, offer default message:
          "docs(handoff): <slug> — <status>"
        and let user edit before running git commit.

Step 5  Final message
        Summary of what was written + explicit next actions for the successor.
```

## 9. Anti-Hallucination Invariants

Both `hand-off` and `take-over` must obey (this file focuses on what `hand-off` upholds):

1. **No claims without evidence.** "Completed X" is written only if `git log` or `git status --short` confirms X. The optional `<session-tools-log>` block is auxiliary evidence only — it can complement git but cannot substitute for it. Absent primary git evidence, write "attempted X, unverified".
2. **`last_verified` timestamp is required.** If reality-check was skipped, mark it explicitly: `last_verified: SKIPPED`.
3. **`todo` items are never dropped implicitly.** Open items on hand-off carry over verbatim; closed items are removed only if the corresponding commit / evidence is present.
4. **Walkthrough is written last**, after all mutations are done, so it reflects the final state — not intermediate.
5. **Atomic Write Rule.** Every file mutation must write to a `.tmp` file and rename (POSIX `rename()`) to replace the target file.
6. **Script-assisted Execution.** Major verification, cleanup classification, and conflict calculations must be offloaded to this skill's `scripts/reconcile.py` rather than done purely in LLM memory.

## 9a. Smart Cleanup (confidence-based auto-approval)

Modeled on Hermes' "Smart" dangerous-command mode: hand-off must compress living documents (`walkthrough.md`, `questions.md`, `review.md`) but must not delete anything it isn't sure about.

**Decision Priority:** `KEEP > CLEAR > STALE > UNSURE` (retaining tags takes precedence over deleting tags).

Every candidate entry is classified into one of four buckets:

| Verdict | Action | Requires |
|---|---|---|
| **CLEAR** | Auto-delete or compress to one-line | Hard evidence the item is resolved (see criteria below) |
| **STALE** | Auto-delete | Long-untouched (>30 days) AND no explicit text or path references to the file/topic in the rest of `task.md`, `context.md`, or current walkthrough entries. If ambiguous, defaults to UNSURE. |
| **KEEP** | Retain verbatim | Marked as decision / surprise / lesson, or explicitly tagged for future reference |
| **UNSURE** | Batch-ask user at end of hand-off | Anything that fails KEEP/CLEAR/STALE criteria |

**Hard-evidence criteria for CLEAR** (any one suffices):
1. Item body contains an explicit `<!-- resolved -->` marker (or the header contains one).
2. All file paths referenced in the item body appear in `git log --diff-filter=D --since=90.days` (files have been deleted from the repo).

The following auxiliary criteria are DEFERRED to a future revision and are NOT implemented in the MVP classifier (agents that need them should manually mark entries `<!-- resolved -->`):
- Error message referenced is absent from the last N successful test runs.
- Corresponding entry in `questions.md` is marked resolved.

**Rationale for MVP restraint:** free-text grep for "resolved" produced too many false positives (matching phrases like "not resolved yet"). Explicit HTML-comment markers are unambiguous, machine-checkable, and orthogonal to prose.

**Two-phase execution (MVP dry-run requirement):**
1. `hand-off` calls `reconcile.py clean-up --dry-run` first, receives a classification plan JSON, presents `unsure` items in a batched `clarify` prompt, and shows the user which entries would be removed as CLEAR / STALE.
2. Only after user confirmation does `hand-off` call `reconcile.py clean-up --apply`. UNSURE entries are ALWAYS preserved even after apply.

**User interaction rule:** UNSURE items are presented as a **single batched prompt at the end of hand-off via `clarify`**, not per-item. Example:

```
Cleanup review: auto-removed 3 CLEAR + 2 STALE items.
Unsure about 2 items — keep or drop?
  [1] 2026-07-10 · Chrome portable path — still needed?
  [2] 2026-06-28 · Playwright version conflict — upgraded but unverified
```

**Audit trail:** every CLEAR/STALE removal is listed in the hand-off's final summary so the user sees what was cleaned. If uncertain, `hand-off` errs toward UNSURE over CLEAR.

## 9b. Question Archive Semantics (v0.5-rev-C)

`questions.md` uses a two-section structure — `## Open` (active) and `## Closed` (archive). Entries are `###`-level subsections under either heading.

- Mark an Open entry with `<!-- resolved -->` to signal it is answered.
- The next `hand-off clean-up --apply` **moves** every `<!-- resolved -->` entry from `## Open` to `## Closed`. The full body is preserved verbatim; the archive is permanent (retained for historical review).
- Entries already under `## Closed` are never touched by cleanup — they are the archive.
- The classifier reports moved entries in the `archived` bucket (in addition to `clear` / `stale` / `kept` / `unsure`).
- Rationale: unlike `walkthrough.md` (working memory, safely prunable), `questions.md` records **decision history** that stays valuable across sessions. Deletion loses that; archive keeps it.

**SOFT conflict integration.** `take-over check-reality --apply-soft-conflicts` writes each SOFT conflict as its own `### Soft conflict · <type> · <timestamp>` entry under `## Open`, making SOFT items individually resolvable through the same `<!-- resolved -->` → archive flow.

## 10. Decision Points relevant to hand-off

| # | Question | Decision |
|---|---|---|
| ① | Document format: YAML frontmatter + MD, or plain MD? | **✅ YAML frontmatter + MD** — machine-scannable frontmatter enables cheap L1 pre-filter. |
| ② | `walkthrough` growth control? | **✅ Single `walkthrough.md`, prune resolved items** — living work-memory, not audit log. Long-term audit trail lives in git history + `session_search`. |
| ③ | Git commit on hand-off (promote path only)? | **✅ Ask via `clarify`, then commit with default message** — private `<scope>/` is gitignored so N/A. Promote → `docs/handoff/` always prompts with structured choices. |

See `DECISIONS.md` for the full rationale and rejected alternatives.

## 10a. User Interaction Rule

**All user-facing prompts issued by `hand-off` MUST use the `AskUserQuestion` tool (in Hermes: `clarify`) with structured `choices`**, not free-text messages. Applies to:

- promote-and-commit confirmation (③)
- Smart Cleanup UNSURE items (§9a)
- any point where the flow branches on user input

Rationale: structured choices render as pickable UI, avoid ambiguity from typed answers, and keep the agent's branching logic deterministic. Free-text is only appropriate for genuinely open-ended follow-ups (e.g. "why?").

## 11. MVP Scope

Ship the minimum that closes the loop:

- **Documents:** `context.md`, `task.md`, `walkthrough.md`, `questions.md` only. Skip `plan.md` and `review.md` for MVP — they're optional anyway.
- **Reality check:** `git status` + `git log -5` + `todo` diff + `<session-tools-log>` check. Skip smoke tests for MVP unless marked REQUIRED in task.md.
- **No auto-promotion** to `docs/handoff/` — always private scratch by default.
- **No branch-prefix** — single-branch assumption.

Expand only after the MVP feedback loop shows what's actually missing.

## 12. Implementation Layout (Self-contained)

This skill is **self-contained**. Everything it needs — protocol, decision log, helper scripts, templates — lives under its own directory:

```
skills/hand-off/
  SKILL.md
  PROTOCOL.md           ← THIS FILE
  DECISIONS.md
  scripts/
    reconcile.py        (helper for init / reality-check / clean-up / write-atomic)
  templates/
    context.md
    task.md
    walkthrough.md
    questions.md
```

The companion skill `take-over` maintains an **independent** copy of the protocol from the resume side. The two skills do NOT share files at runtime; users can install either or both. See `DECISIONS.md` (this directory) for the rationale behind this self-contained layout.

## 13. Open Questions (Not Yet Decision Points)

- How does this interact with `subagent-driven-development`? Sub-agents don't currently write handoff docs — should orchestrators propagate context to them?
- Any hook for auto-suggesting `hand-off` when context window > 75%? (Runtime-dependent; may not be portable.)
- Concurrent hand-off from two live sessions writing to the same `<scope>/` — MVP assumes serial execution; needs a lock file or timestamp-based conflict prompt in v2.
- Multi-branch layout — prefix with branch (`<scope>/<branch>/…`); deferred (see §5 caveat). Reintroduces `branch:` frontmatter field.
- `next_agent` claim protocol — currently no way to signal "I'm about to pick this up"; if collaborative workflows appear, add a claim step.
- Dry-run mode for `hand-off` — print diff of every file it would write, confirm via `clarify` before landing. Useful especially for first Smart Cleanup run on a project.
- Drift-detection tooling between the two self-contained skills — currently manual (see `DECISIONS.md` 2026-07-17 · adoption of 方案 A).

## 14. References

- Companion skill: `take-over` (independent self-contained skill; each half of the protocol is installable on its own).
- `../../spec/agent-skills-spec.md` — SKILL.md format this skill conforms to.
- Hermes primitives: `memory`, `todo`, `session_search`, `skill_manage`.
- `./DECISIONS.md` — append-only log of resolved design decisions; consult before proposing changes that touch ①②③.

---

*End of PROTOCOL.md (hand-off perspective). Status: v0.3 rev-A (2026-07-17). Companion: `skills/take-over/PROTOCOL.md`.*
