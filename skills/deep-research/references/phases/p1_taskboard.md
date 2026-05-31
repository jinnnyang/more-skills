# Phase 1: 调研任务板规划 (Task Board Planning)

本阶段指导智能体如何将复杂的调研课题拆分为具体的子任务，更新看板并执行首次 Git 提交。

---

## 1. 任务分解策略
根据调研深度（标准模式 4-6 个任务，轻量模式 3-4 个任务），将课题分解为独立的子任务。

每个任务包含以下要素：
- **专家角色 (Role)**：如“半导体供应链分析师”、“政策合规官”。
- **研究目标 (Objective)**：一句话说明当前任务要探明什么。
- **搜索词 (Queries)**：2-3 个预选搜索词。
- **深度级别 (Depth)**：`DEEP`（深度阅读，利用 web_fetch 爬取全文）或 `SCAN`（快速扫描，基于搜索摘要）。
- **输出路径 (Output Path)**：必须统一存放在 `findings/task-{id}.md`。

*注：如果是企业调研模式，直接跳转至 [enterprise_workflow.md](../enterprise_workflow.md) 获取专属的六维度任务看板。*

---

## 2. 更新 KANBAN.md
将分解好的任务列表写入 `kanban/KANBAN.md` 的 `## 3. 任务分配板` 章节，并将阶段二标记为进行中。

### 看板更新示例：
```markdown
## 2. 阶段生命周期进度
- [x] P0: 环境初始化与交互式 Intake
- [/] P1: 调研任务板规划 (进行中)
...

## 3. 任务分配板
- [ ] **Task A**: 政策合规官 | 目标: 探明稀土出口许可目录及出口量控制 | 状态: TODO
- [ ] **Task B**: 供应链分析师 | 目标: 探明对晶圆代工关键辅料的供需冲击 | 状态: TODO
```

---

## 3. 首次 Git 自动提交 (Git Commit)
检查本地环境是否存在 Git，若可用，在项目根目录下执行自动提交：
```powershell
git add .
git commit -m "stage: plan-initialized"
```
*如果 Git 命令执行失败，打印日志并警告，但绝不中断流程。*

---

## 4. 进度汇报格式
`[P1 complete] {N} tasks planned. Git Stage: plan-initialized.`
