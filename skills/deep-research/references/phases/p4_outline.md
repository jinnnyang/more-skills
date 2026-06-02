# Phase 4: Outline Mapping & Visual Planning (Evidence-Mapped Outline)

This phase guides the Lead Agent in designing a logical, topic-first research outline mapped to findings, and planning the layout and textual metadata (MITTS) for all planned diagrams.

---

## 1. Topic-First Outline Design Rules
1. **Thematic Over Task-Order**: Do NOT structure the outline based on "Task A Findings, Task B Findings" chronologically. Organize it around the logical thesis (e.g., Background -> Tech Bottlenecks -> Industry Chain -> Competitive Scenarios -> Strategic Recommendations).
2. **Evidence Mapping**: Every section and subsection in the outline MUST explicitly list the subagent findings (`Task A-Finding 2`, etc.) and the global citation numbers (`[1]`, `[3]`) that support its facts.
3. **Recency Audit**: Verify the publication dates of the evidence against the `AS_OF` target defined in Phase 0. Highlight highly time-sensitive metrics that are over 1 year old, and tag them for credibility adjustment during drafting.

---

## 2. Diagram & SMIS Planning (CRITICAL)
Based on the visualization decision from Phase 3, plan the visual inserts and pre-draft their **SMIS wrappers**:
- **If specialized drawing is active (doc-illustrator)**: Plan the target PNG filename (e.g., `assets/chart_market_share.png`). Outlines of core data, flows, and the **judgmental conclusion** must be pre-drafted to be embedded as either the native Alt-text (Pattern A) or wrapped inside semantic HTML `<figure>` / `<figcaption>` wrappers (Pattern B) in P5.
- **If inline Mermaid is active (Fallback)**: Plan the Mermaid diagram type (flowchart, sequence, mindmap). Pre-draft the structural nodes using standard anti-error rules (double quotes for labels, unique simple IDs), and plan its corresponding `<figure>` HTML wrapper and description.

---

## 3. 看板登记与大纲格式 (Kanban Registry & Outline Format)
Register the designed outline and visual plan as a checklist of `Pending Sections` in `kanban/KANBAN.md`.

### Kanban Outline Example (Chinese Adaptive):
```markdown
## 4. 报告写作大纲与进度 (Report Outline & Progress)

### 待撰写章节清单 (Pending Sections)
- [ ] 章节 1：稀土全球供应链格局及中国垄断地位
  - 引文来源：[1][2][5]
  - 支撑证据：Task A-Finding 2, Task B-Finding 4
  - 图表规划：生成 `./assets/supply_chain_share.png` (全球开采/冶炼份额占比饼图)
  - SMIS规划：使用 Pattern A 模式，Alt文本内包含图表类型为占比饼图、中国冶炼占89%垄断数据、以及推导西方短期无法脱钩需保持合作的结论。
- [ ] 章节 2：主要出口管制政策及对企业合规冲击
  - 引文来源：[3][4]
  - 支撑证据：Task C-Finding 1, 3
  - 图表规划：内联 Mermaid 流程图 (展示双向申报与审批合规流程)
  - SMIS规划：使用 Pattern B 模式，用 `<figure>` 标签包裹，并在 `<figcaption>` 内写入双向申报审批流程，包含从申请至终审的五大关卡，并得出合规审核周期将延长至60天以上的预判性结论。
```

*Note: Phase 4 does not require triggering a silent Git commit.*
