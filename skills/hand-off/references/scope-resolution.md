# Scope Resolution & Selection

> Loaded by hand-off when the agent needs to resolve which scope a command targets, or when `list-scopes` returns 0 / N > 1 results.

## What is a "scope"?

A scope is any directory containing at least one file whose YAML frontmatter carries a recognised `kind` value (`context` / `task` / `walkthrough` / `questions` / `plan` / `review`). The kind-based check avoids false positives from arbitrary `context.md` / `task.md` files in generic projects — the directory qualifies **only** if the frontmatter markers are present.

**Scope is defined by the task's range, not by directory role.** Neither "one per skill" nor "always repo root" is a rule; the agent and user negotiate per task:

- Refactor spanning the entire repo → scope at the repo root is appropriate.
- Rework limited to a subtree (`skills/`, a package dir, a feature module) → scope at that subtree's root.
- Multiple truly independent parallel tasks → separate scopes at each task's natural root.

## Discovering scopes

```bash
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

`list-scopes` enumerates every live scope under pwd neutrally — no canonical or "default" scope. Output is JSON; `scope_count` + `scopes[]` are the fields to read.

## `--scope` resolution rules

All commands except `write-atomic` and `list-scopes` take an optional `--scope <path>`. Resolution priority:

1. `--scope <path>` explicit — used verbatim.
2. No `--scope`, and **pwd itself contains recognised handoff docs** — pwd is used silently.
3. No `--scope`, pwd has no recognised handoff docs — script emits `WARNING`, prints `ambiguous_scope` JSON, and exits with code 3. **Agent must `clarify` with the user** before proceeding — either `init --scope <pwd>` to create a new scope, or specify an existing scope's path.

## Bootstrap decision matrix (Step 0)

| `list-scopes` result | Action |
| --- | --- |
| 0 scopes | `clarify` — init new scope at pwd? or point to existing scope path? |
| 1 scope at pwd | Silent use. |
| 1 scope not at pwd | Confirm the path with `clarify` before continuing (may not be what the user meant). |
| N ≥ 2 scopes | Present list via `clarify`, user picks one, pass as `--scope <path>`. |

## Batch operations

`validate`, `check-reality`, `clean-up`, `prepare` all accept `--all-scopes` to apply across every scope discovered under pwd. Output is wrapped as `{status, scope_count, scopes: [...]}`. Use batch mode when doing repo-wide audits; use single `--scope` for the normal per-task flow.

`init` and `write-atomic` are always single-target — batching them makes no semantic sense.
