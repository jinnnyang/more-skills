# Phase 2: Subagent Dispatch & Recursive Exploration

This phase guides the Lead Agent through initiating parallel subtask execution, running the adaptive recursive bibliographical-chasing loop (Rinse-and-Repeat), harvesting structured evidence, and formatting initial media assets.

---

## 1. Cross-Project Context Loading (先验对比上下文加载)
Before triggering any web search queries, if a subtask's objective contains a **cross-project comparison directive** (e.g., *"First read `../project-a/report.md`"*):
- The subagent MUST prioritize reading the specified historical report or findings from that local path.
- Ingest and store its key metrics, dates, and conclusions in active temporary context to enable horizontal comparison during the search. **DO NOT** make up or hallucinate comparative data without reading the actual file.

---

## 2. Recursive exploration Loop (Rinse-and-Repeat)
To break out of "information silos" and bypass search engine biases, each subagent executes an adaptive deep-dive recursion loop:

```
[Level 0: Initial Search] ──→ Run Initial Queries and fetch page full-text (DEEP Mode)
        │
[Knowledge Extraction] ──→ Parse raw facts and form initial "Learnings"
        │
[Gap Audit & Chain CoT] ──→ Analyze gaps in current Learnings, identify missing statistics
        │      └── 🧠 Generate up to [Breadth] Follow-up Queries via Chain-of-Thought
        │
[Chasing Down Rabbit Hole] ──→ Run follow-up searches and descend layers (Level 1 to Level Depth)
        │
[Loop Termination] ──→ Reached Depth ceiling, or zero new Learnings discovered in a layer
```

### Recursive Execution Rules:
1. **Level 0 (Base Layer)**: Execute initial queries assigned in KANBAN.md, fetch highly relevant full-text pages, and extract base objective facts.
2. **Follow-up Query Generation**: Run CoT analysis on current findings to find data conflicts or missing segments. Dynamically assemble up to `Breadth` highly precise query branches.
3. **Recursive Crawl**: Execute follow-up queries and merge fresh insights into the knowledge pool. Restrict the descent to at most `Depth` layers.
4. **Active Sibling Skill Invocation**: If highly domain-specific keywords are queried, prioritize calling the discovered sibling APIs (e.g., `pubmed-database` for medical research).

---

## 3. Dispatch Routing Modes

### Mode A: Subagent Mode (Recommended)
- The Lead Agent dispatches subtasks to parallel `research` subagents, passing the custom `Depth` and `Breadth` parameters.
- Subagents load the standard [subagent_prompt.md](../subagent_prompt.md), execute in isolated sandboxes, and write structured notes directly to `findings/task-*.md`.

### Mode B: Monolithic Fallback (Degraded Execution)
- If subagents are unavailable, the Lead Agent sequentially executes the recursive search.
- **CRITICAL**: The Lead Agent MUST clear full-text page cache from active context memory after completing each subtask to prevent context overflow and model distraction.

---

## 4. Source Governance & SMIS Gathering
All recorded literature and media assets MUST adhere to [research_notes_format.md](../research_notes_format.md).
* **Media Asset Registry**: Do NOT download binary image files. **ONLY record** their original Web URLs.
* **Initial SMIS Drafting**: Subagents MUST pre-draft a highly detailed, context-inferred description directly encapsulated inside standard Markdown Alt-text (Pattern A) or standard semantic HTML wrappers (Pattern B) using the Semantic Media Integration Standard (SMIS).
* **Language Adaptive**: Compile descriptions matching the main report's target output language context (dynamic Chinese/English adaptation).

---

## 5. Information Density & Independent Agent Insights
To prevent reports from becoming chaotic data dumps, every `findings/task-{id}.md` file MUST conform to these tight budgets:
- **## Research Findings (Findings)**: At most **10 core objective facts**, formatted as standalone single sentences with clear citation brackets (e.g., `[1]`).
- **## Deep Read Notes (Notes)**: Synthesize only 2 or 3 critical papers. Limit description to at most 4 lines per source.
- **## Agent Insights (Insights) [MANDATORY]**:
  - Based on the gathered facts and comparison data, **compile 2 or 3 independent, logical, and judgmental deductions** (e.g., supply chain risk rating, market bottleneck foresight, or tech maturity prognosis).
  - Explicitly distinguish objective facts from the agent's independent deductions.
  - *(Note: For continuation research, writing to these findings files cleanly overwrites the old baseline with a fresh, clean dataset.)*

---

## 6. Kanban Registry
Upon completion of all subtasks, the Lead Agent marks them as completed in `kanban/KANBAN.md`. Phase 2 does not require executing a silent Git commit.
