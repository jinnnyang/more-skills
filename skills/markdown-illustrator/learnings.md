# 📝 Markdown Illustrator 踩坑与学习笔记 (Learnings & Pitfalls)

本文件记录在开发与运行 `markdown-illustrator` 及 `pretty-mermaid` 本地集成时遇到的技术缺陷、语法边界与踩坑经验，以供后续维护和 AI Agent 编写图表时参考。

---

## 🚨 1. Sankey Diagram (桑基图) 字符集与双引号语法陷阱

*   **问题现象 1 (双引号报错)**：
    在 `sankey-beta` 中，为节点文本加上双引号（如 `"学习总预算", "精读", 10`）时，本地校验报错：`Expecting 'DQUOTE', got 'ESCAPED_TEXT'` 或类似错误。
*   **问题现象 2 (中文/空格报错)**：
    如果移除双引号，直接写 `学习总预算, 精读, 200`，报错：`Expecting 'NEWLINE', 'EOF', 'COMMA', got 'NON_ESCAPED_TEXT'`。
*   **根本原因剖析 (Lexer Bug)**：
    1.  Mermaid 的 `sankey-beta` 采用极简 CSV 解析器，其 Lexer 正则表达式（识别 `NON_ESCAPED_TEXT`）存在遗漏，**未能包含 Unicode 字符集（如中文汉字）**。
    2.  因此，当 Lexer 遇到“学习”等中文字符时，将其判定为非法 Token，导致抛出 `NON_ESCAPED_TEXT` 无法被吃掉的语法错误。
    3.  即使强制加入英文双引号，由于内部词法解析器的脆弱性，亦极易导致转义匹配失败。
    4.  **注意：经过实测，即使升级至目前的最新版 `mermaid@11.15.0`，此 Bug 依然存在！**
*   **AI Agent 执行策略**：
    *   **严格规范书写**：`源节点,目标节点,数值` (切勿用引号，逗号两侧切勿留空格)。
    *   **跳过本地校验**：如果业务上图表**必须包含中文节点**，由于上游 Mermaid 存在不可逆的 Lexer Bug，校验必然失败。Agent **必须跳过对含中文 Sankey 的本地 CLI 校验**，直接将 `.mmd` 源码写入磁盘，或者在不影响语意的情况下全部使用纯英文节点。
    *   为了不阻塞工作区级自动化脚本的全量扫描验证，`mermaid-diagram-writing-guide.md` 中的 Sankey 示例全部采用了纯 ASCII 英文编写。

---

## 🚨 2. 雷达图 (Radar) 与 韦恩图 (Venn)
由于这两种图表属于 `v11+` 版本新特性，现已将本地 `pretty-mermaid` 的 `mermaid` 依赖升级至最新版本（`^11.0.0` 以上）。目前本地环境已完全支持对它们的语法安全校验，你可以放心使用并调用 `cli.js` 验证，只要符合官网规范就不会再报错。
