# Phase 1: Cognitive Map & Dynamic Backlog Setup

This phase guides the Lead Agent through establishing the initial cognitive map (`walkthrough.md`) and decomposing the core topic into an initial dynamic backlog of hypotheses and knowledge gaps in `tasks.md`.

---

## 1. Map Unknowns & Hypothesis Formulation
Based on the research boundaries, audience, and target language confirmed during the Phase 0 intake, decompose the main topic into **3 to 6 independent subtasks**. To equip each subtask with adaptive exploration and comparative capabilities, explicitly assign the following parameters:

* **Search Breadth (Breadth)**: The maximum number of parallel follow-up query branches generated during each recursive layer (recommended setting: `2 to 3`).
* **Search Depth (Depth)**: The maximum number of recursive bibliography-chasing layers allowed downward (recommended setting: `2 to 4`).
* **Sibling Skill Binding**: If sibling domain skills (e.g., `pubmed-database`, `clinical-trials-database`, or `doc-illustrator`) were discovered during Phase 0, bind them directly to the task instructions (e.g., *"Retrieve clinical trials prioritizing the clinical-trials-database skill"*).
* **Cross-Project Referencing (先验对比上下文)**: **If a relationship to an existing local project was aligned in P0**, enforce a hard rule requiring the subagent to **first read the core outputs of that project** (e.g., `read ../[existing-project-name]/report.md` or its findings) as primary context before executing new searches. This prevents the agent from hallucinating historical comparison metrics.

For each initial knowledge gap, register an item in the backlog:
- **Hypothesis / Knowledge Gap**: A precise description of the unknown (e.g., *"Is the 2026 Q1 housing sales drop nationwide or isolated to tier-3 cities?"*).
- **Initial Queries**: 2 to 3 high-value keyword searches.
- **Settings**: `Depth=[D], Breadth=[B]`.
- **Target Subagent Role**: e.g., *"Real Estate Market Data Analyst"*.

*Note: Do NOT pre-assign `findings/task-*.md` filenames. Subagents will generate their own semantic filenames upon discovery.*

*Note: If the research is in Enterprise mode, bypass this section and jump directly to [enterprise_workflow.md](../enterprise_workflow.md) to retrieve the specialized six-dimension task template.*

---

## 2. Dynamic Backlog Integration (tasks.md)
Write the initial hypotheses into the `## Phase 2: Dynamic Research Backlog` section of `tasks.md` (or `task.md`), and advance Phase 1 to completed by checking off the Pre-flight items.

### Backlog Update Example:
```markdown
## Pre-flight Checklist
- `[x]` Run check_env.py
- `[x]` Initialize workspace directories
- `[x]` Create root artifacts

## Phase 2: Dynamic Research Backlog
- `[ ]` **Gap**: Determine if new export licenses restrict specific heavy rare earths | Queries: "China heavy rare earth export quota 2026" | Settings: Depth=3, Breadth=2 | Role: Policy Compliance Analyst
- `[ ]` **Hypothesis**: The Q1 2026 housing sales drop is less severe in tier-1 cities compared to historical baselines | Queries: "tier 1 housing sales Q1 2026 vs 2024" | Settings: Depth=2, Breadth=3 | Role: Real Estate Market Data Analyst
```

---

## 3. First Lifecycle Git Commit 📌 [Silent Git Commit 1/3]
If the Git CLI is active in the environment, run the first milestone commit silently to lock down the taskboard skeleton:
```bash
git add .
git commit -m "stage: plan-initialized"
```
*(Note: For Continuation Research, since the old findings were safely tagged and purged in Phase 0, this commit establishes a clean, isolate baseline for the new round's tasks with zero historical file contamination.)*

---

## 4. Phase Completion Reporting Format
`[P1 complete] {N} tasks planned. Git Stage: plan-initialized.`
