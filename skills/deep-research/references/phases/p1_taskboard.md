# Phase 1: 调研任务板规划 (Task Board Planning)

本阶段指导智能体将复杂的调研课题拆分为具体的子任务，分配递归探索参数（深度与宽度），更新看板并执行首次 Git 提交。

---

## 1. 任务分解与递归探索参数分配

根据在 P0 Intake 阶段与用户确认的调研范围，将课题拆分为 3-6 个独立的子任务。为了让子任务具备自适应探索能力，必须为每个任务显式分配 **探索深度 (Depth)** 与 **探索宽度 (Breadth)** 参数：

* **探索宽度 (Breadth - 分支数)**：定义在每一层递归中，子代理最多并行生成并检索多少个不同的 Follow-up 检索词。
  - 推荐范围：`2 - 4`（分支过多会导致信息发散和 Token 浪费，默认设为 `2` 或 `3`）。
* **探索深度 (Depth - 兔子洞层数)**：定义子代理顺着文献线索向下挖掘的最大层数限制。
  - 推荐范围：`2 - 4`（层数过深会导致偏离核心主题，默认设为 `3`）。
* **自适应关联专属技能**：如果 P0 阶段检测到就绪的兄弟技能（如 `pubmed-database`），应在拆解任务时，将与该领域高度相关的任务指引绑定该技能（例如：“Task B（临床数据提取）中，子代理在检索时优先调用 `clinical-trials-database` 技能进行信息提取”）。

每个任务分配要素包括：
- **专家角色 (Role)**：如“半导体供应链分析师”、“政策合规官”。
- **研究目标 (Objective)**：一句话说明当前任务要探明什么。
- **初始检索词 (Initial Queries)**：2-3 个预选检索词。
- **探索设置 (Settings)**：`Depth=[D]` 深度层数限制，`Breadth=[B]` 并发宽度分支限制。
- **输出路径 (Output Path)**：存放在 `findings/task-{id}.md`。

*注：如果是企业调研模式，直接跳转至 [enterprise_workflow.md](../enterprise_workflow.md) 获取专属的六维度任务看板。*

---

## 2. 更新 KANBAN.md 看板

将规划好的子任务列表及对应的 `Depth`、`Breadth` 属性写入项目根目录下 `kanban/KANBAN.md` 的 `## 3. 任务分配板` 中，并将阶段一标记为已完成。

### 看板更新示例：
```markdown
## 2. 阶段生命周期进度
- [x] P0: 环境初始化与交互式 Intake
- [x] P1: 调研任务板规划
- [ ] P2: 子任务分发与抓取 (TODO)
...

## 3. 任务分配板
- [ ] **Task A**: 政策合规官 | 目标: 探明稀土出口许可目录及出口量控制 | 设置: Depth=3, Breadth=2 | 状态: TODO
- [ ] **Task B**: 供应链分析师 | 目标: 探明对晶圆代工关键辅料的供需冲击 | 设置: Depth=2, Breadth=3 | 状态: TODO
```

---

## 3. 首次 Git 自动提交 📌 [Git 自动提交 1/3]

检查项目根目录下是否存在 Git 命令行工具，如果可用，执行首次里程碑自动提交：
```powershell
git add .
git commit -m "stage: plan-initialized"
```
*如果 Git 命令不可用，打印 Warning 日志直接跳过，绝不阻断流程。*

---

## 4. 进度汇报格式

`[P1 complete] {N} tasks planned with Depth/Breadth settings. Git Stage: plan-initialized.`
