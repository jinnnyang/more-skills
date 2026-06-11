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
