# Enterprise Research Workflow (企业级调研专业叠加工作流)

企业/机构调研模式并不是脱离 `deep-research` 主生命周期的独立并轨流程，而是作为主生命周期（P0 到 P7 阶段）在特定数据源、规划、分析框架和质检标准上的**“专业配置叠加（Overlay）”**。

在 Intake 确认启动企业模式后，主智能体（Lead Agent）在执行主干生命周期时，必须无缝叠加本工作流中所载的各项细则。

---

## 🧭 主生命周期叠加映射关系 (Lifecycle Overlay Mapping)

```
[P0: Setup] ──→ 额外明确法律实体、调研深度及对标企业 (Intake)
     │
[P1: Taskboard] ──→ 任务分解严格对应【六维度数据采集】(Task A 到 Task F)
     │
[P2: Dispatch] ──→ 调用 subagent_prompt 进行检索，遵循【数据采集方法论】
     │              └── 📚 关联参考：enterprise_research_methodology.md
     │
[P3: Wash] ──→ 执行全局引文注册与清洗，进行多源数据交叉校验
     │
[P4: Outline] ──→ 规划 7 章节企业大纲，并启动【量化分析框架】计算
     │              └── 📚 关联参考：enterprise_analysis_frameworks.md
     │
[P5: Drafting] ──→ 按 7 章节大纲循环生成与分段追加写入，执行 L1/L2 质检
     │              └── 📚 关联参考：enterprise_quality_checklist.md
     │
[P6: Review] ──→ 执行 Manual Counter-Review 反方审查与 L3 格式质检
     │
[P7: Verify] ──→ 对账复核、更新 README 并执行归档 Git 提交
```

---

## E1: 需求定义叠加 (Intake - P0)
在 P0 确认阶段，主代理需要额外向用户以选择题形式明确：
1. **确切法律实体范围**：明确是调研集团母公司，还是特定子公司或关联实体。
2. **调研报告目标深度**：快速扫描（3-5页，对标 Lightweight）/ 标准版（10-20页，对标 Standard） / 深度剖析（20-40页，对标 Deep）。
3. **指定竞争对标实体**：指定 1-3 个竞争对手或标杆公司进行对比。

---

## E2: 六维度任务规划叠加 (Six Dimensions - P1/P2)
在 P1 阶段的任务分解和 P2 阶段的分发执行中，任务规划必须完全映射到以下六个核心收集维度，并装载子代理 Prompt 进行检索。
具体检索词设计、优先级矩阵及交叉校验原则，必须遵循并执行：
- **📚 阶段收集指南**：[enterprise_research_methodology.md](enterprise_research_methodology.md)
  - *D1：公司基础情况 (Company Fundamentals - Task A)*
  - *D2：业务与产品分析 (Business & Products - Task B)*
  - *D3：市场与竞争格局 (Competitive Position - Task C)*
  - *D4：财务与运营指标 (Financial & Operations - Task D)*
  - *D5：最新动态与战略信号 (Recent Developments - Task E)*
  - *D6：专属/敏感信源审计 (Exclusive/Internal Sources - Task F)*

---

## E3: 分析框架与计算叠加 (Analysis Frameworks - P3/P4)
在 P3 文献清洗与 P4 大纲设计阶段，主代理在完成引文梳理后，必须在撰写前启动量化分析框架的推导。大纲设计必须预留出这四个量化框架的展示章节。
具体 SWOT 对策、Moat 壁垒加权打分表、风险级别计算规则，必须遵循并执行：
- **📚 量化计算指南**：[enterprise_analysis_frameworks.md](enterprise_analysis_frameworks.md)
  - * SWOT 综合分析与战略对策矩阵 (SO/WO/ST/WT)*
  - * 竞争壁垒量化评分模型 (7维度加权评级 A+ 至 C)*
  - * 8 大关键风险类别评估矩阵 (概率 × 影响)*
  - * 企业核心加权得分卡 (Scorecard)*

---

## E4: 质量卡点与模板写作叠加 (Quality Gates & Template - P5/P6/P7)
在 P5 追加写作与 P6 反方审查中，主 Agent 必须强制套用专门的“企业级 7 章节大纲模板”进行章节流式循环撰写，并严格按照 L1 数据级、L2 分析级、L3 文档级的三级质检标准进行逐级卡点放行。
具体质检 Checklist 及各章节二级小节要求，必须遵循并执行：
- **📚 质检与大纲规范**：[enterprise_quality_checklist.md](enterprise_quality_checklist.md)
  - * L1 数据收集质量核验卡点*
  - * L2 分析质量核验卡点*
  - * L3 文档编排与可读性质量核验卡点*
  - * 7 章节企业级调研报告模板大纲规范*
