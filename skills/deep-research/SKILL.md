---
name: deep-research
description: |
  生成格式受控的研究报告，具有环境就绪工具发现、文献引用治理、自适应递归深度探索与分阶段流式合成功能。
  当用户提到“帮我调研一下”、“深度研究”、“综述报告”、“深入分析”、“竞品研究”、“行业报告”或需要编写任何需要严密事实支撑、对立论证及多媒体插图的研报时，必须强制激活此技能。
---

# Deep Research (深度研究主指令路由)

本技能采用**模块化分阶段指令架构**。为了防止长上下文导致智能体记忆模糊及报告写入时触发最大输出 Token 限制（`max_output_tokens`），核心执行细节已拆分至专用阶段文件中。

主智能体（Lead Agent）在执行时，**必须按部就班按阶段运行**，并且在进入每个阶段时，**仅按需加载并严格执行**对应的子阶段参考指令。

---

## 📐 核心生命周期与路由分发 (Lifecycle Routing)

```
Lead Agent (主路由入口 — 最小化上下文占用)
  │
  ├── [P0] 环境探测、已有项目扫描与 Grill-Me 需求对齐 ──→ 载入 references/phases/p0_setup.md
  │    └── 🔍 获取 HOME 路径，扫描已有项目及可用工具，执行精英反问澄清需求，初始化 KANBAN 与 Git 延续标记
  │
  ├── [P1] 任务分解与递归参数规划 ──→ 载入 references/phases/p1_taskboard.md
  │    └── 为任务分派 Depth（深度）和 Breadth（宽度）参数
  │    └── 📌 [Git 自动提交 1/3]: stage: plan-initialized
  │
  ├── [P2] 子代理自适应递归深挖 ──→ 载入 references/phases/p2_dispatch.md
  │    └── 顺着文献线索层层递归检索（Rinse-and-Repeat），写入 findings/task-*.md
  │
  ├── [P3] 文献数据清洗与绘图决策 ──→ 载入 references/phases/p3_wash_governance.md
  │    └── 进行引文排重，审计 Alt 描述，检测可用绘图技能以确定回落路由
  │
  ├── [P4] 报告大纲设计与绘图规划 ──→ 载入 references/phases/p4_outline.md
  │    └── 登记待写作章节列表至 KANBAN.md，规划可视化结构
  │
  ├── [P5] 分章节顺序生成与追加拼接 ──→ 载入 references/phases/p5_drafting_append.md
  │    └── 按照看板章节逐章生成（单章 400-800 字）并流式追加，支持断点恢复续写
  │    └── 📌 [Git 自动提交 2/3]: stage: draft-report-written
  │
  ├── [P6] 反方立场审查与纠错 (Counter-Review) ──→ 载入 references/phases/p6_p7_review_verify.md
  │    └── 对正文核心观点进行对立立场自我反思与排查
  │
  └── [P7] 对账复核、README 归档封版 ──→ 载入 references/phases/p6_p7_review_verify.md
       └── 📌 [Git 自动提交 3/3]: stage: report-finalized
```

---

## 🔀 双轨路由与模式叠加 (Workflow Overlay)

启动 Intake 确认后，根据调研类型执行条件分发：
- **企业/机构调研模式 (Enterprise Research Mode)**：
  - **触发条件**：调研目标为单一特定企业或具体商业实体。
  - **叠加规则**：企业模式是 P0-P7 主生命周期的**“专业配置叠加（Overlay）”**。执行时继续遵循主生命周期各个阶段，但在对应阶段时，必须载入并执行 [enterprise_workflow.md](references/enterprise_workflow.md) 中规定的六维度数据抓取（E2）、SWOT与壁垒评分（E3）、三级质检（E4）及7章节企业报告模板（E5）。
- **通用专题调研模式 (General Research Mode)**：
  - **触发条件**：调研目标为行业趋势、宏观政策、技术选型或科普综述。
  - **路由动作**：顺序执行通用版 `P0` 到 `P7` 指令。

---

## 🚀 执行核心原则 (Core Execution Principles)

1. **按需加载 (Lazy Loading)**：仅在转换至新阶段时，才通过点击相对路径链接读取对应参考文件。禁止提前载入无关阶段的指导文件。
2. **环境感知与 Grill-Me 交互**：在 P0 阶段，必须探测当前可用的辅助工具与 `$HOME/projects/` 下的历史项目，并利用 Grill-Me 互动问答强制与用户对齐目标受众、跨界关联，绝不盲目开工。
3. **自适应递归深挖**：在 P2 阶段通过宽度（Breadth）与深度（Depth）参数限制，允许子代理沿着网络线索递归检索，并动态合流知识点，防御未知盲区。
4. **流式分段追加与断点恢复**：大文本生成（P5）必须以 Section 为单位逐章流式追加写入 `report.md`，并在看板 `KANBAN.md` 中记录状态。崩溃后从断点章节自适应拉起并追加。
5. **非阻断式 Git 提交**：
   - 自动提交在 Git CLI 可用时静默运行；若 Git 不存在，则打印 warning 日志直接跳过，**严禁报错阻断**。
   - 严格限制 Git 提交频次为上述 **3 个核心阶段节点**，禁止在中间章节写入或子代理 Notes 抓取时频繁提交。
6. **Git 版本控制下的延续研究**：若在已有项目上启动延续研究，通过前后打上 `v[X.X.X]` 的 Git Tag 实现版本冻结与隔离。新一轮启动前必须清空旧的 Findings 文件以防历史污染，通过 Git 原址覆盖保障工作区绝对干净。

---

## 📁 核心阶段子指令清单 (Reference Guides)

- **[P0] 环境、工具探测与 Intake 初始化**: [p0_setup.md](references/phases/p0_setup.md)
- **[P1] 任务分解与大纲看板**: [p1_taskboard.md](references/phases/p1_taskboard.md)
- **[P2] 子任务分发与自适应递归深挖**: [p2_dispatch.md](references/phases/p2_dispatch.md)
- **[P3] 文献清洗与绘图发现**: [p3_wash_governance.md](references/phases/p3_wash_governance.md)
- **[P4] 大纲映射与可视化规划**: [p4_outline.md](references/phases/p4_outline.md)
- **[P5] 分章节流式写作与断点恢复**: [p5_drafting_append.md](references/phases/p5_drafting_append.md)
- **[P6/P7] 反方纠错与对账归档**: [p6_p7_review_verify.md](references/phases/p6_p7_review_verify.md)
- **[Enterprise] 企业模式叠加工作流**: [enterprise_workflow.md](references/enterprise_workflow.md)
