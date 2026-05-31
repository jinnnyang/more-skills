# 调研报告模板 (Report Template)

最终生成的 Markdown 研究报告必须严格套用以下排版和章节大纲。

---

## 报告模板大纲

```markdown
# {{报告标题 / TITLE}}

> 调研日期: {{DATE}} | 来源文献数: {{SOURCE_COUNT}} | 模式: {{MODE}} | AS_OF: {{AS_OF}} | 官方/学术信源占比: {{OFFICIAL_SHARE}}

## 摘要 / Executive Summary

{{对调研的核心发现、供应链或技术冲击、关键结论和潜在风险进行 200-400 字的精炼概述。}}

---

## 目录 / Table of Contents

{{从下方各章节标题自动生成目录列表。}}

---

{{正文章节 — 按照大纲设计分章节流式追加。单章字数严格控制在 400-800 字，防范 Token 溢出。}}

## 1. {{章节一标题}}

{{章节正文叙述。必须包含对立事实的客观平衡陈述。所有论断必须附带引文标记如 [1][2]，数据必须引用明确。

数据可视化规则：
- 优先检测并调用绘图工具生成 PNG 图片并存入 assets/ 目录，使用标准 markdown 格式 !["alt"](./assets/文件名.png "Title") 进行嵌入。alt 必须是能让其他 LLM 准确理解图片内容的详细描述。
- 若无专门绘图工具，则回落为 Mermaid.js 代码块，例如：
  ```mermaid
  flowchart TD
      A["A 节点"] --> B["B 节点"]
  ```
  （注意：Mermaid 节点内的文本必须使用双引号包裹，ID 禁用特殊字符）。
}}

**置信度**: High / Medium / Low
**依据说明**: {{为什么给出该置信度打分：信源交叉验证程度、文献发布时间、数据详实度}}
**对立观点**: {{明确列出一种反方解释，若无支持数据，则标注 [unverified]}}

---

## 2. {{章节二标题}}
...

---

## 核心争议与对立解释 / Key Controversies

- **核心争议 1:** [主张 A 与反向证据 B 对比说明] [1][3]
- **核心争议 2:** ...

## 关键发现 / Key Findings

- **发现 1:** [最重要的调研发现事实陈述] [3]
- **发现 2:** [次重要的调研发现事实陈述] [1][4]

---

## 研究局限与未来方向 / Limitations & Future Directions

### 调研局限性说明
- 本研究范围受阻于公开网络可获得的数据源、语言及时间阻断限制。
- 缺乏部分商业机密/专利许可数据 [unverified]。

### 未来调研建议
- 针对特定环节进行更精细的专家调研或实地考查。

---

## 参考文献 / References

[1] 作者/机构. "文献/报告标题". 信源类型 (official/academic/secondary-industry/journalism/community/other). 截止时间: YYYY-MM-DD. 原始网页URL.
[2] 作者/机构. "文献/报告标题". 信源类型. 截止时间: YYYY-MM-DD. 原始网页URL.

---

## 附录：多媒体佐证汇总 / Appendix: Multimedia Evidence

- !["[描述：如2024年全球中重稀土开采与冶炼份额占比饼图，展示中国在冶炼环节占全球89%份额...]"](https://example.com/charts/supply-chain.png "全球中重稀土开采冶炼占比") [1]
- !["[描述：如芯片供应链系统架构图，包含原材料、设计、制造、封测和组装五个阶段...]"](https://example.com/charts/semiconductor-chain.png "半导体精细材料供应链流向图") [2]
```

