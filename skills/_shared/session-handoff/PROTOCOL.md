# Session Handoff Protocol

> **Status:** v0.2 (2026-07-16 rev-2) — ①②③④ resolved (§10); MVP simplifications applied (see `DECISIONS.md` rev-2).
> **Authors:** 刘工 + Hermes Agent (2026-07-16)
> **Location:** `skills/_shared/session-handoff/PROTOCOL.md` — single source of truth referenced by `skills/hand-off/` and `skills/take-over/`.
> **Scope:** Joint design for a pair of skills — `hand-off` (session close) and `take-over` (session resume) — that give multi-agent / multi-session work a shared protocol for transferring project state.

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

Establish a **protocol + pair of skills** so that a session boundary is a well-defined handoff, not a memory-hole.

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
| `skill_manage` | Reusable procedures | This PROTOCOL.md → future `hand-off` / `take-over` skills. Project-temporary state stays in handoff docs. |

`plan-mode` is **design inspiration only** — it demonstrated that a "planning-only" workflow works. `hand-off` / `take-over` do not read or write `.hermes/plans/`, do not depend on `plan-mode` being installed, and do not require the user to have run it. Independence is a design goal.

**Key rule:** duplicate nothing. Every document is either the source of truth for its concern, or a pointer to one.

## 4. Document Set

Four **core** documents (always considered), two **optional** (only when produced):

### 4.1 Core

| File | Answers | Lifecycle | Size |
|---|---|---|---|
| `context.md` | *What must never break* — invariants, env, credentials location, "don't touch X because Y" | Overwrite-append (grows monotonically) | Small (< 2 KB target) |
| `task.md` | *What's happening now + next up* — persisted `todo` state | Overwritten each hand-off | Small |
| `walkthrough.md` | *What happened, why, and any surprises* — living work-memory, pruned when items resolve | **Editable** (add on hand-off, prune resolved items) | Bounded (target < 20 KB) |
| `open-questions.md` | *What's blocked pending human input* — **only** items requiring a **human** answer. Agent-side blockers (waiting on API/build/tool) stay in `task.md` with `[!]` marker. | Overwritten; entries removed when resolved | Small |

### 4.2 Optional (create only when relevant)

| File | Answers | Lifecycle |
|---|---|---|
| `plan.md` | *Future intent* — the next-phase roadmap, self-contained | Overwritten |
| `review.md` | *Known bugs / TODOs in the code itself* | Entries removed when fixed |

**Discipline:** never write empty stubs to satisfy the template. If nothing changed on `plan.md` this session, don't touch it.

## 5. Directory Layout

Dual-track:

```
.hermes/handoff/                    # Private scratch, .gitignore'd
    context.md
    task.md
    walkthrough.md                  # single living file, pruned on hand-off (see §9a)
    open-questions.md
    plan.md                         # optional
    review.md                       # optional

docs/handoff/                       # Public, git-tracked snapshot — only when user promotes
    (copy of the above, produced by explicit "promote" action; see §8 Step 4)
```

**Why single `walkthrough.md` (not `walkthrough/*.md`):** per DECISIONS ②, walkthrough is *working memory*, not audit log. A single file makes L3 load cost bounded by pruning discipline (§9a) — long-term audit trail already lives in `git log` and `session_search`. Per-session files created a pruning + indexing problem and were explicitly rejected.

**Rule:** `hand-off` writes to `.hermes/handoff/` by default. Promoting to `docs/handoff/` is an explicit user choice ("这批留档" / "commit into repo").

### Multi-branch caveat (deferred)

Git worktree / branch-parallel work is a real problem but out of scope for MVP. If it becomes an issue, prefix with branch: `.hermes/handoff/<branch>/…`. Ignore for now.

## 6. Document Format

**YAML frontmatter + Markdown body**, matching how SKILL.md itself is structured.

```yaml
---
kind: handoff/task            # one of: context, task, walkthrough, open-questions, plan, review
version: 1
last_updated: 2026-07-16T14:20:00+08:00     # MUST include timezone offset (avoid Windows/Unix parse drift)
last_verified: 2026-07-16T14:20:00+08:00    # when reality-check last ran; use `SKIPPED` if skipped
last_agent: claude-sonnet-4 via Hermes/devops
last_writer: hand-off        # hand-off | take-over | user | migration — for audit / anti-hallucination
session_id: <hermes-session-id>            # optional; include only if runtime exposes it
status: in-progress | blocked | phase-complete | archived
---

# <human-readable title>

<markdown body>
```

The frontmatter is what makes take-over's **L1 scan** cheap: an agent can slurp all frontmatter and know the shape of everything before deciding what to load.

**MVP frontmatter is intentionally minimal.** Fields deferred (see §13): `project` (implied by cwd), `branch` (v2, requires branch-prefix layout), `next_agent` (no claim protocol yet). Do not invent extra fields — every field must have a reader in `hand-off` or `take-over`.

## 7. The Take-Over Flow

Triggered by: loading the skill; user says "continue previous work" / "接着之前的做".

```
Step 1  Discover
        - Scan .hermes/handoff/ (and docs/handoff/ if present) for the document set.
        - Read only YAML frontmatter of every file first.
        - Determine freshness: last_updated vs `git log -1 --format=%cI`.

Step 2  Reality check (reconciliation)     ← the hard part
        - `git status --short`             → uncommitted changes?
        - `git log -5 --oneline`           → do commit messages match walkthrough claims?
        - Sanity-existence of key files mentioned in task.md.
        - Optional: run declared smoke test if fast (< 10s).

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
        Classify each discrepancy per §9b:
          HARD → halt, `clarify` prompt with structured choices, block loading
          SOFT → append to `open-questions.md` with ⚠️ stale tag, continue
          AMBIGUOUS → escalate to HARD (fail-safe)

Step 6  Report to user
        "Previous agent: <last_agent>. Last verified: <ts>.
         Done: … Now: … Next: … Blocked on: …
         Where would you like to resume?"

Step 7  plan-mode coexistence check
        If `.hermes/plans/` exists (plan-mode artifacts), do NOT auto-merge.
        Include one line in the Step 6 report:
          "Detected plan-mode artifacts in .hermes/plans/. Import manually? (see clarify)"
        On explicit user request, offer a `clarify` with:
          - Ignore (default) — keep both directories independent
          - Import plan-mode's plan.md → .hermes/handoff/plan.md (copy, one-shot)
          - Show diff first
        Never modify `.hermes/plans/` from this skill.
```

**Compression is by layering, not summarization.** L1 is intentionally kept small (target < 3 KB total for all three files) so the take-over cost is bounded regardless of project size.

## 8. The Hand-Off Flow

Triggered by: user says "先到这" / "换你上" / `/handoff`; auto-suggested when context > 75% or when a `todo` phase completes.

```
Step 1  Reality check (anti-hallucination)
        - `git status --short`             → what's uncommitted?
        - List files this session actually modified
          (from tool-call history, NOT from memory).
        - Diff against what task.md claims is in-progress.

Step 2  Update core docs
        a) task.md      ← dump current `todo` verbatim; do not "summarize" open items away.
        b) walkthrough.md ← UPDATE the single living file.
           - APPEND today's entry (dated + slug header) with:
               * Decisions made & why (rationale)
               * Files changed (paths)
               * Surprises / gotchas discovered
               * session_id back-reference (if runtime exposes it; else omit)
               * NOT a transcript replay — decisions + deltas + surprises only
           - PRUNE resolved / obsolete entries per §9a (Smart Cleanup).
           - Target size < 20 KB. If exceeded, tighten pruning; do NOT split into per-session files.
        c) open-questions.md ← add any blockers found this session.
        d) context.md   ← only if a new invariant was learned. Additive.
        e) plan.md / review.md ← only if produced/updated this session.

Step 3  Update frontmatter
        - Bump last_updated everywhere touched.
        - Set last_verified to now.
        - Set last_agent, session_id.
        - Set status appropriately (in-progress / blocked / phase-complete).

Step 4  Promote decision (optional; default = private)
        `.hermes/handoff/` is gitignored, so no commit action for private scratch.
        Ask via AskUserQuestion (clarify) with structured choices:
          "How to handle this handoff?"
            - Leave in .hermes/handoff/ (private, no commit)
            - Promote to docs/handoff/ and commit now
            - Promote to docs/handoff/, stage but don't commit
        Default: Leave private.

        **Promote semantics = COPY snapshot, not move.**
        - `.hermes/handoff/` remains the live working set and keeps evolving.
        - `docs/handoff/` receives a copy with `frozen: true` added to each
          file's frontmatter. Skills MUST NOT re-touch frozen files on
          subsequent runs; they are a historical snapshot for humans / PR review.
        - To publish a new snapshot later, promote again → overwrites the frozen copy.

        If "commit now" chosen, offer default message
          "docs(handoff): <slug> — <status>"
        and let user edit before running git commit.

Step 5  Final message
        Summary of what was written + explicit next actions for the successor.
```

## 9. Anti-Hallucination Invariants

Both skills must obey:

1. **No claims without evidence.** "Completed X" is written only if `git log` or a tool-call record confirms X. Otherwise write "attempted X, unverified".
2. **`last_verified` timestamp is required.** If reality-check was skipped, mark it explicitly: `last_verified: SKIPPED`.
3. **`todo` items are never dropped implicitly.** Open items on hand-off carry over verbatim; closed items are removed only if the corresponding commit / evidence is present.
4. **Walkthrough is written last**, after all mutations are done, so it reflects the final state — not intermediate.
5. **On take-over conflict, apply §9b tiered handling.** Hard conflicts halt via `clarify`; soft conflicts are logged to `open-questions.md` with a `⚠️ stale` tag and loading continues. Never silently reconcile away a hard conflict.

## 9a. Smart Cleanup (confidence-based auto-approval)

Modeled on Hermes' "Smart" dangerous-command mode: hand-off must compress living documents (`walkthrough.md`, `open-questions.md`, `review.md`) but must not delete anything it isn't sure about. Every candidate entry is classified into one of four buckets:

| Verdict | Action | Requires |
|---|---|---|
| **CLEAR** | Auto-delete or compress to one-line | Hard evidence the item is resolved (see criteria below) |
| **STALE** | Auto-delete | Long-untouched (>30 days) AND no reference in current `task.md` / `context.md` |
| **KEEP** | Retain verbatim | Marked as decision / surprise / lesson, or explicitly tagged for future reference |
| **UNSURE** | Batch-ask user at end of hand-off | Anything that fails CLEAR/STALE/KEEP criteria |

**Hard-evidence criteria for CLEAR** (any one suffices):
1. Files referenced in the item have been deleted (`git log --diff-filter=D` hit).
2. Error message referenced is absent from the last N successful runs.
3. Corresponding entry in `open-questions.md` is marked resolved.
4. Item body contains `Status: resolved` or a strikethrough marker.

**User interaction rule:** UNSURE items are presented as a **single batched prompt at the end of hand-off via `clarify`**, not per-item. Example:

```
Cleanup review: auto-removed 3 CLEAR + 2 STALE items.
Unsure about 2 items — keep or drop?
  [1] 2026-07-10 · Chrome portable path — still needed?
  [2] 2026-06-28 · Playwright version conflict — upgraded but unverified
```

**Audit trail:** every CLEAR/STALE removal is listed in the hand-off's final summary so the user sees what was cleaned. If uncertain, `hand-off` errs toward UNSURE over CLEAR.

## 9b. Take-Over Conflict Handling (tiered)

Mirrors the confidence-based philosophy of §9a. Every reality-check discrepancy is classified:

| Tier | Trigger | Action |
|---|---|---|
| **HARD** | Document claims "completed X" but no git/code evidence for X. Two handoff docs contradict each other. `context.md` invariant directly contradicts current code/config. | **HALT.** Present conflicts via `clarify` (structured choices): "trust doc / trust reality / user explains". Loading blocks until resolved. |
| **SOFT** | `last_verified` older than 7 days. Referenced file was renamed/moved but content intact. `session_id` not found in `session_search` (likely pruned). | Log to `open-questions.md` with `⚠️ stale` tag. Continue L1 load. Report count in take-over summary. |
| **AMBIGUOUS** | Fails both categorization tests. | Escalate to HARD (fail-safe). |

Reporting: take-over's final summary must state "N soft conflicts logged, M hard conflicts resolved" so the user always sees the reconciliation footprint.

## 10. Decision Points (All Resolved ✅)

| # | Question | Recommended default | Rationale |
|---|---|---|---|
| ① | Document format: YAML frontmatter + MD, or plain MD? | **✅ DECIDED: YAML frontmatter + MD** | Machine-scannable frontmatter enables cheap L1 pre-filter. |
| ② | `walkthrough` growth control? | **✅ DECIDED: single `walkthrough.md`, prune resolved items** | Living work-memory, not audit log. Resolved-issue entries are compressed/removed on hand-off. Long-term audit trail lives in git history + `session_search`, not here. |
| ③ | Git commit on hand-off (promote path only)? | **✅ DECIDED: ask via `AskUserQuestion` (`clarify`), then commit** | Private `.hermes/handoff/` is gitignored so N/A. Promote → `docs/handoff/` always prompts via the structured question tool with a default commit message; user can approve, edit, or skip. |
| ④ | On take-over conflict (docs disagree with git/code): halt vs auto-log to `open-questions.md`? | **✅ DECIDED: tiered — hard conflicts halt via `clarify`, soft conflicts logged with `⚠️ stale`, ambiguous → escalate to hard (fail-safe). See §9b.** | Consistent with §9a Smart Cleanup philosophy: confidence-based auto-approval; user only interrupted for the highest-signal cases. |

## 10a. User Interaction Rule

**All user-facing prompts issued by `hand-off` / `take-over` MUST use the `AskUserQuestion` tool (in Hermes: `clarify`) with structured `choices`**, not free-text messages. Applies to:

- promote-and-commit confirmation (③)
- Smart Cleanup UNSURE items (§9a)
- take-over conflict resolution (④)
- any point where the flow branches on user input

Rationale: structured choices render as pickable UI, avoid ambiguity from typed answers, and keep the agent's branching logic deterministic. Free-text is only appropriate for genuinely open-ended follow-ups (e.g. "why?").

## 11. MVP Scope

Ship the minimum that closes the loop:

- **Documents:** `context.md`, `task.md`, `walkthrough/*.md`, `open-questions.md` only. Skip `plan.md` and `review.md` for MVP — they're optional anyway.
- **Reality check:** `git status` + `git log -5` + `todo` diff. Skip smoke tests for MVP.
- **Layered load:** L1 mandatory, L2 on demand, L3 via `session_search`.
- **No auto-promotion** to `docs/handoff/` — always private scratch by default.
- **No branch-prefix** — single-branch assumption.

Expand only after the MVP feedback loop shows what's actually missing.

## 12. Implementation Layout (Decided)

Two sibling skills sharing this protocol as single source of truth:

```
skills/
  hand-off/
    SKILL.md              (session-close workflow; links here)
    references/protocol.md → pointer to ../../_shared/session-handoff/PROTOCOL.md
  take-over/
    SKILL.md              (session-resume workflow; links here)
    references/protocol.md → pointer to ../../_shared/session-handoff/PROTOCOL.md
  _shared/session-handoff/
    PROTOCOL.md           ← THIS FILE
    DECISIONS.md          (append-only log resolving ①②③④ and later choices)
    templates/            (context.md, task.md, walkthrough.md, open-questions.md — used by both skills)
```

Rationale: both skills are peers (neither is subordinate); protocol and templates deduplicated; future related skills (e.g. `session-audit`) can reuse the `_shared/` area.

## 13. Open Questions (Not Yet Decision Points)

- Should `context.md` be additive-only, or allowed to correct-in-place (with `walkthrough` entry recording the correction)?
- How does this interact with `subagent-driven-development`? Sub-agents don't currently write handoff docs — should orchestrators propagate context to them?
- Any hook for auto-suggesting `hand-off` when context window > 75%? (Runtime-dependent; may not be portable.)
- Concurrent hand-off from two live sessions writing to the same `.hermes/handoff/` — MVP assumes serial execution; needs a lock file or timestamp-based conflict prompt in v2.
- Multi-branch layout — prefix with branch (`.hermes/handoff/<branch>/…`); deferred (see §5 caveat). Reintroduces `branch:` frontmatter field.
- `next_agent` claim protocol — currently no way to signal "I'm about to pick this up"; if collaborative workflows appear, add a claim step.
- Dry-run mode for `hand-off` — print diff of every file it would write, confirm via `clarify` before landing. Useful especially for first Smart Cleanup run on a project.

## 14. References

- `../../plan-mode/SKILL.md` — **prior art / inspiration only**. Demonstrates the "write-only workflow" pattern this design extends into a bidirectional protocol. No runtime coupling: `hand-off` / `take-over` do not read `.hermes/plans/` or invoke `plan-mode`.
- `../../../spec/agent-skills-spec.md` — SKILL.md format the two implementing skills will conform to.
- Hermes primitives: `memory`, `todo`, `session_search`, `skill_manage`.
- `./DECISIONS.md` — append-only log of resolved design decisions; consult before proposing changes that touch ①②③④.

---

*End of PROTOCOL.md. Status: v0.2 (2026-07-16 rev-2) — MVP simplifications applied. Next step: draft `skills/hand-off/SKILL.md` and `skills/take-over/SKILL.md` referencing this file.*
