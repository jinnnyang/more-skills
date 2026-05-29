# {{TITLE}}

> 研究日期: {{DATE}} | 来源数量: {{SOURCE_COUNT}} | 字数: ~{{WORD_COUNT}} | 模式: {{MODE}} | AS_OF: {{AS_OF}} | 官方源占比: {{OFFICIAL_SHARE}}

## 摘要 / Executive Summary

{{200-400 words summarizing key findings, methodology, conclusions, and risks.}}

---

## 目录

{{Auto-generate from actual section headers below.}}

---

{{BODY SECTIONS —  Adapt to topic type and include opposing interpretation per section.}}

For each section:

## N. [Topic-Specific Section Title]

{{Section content with inline citations [1][2].
Standard mode: 500-1000 words per section.
Lightweight mode: 300-600 words per section.

数据可视化与绘图规则：
- 优先利用工具发现机制，调用专门的绘图技能（如 canvas-design / matplotlib 等）将结果输出为图片文件，移动至 assets/ 目录下，使用 !["alt"](relative_path "title") 进行正文嵌入。
- 若无专门的绘图技能，则回落至使用 Mermaid 语法直接在报告正文中进行绘图，例如：
  ```mermaid
  flowchart TD
      A["A 节点"] --> B["B 节点"]
  ```
  （请严格遵循 visualization_mermaid_guide.md 防错规范，节点文本一律用双引号包裹）。

Rules:
- 每个事实性论点都需要引用 [n]
- 数字/百分比必须有来源
- 出现不同证据时要成对给出支持与反驳
}}

**置信度:** High/Medium/Low

**依据:** {{Why this confidence level — source agreement, evidence quality, data availability}}

**反方解释:** {{One explicit opposing interpretation with supporting citations if any, or [unverified] if insufficient.}}

---

{{COUNTER-REVIEW SUMMARY}}

- **核心争议 1:** [主张 A 与反向证据 B 对比] [n][m]
- **核心争议 2:** ...

## 关键发现 / Key Findings

{{3-5 findings in Standard mode, 2-3 in Lightweight. Each finding should:}}
- 具体结论
- 对应引文
- 信心说明

Example:
- **发现 1:** [Most important discovery] [3][7]
- **发现 2:** [Second most important] [1][4]

---

## 局限性与未来方向 / Limitations & Future Directions

### 本研究局限
{{Be explicit:
- What topics/angles couldn't be covered and why
- Methodological limits (web-accessible sources, paywall, language, timing)
- Source coverage gaps and counter-claim evidence gaps
}}

### 未来方向
{{Concrete suggestions for follow-up research with priority and responsible evidence type.}}

---

## 参考文献 / References

[1] Author/Org. "Title". Source-Type: official/academic/secondary-industry/journalism/community/other. As Of: YYYY-MM-DD. URL.
[2] Author/Org. "Title". Source-Type: ... As Of: YYYY-MM-DD. URL.

Rules:
- Every [n] in body MUST have matching entry here
- Every entry here MUST be cited at least once
- Source-Type and As Of fields are mandatory
- All URLs MUST come from actual search results (P2 source pool)

---

## 附录：多媒体佐证 / Appendix: Multimedia Evidence

{{所有本地化并下载成功的佐证图片，采用标准相对路径 Markdown 图片嵌入格式，方便其他 LLM 直接阅读，例如：}}
- !["[描述：如2024年全球中重稀土开采与冶炼份额占比饼图，展示中国在冶炼环节占全球89%份额...]"](assets/task-a_1716943800_sha256.png "全球中重稀土开采冶炼占比")
- !["[描述：如芯片供应链系统架构图，包含原材料、设计、制造、封测和组装五个阶段...]"](assets/task-b_1716943800_sha256.png "芯片供应链系统架构图")
