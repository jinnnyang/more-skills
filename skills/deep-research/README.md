# Deep Research (Engineered Research Skill Documentation)

`deep-research` is the core research and intelligence synthesis skill in the Antigravity Agent Framework. It is designed to generate high-quality research reports with strict format control, traceable evidence, source governance, and multi-pass synthesis.

Following this optimization, the skill has been upgraded to an **engineered persistent research version**. It fully supports cross-session Markdown project board tracking, localized multimedia mapping, plotting skill discovery with Mermaid fallback, robust pre-flight environment checks, and Chinese-first modular execution guides.

---

## 🛠️ Core Capabilities

1. **Engineered Project Management**: Integrates independent project directory structures with Git version control. Each research project is isolated under its own kebab-case folder (e.g., `rare-earth-export-control-study`).
2. **Active Tool & Sibling Skill Discovery**: Automatically scans registered MCP tools and available workspace sibling skills (e.g., `pubmed-database`, `fact-checker`) in P0, explicitly prompting the user with the list of detected capabilities during intake for clear pipeline alignment.
3. **Adaptive Multi-Level Recursive Exploration**: Incorporates Depth (layers of recursive rabbit-hole digging) and Breadth (parallel queries per iteration) parameters. Subagents employ CoT reasoning to recursively retrieve insights down the citation graph and adaptively call specific sibling skills for domain-specific tasks.
4. **Persistent Task State Tracking**: Uses `task.md` to record and update stages, subagent tasks (with recursive parameters), global validated citations, and media registries, supporting research resume and pause cycles.
5. **Multimedia Evidence URL Policy**: Subagents scan and record web image URLs. The Lead Agent filters and audits Alt descriptions in P3 without downloading binary files, avoiding blocker errors associated with web scrapers.
6. **LLM-Friendly Alt Text Standards**: Captured media assets must be annotated with highly descriptive `alt` data trends (Markdown format: `!["alt"](url "title")` where both alt and title are mandatory) to help downstream LLMs comprehend the visual details without image inputs.
7. **Diagram Plotting & Fallback Policy**: Prioritizes tool discovery to check for registered drawing/plotting skills. If found, it outputs PNG files to `assets/` and links them relatively; otherwise, it falls back to writing robust inline Mermaid syntax.
8. **Automated Pre-flight Environment Checks**: Integrates `check_env.py` to automatically check network latencies, Git CLI availability, directory write permissions, and required Python packages. Missing Git or network timeouts are logged as Warnings and will not block execution.
9. **Giant Text Streaming & Resumption**: Refactors the drafting stage (P5) into segmented, section-by-section generation and stream appending (Loop-Append). Realizes a checkpoint-resume mechanism using the progress registry in `task.md`, and applies strict output budgeting for subagents, preventing token truncation errors.
10. **Workspace as Long-Term Memory**: Introduces a flat shared directory structure (`memories/`, `findings/`, `clues/`, `hypotheses/`). Lead and subagents periodically sync and write their discoveries and speculations into these folders, intentionally dropping raw scraped context to prevent memory overflow in super-large research projects.

---

## 📐 Core Design Patterns & Workflow Control

### 1. Interactive Intake Mechanism
Prior to project initialization, the Lead Agent automatically generates **about 3 candidate options** based on the user's initial request:
- **Research Topic** suggestions
- **Scope & Boundaries** suggestions
- **Project Folder Name** suggestions
The user makes selection choices or minor adjustments, allowing swift intake.

### 2. 3-Stage Git Auto-Commit Lifecycle
To ensure data safety across long-running research cycles and keep a clean history, the skill performs automated commits at key stages:
- **📌 [Git Auto-Commit 1/3]**: `stage: plan-initialized` (P1 completion: outlines and project tasks designed)
- **📌 [Git Auto-Commit 2/3]**: `stage: draft-report-written` (P5 completion: all draft sections appended and completed)
- **📌 [Git Auto-Commit 3/3]**: `stage: report-finalized` (P7 completion: final reviews complete, citations verified, and project archived)

---

## 📁 Directory Structure

Upon starting a new research project, the skill automatically initializes the following folder layout:

```
[project-name]/               # Project Root Directory (kebab-case)
  ├── .git/                  # Git Version Control Repository
  ├── task.md                # Task tracking and phase completion
  ├── plan.md                # Execution plan, boundaries, and outline logic
  ├── brief.md               # Static executive summary of the research goal
  ├── review.md              # Adversarial counter-review results
  ├── walkthrough.md         # Final dynamic run walkthrough
  ├── artifacts.md           # SMIS media registry
  ├── assets/                # Localized images, charts, supply chain maps, etc.
  ├── chapters/              # Drafted outline and individual chapter sections
  ├── scratch/               # Ephemeral scripts for plotting, stats, and testing
  ├── findings/              # Raw objective findings and notes written by subagents (task-*.md)
  ├── templates/             # Source templates for root markdown files
  ├── memories/              # Historical context and factual background memory
  ├── clues/                 # Unverified leads or potential exploration paths
  ├── hypotheses/            # Analytical deductions and logical assumptions generated by agents
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
*Note: This script tests connectivity to search engines (e.g., Bing, EuropePMC), verifies Git commands, checks write permissions, and tests for python dependencies (removing unused dependencies like PIL).*

### 2. Start a New Research Project
When you request a research topic (e.g., "Research Rare Earth export restrictions"):
1. The skill starts the Interactive Intake and offers 3 suggestions for topic, boundaries, and folder name.
2. Once chosen, it initializes the project directory and Git repo.
3. It designs the task board in `task.md`.

### 3. Resume / Recover Interrupted Research
If a research run is interrupted, the skill reloads `task.md` on restart:
1. It loads all completed task findings.
2. It only dispatches tasks marked as `TODO`.
3. It resumes seamlessly into citation data scrubbing, segmented report synthesis, and counter-review.
