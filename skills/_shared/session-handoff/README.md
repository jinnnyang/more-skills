# _shared/session-handoff — 开发底稿（NOT a skill）

> **Status:** 开发时正本（development source-of-reference）
> **不作为 skill 加载。** Skill loader 忽略 `_shared/` 前缀。
> **PROTOCOL.md 状态:** v0.3 全景快照，仅供参考。两个 skill 的 `PROTOCOL.md` 已演进为 v0.5-rev-C（flat-file layout, no HANDOFF- prefix, kind-based scope, question `## Open`/`## Closed` archive），是唯一权威。
> **scripts/ 状态 (2026-07-17 rev-D):** 已删除。3-way 同步纪律已放弃，`scripts/reconcile.py` 只在 `skills/hand-off/scripts/` 与 `skills/take-over/scripts/` 两处保持字节相同。见下文"同步纪律"。

---

## 用途

本目录是 `skills/hand-off/` 和 `skills/take-over/` 两个**独立自包含**技能的**手工同步参考底稿**：

- 两个技能实施**方案 A**（完全独立、目录自包含）
- 每个技能有各自的 `scripts/reconcile.py`（逐字复制）
- 每个技能有各自的 `PROTOCOL.md`（**视角改写**，只讲自身相关的部分）
- 每个技能有各自的 `DECISIONS.md`（**各自记录**，只记本技能关心的决策）
- 两个技能的 `templates/` 相同（逐字复制）

## 同步纪律（MVP：纯人工，2-way）

- **`scripts/reconcile.py` 改动 → 手动同步到两个 skill 目录**：改一处强制在同一个 commit 里附上另一处的 diff。两处应字节相同（`diff -q` 无输出）。`_shared/scripts/` 已在 rev-D 删除（曾漂移 57 行），不再作为第三份参考。
- **`PROTOCOL.md`**：本目录的 v0.3 快照**不再实时同步**。协议演进只在两个 skill 目录的 `PROTOCOL.md` 里做，遵循「视角改写」原则。
- **`DECISIONS.md`**：本目录的决策全集**不再实时同步**。新决策直接在相应 skill 目录记录。
- **`templates/*.md` 改动 → 两个 skill 逐字同步**。本目录的 `templates/` 保留为开发底稿。

未来 escalate 到 diff 脚本 / pre-commit hook 检查 `scripts/reconcile.py` 与 `templates/` 的两方漂移，见两个 skill 的 `PROTOCOL.md` §13。

## 目录内容

- `PROTOCOL.md` — 协议 v0.3 全景快照（参考底稿；权威版本在两个 skill 目录）
- `DECISIONS.md` — 决策日志历史全集（参考底稿；实际决策在两个 skill 目录追加）
- ~~`scripts/reconcile.py`~~ — 已删除 (rev-D)，权威副本在两个 skill 目录
- `templates/` — 模板底稿，两个 skill 逐字复制

## 不要

- **不要**在 `skills/hand-off/SKILL.md` 或 `skills/take-over/SKILL.md` 里引用本目录任何文件（技能必须自包含）
- **不要**从两个 skill 目录 symlink 到本目录
- **不要**把本目录当作某个技能加载
- **不要**继续同步 `_shared/PROTOCOL.md`——已冻结为 v0.3 历史快照

