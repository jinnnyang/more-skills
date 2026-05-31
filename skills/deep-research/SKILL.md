---
name: deep-research
description: |
  生成格式受控的研究报告，具有证据追踪、文献引用治理与分阶段流式合成功能。
  触发词：帮我调研一下, 深度研究, 综述报告, 深入分析, research this topic, write a report on, 技术选型分析, 竞品研究, 行业报告。
---

# Deep Research (深度研究主指令路由)

本技能采用**模块化分阶段指令架构**。为了防止长上下文导致智能体记忆模糊及报告写入时触发最大输出 Token 限制（`max_output_tokens`），核心执行细节已拆分至专用阶段文件中。

主智能体（Lead Agent）在执行时，**必须按部就班按阶段运行**，并且在进入每个阶段时，**仅按需加载并严格执行**对应的子阶段参考指令。

---

## 📐 核心生命周期与路由分发 (Lifecycle Routing)

```
Lead Agent (主路由入口 — 最小化上下文占用)
  │
  ├── [P0] 环境检查与 Interactive Intake 确认 ──→ 载入 references/phases/p0_setup.md
  │    └── 初始化 KANBAN.md 看板与 Git 仓库
  │
  ├── [P1] 调研任务分解与规划 ──→ 载入 references/phases/p1_taskboard.md
  │    └── [Git 自动提交]: stage: plan-initialized
  │
  ├── [P2] 子任务分发与抓取 (Lead/Subagents) ──→ 写入 findings/task-*.md
  │    └── [Git 自动提交]: stage: research-notes-completed
  │
  ├── [P3] 文献引文清洗与图表规划 ──→ 载入 references/phases/p3_wash_governance.md
  │    └── 进行引文排重，审计 Alt 描述，并执行绘图工具发现
  │
  ├── [P4] 报告大纲设计与绘图规划 ──→ 登记至 KANBAN.md 报告写作进度列表
  │
  ├── [P5] 分章节顺序生成与追加拼接 ──→ 载入 references/phases/p5_drafting_append.md
  │    └── [Git 自动提交]: stage: draft-report-written
  │
  ├── [P6] 反方立场审查与纠错 (Counter-Review) ──→ 载入 references/phases/p6_p7_review_verify.md
  │
  └── [P7] 对账复核、README 更新与归档封版 ──→ 载入 references/phases/p6_p7_review_verify.md
       └── [Git 自动提交]: stage: report-finalized
```

---

## 🔀 双轨路由分支 (Workflow Branching)
启动 Intake 确认后，根据调研类型执行条件分发：
- **企业/机构调研模式 (Enterprise Research Mode)**：
  - 触发条件：调研目标为单一特定企业或具体商业实体。
  - 路由动作：直接跳转并完全遵循 [enterprise_workflow.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/enterprise_workflow.md) 指令包，进行六维度深度采集与 SWOT 矩阵、竞争壁垒评分。
- **通用专题调研模式 (General Research Mode)**：
  - 触发条件：调研目标为行业趋势、宏观政策、技术选型或科普综述。
  - 路由动作：顺序执行 `P0` 到 `P7` 指令。

---

## 🚀 执行核心原则 (Core Execution Principles)

1. **按需加载 (Lazy Loading)**：禁止在 P0-P2 阶段一次性读取全部 P5-P7 参考文件。仅在转换至新阶段时，才通过点击链接读取对应文件。
2. **Markdown 看板优先**：项目状态一律登记于项目根目录下的 `kanban/KANBAN.md` 中。断电中断后重启时，先读取该看板进行断点状态机恢复。
3. **流式分段追加**：大文本生成（P5）必须以 Section 为单位逐章流式追加写入 `report.md`，单章节控制在 400-800 字，释放历史废弃上下文以防截断。
4. **轻量 Git 提交**：
   - 自动提交在 Git CLI 可用时静默运行；若 Git 不存在，则打印 warning 日志直接跳过，**严禁报错阻断**。
   - 仅在以下三个主生命周期节点自动执行 Git 提交：
     - P1 任务板完成：`git commit -m "stage: plan-initialized"`
     - P5 报告初稿完成：`git commit -m "stage: draft-report-written"`
     - P7 最终归档发布：`git commit -m "stage: report-finalized"`

---

## 📁 核心阶段子指令清单 (Reference Guides)

- **环境、Intake与目录初始化**: [p0_setup.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/phases/p0_setup.md) (P0)
- **任务分解与大纲看板**: [p1_taskboard.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/phases/p1_taskboard.md) (P1)
- **文献清洗与绘图发现**: [p3_wash_governance.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/phases/p3_wash_governance.md) (P3)
- **分章节流式写作与断点恢复**: [p5_drafting_append.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/phases/p5_drafting_append.md) (P5)
- **反方纠错与对账发布**: [p6_p7_review_verify.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/phases/p6_p7_review_verify.md) (P6-P7)
- **企业模式专属工作流**: [enterprise_workflow.md](file:///c:/Users/jinnn/Documents/more-skills/skills/deep-research/references/enterprise_workflow.md)
