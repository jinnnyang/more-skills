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
   - Ingest the actual physical path of the user's home directory. Print this absolute path in your first reply to the user.
   - **Default Project Storage**: All deep-research projects MUST default to being created under the `$HOME/projects/` directory.

---

## 2. Progressive Tool & History Discovery
To avoid black-box execution, the Lead Agent **MUST actively discover** active tools and historical data before formulating the intake response:
1. **MCP Tool Discovery**: Discover active search and retrieval tools.
2. **Sibling Skill Discovery**: Check for active neighboring domain-specific skills (e.g., `doc-illustrator`).
3. **Historical Project Discovery**:
   - Scan subdirectories under `$HOME/projects/`. If a subdirectory contains a `task.md`, classify it as a historical research project.
4. **Intent Routing Analysis**:
   - Keyword match against history folder names to determine Continuation Research vs New Research.

---

## 3. Pre-flight Checklist Execution & Interactive Intake
Before formulating a response, the Lead Agent MUST evaluate the `pre_flight_cognitive_checklist.md` directly into the chat, demonstrating active "Skills over Primitives" evaluation. Then, run a sharp 1-2 round Q&A with the user.

### A. Intake Template: No Initial Topic Provided
If the user starts the skill without specifying a research topic, respond with:
```markdown
### 🛫 Pre-flight Verification
- [x] **Skill Audit**: Target skills to activate: `[AGENT MUST EXTRACT & WRITE EXACT SKILL NAMES HERE]`.

Hello! I am your Deep-Research Agent. Environment initialized:
- **Default Research Registry**: `$HOME/projects/` (Physical Path: [Resolved Absolute Path])
- **Active Domain Skills Discovered**: [List active tools/skills]

### 📂 Historical Research Projects Found
1. `project-a`
2. `project-b`

【Grill-Me Q&A Alignment】
1. Would you like to start a brand new topic, or continue an existing historical project?
2. Who is the target audience for this report?
3. **Adaptive Output Language**: I will automatically match my output language to your primary language. Let me know if you want to override this!
```

### B. Intake Template: Topic Provided (New Research)
If a new topic is identified, respond with proposed settings and a similar Grill-Me Q&A.

**Rule**: You MUST adjust your downstream planning based on user answers. Do NOT start fetching before the user confirms the parameters.

---

## 4. Project Directory & Artifact Initialization
Once aligned, navigate to the target directory `$HOME/projects/[project-name]` and run the corresponding setup:

### Pattern A: New Research Project
1. Create the project directory and run `git init` inside it.
2. Initialize subfolders: `assets/`, `findings/`, `chapters/`, `scratch/` (Note: `scratch/` is strictly for temporary coding scripts, plotting code, or data processing, NOT for downloading image artifacts).
3. Create root artifacts:
   - Copy `templates/task.md` to `task.md`
   - Copy `templates/plan.md` to `plan.md`
   - Copy `templates/brief.md` to `brief.md`
   - Copy `templates/review.md` to `review.md`
   - Copy `templates/walkthrough.md` to `walkthrough.md`
   - Copy `templates/artifacts.md` to `artifacts.md`
4. **Initialize brief.md**: Fill in `brief.md` with `Status: Setup`, the current date under `Last Updated`, and pre-populate the `Executive Summary` with a brief paragraph describing the initial research objective.
5. Populate `plan.md` with the aligned Project Information.

### Pattern B: Continuation Research
If writing a follow-up or expansion to an existing project:
1. **CRITICAL Structural Rule**: NEVER create nested subdirectories like `followups/`. Continuation research MUST remain flat in the original project root. The newly compiled reports will naturally co-exist in the root directory via timestamp differentiation.
2. **Base Version Tagging**: Run `git tag -a v[X.0.0]-base -m "Prior to new round"` to lock down historical state.
3. **Workspace Purging**: Delete/purge old Markdown files inside `findings/` to prevent cross-contamination. Old drafts in `chapters/` can be archived to an `archive/` folder.
4. Update `plan.md` to reflect the new expansion scope.

---

## 5. Phase Checklist (Tracked in task.md)
The Lead Agent must manually update the checkboxes in `task.md` as they progress through the 8 phases (P0 to P7). Do not hardcode the state here.
