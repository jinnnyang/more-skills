# Long-Form Research Report Template (V6)

This template defines the exact formatting and structural rules for the final Markdown research report (`report.md`) compiled by the Lead Agent.

---

## Report Structure Template

```markdown
# {Report Title / TITLE}

> Date: {DATE} | Sources Audited: {SOURCE_COUNT} | Mode: {MODE} | AS_OF: {AS_OF} | Official & Academic Share: {OFFICIAL_SHARE}

## Executive Summary

{Provide a dense, 200-400 word synthesis of the core findings, supply chain or technical impacts, critical conclusions, and primary recommendations.}

---

## Table of Contents

{Auto-generate a table of contents list based on the main chapter headers below.}

---

{Main Body Chapters - Appended section-by-section during Phase 5. Each section should range between 400-800 words.}

## 1. {Chapter 1 Title}

{Chapter body narrative. Must present objective, balanced arguments, using citation tags [1][2] for every claim. Propose counter-arguments and acknowledge gaps.}

### Visual & Data Integration Standards:
- **Specialized Visuals (Priority 1)**: Inspect the `artifacts.md` registry. If doc-illustrator has generated a local PNG, embed it immediately.
- **Mermaid Fallback (Priority 2)**: If fallback is chosen, embed a double-quote-protected Mermaid block.
- **Semantic Media Integration (MANDATORY)**: Embed visual and video assets using standard Markdown Alt-text (Pattern A) or semantic HTML wrappers (Pattern B) in the target output language under the Semantic Media Integration Standard (SMIS). Avoid custom blockquotes.

*Example Diagram Embedding (Chinese Adaptive Mode - Pattern A Simple Visual):*
![【占比饼图：2024年全球中重稀土在开采、冶炼及分离各环节的份额占比】开采端中国占比70%，冶炼及加工环节中国占比高达89%，其余份额零星分布在美澳和东南亚。稀土供应链呈现出“开采分布中度集中、冶炼环节绝对垄断”的不对称物理分布格局，中国在深加工冶炼端掌握定价权。结论：数据直接印证了西方在短期内无法完成“稀土脱钩”；若要保障尖端芯片及磁材供应，海外企业在2026年以前必须维持对中国冶炼产线的采购，否则将面临建厂周期带来的断供风险。](assets/supply_chain_share.png "2024年全球中重稀土供应链及中国份额占比饼图")

*Example Diagram Embedding (Chinese Adaptive Mode - Pattern B Complex Visual):*
<figure>
  <img src="assets/supply_chain_share.png" alt="【占比饼图】2024年全球中重稀土在开采、冶炼各环节份额分布图" />
  <figcaption><b>图 1.1: 2024年全球中重稀土供应链分布占比图</b> — 中国在开采端占70%，冶炼端占89%以上。展现了“开采分布中度集中、冶炼绝对垄断”的格局，中国拥有极强定价权。海外企业在2026年前必须与中国维持合作。 <a href="https://example.com/charts/supply-chain">[1]</a></figcaption>
</figure>

**Confidence Score**: High / Medium / Low
**Justification**: {Explain the score: level of citation cross-validation, recency of publication, authority of sources}
**Counter-Argument**: {Clearly state a contrasting claim or alternative explanation. If not fully validated, tag it as [unverified]}

---

## 2. {Chapter 2 Title}
...

---

## Key Controversies & Adversarial Views

- **Controversy 1**: [Contrasting claim A vs. counter-evidence B] [1][3]
- **Controversy 2**: [Alternative thesis C vs. data D] [2][4]

## Core Factual Findings (Findings Summary)

- **Finding 1**: [Primary high-value objective statement from the gathered evidence] [3]
- **Finding 2**: [Secondary high-value objective statement] [1][5]

---

## AI Synthesis & Strategic Projections (AI Insights)

- **Insight 1**: [Independent synthesis outlining upstream/downstream bottleneck correlations, policy trends, or hidden risks deduced from the data]
- **Insight 2**: [Higher-level prescriptive takeaway or causal inference distinct from simple fact-listing]

---

## Limitations & Future Directions

### Research Gaps & Limitations
- Scope constrained by publicly available online sources, language barriers, and strict paywalls.
- Lack of proprietary corporate secrets or raw patent licensing details [unverified].

### Future Research Recommendations
- Recommend deep expert interviews or targeted field audits for highly critical processing nodes.

---

## References

[1] Author/Organization. "Title of Literature/Report". Source-Type (official/academic/secondary-industry/journalism/community/other). Date: YYYY-MM-DD. URL.
[2] Author/Organization. "Title of Literature/Report". Source-Type. Date: YYYY-MM-DD. URL.

---

## Appendix: Multimedia Evidence (Appendix SMIS Registry)

{Washed list of all external media assets harvested during the research represented using SMIS standard Markdown Alt-text or semantic HTML wrappers in the target language.}

### Example Pattern A (Simple Visual):
- ![【流程图：全球半导体多级流程流向图】展现半导体制造的五个明确阶段：原材料（硅片、化学品）、设计、晶圆制造、封装测试、组装。呈现了高度地理集中且多国级联的生产制造特征，表明任何原料或封测单一节点的断裂都将瞬间瘫痪下游组装。由此推论，企业需维持至少90天的战略库存缓冲。](https://example.com/charts/semiconductor-chain.png "全球半导体供应链多级流程图") [2]

### Example Pattern B (Complex/Video Visual):
<figure>
  <img src="https://example.com/charts/semiconductor-chain.png" alt="【流程图】全球半导体多级流程流向图" />
  <figcaption><b>图 1.3: 全球半导体多级生产流程与多国级联制造流向图</b> — 展现从原材料、设计、晶圆厂，最终流向晶圆封测与组装的五个核心段落。证明任一节点受阻均能使下游组装停滞，强调企业需维持至少90天的缓冲区。 <a href="https://example.com/charts/semiconductor-chain">[2]</a></figcaption>
</figure>
```
