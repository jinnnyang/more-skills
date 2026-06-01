# Phase 2: 子任务分发与递归深挖 (Dispatch & Recursive Investigation)

本阶段指导智能体启动并行子任务分发，并在执行中全面推行基于**宽度（Breadth）**与**深度（Depth）**的递归深挖机制，收集渐进式知识并形成智能体独立洞察（Insights）。

---

## 1. 跨项目上下文加载 (Cross-Project Context Load)
在开始正式网络检索前，如果该任务的目标（Objective）中包含了**跨项目引用指令**（例如：“首先读取 `../project-a/report.md`”）：
- 子代理必须优先调用文件读取工具，加载目标项目的指定产出文件。
- 将其核心结论和数据保存在临时上下文中，用于后续搜索中的横向比对，**严禁凭空捏造对比事实**。

---

## 2. 递归深挖循环机制 (Rinse-and-Repeat Loop)

为了打破“信息孤岛”，子代理必须执行自适应的递归挖掘循环：

```
[Level 0: 初始检索] ──→ 运行 Initial Queries 并 Fetch 全文 (DEEP 模式)
        │
[知识提取] ──→ 提取事实碎片并形成初步【知识点 (Learnings)】
        │
[评估与追问] ──→ 审计已有 Learnings，寻找关键数据漏洞或新线索
        │      └── 🧠 生成最多 [Breadth] 个 Follow-up 追问词 (CoT 推导)
        │
[下钻检索] ──→ 运行新追问词检索，深入下一层兔子洞 (Level 1 至 Level Depth)
        │
[循环终止] ──→ 达到 Depth 深度上限，或单层未发现新 Learnings
```

### 递归循环具体规程：
1. **Level 0 (初始层)**：运行 P1 分配的 Initial Queries，抓取高价值页面，提炼基础 Learnings。
2. **渐进式追问生成 (Follow-up Queries)**：分析当前 Learnings 的断层，动态生成最多 `Breadth` 个精准追问词。
3. **递归下钻 (Recursive Crawl)**：进入下一层深度检索并合流知识点，层数不超过 `Depth`。
4. **自适应调用就绪技能**：涉及专属领域时，优先使用 P0 检测到的专属技能（如 `pubmed-database` API）。

---

## 3. 执行路由模式 (Execution Modes)

### 模式 A：子代理模式 (With Subagents - 推荐)
- 主代理派发子任务给 `research` 子代理，带上 `Depth` 和 `Breadth` 参数。
- 子代理加载 [subagent_prompt.md](../subagent_prompt.md) 在沙箱中执行，完毕后将提炼笔记写入 `findings/task-*.md`。

### 模式 B：单体降级模式 (Degraded Mode - 无子代理时)
- Lead Agent 顺序执行递归检索。每写完一个 `findings/task-*.md` 后，**必须清空**大网页文本缓存，防范上下文穿舱。

---

## 4. 信源治理与 URL 提取 (Source Governance)
信源必须遵循 [research_notes_format.md](../research_notes_format.md) 格式（包含 Accessibility, Source-Type, As Of, Authority）。
* **首发图片 URL 提取**：仅提取高价值原图的 Web URL，附带详尽 `alt` 描述，严禁下载二进制图片。

---

## 5. 严格的信息密度控制与独立洞察输出 (Token Budget & Insights)

为防范报告泥沙俱下，子代理最终写入的 `findings/task-{id}.md` 必须执行以下硬性标准：
* **## 调研发现 (Findings)**：最多保留 **10 条**核心事实，均为附带引用序号的单句陈述。
* **## 深度阅读笔记 (Deep Read Notes)**：最多列出 2-3 个核心文献的提炼，每个描述控制在 4 行以内。
* **## 智能体洞察 (Insights) 【必填项】**：
  - 基于收集到的客观事实（包括前置跨项目加载的对比数据），**强制输出 2-3 条智能体的独立逻辑推演、瓶颈推测或发展研判**。
  - 必须明确区分哪些是文献陈述（Fact），哪些是智能体的自有推断（Insight）。
  - （注：如果是延续性研究，子代理必须直接写入或覆写此回合对应的目标 findings 路径，旧回合产物由于已被净空，此处产生的是全新的干净报告段）。

---

## 6. 看板更新与归档
各子任务提炼完成后，Lead Agent 在看板 `kanban/KANBAN.md` 标记完成，本阶段**不需要触发 Git 自动提交**。
