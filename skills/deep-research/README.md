# Deep Research (Engineered Research Skill Documentation)

`deep-research` is the core research and intelligence synthesis skill in the Antigravity Agent Framework. It is designed to generate high-quality research reports with strict format control, traceable evidence, source governance, and multi-pass synthesis.

Following this optimization, the skill has been upgraded to an **engineered persistent research version**. It fully supports cross-session Kanban project board tracking, localized multimedia archiving, plotting skill discovery with Mermaid fallback, and robust pre-flight environment checks.

---

## 🛠️ Core Capabilities

1. **Engineered Project Management**: Integrates independent project directory structures with Git version control. Each research project is isolated under its own kebab-case folder (e.g., `rare-earth-export-control-study`).
2. **Persistent Kanban State Tracking**: Uses `kanban/project_state.json` to serialize stages, subagent tasks, global citations, and media registries, supporting research resume and pause cycles.
3. **Multimedia Evidence Localization**: Subagents scan and mark web images in standard Markdown. The Lead Agent filters, downloads, localizes them to `assets/` before drafting, and rewrites URLs to relative paths.
4. **LLM-Friendly Alt Text Standards**: Localized media assets must be described with highly descriptive `alt` data trends to help downstream LLMs comprehend the visual details without image inputs.
5. **Diagram Plotting & Fallback Policy**: Prioritizes tool discovery to check for registered drawing/plotting skills (e.g. `canvas-design` or Python libraries). If found, it outputs PNG files to `assets/`; otherwise, it falls back to writing robust inline Mermaid syntax.
6. **Automated Pre-flight Environment Checks**: Integrates `check_env.py` to automatically check network latencies, Git CLI availability, directory write permissions, and required Python library packages.

---

## 📐 Core Design Patterns

### 1. Interactive Intake Mechanism
Prior to project initialization, the Lead Agent automatically generates **about 3 candidate options** based on the user's initial request:
- **Research Topic** suggestions
- **Scope & Boundaries** suggestions
- **Project Folder Name** suggestions
The user makes selection choices or minor adjustments, allowing swift intake.

### 2. Five-Stage Git Auto-Commit Lifecycle
To ensure data safety across long-running research cycles, the skill performs automated commits at key stages:
- **P1 Completion**: `stage: plan-initialized` (outlines and Kanban tasks designed)
- **P2 Completion**: `stage: research-notes-completed` (all raw task notes written back to `findings/`)
- **P4 Completion**: `stage: registry-outline-built` (citations audited and outline/diagrams designed)
- **P5 Completion**: `stage: draft-report-written` (initial draft completed)
- **P7 Completion**: `stage: report-finalized` (final reviews complete, media and Mermaid diagrams fully localized and verified)

---

## 📁 Directory Structure

Upon starting a new research project, the skill automatically initializes the following folder layout:

```
[project-name]/               # Project Root Directory (kebab-case)
  ├── .git/                  # Git Version Control Repository
  ├── assets/                # Localized images, charts, supply chain maps, etc.
  ├── findings/              # Raw findings and notes written by subagents (task-*.md)
  ├── tasks/                 # Task descriptions, queries, and logs
  ├── plan/                  # Research plans, boundaries, and outlines
  ├── kanban/                # Kanban and state database folder
  │     └── project_state.json # Kanban states, global citation registries, and media registries
  ├── README.md              # Project Overview (English, main entrypoint)
  └── README_zh-CN.md        # Project Overview (Chinese, main entrypoint)
```

---

## 🚀 Usage Guide

### 1. Run Pre-flight Checks
The Lead Agent runs this check automatically in P0. You can also run it manually under the `deep-research` skill root:
```bash
python scripts/check_env.py
```
*Note: This script tests connectivity to search engines (e.g., Bing, EuropePMC), verifies Git commands, checks write permissions, and tests for python dependencies.*

### 2. Start a New Research Project
When you request a research topic (e.g., "Research Rare Earth export restrictions"):
1. The skill starts the Interactive Intake and offers 3 suggestions for topic, boundaries, and folder name.
2. Once chosen, it initializes the project directory and Git repo.
3. It designs the task board in `kanban/project_state.json`.

### 3. Resume / Recover Interrupted Research
If a research run is interrupted, the skill reloads `kanban/project_state.json` on restart:
1. It loads all completed task findings.
2. It only dispatches tasks marked as `TODO` or `FAILED`.
3. It resumes seamlessly into media localization and report synthesis.

---

## 📅 CHANGELOG & Version Control

| Version | Milestone & Changes | Commit Hash |
| :--- | :--- | :--- |
| **v2.5.0** (Current) | **Engineered Persistent Version**: Project folder structures and Git tracking; Kanban JSON state management; multimedia localization and downloading pipeline; diagram plotting tool discovery & Mermaid fallback; pre-flight check script. | `Current Modification` |
| **v2.4.0** | Fixed source accessibility policy (circular verification vs exclusive advantages); updated citation registry formats; Counter-Review Team v2. | `693c403` |
| **v2.0.0** | Enterprise Research Mode with SWOT matrices and 3-level quality control. | `064c73e` |
| **v1.0.0** | Legacy deep research workflow. | `ffda537` |

### 🔄 Version Rollback & Auditing

If you need to roll back to a legacy version:

*   **Roll back to v2.4.0 (Counter-Review Team v2 without persistent engineering changes)**:
    ```bash
    git checkout 693c403 -- skills/deep-research/
    ```

*   **Roll back to v2.0.0 legacy enterprise mode**:
    ```bash
    git checkout 064c73e -- skills/deep-research/
    ```

*   **Discard all local changes and check out the latest repository version**:
    ```bash
    git checkout main -- skills/deep-research/
    ```
