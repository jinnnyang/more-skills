# Phase 1: 调研任务板规划 (Task Board Planning)

本阶段指导智能体将复杂的调研课题拆分为具体的子任务，分配递归探索参数（深度与宽度），更新看板并执行首次 Git 提交。

---

## 1. 任务分解、递归参数与前置上下文分配

根据在 P0 Intake 阶段与用户确认的调研范围，将课题拆分为 3-6 个独立的子任务。为了让子任务具备自适应探索与跨项目联动能力，必须为每个任务显式分配以下参数：

* **探索宽度 (Breadth)**：每一层递归中，子代理并行生成的 Follow-up 检索词分支数（推荐 `2 - 3`）。
* **探索深度 (Depth)**：子代理顺着文献线索向下挖掘的最大层数限制（推荐 `2 - 4`）。
* **自适应关联专属技能**：若 P0 探测到就绪的兄弟技能（如 `pubmed-database`），必须在任务指引中显式绑定（例如：“检索时优先调用 `clinical-trials-database` 技能”）。
* **前置交叉引用 (Cross-Project Context)**：**如果在 P0 的 Grill-Me 交互中明确了需要关联本地已有项目**，必须在子任务的初始目标中，强制要求子代理**率先读取**关联项目的高密度结果文件（如 `读取 ../[已有项目名称]/report.md` 或 findings）作为先验上下文，绝不可凭空编造对比数据。

每个任务分配要素包括：
- **专家角色 (Role)**：如“半导体供应链分析师”。
- **研究目标 (Objective)**：说明要探明什么。若有跨项目关联，则补充：“首先读取 `../project-a/report.md` 获取其结论，再检索最新数据进行比对”。
- **初始检索词 (Initial Queries)**：2-3 个预选检索词。
- **探索设置 (Settings)**：`Depth=[D]`, `Breadth=[B]`。
- **输出路径 (Output Path)**：存放在 `findings/task-{id}.md`。

*注：若是企业调研模式，直接跳至 [enterprise_workflow.md](../enterprise_workflow.md) 获取专属六维度看板。*

---

## 2. 更新 KANBAN.md 看板

将规划好的子任务列表写入项目根目录下 `kanban/KANBAN.md` 的 `## 3. 任务分配板` 中，并将阶段一标记为已完成。

### 看板更新示例：
```markdown
## 2. 阶段生命周期进度 (Current Round)
- [x] P0: 环境初始化与交互式 Intake
- [x] P1: 调研任务板规划
- [ ] P2: 子任务分发与抓取 (TODO)
...

## 3. 任务分配板
- [ ] **Task A**: 政策合规官 | 目标: 探明稀土出口许可目录及出口量控制 | 设置: Depth=3, Breadth=2 | 状态: TODO
- [ ] **Task B**: 对比分析师 | 目标: 务必先读取 `../project-a/report.md`，然后提取核心指标进行横向比对 | 设置: Depth=2, Breadth=3 | 状态: TODO
```

---

## 3. 首次 Git 自动提交 📌 [Git 自动提交 1/3]

检查项目根目录下是否存在 Git 命令行工具，如果可用，执行当前回合（Current Round）的首次里程碑自动提交：
```powershell
git add .
git commit -m "stage: plan-initialized"
```
*(注：对于延续性研究，由于 P0 已经清空了旧 Findings 并打好了旧版本 Tag，此处提交将干净地记录下新一轮迭代的任务骨架，且没有任何历史文件残留污染。)*

---

## 4. 进度汇报格式

`[P1 complete] {N} tasks planned. Git Stage: plan-initialized.`
