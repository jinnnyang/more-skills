# Role Creator: Autonomous AI Agent Architect 🤖✨

An advanced metacognitive skill designed to structure, diagnose, and compile production-ready, 7-dimensional configuration suites for professional AI Agents.

---

## 📖 Core Philosophy

Instead of treating Large Language Models as simple "long prompt receivers," `role-creator` models AI agents as **dynamic job containers**. A production-ready agent is defined by a modular, decoupled architecture rather than a single monolithic prompt:

1. **`SOUL.md` (Mindset & Core Values)**: Underlying ethics, filters, and resolution of core tensions.
2. **`IDENTITY.md` (Persona & Boundaries)**: External appearance, greeting tone, and hard boundaries (red lines).
3. **`AGENTS.md` (SOPs & Checklists)**: Step-by-step Standard Operating Procedures and robust Pre-flight Checklists (Type A for parsing validation; Type B for aesthetic verification).
4. **`PERSONALITY.md` (Workplace Persona)**: Tailored behavior options optimized for tone and execution efficiency.
5. **`TOOLS.md` (Physical Action Interfaces)**: Granular, orthogonal command-line tool definitions mapped to the filesystem.
6. **`WIKI.md` (Compiled Knowledge)**: A dense entity network inspired by Karpathy's "Stop Retrieving, Start Compiling" paradigm.
7. **`BOOTSTRAP.md` & `HEARTBEAT.md` (Execution Hooks)**: Runtime initialization guidelines and recurring background loops.

---

## 🛠️ Features

* **Phase 1: Grill-Me Diagnostic Pipeline**: Step-by-step interview targeting upstream/downstream integrations, tool design, and agent type classification (Type A: Deterministic vs. Type B: Creative).
* **Decoupled 7-Dimensional Config Suites**: Automatically compiles the modular configuration directory structure under `profiles/<role-name>/`.
* **Karpathy-Style Self-Compiling WIKI**: Sets up a dynamic schema to capture domain knowledge, platform hard constraints, and a compilation protocol for learning from runtime failures.
* **Incremental Optimization**: Supports refining existing agents via precise git-diff patches rather than rewriting entire config suites.

---

## 📂 Generated Structure

When you create a role (e.g., `wechat-author`), the skill generates the following structure:
```text
profiles/wechat-author/
├── SOUL.md          # Values & Tensions
├── IDENTITY.md      # Tone & Red Lines
├── AGENTS.md        # Step-by-step SOP & Pre-flight Checklists
├── PERSONALITY.md   # Choose execution personalities (e.g. Pragmatic vs. Aesthetic)
├── TOOLS.md         # Mapped local execution tools & CLI interfaces
├── WIKI.md          # Compiled domain entities & quality metrics
├── BOOTSTRAP.md     # First-run credential setup
└── HEARTBEAT.md     # Loop frequencies and cron list
```

---

## 🚀 How to Use

### 1. Create a New Role
Invoke the skill using any of the trigger words:
> **Trigger Words**: `造人`, `做个角色`, `创建智能体`, `/role-creator`, `生成角色`

**Example Command:**
```bash
/role-creator translator
```

### 2. Optimize an Existing Role
Provide details of the optimization or feed back execution errors:
```bash
Optimize the wechat-author agent's pre-flight checks to filter out empty lines in raw notes.
```
The skill will analyze the current files in `profiles/wechat-author/` and suggest a localized markdown diff.

---

## 🧪 Testing & Evaluation

Tests are located under the `evals/` folder. Use the `/skill-creator` workspace evaluation system to run and assert output correctness:

```bash
# Run evaluations
python scripts/run_evals.py --skill role-creator
```
Verify assertion rates via `grading.json` generated in target outputs.
