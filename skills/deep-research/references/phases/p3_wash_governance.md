# Phase 3: Citation Washing & Semantic Media Audit (Citation Registry & Media Validation)

This phase guides the Lead Agent in compiling, de-duplicating, and cleansing all raw source citations from subagents, auditing collected media assets, and applying the Semantic Media Integration Standard (SMIS).

---

## 0. Skill Context Refresh (Crucial Cognitive Pause)
**Extremely Important**: Before starting any operations in this phase, the Lead Agent is highly prone to "skill amnesia" due to the massive context loaded during Phase 1 & 2.
- **Action**: Pause and explicitly **search and print out** the discovered drawing/illustration skills (e.g., `doc-illustrator`, `pretty-mermaid`) and verification skills (e.g., `fact-checker`) found during Phase 0.
- This prevents forgetting these powerful visualization skills and ensures they are accurately planned in subsequent drawing/diagramming tasks.

---

## 1. Global Citation Registry & Washing
1. **De-duplication & Global Indexing (Automated)**: Execute the script `python scripts/wash_citations.py` from the project root. This script automatically parses all `findings/task-*.md` files, deduplicates URLs safely, assigns unique global indices, and outputs to `citations.md` in the root directory. The Lead Agent MUST then read this output file directly to reference global citations, eliminating manual numbering errors.
2. **Quality Gate Auditing**:
   - **Standard Mode**: Global validated sources ≥ 12, independent domains ≥ 5, official/academic source share ≥ 30%. Max weight of any single source ≤ 25%.
   - **Lightweight Mode**: Global validated sources ≥ 6, independent domains ≥ 3, official/academic source share ≥ 20%. Max weight of any single source ≤ 30%.
   - *If target thresholds fail due to highly niche subjects, document the warning in `task.md` under Phase 3 checklist and continue. Do not block execution.*

---

## 2. Semantic Media Integration Standard (SMIS) Audit
Since binary files are not downloaded, the Lead Agent MUST audit and refine the textual alternative metadata and semantic HTML wrappers for all gathered external images or video links:
1. **Extraction**: Scan `findings/task-*.md` and pull all media assets from `## Media Assets`.
2. **Smart SMIS Auditing & Verification (CRITICAL)**:
   - Verify that subagents successfully encapsulated high-value media into either **Pattern A (Simple/Compact Alt-text)** or **Pattern B (Semantic HTML figure/details wrappers)**.
   - The Lead Agent **MUST perform a smart audit**: ensure the description correctly infers the original context, key metrics, and logical conclusions. Make sure that any formatting styling inside HTML wrappers uses standard HTML tags (`<b>`, `<i>`, `<a href="...">`) rather than Markdown formatting to guarantee rendering stability.
   - Refine or expand the subagent's drafted descriptions inside the `alt`, `<figcaption>`, or `<details>` tags in the target adaptive language (Chinese or English).
   - This ensures visual evidence natively preserves factual proof, drastically boosting final report credibility.
3. **Registry**:
   - Open the root `artifacts.md` file.
   - Save and register all audited, fully compliant SMIS media blocks under `## Registered Media` in `artifacts.md`. Format each entry strictly using `[Global Citation Number]: [SMIS Block]` (e.g., `[1]: ![Alt](url "Title")` or `[2]: <figure>...</figure>`).
   - If no media assets are harvested during the research, write `No media assets registered.` under `## Registered Media`.

---

## 3. Visualization and Fallback Discovery Decision
1. **Check Tool Availability**: Inspect the refresh cache from Step 0. Confirm if specialized drawing skills (e.g., `doc-illustrator`) or plotting libraries (e.g., `matplotlib`) are active.
2. **Decide Route**:
   - **Route A (Specialized Drawing)**: If `doc-illustrator` is available, note that specialized drawing is priority 1, and add a task under Phase 5 in `task.md` (e.g., `Invoke doc-illustrator for PNG generation`).
   - **Route B (Fallback)**: If no drawing skill is available, fallback to inline Mermaid.js diagrams.

---

## 4. task.md Updating
Mark the Phase 3 tasks as completed in the root `task.md` file, and advance the phase progress checklist.

### Task Board Update Example (Chinese Adaptive):
```markdown
## Phase 3: Wash & Governance
- `[x]` Run wash_citations.py
- `[x]` Audit SMIS Media
- `[x]` Quality Gate Check
```

*Note: Phase 3 does not require triggering a silent Git commit.*
