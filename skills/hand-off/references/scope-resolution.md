# Scope resolution and selection

> Loaded during hand-off whenever the agent needs to figure out which scope a command should target, or when `list-scopes` comes back with 0 or with N ≥ 2 results.

## What counts as a "scope"?

A scope is any directory that holds at least one file whose YAML frontmatter carries a recognised `kind` value (`context` / `task` / `walkthrough` / `questions` / `plan` / `review`). Checking `kind` rather than filename avoids false positives from projects that happen to have their own `context.md` or `task.md`. The directory only qualifies once the frontmatter markers are actually there.

**Scope is defined by the task's range, not by directory role.** There's no rule that says "one scope per skill" or "always the repo root". You and the user pick per task:

- A refactor that spans the entire repo → a scope at the repo root is the right call.
- Work confined to a subtree (`skills/`, a package directory, a feature module) → put the scope at that subtree's root.
- Several genuinely independent tasks running in parallel → give each one its own scope at whatever root feels natural to it.

## Discovering scopes

```bash
uv run <SKILL_DIR>/scripts/reconcile.py list-scopes
```

`list-scopes` enumerates every live scope under pwd without picking favourites. There is no canonical or "default" scope. Output is JSON, and the two fields worth reading are `scope_count` and `scopes[]`.

## `--scope` resolution rules

Every command except `write-atomic` and `list-scopes` accepts an optional `--scope <path>`. Resolution order:

1. Explicit `--scope <path>` — used verbatim.
2. No `--scope`, and pwd itself contains recognised handoff docs → pwd is used silently.
3. No `--scope`, and pwd has no recognised handoff docs → the script emits a `WARNING`, prints `ambiguous_scope` JSON, and exits with code 3. Don't guess your way past this. Run `clarify` and let the user decide: `init --scope <pwd>` to create a new scope here, or point at an existing scope by path.

## Bootstrap decision matrix (Step 0)

| `list-scopes` result | Action |
| --- | --- |
| 0 scopes | `clarify` — init a new scope at pwd, or point at an existing scope path? |
| 1 scope at pwd | Silent use. |
| 1 scope not at pwd | Confirm the path with `clarify` first — it might not be the scope the user had in mind. |
| N ≥ 2 scopes | Show the list through `clarify`, let the user pick, then pass the choice as `--scope <path>`. |

## Batch operations

`validate`, `check-reality`, `clean-up`, and `prepare` all accept `--all-scopes` to run across every scope discovered under pwd. The wrapped output shape is `{status, scope_count, scopes: [...]}`. Batch mode is the right tool for a repo-wide audit; for the ordinary per-task flow, stick with a single `--scope`.

`init` and `write-atomic` are always single-target. Batching them doesn't have a meaningful interpretation, so they simply don't accept `--all-scopes`.
