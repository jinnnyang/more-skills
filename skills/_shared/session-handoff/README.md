# _shared/session-handoff — 开发底稿（NOT a skill）

> **Status:** 开发时正本（development source-of-reference）
> **不作为 skill 加载。** Skill loader 忽略 `_shared/` 前缀。

---

## 用途

本目录是 `skills/hand-off/` 和 `skills/take-over/` 两个**独立自包含**技能的**手工同步参考底稿**：

- 两个技能实施**方案 A**（完全独立、目录自包含）
- 每个技能有各自的 `scripts/reconcile.py`（逐字复制）
- 每个技能有各自的 `PROTOCOL.md`（**视角改写**，只讲自身相关的部分）
- 每个技能有各自的 `DECISIONS.md`（**各自记录**，只记本技能关心的决策）
- 两个技能的 `templates/` 相同（逐字复制）

## 同步纪律（MVP：纯人工）

- **`scripts/reconcile.py` 改动 → 手动同步到两个 skill 目录**：改一处强制在同一个 commit 里附上另一处的 diff。
- **`PROTOCOL.md` 通用章节（§1–§3、§12–§14）改动 → 两个 skill 各自视角下都需更新**。
- **`DECISIONS.md`** 只在**跨切面决策**（如 ① 格式、③ commit 策略）时两边同步；单侧决策（② walkthrough 是 hand-off 关心，④ conflict tiering 是 take-over 关心）只写到相应 skill 目录。
- **`templates/*.md` 改动 → 两个 skill 逐字同步**。

未来 escalate 到 diff 脚本 / pre-commit hook 检查漂移，见 `PROTOCOL.md` §13。

## 目录内容

- `PROTOCOL.md` — 协议全文（v0.3），作为两个 skill 视角改写的参考底稿
- `DECISIONS.md` — 决策日志全集，作为两个 skill 各自记录的参考底稿
- `scripts/reconcile.py` — 参考实现，两个 skill 逐字复制
- `templates/` — 模板底稿，两个 skill 逐字复制

## 不要

- **不要**在 `skills/hand-off/SKILL.md` 或 `skills/take-over/SKILL.md` 里引用本目录任何文件（技能必须自包含）
- **不要**从两个 skill 目录 symlink 到本目录
- **不要**把本目录当作某个技能加载
