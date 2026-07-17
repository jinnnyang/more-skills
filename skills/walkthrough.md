---
kind: walkthrough
version: 1
last_updated: '2026-07-17T07:00:00+00:00'
last_verified: '2026-07-17T07:00:00+00:00'
last_agent: ark-code-latest via Hermes/devops
last_writer: hand-off
session_id: rev-D-close-out-20260717T145717
status: phase-complete
---

# Living Work Memory & Walkthrough — `skills/` scope

> [!NOTE]
> Entry header format: `## YYYY-MM-DD — <slug>` (required for cleanup classifier).
>
> Lifecycle markers:
> - `<!-- keep -->` or keywords `lesson` / `surprise` / `decision` / `invariant` in header → KEEP forever.
> - `<!-- resolved -->` → CLEAR on next hand-off.
> - No marker + age > 30 days + not referenced from task/context → STALE.
> - Anything else → UNSURE (batched confirmation before deletion).

## History of Active Entries

## 2026-07-17 — v0.5-rev-C: scope is task-defined, not directory-role-defined <!-- invariant -->

**Decision.** Discarded prior notion that scope must live at a "canonical" location (repo root, or per-skill directory). Scope is defined by the **task's range** and is agent+user negotiated. For the session-handoff protocol rework, the scope is `skills/` because that's what the task modifies — nothing in the repo root, no independent per-skill agenda.

**Rationale.** User pushback: "这一套方法是有明确范围的，取决于我们讨论的范围、处理任务的范围... 说白了，这个是一套方法，不是死板的程序。" `list-scopes` now enumerates every live scope neutrally — no scope is "canonical" or "default"; agents pick per task with the user.

**Impact on SKILL.md.** The Bootstrap Step in `hand-off` and `take-over` SKILLs must **not** suggest "each skill gets one" or "root is the default". It must say "agent negotiates scope with user based on task range; `list-scopes` shows options".

## 2026-07-17 — Flat-file layout with no filename prefix <!-- decision -->

**Decision.** `HANDOFF-` filename prefix retired. Docs live as `context.md`, `task.md`, `walkthrough.md`, `questions.md` — enclosing directory identifies which scope they describe. `.hermes/handoff/` subdirectory also retired (rev-B legacy).

**Rationale.** User pushback: "为什么每个文件前面都要加一个 HANDOFF ？？？？？不需要啊，这个完全没有意义... 这几个文件在那个目录就是描述的哪个目录，自解释自包含。"

**Implication.** Scope discovery cannot rely on filename patterns. Rev-C introduces **kind-based scope detection** — a directory qualifies as a scope only if one of its `context.md` / `task.md` / `walkthrough.md` / `questions.md` / `plan.md` / `review.md` files has YAML frontmatter with a recognised `kind` value. Prevents false positives from unrelated `context.md` files in arbitrary projects.

**Files changed.**
- `skills/_shared/session-handoff/scripts/reconcile.py` — constants (`DEFAULT_DOCS`, `VALID_KINDS`), removed `DOC_PREFIX` and `TEMPLATE_MAP`, added `_peek_kind()`, updated `scope_has_docs()`, `find_scopes()`, all filename literals
- `skills/_shared/session-handoff/templates/questions.md` — renamed from `open-questions.md`; restructured to `## Open` + `## Closed`
- `skills/{hand-off,take-over}/scripts/reconcile.py` + templates — synced byte-identical

## 2026-07-17 — Questions archive semantics: <!-- resolved --> moves to ## Closed <!-- decision -->

**Decision.** `<!-- resolved -->` on a question no longer deletes it. Instead, the next `hand-off clean-up --apply` **archives** the entry into `## Closed` — a permanent history section within the same file. Choice (A) from a two-option prompt: "永久保留，便于历史回顾".

**Implementation.** `classify_cleanup()` in `reconcile.py` now returns a fifth bucket `archived` (in addition to `clear` / `stale` / `kept` / `unsure`). `apply_cleanup()` reads that bucket + calls new `_rebuild_questions_body()` which surgically moves the entries from `## Open` to `## Closed`. Sections in the rebuild are `##` for Open/Closed top-level, `###` for individual questions. The section regex was extended from `##` to `#{2,3}` to pick up entry-level headers.

**Also affected.** `apply_soft_conflicts` (used by `take-over check-reality --apply-soft-conflicts`) now writes SOFT conflicts as `### Soft conflict · <type> · <timestamp>` entries under `## Open` (used to write a bulleted list under a legacy `## Soft Conflicts (Reconciled)` section).

**Smoke test verified.** A `questions.md` with mixed Open/Closed sections and a `<!-- resolved -->` marker on one Open Q was cleanly archived by `clean-up --apply`; existing Closed entries preserved; Open still contains the unresolved ones + placeholders.

## 2026-07-17 — Rev-C script bugfixes carried in <!-- decision -->

**Decisions carried from rev-C:**
- `write-atomic --content-file` now resolves MSYS `/tmp/...` and `/c/...` paths via `resolve_msys_path` on both `--filepath` and `--content-file` args.
- `<session-tools-log>` regex is line-anchored (`^<session-tools-log>\s*$` + `re.MULTILINE`) so prose mentions of the tag names in walkthrough decision entries no longer hijack the match.

Both bugs originally caught by the rev-B eat-your-own-dogfood test on this repo.

## 2026-07-17 — rev-D: CRITICAL fixes before independent-development split <!-- decision -->

**Decision.** Pre-split design-doc review of `hand-off` and `take-over` (both v1.3.0 SKILL / v0.3-rev-A PROTOCOL) surfaced 3 CRITICAL findings that would cause the first divergent commit to introduce a protocol-vs-SKILL contradiction. Fixed atomically before opening independent development.

**Findings & fixes (all in the same commit):**
1. **C1** — `take-over/PROTOCOL.md` §7 code-fence structure was broken (an orphan closing fence after Step 2 leaked Steps 3–7 out of the code block, and a second lonely fence appeared at line 196). Repaired to a single fence enclosing Step 0–7. Fence count 9 → 8, even and balanced.
2. **C2** — SOFT-conflict landing site was inconsistent across `take-over/PROTOCOL.md` §7 Step 2 (L159), §7 Step 5 (L181), §9 rule 7 (L210). Two of them still named the legacy `## Soft Conflicts (Reconciled)` / `## Soft Conflicts` section (rev-B). Unified all three to the rev-C canonical form — `questions.md` § Open, entries as `### Soft conflict · <type> · <timestamp>`. Now aligned with `take-over/SKILL.md` L120/L146/L167, `hand-off/PROTOCOL.md` §9b L248, and DECISIONS R19+R20.
3. **C3** — `hand-off/PROTOCOL.md` L134 and `take-over/PROTOCOL.md` L136 still wrote `uv run --isolated python …`, contradicting SKILL.md and DECISIONS R16 ("do not pass `--isolated`"). Both lines rewritten to `uv run <SKILL_DIR>/scripts/reconcile.py …` with the negative guidance inline. R16 履历 preserved.

**W2 (also landed this session):** `_shared/session-handoff/scripts/` deleted (Q2 resolution). Was drifted 57 lines behind the hand-off/take-over copies at rev-D verification. `_shared/session-handoff/README.md` updated: 3-way sync discipline → 2-way; scripts/ marked deleted; templates/ still shared as reference.

**Files changed.**
- `skills/hand-off/PROTOCOL.md` — 1 line (C3)
- `skills/take-over/PROTOCOL.md` — 6 lines (C1 fence + C2 three sites + C3)
- `skills/_shared/session-handoff/README.md` — rev-D header + 2-way sync rewording (W2)
- `skills/_shared/session-handoff/scripts/reconcile.py` — DELETED (W2)

**Verification.**
- `grep -c '^\`\`\`'` on `take-over/PROTOCOL.md`: 8 (even, balanced).
- `grep -rn 'Soft Conflicts (Reconciled)\|## Soft Conflicts' skills/hand-off skills/take-over` → empty.
- `grep -rn '\-\-isolated' skills/hand-off/SKILL.md skills/take-over/SKILL.md skills/hand-off/PROTOCOL.md skills/take-over/PROTOCOL.md` → only negative-guidance mentions remain; DECISIONS R16 still records the history.

**Downstream.** WORTH findings (W1 docs/handoff supersede, W3 decision-ID mirror discipline, W4 R17 重号, W5 MIRROR block, W6 list-scopes depth, W7 no-git fallback) and SMALL findings deferred to independent-development phase. Session concludes with the two skills internally consistent and ready to diverge.

## 2026-07-17 — rev-D close-out: this scope archived <!-- decision -->

**Decision.** The `skills/` handoff scope is closed. All rev-B → rev-C rework tasks committed (see 0c56a9a, 0df58cf); rev-D CRITICAL fix committed atomically with this hand-off. Both remaining open questions (Q1/Q2) resolved and archived to `## Closed`.

**Rationale.** The two skills are now sufficient to enter independent-development phase without a session-wide coordination scope. Any future work on `hand-off/` or `take-over/` in isolation will spin up its own scope at that subtree if needed. This scope becomes historical.

---

<session-tools-log>
[]
</session-tools-log>
