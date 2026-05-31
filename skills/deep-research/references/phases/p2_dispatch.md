# Phase 2: 子任务分发与递归深挖 (Dispatch & Recursive Investigation)

本阶段指导智能体启动并行子任务分发，并在各子代理（或 Lead Agent 自身）的执行中全面推行基于**宽度（Breadth）**与**深度（Depth）**的递归深挖机制，收集渐进式知识并回流笔记。

---

## 1. 递归深挖循环机制 (Rinse-and-Repeat Loop)

为了在未知领域打破“信息孤岛”，子代理在执行单个任务时，不允许仅做单次检索，必须执行自适应的递归挖掘循环：

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
[循环终止] ──→ 达到 Depth 深度上限，或单层检索未发现任何新 Learnings
```

### 递归循环具体规程：
1. **Level 0 (初始层)**：运行 P1 看板分配的 Initial Queries，抓取并分析首批高价值页面，提炼基础 Learnings。
2. **渐进式追问生成 (Follow-up Queries)**：分析当前已收集的 Learnings。如果发现断层（如“得知了该材料被管制，但没有具体的年度配额数据”），必须动态生成最多 `Breadth` 数量的精准追问词。
3. **递归下钻 (Recursive Crawl)**：进入 Level 1 深度运行追问检索，分析提取并合并到全局事实树中。以此往下层层递归，最大层数不得超过任务设定的 `Depth`。
4. **自适应调用就绪技能**：如果任务涉及专属领域（如医学/临床），递归检索中每次发送查询必须优先使用 P0 检测到的专属技能（如 `pubmed-database` 提供的 API 检索工具）进行文献获取，以提高可信度。

---

## 2. 执行路由模式 (Execution Modes)

### 模式 A：子代理模式 (With Subagents - 推荐)
- 主代理（Lead Agent）并行派发子任务给 `research` 子代理。
- 派发时，在任务参数中填入看板里该任务专属的 `Depth` 和 `Breadth` 限制。
- 子代理加载 [subagent_prompt.md](../subagent_prompt.md)，在沙箱中递归执行上述深挖循环，并将提炼完的静态 notes 写入 `findings/task-*.md`。

### 模式 B：单体降级模式 (Degraded Mode - 无子代理时)
- Lead Agent 顺序执行每个子任务，扮演对应的专家角色进行递归检索。
- **上下文垃圾回收（GC）**：每写完一个 `findings/task-*.md` 任务笔记，**必须清空**主智能体上下文中的所有原始抓取大网页文本，只保留提炼出的 Findings，防范 Context 穿舱。

---

## 3. 信源治理标记与首发图片 URL (Source Governance)
在每一层递归中获取的信源，写回笔记时必须严格遵循 [research_notes_format.md](../research_notes_format.md) 格式要求，包含可访问性（Accessibility）、信源标签（Source-Type）、时效戳记（As Of）及权威度评分（Authority）。

* **图片 URL 的首发提取**：如果在递归网页中发现高价值趋势图、供应链图，子代理**只允许提取其原始 Web URL**，并配以极详尽的 `alt` 说明进行登记。严禁尝试下载二进制图片文件。

---

## 4. 严格的信息密度控制 (Token Budget)
为防止递归产生巨量事实泥沙俱下撑爆后续报告撰写，子代理最终写回的 `findings/task-{id}.md` 必须执行以下硬限制：
* **## 调研发现 (Findings)**：最多保留 **10 条**核心事实，每一条事实**必须是单句陈述**，行尾必须有文献引用序号（如 `[1]`）。
* **## 深度阅读笔记 (Deep Read Notes)**：对于 DEEP 模式任务，最多列出 2-3 个核心文献的提炼，且每个文献描述**严格控制在 4 行以内**。

---

## 5. 看板更新与归档
各子代理将数据提炼写入 `findings/` 目录后，Lead Agent 在看板 `kanban/KANBAN.md` 中将对应任务标记为已完成。

*注：本阶段仅在看板中记录进度，**不需要触发 Git 自动提交**，以符合全局 3 次 Git commit 的精简设计要求。*
