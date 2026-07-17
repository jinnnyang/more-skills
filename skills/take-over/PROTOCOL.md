# Session Handoff Protocol — take-over perspective

> **Status:** v0.3 (2026-07-17 rev-A) — Adopted self-contained skill layout (方案 A).
> **Scope:** Protocol reference for the **take-over** side of the session handoff workflow. The companion skill `hand-off` maintains its own copy of this protocol from the closing side; the two skills are independently installable and do not share files.
> **Location:** This file is part of the self-contained `skills/take-over/` directory. See `DECISIONS.md` in the same directory for the design decision log.

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

Four **core** documents (always considered), two **optional** (only when produced). This section describes what `take-over` **reads** and reconciles.

### 4.1 Core

| File | Answers | Lifecycle | Size |
|---|---|---|---|
| `context.md` | *What must never break* — invariants, env, credentials location, "don't touch X because Y" | **Strictly Additive-only** (grows monotonically; corrections appended at the bottom with dated entries) | Small (< 2 KB target) |
| `task.md` | *What's happening now + next up* — persisted `todo` state | Overwritten each hand-off | Small |
| `walkthrough.md` | *What happened, why, and any surprises* — living work-memory, pruned when items resolve | **Editable** (add on hand-off, prune resolved items) | Bounded (target < 20 KB) |
| `open-questions.md` | *What's blocked pending human input* — **only** items requiring a **human** answer. Agent-side blockers (waiting on API/build/tool) stay in `task.md` with `[!]` marker. | Overwritten; entries removed when resolved | Small |

### 4.2 Optional (create only when relevant)

| File | Answers | Lifecycle |
|---|---|---|
| `plan.md` | *Future intent* — the next-phase roadmap, self-contained | Overwritten |
| `review.md` | *Known bugs / TODOs in the code itself* | Entries removed when fixed |

**Discipline for take-over:** `L1 (always load) = context.md + task.md + open-questions.md`. Optional files load only on demand. `walkthrough.md` is L3 — reference only, never auto-loaded.

## 5. Directory Layout

Dual-track (project-scoped, in the current working directory):

```
.hermes/handoff/                    # Private scratch, .gitignore'd — take-over reads here by default
    context.md
    task.md
    walkthrough.md
    open-questions.md
    plan.md                         # optional
    review.md                       # optional

docs/handoff/                       # Public, git-tracked snapshot — take-over reads here if present
    (copy of the above, produced by hand-off's explicit "promote" action)
```

**Precedence rule:** if both `.hermes/handoff/` and `docs/handoff/` exist, `.hermes/handoff/` wins (it's the live working set). `docs/handoff/` is a frozen historical snapshot; do NOT modify its contents.

### Multi-branch caveat (deferred)

Git worktree / branch-parallel work is a real problem but out of scope for MVP. If it becomes an issue, prefix with branch: `.hermes/handoff/<branch>/…`. Ignore for now.

## 6. Document Format

**YAML frontmatter + Markdown body**, matching how SKILL.md itself is structured.

```yaml
---
kind: context | task | walkthrough | open-questions | plan | review   # MUST be one of these exact values
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

**MVP frontmatter is intentionally minimal.** Fields deferred (see §13): `project` (implied by cwd), `branch` (v2, requires branch-prefix layout), `next_agent` (no claim protocol yet).

## 7. The Take-Over Flow

Triggered by: loading the skill; user says "continue previous work" / "接着之前的做".

All Python invocations use `uv run --isolated python <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is this skill's directory.

```
Step 0  Bootstrap Check & Initial Loading
        - If `.hermes/handoff/` is missing, initialize the directory.
        - Create empty default files using templates from this skill's templates/ directory.
        - Report: "No previous handoff history found. Initialized empty session." and exit take-over flow.

Step 1  Discover
        - Scan .hermes/handoff/ (and docs/handoff/ if present) for the document set.
        - Read only YAML frontmatter of every file first.
        - Determine freshness: last_updated vs `git log -1 --format=%cI`.

Step 2  Reality check (reconciliation)     ← Offloaded to reconcile.py
        - Execute reality-check via reconcile.py to verify:
          * `git status --short`             → uncommitted changes?
          * `git log -5 --oneline`           → do commit messages match walkthrough claims?
          * Cross-reference walkthrough's `<session-tools-log>` metadata to verify tool call history.
          * Sanity-existence of key files mentioned in task.md.
          * Optional: run declared smoke test if fast (< 10s) and specified as REQUIRED in task.md.

Step 3  Layered load
        L1 (always):  context.md + task.md + open-questions.md
        L2 (on demand): plan.md, review.md, current-phase excerpt of plan.md
        L3 (reference only, do NOT auto-load): walkthrough.md
                       Read the single walkthrough.md only when digging
                       into a specific past decision surfaced by L1/L2.
                       For older/pruned detail, use `session_search`
                       against the recorded session_id.

Step 4  Restore todo
        - Parse task.md's checklist → repopulate `todo` tool.

Step 5  Conflict handling
        - Classify discrepancy per §9b:
          HARD → halt, `clarify` prompt with structured choices, block loading.
                 If running in non-interactive/CI mode, HALT times out after 5 minutes,
                 writes `conflict_pending.json` with details, and aborts execution.
          SOFT → append to `open-questions.md` under a structured `## Soft Conflicts` section with UTC timestamp. Continue L1 load.
          AMBIGUOUS → escalate to HARD (fail-safe).

Step 6  plan-mode coexistence check (Pre-empt final report)
        If `.hermes/plans/` exists (plan-mode artifacts), do NOT auto-merge.
        Prompt user via `clarify` with:
          - Ignore (default) — keep both directories independent
          - Import plan-mode's plan.md → .hermes/handoff/plan.md (copy, one-shot)
          - Show diff first
        Never modify `.hermes/plans/` from this skill. Adjust task state before reporting if imported.

Step 7  Report to user
        "Previous agent: <last_agent>. Last verified: <ts>.
         Done: … Now: … Next: … Blocked on: …
         Where would you like to resume?"
```

**Compression is by layering, not summarization.** L1 is intentionally kept small (target < 3 KB total for all three files) so the take-over cost is bounded regardless of project size.

## 9. Anti-Hallucination Invariants

Both `hand-off` and `take-over` must obey (this file focuses on what `take-over` upholds):

1. **No claims without evidence.** When surfacing "Previous session did X", cross-check `git log` or the serialized `<session-tools-log>` before repeating the claim. Otherwise mark it "attempted X, unverified" in the summary.
2. **`last_verified` timestamp is required.** If reality-check was skipped for any reason, surface `last_verified: SKIPPED` in the take-over summary.
3. **`todo` items are never inferred.** Restore verbatim from `task.md`; do not fabricate items or drop unrecognized entries.
4. **Reality trumps documentation on hard conflicts.** See §9b — HARD conflicts halt loading until the user resolves them.
5. **Atomic Write Rule.** Any write take-over performs (e.g. logging SOFT conflicts to `open-questions.md`, initializing empty files) must write to a `.tmp` file and rename (POSIX `rename()`) to replace the target.
6. **Script-assisted Execution.** Reality-check and conflict classification are offloaded to this skill's `scripts/reconcile.py` rather than done purely in LLM memory.
7. **On take-over conflict, apply §9b tiered handling.** Hard conflicts halt via `clarify`; soft conflicts are logged to `open-questions.md` under a structured `## Soft Conflicts` section with UTC timestamp, and loading continues. Never silently reconcile away a hard conflict.

## 9b. Take-Over Conflict Handling (tiered)

Confidence-based classification. Every reality-check discrepancy falls into one of:

| Tier | Trigger | Action |
|---|---|---|
| **HARD** | Document claims "completed X" but no git/code evidence for X. Two handoff docs contradict each other. `context.md` invariant directly contradicts current code/config. | **HALT.** Present conflicts via `clarify` (structured choices): "trust doc / trust reality / user explains". Loading blocks until resolved. |
| **SOFT** | `last_verified` older than 7 days. Referenced file was renamed/moved but content intact. `session_id` not found in `session_search` (likely pruned). | Log to `open-questions.md` with `⚠️ stale` tag under `## Soft Conflicts (Reconciled)` with UTC timestamp. Continue L1 load. Report count in take-over summary. |
| **AMBIGUOUS** | Fails both categorization tests. | Escalate to HARD (fail-safe). |

**Reporting:** take-over's final summary MUST state "N soft conflicts logged, M hard conflicts resolved" so the user always sees the reconciliation footprint.

## 10. Decision Points relevant to take-over

| # | Question | Decision |
|---|---|---|
| ① | Document format: YAML frontmatter + MD, or plain MD? | **✅ YAML frontmatter + MD** — machine-scannable frontmatter enables cheap L1 pre-filter. |
| ④ | On take-over conflict (docs disagree with git/code): halt vs auto-log? | **✅ Tiered per §9b** — hard conflicts halt via `clarify`, soft conflicts logged with `⚠️ stale`, ambiguous → escalate to hard (fail-safe). |

See `DECISIONS.md` for the full rationale and rejected alternatives.

## 10a. User Interaction Rule

**All user-facing prompts issued by `take-over` MUST use the `AskUserQuestion` tool (in Hermes: `clarify`) with structured `choices`**, not free-text messages. Applies to:

- HARD conflict resolution (④)
- plan-mode coexistence choice (Step 6)
- any point where the flow branches on user input

Rationale: structured choices render as pickable UI, avoid ambiguity from typed answers, and keep the agent's branching logic deterministic. Free-text is only appropriate for genuinely open-ended follow-ups (e.g. "why?").

## 11. MVP Scope

Ship the minimum that closes the loop:

- **Documents read:** `context.md`, `task.md`, `walkthrough.md` (L3 on-demand only), `open-questions.md`. Optional: `plan.md`, `review.md`.
- **Reality check:** `git status` + `git log -5` + `<session-tools-log>` check + file-existence sanity. Skip smoke tests for MVP unless marked REQUIRED in task.md.
- **Layered load:** L1 mandatory, L2 on demand, L3 via `session_search`.
- **No branch-prefix** — single-branch assumption.

Expand only after the MVP feedback loop shows what's actually missing.

## 12. Implementation Layout (Self-contained)

This skill is **self-contained**. Everything it needs — protocol, decision log, helper scripts, templates — lives under its own directory:

```
skills/take-over/
  SKILL.md
  PROTOCOL.md           ← THIS FILE
  DECISIONS.md
  scripts/
    reconcile.py        (helper for init / reality-check / clean-up / write-atomic)
  templates/
    context.md
    task.md
    walkthrough.md
    open-questions.md
```

The companion skill `hand-off` maintains an **independent** copy of the protocol from the closing side. The two skills do NOT share files at runtime; users can install either or both. See `DECISIONS.md` (this directory) for the rationale behind this self-contained layout.

## 13. Open Questions (Not Yet Decision Points)

- How does this interact with `subagent-driven-development`? Sub-agents don't currently write handoff docs — should orchestrators propagate context to them?
- Concurrent take-over from two live sessions reading from the same `.hermes/handoff/` — MVP assumes serial execution; needs a lock/leader-election mechanism in v2.
- Multi-branch layout — prefix with branch (`.hermes/handoff/<branch>/…`); deferred (see §5 caveat). Reintroduces `branch:` frontmatter field.
- `next_agent` claim protocol — currently no way to signal "I'm about to pick this up"; if collaborative workflows appear, add a claim step.
- Dry-run mode for `take-over` — describe what would be loaded and what conflicts would be raised without mutating `open-questions.md`.
- Drift-detection tooling between the two self-contained skills — currently manual (see `DECISIONS.md` 2026-07-17 · adoption of 方案 A).

## 14. References

- Companion skill: `hand-off` (independent self-contained skill; each half of the protocol is installable on its own).
- `../../spec/agent-skills-spec.md` — SKILL.md format this skill conforms to.
- Hermes primitives: `memory`, `todo`, `session_search`, `skill_manage`.
- `./DECISIONS.md` — append-only log of resolved design decisions; consult before proposing changes that touch ①④.

---

*End of PROTOCOL.md (take-over perspective). Status: v0.3 rev-A (2026-07-17). Companion: `skills/hand-off/PROTOCOL.md`.*
