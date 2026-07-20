---
kind: context
version: 1
last_updated: 2026-07-20T03:15:00+00:00
last_verified: 2026-07-20T03:15:00+00:00
last_agent: Hermes Agent (ark-code-latest)
last_writer: take-over
session_id: sess-20260720-make-soul-refactor
status: in-progress
---

# Project Invariants & Context

> [!NOTE]
> This file contains invariants, credentials locations, environmental variables, and project constraints that must never break.
> This document is strictly additive-only. Add corrections as new dated entries at the bottom.

## Project Description

- **Skill name**: `make-soul` (renamed from upstream `soul-md-creator`)
- **Purpose**: Anthropic-style Claude Skill that helps users author `SOUL.md` files for OpenClaw agents (create, rewrite, refactor, publish-ready, alignment).
- **Source**: Copied from `~/Downloads/souls-directory/skills/soul-md-creator/` on 2026-07-20; 4 files, 405 lines total.
- **Current phase**: Refactoring per **Plan B (Restructure)** decided on 2026-07-20.

## Refactor Decisions (2026-07-20)

Selected direction after diagnostic pass on the copied files:

1. **Plan B — Restructure**. Reorganize `SKILL.md` around four verbs: **Discover → Draft → Stress-Test → Deliver**.
2. **Rename frontmatter**: `name: soul-md-creator` → `name: make-soul`. Update `description` to match the new scope.
3. **Frontmatter dialect**: keep Anthropic Skill style (`name` + `description` only). Do NOT switch to Hermes multi-field frontmatter — this skill targets OpenClaw / Claude ecosystem consumers.
4. **Operating Modes** collapse from prose section into a 3-column decision table at the top of `SKILL.md` (input → mode → key emphasis).
5. **Discovery Patterns A/B/C** merge into a single "Discover" step; the three patterns become branches inside that step, not siblings.
6. **Writing Rules ∪ Anti-Patterns**: consolidate into ONE red-line list in `SKILL.md`; move the elaborated rationale to `references/persona-research-heuristics.md`.
7. **New reference**: `references/deliverable-format.md` — canonical output shape (rationale block, fenced SOUL.md body, optional IDENTITY.md, 3 test prompts).
8. **Reference count** after refactor: 4 files (was 3).
9. **Read-before-drafting gating**: consolidate into ONE table near the top of `SKILL.md`; remove the duplicated Reference Map at the bottom.
10. **Target size**: `SKILL.md` ≈ 100 lines (from 192); each reference ≤ 90 lines.

## Invariants & Rules

- **Do not break Anthropic Skill frontmatter**. The `name` and `description` fields must be parseable and the description must remain a single terse sentence (Anthropic Skills use it as the retrieval hook).
- **Do not weaken OpenClaw semantic content**. Structure changes are fine; the underlying advice about Core Truths / Boundaries / Vibe / Continuity, anti-sycophancy, and publishing rules must survive intact.
- **Original file is preserved upstream** at `~/Downloads/souls-directory/skills/soul-md-creator/`. This copy is the working refactor target — safe to rewrite freely.

## Environment & Build

- **Env variables**: none required.
- **Build/Test commands**: none — pure documentation skill. Verification is human review + optional `frontmatter` YAML lint.

## Invariant Corrections Log

- None.
