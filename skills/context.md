---
kind: context
version: 1
last_updated: 2026-07-17T02:45:00+00:00
last_verified: 2026-07-17T02:45:00+00:00
last_agent: hermes-agent-devops
last_writer: hand-off
session_id: 2026-07-17-v05-adoption
status: in-progress
---

# Context & Invariants — `skills/` scope

> [!NOTE]
> This handoff scope is `skills/` because the current task's range is that directory (rev-B → rev-C rework of the `hand-off` / `take-over` skill pair and the shared session-handoff protocol).
> Context is additive-only. Never rewrite past invariants; add new ones.

## Task Scope Boundary

- **In scope:** `skills/hand-off/`, `skills/take-over/`, `skills/_shared/session-handoff/` — the session-handoff protocol trio.
- **Out of scope:** every other skill under `skills/` (37 unrelated skills), tooling, docs outside `skills/`.
- **Why `skills/` and not the repo root?** The rework touched only files under `skills/`; nothing in the repo root was modified.
- **Why not each skill sub-dir separately?** The three subdirs (`hand-off/`, `take-over/`, `_shared/session-handoff/`) are being changed **together** by the same rework — they share the reconcile.py script byte-identically and share protocol semantics. One coherent scope keeps the task's decisions co-located.

## Method Note: Scope Selection

Scope is defined by **task range**, not by directory role. Rules of thumb:

- One task spans one directory tree → one scope at the tree's natural root.
- Multiple truly independent tasks running in parallel → separate scopes.
- No policy: neither "every skill has its own scope" nor "always the repo root". Agent + user decide per task.
- `reconcile.py list-scopes` finds every live scope; nothing is "canonical".

## Repository

- **Repo:** `more-skills` (owner: `jinnnyang`, branch: `more`)
- **Root:** `C:\Users\jinnn\Documents\more-skills\`
- **Purpose:** Curated collection of custom skills for Hermes Agent. 39 skills total; most are functionally independent.
- **Host / shell / toolchain:** Windows 10; `terminal` runs bash via git-bash / MSYS. Python 3.11.11; `uv` at `/c/Users/jinnn/AppData/Local/hermes/bin/uv`; no `python3` shim.

## Session-Handoff Protocol Invariants (v0.5, rev-C · 2026-07-17)

1. **Every skill directory is self-contained.** No cross-skill file references; no `_shared/` runtime dependency. `skills/_shared/session-handoff/` is a **development snapshot only** and is not loaded by the skill runtime (prefix `_shared/` is ignored by the skill loader).
2. **Three-way byte-identical copies.** `scripts/reconcile.py` and each `templates/*.md` must be byte-identical across `skills/_shared/session-handoff/`, `skills/hand-off/`, and `skills/take-over/`. Verified by `diff -q` before commit.
3. **Scripts are the source of authority for behaviour.** All deterministic logic lives in `reconcile.py`.
4. **All CLI invocations run through `uv run`** (not bare `python`). Never pass `--isolated`.
5. **Primary evidence is git.** `git status --short` + `git log -N --name-only` are authoritative. `<session-tools-log>` is auxiliary.
6. **Lifecycle markers are explicit HTML comments** — `<!-- keep -->` and `<!-- resolved -->`, not free-text keywords.
7. **Two-phase cleanup.** `reconcile.py clean-up` requires `--dry-run` or `--apply`.
8. **Timezone-aware timestamps required.** Naive `datetime` is rejected.
9. **Flat file layout, no prefix.** Docs live directly in the scope directory as `context.md`, `task.md`, `walkthrough.md`, `questions.md`. **No `.hermes/handoff/` subdirectory.** **No `HANDOFF-` filename prefix.** The enclosing directory identifies the scope.
10. **Scope resolution is explicit-first.** `--scope <path>` wins; else pwd (silent) if pwd has recognised handoff kind frontmatter; else `WARNING` + exit-3 `ambiguous_scope`.
11. **Scope discovery is kind-based, not filename-based.** A directory qualifies as a scope only if it contains `*.md` files whose YAML frontmatter carries a recognised `kind` value from `{context, task, walkthrough, questions, plan, review}`. Prevents false positives from arbitrary `context.md` / `task.md` files.
12. **Questions have two states.** `questions.md` uses `## Open` and `## Closed` sections. `<!-- resolved -->` on an Open question **archives** it to `## Closed` (permanent, for historical review) — it is never deleted.

## Related Skills & Docs

- `skills/hand-off/{SKILL,PROTOCOL,DECISIONS}.md` — closing-side reference.
- `skills/take-over/{SKILL,PROTOCOL,DECISIONS}.md` — resume-side reference.
- `skills/_shared/session-handoff/` — development snapshot (v0.3 frozen protocol, current script + templates as SSOT for the byte-identical sync).
- `skill_view name=design-doc-review` — review methodology.
- `skill_view name=hermes-agent` — Hermes Agent CLI/config reference.
