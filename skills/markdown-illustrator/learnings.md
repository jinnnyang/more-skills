# 📝 Markdown Illustrator 踩坑与学习笔记 (Learnings & Pitfalls)

本文件记录在开发与运行 `markdown-illustrator` 及 `pretty-mermaid` 本地集成时遇到的技术缺陷、语法边界与踩坑经验，以供后续维护和 AI Agent 编写图表时参考。

---

## Known Environment Issues

*   **Sankey Diagram (桑基图) Lexer Bug**:
    Mermaid 的 `sankey-beta` 采用极简 CSV 解析器，其 Lexer 正则表达式（识别 `NON_ESCAPED_TEXT`）存在遗漏，**未能包含 Unicode 字符集（如中文汉字）**。
    当 Lexer 遇到“学习”等中文字符时，将其判定为非法 Token，导致抛出 `NON_ESCAPED_TEXT`。经过实测，即使升级至最新版 `mermaid@11.15.0`，此 Bug 依然存在！如果业务必须包含中文，本地 CLI 校验必然报错。

---

## Success Patterns

*   **Radar & Venn Diagrams**:
    目前本地 `pretty-mermaid` 已经升级支持 `v11+`。现在你可以安全使用 `radar-beta` 和 `venn-beta` 并调用本地工具校验，只要符合官方规范即可通过。
*   **Sankey Diagram 变通方案**:
    *   为了通过本地校验：写纯 ASCII 英文节点。
    *   为了通过渲染管线：如果是中文节点，请**主动跳过**包含中文的 Sankey 源码本地校验，下游 v11+ 渲染管线能正常渲染。

---

## Failures & Anti-patterns

*   **Sankey 语法书写禁忌**:
    *   **禁忌 1**：不要使用双引号包裹文本，如 `"学习总预算", "精读", 10`。这会导致 `Expecting 'DQUOTE', got 'ESCAPED_TEXT'`。
    *   **禁忌 2**：逗号两侧切勿留空格，例如 `节点 A, 节点 B, 10`。
    *   **正确写法**：`源节点,目标节点,数值`（纯英文 ASCII最佳）。

---

## 2026-06-15 踩坑：布局方向、极端宽高比与高清晰度输出

*   **子图流向失效与跨子图连接**:
    *   **问题**：如果直接连接两个 `subgraph` 内部的节点（例如 `B --> C`），会破坏子图的独立作用域，导致子图内声明的局部方向（如 `direction RL`）失效，从而被强制继承父图的全局排版方向。
    *   **解决方案**：如果想要实现混合排版，必须在跨域连接时使用**子图的 ID 进行连接**（例如 `Cabin --> External`），从而完美保留局部的独立方向设置。

*   **极端宽高比崩溃与 2x2 网格重构**:
    *   **问题**：使用一字排开的 `flowchart LR` 或者单层展开的大量 `graph TD`，会生成宽度或高度极其夸张的图片（如达 8000px 宽）。此类图片在报告排版时会被严重压缩导致文字糊成一团。
    *   **解决方案**：我们在 `mermaid-tool.ts` 中引入了自动拦截机制，强制校验生成图片的宽高比（> 2.5 抛出告警）。应当巧妙利用 `subgraph` 将并列的结构重构为“网格状”或“蛇形”连线（如 2x2 结构），强制折叠视觉流。

*   **SVG 转换的高清度控制方案**:
    *   **问题**：早期把转换图片的宽度写死为 `1200px`，面对复杂大图时会导致整体像素密度不足发糊。
    *   **解决方案**：放弃 `mode: 'width'`，改用相对原生 SVG 尺寸的放大倍率 `mode: 'zoom', value: 4.0`，直接输出超高像素密度的 Retina 级别图片，辅以最小双向 1500px 的告警底线。

*   **Agent 上下文的最佳实践（自解释代码）**:
    *   **经验**：为防范 Mermaid 这种解析脆弱的语法，最高效的 Prompt 指导方案是直接在参考示例代码中添加密集的、行级别的 `%% 注释`。直观的“内联文档”是约束其他 Agent 语法的最强保障。
