# Phase 1: Task Board Planning

This phase guides the Lead Agent through decomposing the complex research topic into specific, parallel subtasks, assigning recursive depth/breadth settings, updating the Kanban board, and running the first milestone Git commit.

---

## 1. Task Decomposition, Settings, & Cross-Project Context
Based on the research boundaries, audience, and target language confirmed during the Phase 0 intake, decompose the main topic into **3 to 6 independent subtasks**. To equip each subtask with adaptive exploration and comparative capabilities, explicitly assign the following parameters:

* **Search Breadth (Breadth)**: The maximum number of parallel follow-up query branches generated during each recursive layer (recommended setting: `2 to 3`).
* **Search Depth (Depth)**: The maximum number of recursive bibliography-chasing layers allowed downward (recommended setting: `2 to 4`).
* **Sibling Skill Binding**: If sibling domain skills (e.g., `pubmed-database`, `clinical-trials-database`, or `doc-illustrator`) were discovered during Phase 0, bind them directly to the task instructions (e.g., *"Retrieve clinical trials prioritizing the clinical-trials-database skill"*).
* **Cross-Project Referencing (先验对比上下文)**: **If a relationship to an existing local project was aligned in P0**, enforce a hard rule requiring the subagent to **first read the core outputs of that project** (e.g., `read ../[existing-project-name]/report.md` or its findings) as primary context before executing new searches. This prevents the agent from hallucinating historical comparison metrics.

For each subtask, register:
- **Expert Role**: e.g., *"Semiconductor Material Analyst"*.
- **Objective**: Detailed description of what to uncover. For comparative subtasks, append: *"First read `../project-a/report.md` to extract historical baselines, then search web sources to compare new data."*
- **Initial Queries**: 2 to 3 high-value keyword searches.
- **Settings**: `Depth=[D], Breadth=[B]`.
- **Output File Path**: Directing outputs to a specific note file (e.g., `findings/task-{id}.md`).

*Note: If the research is in Enterprise mode, bypass this section and jump directly to [enterprise_workflow.md](../enterprise_workflow.md) to retrieve the specialized six-dimension task template.*

---

## 2. task.md Integration
Write the planned subtask list into the `## Phase 2: Subagent Dispatch Tasks` section of `task.md`, and advance Phase 1 to completed by checking off the Pre-flight items.

### Task Update Example:
```markdown
## Pre-flight Checklist
- `[x]` Run check_env.py
- `[x]` Initialize workspace directories
- `[x]` Create root artifacts

## Phase 2: Subagent Dispatch Tasks
- `[ ]` **Task A**: Policy Compliance Analyst | Objective: Map out rare earth export licenses and quota constraints | Settings: Depth=3, Breadth=2 | Output: findings/task-a.md
- `[ ]` **Task B**: Comparative Analyst | Objective: First read `../project-a/report.md` to extract historical baselines, then compare current market data | Settings: Depth=2, Breadth=3 | Output: findings/task-b.md
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
