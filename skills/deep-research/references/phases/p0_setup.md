# Phase 0: Setup, Probing, & Interactive Intake

This phase guides the Lead Agent through environmental validation, progressive tool and history discovery, and elite "Grill-Me" interactive alignment to map boundaries, initialize the workspace, and setup version control.

---

## 1. Environment Verification & OS Path Ingestion
Before executing any research tasks, the Lead Agent MUST:
1. **Run Verification Script**:
   ```bash
   python scripts/check_env.py
   ```
   - *Blocking Errors*: If network checks fail entirely or the current working directory lacks write permissions, stop and report the error immediately.
   - *Non-blocking Warnings*: If Git is missing, print a warning: `"Local Git CLI is not found; skipping silent version-control tracking commits."` **DO NOT** block execution.
2. **Resolve OS Path Variables**:
   - Ingest the actual physical path of the user's home directory (e.g., run `echo %USERPROFILE%` on Windows, or `echo $HOME` on macOS/Linux). Print this absolute path in your first reply to the user.
   - **Default Project Storage**: All deep-research projects MUST default to being created and gathered under the `$HOME/projects/` directory.

---

## 2. Progressive Tool & History Discovery
To avoid black-box execution, the Lead Agent **MUST actively discover** active tools and historical data before formulating the intake response:
1. **MCP Tool Discovery**: Discover active search and retrieval tools (e.g., `bing_search`, `read_url_content`).
2. **Sibling Skill Discovery**: Check for active neighboring domain-specific skills (e.g., `pubmed-database`, `fact-checker`, or `doc-illustrator`).
3. **Historical Project Discovery**:
   - Scan subdirectories under the default path `$HOME/projects/`. If a subdirectory contains a `kanban/KANBAN.md`, classify it as a historical research project.
   - Extract the project names and core topics. Limit the list to **at most 10 results**.
4. **Intent Routing Analysis**:
   - If the user provided a `<Topic>` in the initial request, perform keyword matching against discovered history folder names to determine if this is a **Continuation Research** request (existing project) or a **New Research** request.

---

## 3. Pre-flight Checklist Execution & Interactive Intake
Before formulating a response, the Lead Agent MUST evaluate and print the first two modules (1/5 & 2/5) of the `pre_flight_cognitive_checklist.md` directly into the chat, demonstrating active "Skills over Primitives" evaluation. Then, run a sharp 1-2 round Q&A with the user.

### A. Intake Template: No Initial Topic Provided
If the user starts the skill without specifying a research topic, respond with:
```markdown
### 🛫 Pre-flight Verification
- [x] **Skill Audit**: Evaluated `<skills>`. Highly relevant domain skills found: `[AGENT MUST EXTRACT & WRITE EXACT SKILL NAMES HERE (e.g. pubmed-database, finance-tool), OR 'None']`.
- [x] **Data Triage**: Checked `$HOME/projects/`. Will prioritize MCP/Proprietary data before primitive web searches.

Hello! I am your Deep-Research Agent. I have analyzed your local environment:
- **Default Research Registry**: `$HOME/projects/` (Physical Path: [Resolved Absolute Path])
- **Active Domain Skills Discovered**: [List tools/skills, e.g., doc-illustrator, fact-checker]

### 📂 Historical Research Projects Found (Select to continue research)
1. `project-a` (Topic: ...)
2. `project-b` (Topic: ...)

### 💡 Trending Research Suggestions (AI Generated Tech Topics)
- Suggestion A: [AI-curated hot topic]
- Suggestion B: [AI-curated hot topic]

【Grill-Me Q&A Alignment】
1. Would you like to start a brand new topic, or continue an existing historical project?
2. Who is the target audience for this report (Executive Decision Maker vs. Technical R&D)?
3. **Adaptive Output Language**: I will automatically match my output language to your primary language (e.g., Chinese if you type in Chinese, English if in English). Let me know if you want to override this and specify a different target language!
```

### B. Intake Template: Topic Provided (New Research)
If a new topic is identified from the user's initial prompt, respond with:
```markdown
### 🛫 Pre-flight Verification
- [x] **Skill Audit**: Evaluated `<skills>`. Target skills to activate: `[AGENT MUST EXTRACT & WRITE EXACT SKILL NAMES HERE]`.
- [x] **Data Triage**: Checked `$HOME/projects/`. Will prioritize MCP/Proprietary data before primitive web searches.

Hello! Environment initialized.
- **Default Research Registry**: `$HOME/projects/` (Physical Path: [Resolved Absolute Path])
- **Active Domain Skills Discovered**: [List active tools/skills]

**Proposed Research Parameters**:
- **Project Folder**: `$HOME/projects/[kebab-case-name]`
- **Recursive Depth Settings**: Depth = 3, Breadth = 2
- **Output Language**: Automatically adapting to your input language (e.g., Chinese/English).

【Grill-Me Q&A Alignment】
To ensure maximum precision and sharpness in this report:
1. Is the proposed storage registry path and kebab-case directory name correct?
2. Is this report intended for high-level executive decision-making or deep technical R&D?
3. Should we draw cross-domain references or compare data with your existing local project [Project A]?
```

**Rule**: You MUST adjust your downstream planning and `KANBAN.md` based on user answers. Do NOT start planning or fetching before the user confirms the storage path, target audience, and language.

---

## 4. Project Directory & Git Initialization
Once aligned, navigate to the target directory `$HOME/projects/[project-name]` and run the corresponding setup:

### Pattern A: New Research Project
1. If the directory does not exist, create it and run `git init` inside it.
2. Initialize subfolders: `assets/`, `findings/`, `tasks/`, `plan/`, `kanban/`.
3. Generate the initial `KANBAN.md` (see Section 5), completing Phase 0.

### Pattern B: Continuation Research
If writing a follow-up or expansion to an existing project:
1. **Base Version Tagging**:
   Run `git tag -a v[X.0.0]-base -m "Prior to new round"` to lock down the historical state. If no tag exists, default to `v1.0.0-base`.
2. **KANBAN.md Archiving**:
   Open `kanban/KANBAN.md`. Cut the previous "Phased Lifecycle Progress" and "Taskboard" sections and paste them into the `## 6. Historical Archive` section at the bottom. Re-initialize the active checklists at the top.
3. **Workspace Purging**:
   Having secured the history via Git tags, **permanently delete/purge** all old Markdown files inside the `findings/` and `tasks/` directories. This prevents old subagent results from polluting or blending into the new research round. Complete Phase 0.

---

## 5. Initial Kanban Schema (`kanban/KANBAN.md`)

```markdown
# Research Kanban: [project-name]

## 1. Project Information
- **Research Topic**: [Topic]
- **Target Audience & Boundaries**: [Aligned parameters from Grill-Me]
- **AS_OF Cutoff Date**: YYYY-MM-DD
- **Target Output Language**: [Adaptive (Chinese/English/Other)]
- **Cross-References**: [Relative path to other local projects, if any]

## 2. Phased Lifecycle Progress
- [x] P0: Setup, Probing, & Interactive Intake (Completed)
- [ ] P1: Task Decomposition & KANBAN Setup (TODO)
- [ ] P2: Subagent Dispatch & Recursive Exploration (TODO)
- [ ] P3: Citation Washing & Media MITTS Audit (TODO)
- [ ] P4: Outline Design & Visualization Planning (TODO)
- [ ] P5: Segmented Drafting & Stream-Appending (TODO)
- [ ] P6: Counter-Review & Bias Auditing (TODO)
- [ ] P7: Verification, Archiving, & Packaging (TODO)

## 3. Taskboard
(Populated during Phase 1)

## 4. Report Outline & Progress (P5 Enabled)
- **Draft Output File**: report.md

## 5. Global Citations & Media Registry
(Populated during Phase 3)

## 6. Historical Archive
[Applicable for Continuation Research: Stores old Kanban checklists and progression rounds]
```
