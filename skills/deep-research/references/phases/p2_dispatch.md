# Phase 2: The Breathing Foraging Loop

This phase guides the Lead Agent through the dynamic "Breathing Foraging Loop": inhaling (dispatching explorers), capturing atomic insights (Zettelkasten), and exhaling (synthesizing the cognitive map and spawning new tasks).

---

## 1. The Breathing Foraging Loop (Core Mechanism)
Instead of static task dispatch, the Lead Agent MUST execute the following dynamic loop until all tasks in `tasks.md` are resolved or deemed out-of-scope:

### Step 1: Inhale (Dispatch & Explore)
- Read `tasks.md` and select the 1-2 most critical, foundational, or blocking "Unknowns/Hypotheses".
- Dispatch a short-lived `research` subagent for each selected task.
- **CRITICAL RULE**: The Lead Agent MUST NOT perform heavy web reading itself. It only acts as the Coordinator.

### Step 2: Capture (Zettelkasten Atomic Insights)
- The dispatched subagents perform their deep-dive searches.
- When a subagent discovers a meaningful fact, metric, or insight, it MUST NOT output a generic "task report". Instead, it writes a highly focused **Atomic Knowledge Card** to the `findings/` directory.
- **Naming Convention**: Files MUST be semantically named based on the discovery, e.g., `findings/[YYYY-MM-DD]-[3-4-word-summary].md` (like `findings/2026-01-housing-sales-drop.md`). NEVER use generic names like `task-a.md`.

### Step 3: Exhale (Synthesize & Refine)
- Once the subagents return, the Lead Agent reads the new atomic `.md` files in `findings/`.
- **Update the Cognitive Map**: The Lead Agent synthesizes these findings directly into `walkthrough.md`. The `walkthrough.md` acts as the project's running memory—a map of what is now known.
- **Dynamic Task Refinement**: Based on the new map, the Lead Agent updates `tasks.md`:
  - Cross out completed hypotheses.
  - Cross out hypotheses that are now obsolete.
  - **Spawn new tasks**: If the findings reveal new critical blindspots (within the boundaries of `plan.md`), append them to `tasks.md`.

---

## 2. Cross-Project Context Loading
Before triggering any web search queries, if a hypothesis contains a **cross-project comparison directive** (e.g., *"Compare against `../project-a/report.md`"*):
- The subagent MUST prioritize reading the specified historical report from that local path.
- Ingest its key metrics to enable horizontal comparison. DO NOT hallucinate comparative data.

---

## 3. Subagent Execution Rules & Context Shedding
To prevent "Session compressed" failures:
- **Subagent State Persistence**: Subagents MUST NOT run indefinitely. After completing one deep dive or reading 3-4 heavy web pages, they MUST dump their knowledge into semantic `findings/` files and media into `artifacts.md`. Then, they MUST terminate and return control to the Lead Agent.
- **Lead Agent Refresh**: If the Lead Agent has completed several Inhale-Exhale loops and its own context is growing large, it MUST pause, ensure `walkthrough.md` and `tasks.md` are fully updated, and spawn a `self` subagent to take over the remaining loop.

---

## 4. Source Governance & SMIS Gathering
All recorded literature and media assets MUST adhere to [research_notes_format.md](../research_notes_format.md).
* **Media Asset Registry**: Do NOT download binary image files. **ONLY record** their original Web URLs.
* **Initial SMIS Drafting**: Subagents MUST pre-draft a highly detailed description encapsulated inside standard Markdown Alt-text (Pattern A) or HTML wrappers (Pattern B).

---

## 5. Information Density (Zettelkasten Budgets)
To prevent chaotic data dumps, every atomic file in `findings/` MUST conform to these tight budgets:
- **Core Findings**: At most **10 objective facts**, formatted as single sentences with clear citations (e.g., `[1]`).
- **Agent Insights**: Based on the facts, compile 1 or 2 independent, logical deductions. Explicitly distinguish objective facts from independent deductions.

---

## 6. Loop Termination
Phase 2 concludes ONLY when `tasks.md` is empty of viable, in-scope tasks. Do not execute a silent Git commit in this phase.
