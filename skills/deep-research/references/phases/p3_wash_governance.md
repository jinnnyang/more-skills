# Phase 3: 文献治理与多媒体校验 (Citation Registry & Media Validation)

本阶段指导智能体收集并整合所有子任务的原始数据源，清洗文献引用，并对图片证据进行多维校准。

---

## 1. 全局引用注册表数据清洗 (Citations Cleaning)
1. **去重与全局编号**：读取 `findings/task-*.md` 的 `## Sources`，合并重复 URL，分配全局统一编号 `[1]`, `[2]`, `[3]` 等。
2. **应用质量门限阈值 (Quality Gates)**：
   - **标准模式**：已校验文献数 ≥12，独立域名数 ≥5，官方/学术源占比 ≥30%。单源占比最大 ≤25%。
   - **轻量模式**：已校验文献数 ≥6，独立域名数 ≥3，官方/学术源占比 ≥20%。单源占比最大 ≤30%。
   - *如果由于研究对象小众导致阈值未通过，必须在看板中记录 Warning 原因，不阻断运行。*

---

## 2. 多媒体图片数据清洗与 Alt 审计
由于不要求直接下载图片二进制文件，本阶段仅核查多媒体的 URL 引用及 Alt 描述质量：
1. **收集图片**：从 `findings/task-*.md` 提取所有标准 Markdown 图片节点。
2. **审计 Alt 描述**：确保 `alt` 信息详尽完整。如果是图表，必须包含“图表类型、核心指标、数据趋势”，必须符合 downstream LLMs 友好的可读描述，不合格的由 Lead Agent 负责润色重写。
3. **多媒体登记**：将合格的图片原 URL、Alt 描述登记到 `KANBAN.md` 的全局注册表中。

---

## 3. 绘图与可视化工具发现 (Tool Discovery)
1. **检测环境**：检索当前环境（如 MCP 注册工具、本地 Python 绘图库）以寻找专用的绘图技能（如 `canvas-design` 或 `matplotlib` 绘图脚本）。
2. **决策路由**：
   - 若发现可用绘图技能，则在 `KANBAN.md` 中标记：`优先使用绘图技能生成 PNG`。
   - 若未发现，则标记：`回落至 Mermaid 语法内联渲染`。

---

## 4. 更新 KANBAN.md
将生成的全局引文注册表、审计后的图片列表、绘图决策写入 `kanban/KANBAN.md` 的 `## 5. 全局引文与多媒体注册表` 中，并将阶段进度更新。

### 看板更新示例：
```markdown
## 2. 阶段生命周期进度
- [x] P0: 环境初始化与交互式 Intake
- [x] P1: 调研任务板规划
- [x] P2: 子任务分发与抓取
- [/] P3: 文献治理与多媒体过滤 (进行中)
...

## 5. 全局引文与多媒体注册表
### 已校验引文 (Citations)
- [1] 新华社. "稀土出口配额最新管理细则". 官方源. As Of: 2025-10. URL: https://example.com/china-rare-earth-policy
- [2] Gartner. "2026年半导体辅料供应链趋势". 行业源. As Of: 2026-02. URL: https://example.com/gartner-semiconductor-report

### 收集的多媒体佐证 (Media)
- !["2024年全球中重稀土开采与冶炼份额占比饼图..."](https://example.com/charts/supply-chain.png "全球中重稀土开采冶炼占比") [1]

### 数据可视化决策 (Visualization Decision)
- 图表生成策略：未发现可用绘图技能，回落至 Mermaid.js 文本图表
```

*注：本阶段不需要触发 Git 自动提交。*

