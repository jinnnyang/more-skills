---
name: take-over
description: |
  Pick up where the previous session stopped, without amnesia. Loads the handoff docs left by the companion `hand-off` skill, checks they're actually usable (acceptance review), cross-checks what they claim against `git status` / `git log`, and restores the todo list. Triggers on "接着之前的做" / "continue previous work" / "resume", or when the skill is auto-loaded and a handoff scope already exists at pwd.
version: 1.4.0
author: 刘工 + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-handoff, workflow, take-over, context-restore]
    related_skills: [hand-off, plan]
---

# Session Take-Over Skill

Pick up where the previous session stopped, without amnesia.

## 90-second mental model

The previous session (or an agent, or you yourself) ran the companion `hand-off` skill before stopping. That left four short files (`context.md` / `task.md` / `walkthrough.md` / `questions.md`) in a **scope directory** — usually pwd, sometimes a subtree. `take-over` picks that up.

Three things happen, roughly in order:

1. **Discover** — find the scope. Zero, one, or several may exist; you ask the user only when it's genuinely ambiguous.
2. **Verify** — an *acceptance review* checks the docs aren't empty templates, then a *reality check* cross-references what the docs claim against `git status` / `git log`. Anything that looks wrong gets tiered: HARD conflicts halt loading, SOFT conflicts get logged to `questions.md` and you continue.
3. **Restore + summarise** — parse `task.md`'s checklist into the runtime `todo`, greet the user with "here's where we are, what would you like to focus on".

If pwd has no handoff docs and the user clearly wasn't asking to resume, exit silently. Never invent state.

The rest of this file is the walk of that flow (Steps 0–7). Skip to §"Take-Over Execution Workflow" if you know the model already.

## Overview

This skill implements the **take-over** half of the Session Handoff Protocol (v0.5, flat-file layout). It is self-contained: everything it needs lives under this skill's directory. See `PROTOCOL.md` for the protocol reference; see `DECISIONS.md` for the design decision log.

The companion skill `hand-off` implements the closing side of the protocol. Each skill is independently installable.

## Prerequisites

- **`uv`** — required. Runs the helper Python script via `uv run …` and relies on inline script metadata to auto-install `pyyaml`. Check with `command -v uv`.
- **`git`** — required for reality-check (`git status`, `git log`).
- **Python ≥ 3.11** — resolved automatically by uv.

### Path convention on Windows / MSYS

On Windows hosts running through MSYS / git-bash, `uv run` receives paths through Windows' argv layer, NOT the MSYS translation layer. Always pass **native `C:\Users\...` paths** to `uv run <SKILL_DIR>/scripts/reconcile.py` — the MSYS-style `/c/Users/...` form will fail with `系统找不到指定的路径 / cannot find the path specified`. The script itself internally accepts both styles for `--scope` and `--filepath` (via its MSYS translation), but the script path handed to `uv run` must be native.

Correct:
```
uv run 'C:\Users\me\skills\take-over\scripts\reconcile.py' list-scopes
```

Incorrect (fails on Windows/MSYS):
```
uv run '/c/Users/me/skills/take-over/scripts/reconcile.py' list-scopes
```

## When to Run This Skill

The skill runs when **any** of the following signals appear in the user's initial message for this session:

- The literal skill invocation marker: `[IMPORTANT: The user has invoked the "take-over" skill…]`.
- User keywords (Chinese or English): `继续` / `接着` / `接着之前的做` / `继续之前` / `handoff` / `take-over` / `continue previous work` / `resume`.
- The runtime auto-loaded the skill as part of a hook and pwd contains at least one recognised handoff scope (verified via Step 0).

If none of the above signals is present — for instance the user asked an unrelated question and the skill happened to load — **exit silently at Step 0** without initializing anything, and let the agent answer the actual request.

## Layout (v0.5 flat-file, no prefix)

Handoff documents live **directly** in the working scope directory using their natural short names:

```
<scope>/context.md
<scope>/task.md
<scope>/walkthrough.md
<scope>/questions.md
```

The enclosing directory identifies what the docs describe — no filename prefix. A "scope" is any directory where at least one of these files has YAML frontmatter with a recognised `kind` value.

### Choosing a Scope

**Scope is defined by the task's range, not by directory role.** The agent and user negotiate per task: repo root for cross-cutting reworks; a subtree root when the task is limited to that subtree; separate scopes for truly independent parallel tasks.

Discover live scopes:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

## Scope Resolution

Most commands take an optional `--scope <path>`:

1. `--scope <path>` — used verbatim (explicit wins).
2. No `--scope`, and pwd contains recognised handoff docs — pwd used silently.
3. No `--scope`, pwd has no handoff docs — script emits `WARNING`, prints `ambiguous_scope` JSON, exits with code 3. **Agent MUST clarify with the user** before proceeding (see §0a).

Batch operations (`validate`, `check-reality`, `review-handoff`, `clean-up`) accept `--all-scopes` for repository-wide analysis.

---

## §0a · Yield-Turn Fallback Protocol (Choice Tool Fallback Rule)

This skill asks the user a structured question at several branch points. How it looks depends on what the runtime provides.

**When `clarify` / `AskUserQuestion` / `ask_question` is available**, use it with typed `choices`. That's the deterministic path — no ambiguity, the user picks and you continue.

**When no such tool exists**, fall back to a plain Markdown numbered list and yield the turn. Five rules, verbatim:

1. **Preamble is allowed but capped.** ≤ 3 short lines of plain-text context are allowed *before* the numbered list (e.g. "No handoff docs were found in the current directory."). Don't narrate; state the situation.
2. **The list is the last thing you emit.** After the numbered list, produce **zero** further tokens and **zero** tool calls in the same turn. Yield control immediately.
3. **A legal numeric reply from the user is authoritative.** If the user's next message is `1` / `2` / `3` etc. matching an offered option, execute the chosen branch directly — do NOT re-confirm ("You picked 1, are you sure?" is forbidden). This applies to every fallback prompt in this skill.
4. **Illegal replies loop back.** If the reply is not a legal number and not another obviously-recognisable choice, restate the same numbered list once more and yield again.
5. **Tool-availability check is a search, not a guess.** "No structured question tool" means you scanned the exposed tool list and found no entry whose name matches `clarify` / `ask_question` / `AskUserQuestion` / `ask_user_question`. Assume the tool exists unless you've positively confirmed it doesn't.

The preamble cap (≤ 3 lines) applies to fallback mode only. When `clarify` is available, the tool's own preamble field is used and rule 1 does not apply.

---

## Take-Over Execution Workflow

All Python invocations use `uv run <SKILL_DIR>/scripts/reconcile.py …` where `<SKILL_DIR>` is the directory of this SKILL.md file. Do not pass `--isolated`.

### Step 0 · Bootstrap & Scope Discovery

```bash
command -v uv && command -v git
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

Branch based on what `list-scopes` returns AND the "When to Run" signals above.

#### Case A · `list-scopes` returns one or more scopes

- **Exactly one scope** → use it as `--scope <path>` for every subsequent step. Proceed to Step 1.
- **Multiple scopes** → present the list and ask the user (§0a) which to resume from. Store the chosen path.

Skip Step 0.5 (init branch does not apply). Go to Step 1.

#### Case B · `list-scopes` returns zero scopes

Determine whether the user *actually asked to resume* per "When to Run":

- **No resume signal detected** → exit take-over silently. Do not initialize files, do not prompt. Let the outer conversation proceed to the user's real request.

- **Resume signal present, pwd is completely empty** (only `.git/` and the take-over invocation marker files) → ask the user (§0a):
  1. Initialize a new empty scope here at pwd
  2. Specify a different path to initialize at
  3. Exit — no prior handoff to resume from

- **Resume signal present, pwd is non-empty but has no handoff docs** (user is clearly working in this directory but no scope exists yet) → this is the **most common first-time bootstrap path**. Ask a single yes/no rather than a three-way choice:
  1. Initialize a new scope here at pwd (recommended)
  2. Exit — I'll pick this up later

  Default to option 1; the fallback numbered list still applies per §0a.

If the user chose init, run:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py init --scope <path> --agent "<agent_name>" --session-id "<session_id>" --writer take-over
```

Then proceed to **Step 0.5 · Initial Context Seeding**.

### Step 0.5 · Initial Context Seeding (init branch only)

After `init` writes four skeleton files, the seeded templates still contain only placeholders (`- Brief overview:`, an empty `## Now`). Do **not** greet the user with the raw skeletons — the very message that triggered take-over is the best possible seed material for `context.md` and `task.md`.

Do the following, in order:

1. **Extract the user's intent** — re-read the initial user message that triggered this session. That message plus any obvious pwd signals (repo name, existing files, README) is your seed material.
2. **Write `context.md § Project Description`** — a one-paragraph, factual summary of "what this project is / what the user just said they want". Use `write-atomic` (or the standard file edit). Update the frontmatter's `last_writer` to `take-over` and `last_updated` to the current timestamp. `context.md` is otherwise additive-only, but populating an empty seed section is not "rewriting history".
3. **Write `task.md § Now`** — the first concrete `- [ ]` item derived from the user's intent. If the user's message was too vague to yield a task, write `- [ ]` followed by "Clarify project scope with the user" and note the ambiguity in `questions.md § Open`.
4. **Do NOT touch `walkthrough.md`** — it stays empty; the first real hand-off will populate it.

After seeding, run acceptance review with `--allow-fresh` to confirm the seed is usable:

```bash
uv run <SKILL_DIR>/scripts/reconcile.py review-handoff --scope <path> --allow-fresh
```

If it comes back `status: pass` or `status: fresh_init`, greet the user (see wording below and add the hand-off preview line). If it comes back `status: reject`, patch the reported issues and re-run — do not surface the raw review JSON to the user; the seeding step is take-over's own responsibility.

**Greeting after init + seeding**:

```
Initialized a new handoff scope at <path> and seeded it with your stated intent.
Frontmatter status enum for future edits: [in-progress | blocked | phase-complete | archived] (NOT "complete").
Next time you want to save progress say `先到这` / `handoff` / `continue later` — that triggers the companion `hand-off` skill.
Ready to work. What would you like to focus on first?
```

Then exit the take-over flow. Steps 1–7 do not apply to the init branch.

### Step 1 · Validate Handoff State

Frontmatter kind-enum + timestamp sanity:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py validate --scope <path>
```

`errors` in the JSON output are HARD conflicts — halt and surface via §0a-style clarify before loading any body content.

Freshness reference (used later in the summary):
```bash
git log -1 --format=%cI
```

### Step 1.5 · Handoff Acceptance Review

Before spending context on the docs' bodies, check that the previous session actually left something usable:

```bash
uv run <SKILL_DIR>/scripts/reconcile.py review-handoff --scope <path>
```

The helper returns `{"status": "pass" | "reject" | "fresh_init", "issues": [...]}`. Each `issues[]` entry carries `severity ∈ {REJECT, WARN, INFO}`, a machine-readable `kind`, and human-readable `detail` + `suggestion`.

What to do next depends on `status`:

- **`pass`** — continue to Step 2.
- **`fresh_init`** (only appears with `--allow-fresh`) — continue to Step 2, but remember to mention "fresh-init only" in the Step 7 summary so the user knows they're resuming from a bootstrap seed rather than a real prior session.
- **`reject`** — do NOT proceed to Step 2. Present the verdict to the user via §0a. Show:
  - A one-line summary of each REJECT issue (`<file>: <detail>` — do NOT dump the whole JSON).
  - Any WARN issues as a brief bullet list underneath.
  - Then a three-choice prompt:
    1. **Reject the handoff and stop** — take-over exits and reports back that the previous session's artifacts are incomplete. The user or the previous agent should re-run hand-off after fixing the issues before take-over is attempted again.
    2. **Have take-over remediate now** — enters the *Remediation Sub-flow* below, fixes each REJECT issue in place, re-runs `review-handoff`. Only when review returns `pass` (or `fresh_init`) does take-over continue to Step 2.
    3. **Force continue anyway** — user explicitly accepts the risk. Log each remaining REJECT issue into `<scope>/questions.md § Open` as a `### Acceptance override · <kind> · <timestamp>` entry (via `write-atomic`) so the risk is auditable, then continue to Step 2.

#### Remediation Sub-flow (option 2)

Take-over may modify the following in remediation mode, with these constraints:

| Issue kind | Allowed remediation |
|---|---|
| `template_tokens_unfilled` | Replace `{{TIMESTAMP}}` etc. with real values via `write-atomic`. |
| `context_description_empty` | Populate `## Project Description` using the current user message and pwd inspection (README, package.json, etc.). This does **not** violate `context.md`'s additive-only rule because the section was a template stub, not prior content. |
| `task_list_empty` | Populate `## Now` with at least one concrete `- [ ]` item derived from the user's intent. If ambiguous, write "Clarify project scope with the user" and log the ambiguity to `questions.md § Open`. |
| `cross_reference_missing` | If the referenced file (`plan.md` / `review.md`) is truly needed, ask the user (§0a) whether to create a stub or remove the dangling reference. Do not silently invent content. |
| `frontmatter_invalid` / `frontmatter_parse_error` | Fix the frontmatter mechanically (enum coercion, timezone insertion) if the fix is obvious; otherwise escalate to the user. |
| `fresh_init_only` | Not a code-level issue — resolved by adding real content to `context.md` and `task.md` (i.e. by fixing the other issues). |

After every remediation write, re-run `review-handoff --scope <path>` and loop until it returns `pass` (or `fresh_init`), with a maximum of **3 remediation passes** — if the review still rejects after 3 passes, fall back to the three-choice prompt above and default to option 1.

### Step 2 · Reality Check & Reconciliation

Offload reconciliation to the helper, appending any SOFT conflicts to `questions.md`:
```bash
uv run <SKILL_DIR>/scripts/reconcile.py check-reality --scope <path> --apply-soft-conflicts --session-id "<session_id>" --agent "<agent_name>"
```

- Parse the JSON output — `hard_conflicts`, `soft_conflicts`, `applied_soft_conflicts` (count of SOFT entries appended under `## Open` in `questions.md` as `### Soft conflict · …` subsections).
- Handling per §9b of `PROTOCOL.md`:
  - HARD → skip Step 3; jump to Step 5 conflict resolution.
  - SOFT → already logged; continue to Step 3.

### Step 3 · Layered Load

To control context usage:

- **L1 (Always Load)**: `context.md`, `task.md`, `questions.md`. Note that the `check-reality` command outputs `recent_walkthroughs` (the top 3 headers of `walkthrough.md`). You **MUST** read and display these headers as part of L1 loading so you are aware of the most recent sessions' change topics.
- **L2 (Load on Demand)**: `plan.md` or `review.md` only when the current task references them (heuristic: if `task.md` body contains the literal string `plan.md` or `review.md`).
- **L3 (Reference Only — Do NOT Auto-load)**: `walkthrough.md` is a living memory dump. Do not auto-load; only inspect when deep-diving into a specific past decision shown in L1. `session_search` is often preferable.

### Step 4 · Restore Checklist

Parse `task.md`'s open tasks and populate the agent runtime `todo` list.

**Reordering note**: if Step 6 (plan-mode coexistence) imports `plan.md`, re-run Step 4 against the updated `task.md` before the Step 7 summary.

### Step 5 · Conflict Handling

Handle Step 2 discrepancies per tier (§9b of `PROTOCOL.md`):

- **HARD** (e.g. claimed task done but no Git/code evidence): halt loading. Present via §0a-style clarify with options: *Trust Handoff Docs / Trust Git Reality / User Explains*.
  - **Concurrency Lock Conflict**: If the hard conflict is a stale lock file (`concurrency_lock_conflict`), prompt the user: "A stale session lock was found. Would you like to force release the lock?" If they agree, run `uv run <SKILL_DIR>/scripts/reconcile.py unlock --scope <path>` to remove it, and restart the take-over process.
  - **Non-interactive fallback:** In CI/CD or non-interactive environments, do not attempt to wait or pause. Immediately write the conflict details to `<scope>/conflict_pending.json` via `write-atomic` and terminate execution with a descriptive error message.
- **SOFT** — already logged as `### Soft conflict · …` entries under `## Open` in `questions.md` by Step 2. Nothing more to do here; the summary will report the count. To close a SOFT entry once addressed, mark it with `<!-- resolved -->` — the next `hand-off` will archive it to `## Closed`.
- **AMBIGUOUS** — the helper escalates these to HARD (fail-safe).

### Step 6 · Plan-Mode Coexistence Check

If `.hermes/plans/` exists (plan-mode planning artifacts):

- Do NOT auto-merge.
- Prompt the user via §0a-style clarify:
  - *Ignore (default)*: keep plan-mode and handoff scopes independent.
  - *Import plan.md*: copy plan-mode's `plan.md` to `<scope>/plan.md` (one-shot via `write-atomic`). **Task Sync:** If this option is chosen, the agent must read the imported `<scope>/plan.md`, extract any tasks, format them and append them to `<scope>/task.md` using `write-atomic`, and only then re-run Step 4.
  - *Show diff*: compare plan-mode artifacts first.

If import chosen, re-run Step 4 against the updated `task.md`.

### Step 7 · Summary Report to User

Print a resume greeting:
```
Scope: <path>
Previous agent: <last_agent>. Last verified: <last_verified_timestamp>.
Acceptance review: <pass | fresh_init | force-continued (with N overrides)>.
N soft conflicts logged (see questions.md ## Open § Soft conflict), M hard conflicts resolved.
[If N <= 3, list the soft conflicts here, e.g. "• ⚠️ last_verified is 10 days old"]
Done: ...
Now/Next: ...
Blocked on: ...

Next hand-off trigger: say `先到这` / `handoff` / `continue later` to hand off progress via the companion `hand-off` skill.
```

If `list-scopes` returned multiple scopes, mention the others as one-liners so the user can pivot later if they want.

Ask the user where they would like to resume or what task to focus on first.

---

## Companion & References

- Companion skill (closing side): `hand-off` — each is independently installable; they share protocol semantics but not files.
- `PROTOCOL.md` (this directory) — protocol reference from the take-over perspective.
- `DECISIONS.md` (this directory) — design decision log (take-over relevant subset).
- `references/frontmatter-fields.md` (this directory) — enum values for `kind` / `status` / `last_writer` and timestamp format rules. Consult before hand-editing frontmatter.
- `references/adr-and-decisions.md` (this directory) — full playbook on why this skill maintains an ADR log, how to write a compliant entry, and worked examples from this skill's own history. Read this before proposing changes to `DECISIONS.md`.
- `templates/` (this directory) — default document templates, seeded by `scripts/reconcile.py init`.
