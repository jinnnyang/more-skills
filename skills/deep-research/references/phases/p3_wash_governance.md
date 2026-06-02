# Phase 3: Citation Washing & Semantic Media Audit (Citation Registry & Media Validation)

This phase guides the Lead Agent in compiling, de-duplicating, and cleansing all raw source citations from subagents, auditing collected media assets, and applying the Semantic Media Integration Standard (SMIS).

---

## 0. Skill Context Refresh (Crucial Cognitive Pause)
**Extremely Important**: Before starting any operations in this phase, the Lead Agent is highly prone to "skill amnesia" due to the massive context loaded during Phase 1 & 2.
- **Action**: Pause and explicitly **search and print out** the discovered drawing/illustration skills (e.g., `doc-illustrator`, `pretty-mermaid`) and verification skills (e.g., `fact-checker`) found during Phase 0.
- This prevents forgetting these powerful visualization skills and ensures they are accurately planned in subsequent KANBAN.md drawing/diagramming tasks.

---

## 1. Global Citation Registry & Washing
1. **De-duplication & Global Indexing (Automated)**: Execute the script `python scripts/wash_citations.py` from the project root. This script automatically parses all `findings/task-*.md` files, deduplicates URLs safely, assigns unique global indices, and outputs to `kanban/citations_washed.md`. The Lead Agent MUST then read this output file to update the `KANBAN.md` registry, eliminating manual numbering errors.
2. **Quality Gate Auditing**:
   - **Standard Mode**: Global validated sources ≥ 12, independent domains ≥ 5, official/academic source share ≥ 30%. Max weight of any single source ≤ 25%.
   - **Lightweight Mode**: Global validated sources ≥ 6, independent domains ≥ 3, official/academic source share ≥ 20%. Max weight of any single source ≤ 30%.
   - *If target thresholds fail due to highly niche subjects, document the warning in KANBAN.md and continue. Do not block execution.*

---

## 2. Semantic Media Integration Standard (SMIS) Audit
Since binary files are not downloaded, the Lead Agent MUST audit and refine the textual alternative metadata and semantic HTML wrappers for all gathered external images or video links:
1. **Extraction**: Scan `findings/task-*.md` and pull all media assets from `## Media Assets`.
2. **Smart SMIS Auditing & Verification (CRITICAL)**:
   - Verify that subagents successfully encapsulated high-value media into either **Pattern A (Simple/Compact Alt-text)** or **Pattern B (Semantic HTML figure/details wrappers)**.
   - The Lead Agent **MUST perform a smart audit**: ensure the description correctly infers the original context, key metrics, and logical conclusions. Make sure that any formatting styling inside HTML wrappers uses standard HTML tags (`<b>`, `<i>`, `<a href="...">`) rather than Markdown formatting to guarantee rendering stability.
   - Refine or expand the subagent's drafted descriptions inside the `alt`, `<figcaption>`, or `<details>` tags in the target adaptive language (Chinese or English).
   - This ensures visual evidence natively preserves factual proof, drastically boosting final report credibility.
3. **Registry**: Save the audited, fully compliant SMIS media blocks under `## 5. Global Citations & Media Registry` in `KANBAN.md`.

---

## 3. Visualization and Fallback Discovery Decision
1. **Check Tool Availability**: Inspect the refresh cache from Step 0. Confirm if specialized drawing skills (e.g., `doc-illustrator`) or plotting libraries (e.g., `matplotlib`) are active.
2. **Decide Route**:
   - **Route A (Specialized Drawing)**: If `doc-illustrator` is available, mark: `Priority 1: Invoke doc-illustrator for PNG generation` in KANBAN.md.
   - **Route B (Fallback)**: If no drawing skill is available, mark: `Priority 2: Fallback to inline Mermaid.js diagrams` in KANBAN.md.

---

## 4. KANBAN.md Updating
Write the washed global citation list, audited SMIS media blocks, and visualization decisions to `kanban/KANBAN.md` under `## 5. Global Citations & Media Registry`, then advance the phase progress.

### Kanban Update Example (Chinese Adaptive):
```markdown
## 2. Phased Lifecycle Progress
...
- [x] P3: Citation Washing & Semantic Media Audit (Completed)
...

## 5. Global Citations & Media Registry

### Global Validated Citations (Citations)
- [1] Xinhua. "Latest Management Details on Rare Earth Export Quotas". Official Source. As Of: 2025-10. URL: https://example.com/china-rare-earth-policy

### Audited Media Assets (SMIS Compliant)

#### Pattern A (Simple Visuals):
- ![【占比饼图：2024年全球中重稀土开采与冶炼份额占比】中国在冶炼环节占89%份额，开采环节占70%以上，其余份额零星分布在美澳。数据直观展现了全球稀土开采相对分散但冶炼加工高度集中的极度不对称格局，印证了中国在中重稀土供应链上的卡脖子优势。西方企业短期内无法绕过中国的冶炼环节，必须在2026年以前保持合作。](https://example.com/charts/supply-chain.png "全球中重稀土开采冶炼占比") [1]

#### Pattern B (Complex Visuals):
<figure>
  <img src="https://example.com/workflow/license-audit.png" alt="【流程图】两部委出口许可证双向申报与合规审查流向" />
  <figcaption><b>图 1.2: 稀土出口两部委合规审查流程图</b> — 原网页条款指出，企业需依次经过企业申报、省商务厅初审、商务部与海关总署终审三大关卡，平均审批周期为60个工作日。这表明合规门槛将显著提高，跨国企业需提前 60 天以上规划物流。 <a href="https://example.com/policy/details">[1]</a></figcaption>
</figure>

### Visualization Decision
- Strategy: doc-illustrator discovered. Priority 1: Invoke doc-illustrator for PNG generation.
```

*Note: Phase 3 does not require triggering a silent Git commit.*
