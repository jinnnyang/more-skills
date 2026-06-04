---
name: deep-research
description: |
  Generates structure-controlled research reports featuring environment-aware tool discovery, citation governance, adaptive recursive depth exploration, and phased stream-appending compilation.
  This skill MUST be activated when the user requests "help me investigate", "deep research", "review report", "indepth analysis", "competitive study", "industry report", or any work requiring robust factual backing, counter-arguments, and multi-media illustrations.
---

# Deep Research (Lead Agent Main Routing Instruction)

This skill utilizes a **modular phased instruction architecture**. To prevent context bloat and downstream LLM output truncation (avoiding `max_output_tokens` limits) when compiling long reports, core execution details are partitioned into specialized phase files.

The Lead Agent **MUST execute this workflow phase-by-phase**, and only load and strictly execute the corresponding sub-phase instructions when transitioning to that phase.

---

## 📐 Phased Lifecycle & Routing Map

```
Lead Agent (Main Router Entry - Minimal Context Footprint)
  │
  ├── [Pre-flight] Cognitive Verification ──→ Load references/pre_flight_cognitive_checklist.md
  │    └── Enforce "Skills over Primitives" evaluation before triggering P0.
  │
  ├── [P0] Setup, Probing, & Grill-Me Alignment ──→ Load references/phases/p0_setup.md
  │    └── Scan environment, discover history, perform elite Grill-Me Q&A, initialize KANBAN/Git.
  │
  ├── [P1] Task Decomposition & Recursion Planning ──→ Load references/phases/p1_taskboard.md
  │    └── Assign Depth and Breadth parameters, plan subtasks.
  │    └── 📌 [Silent Git Commit 1/3]: stage: plan-initialized
  │
  ├── [P2] Subagent Adaptive Deep Dive ──→ Load references/phases/p2_dispatch.md
  │    └── Recursively gather literature and findings, write to findings/task-*.md.
  │
  ├── [P3] Citation Washing & Semantic Media Audit ──→ Load references/phases/p3_wash_governance.md
  │    └── De-duplicate citations, perform smart semantic media audit (SMIS Alt/HTML tags).
  │
  ├── [P4] Outline Mapping & Visual Planning ──→ Load references/phases/p4_outline.md
  │    └── Set up pending sections in KANBAN.md, plan image/Mermaid placements and SMIS wrappers.
  │
  ├── [P5] Phased Section Drafting & Appending ──→ Load references/phases/p5_drafting_append.md
  │    └── Draft section-by-section (400-800 words/chapter) and stream-append to report.md.
  │    └── 📌 [Silent Git Commit 2/3]: stage: draft-report-written
  │
  ├── [P6] Counter-Review & Bias Auditing ──→ Load references/phases/p6_p7_review_verify.md
  │    └── Perform adversarial self-review, challenge core claims, insert Key Controversies.
  │
  └── [P7] Verification, Archiving, & Packaging ──→ Load references/phases/p6_p7_review_verify.md
       └── Verify citations/Mermaid, archive README, run final commit.
       └── 📌 [Silent Git Commit 3/3]: stage: report-finalized
```

---

## 🔀 Output Language Adaptation (CRITICAL)

- **Adaptive Core Rule**: While the internal prompts, checklists, and guides in this skill are written in standard **Silicon Valley English**, the language of the final generated outputs (including `KANBAN.md`, `findings/task-*.md`, the final `report.md` chapters, and all **media/HTML wrappers**) MUST dynamically adapt to the user's primary input language context.
- **Language Matching**:
  - If the user interacts primarily in **Chinese**, the generated research findings, reports, and image/media descriptions (SMIS) MUST be compiled in **Chinese**.
  - If the user interacts primarily in **English**, all outputs MUST be compiled in **English**.
  - Always respect explicit language descriptors or system configurations if provided.

---

## 🚀 Execution Core Principles

1. **Lazy Loading**: Only read a phase's reference file when transitioning into it. Do NOT clutter the context by loading unrelated phase instructions in advance.
2. **Workspace as Long-Term Memory (Context Optimization)**: For super-large research projects, agents (Lead and Subagents) MUST atomize tasks and drop older context to avoid memory overflow. All agents MUST share states via a flat directory structure (`memories/`, `findings/`, `clues/`, `hypotheses/`). Agents should periodically read these folders to sync state, and explicitly write any valuable discoveries or guesses into them as Markdown files.
3. **Environment & History Probing**: In P0, discover active drawing/illustration skills (like `doc-illustrator`), fact-checkers, and historic projects in `$HOME/projects/`. Use Grill-Me interaction to align on audience, depth, and cross-domain references.
4. **Adaptive Deep Digging**: In P2, restrict subagents with Breadth and Depth parameters, allowing them to recursively follow citations and pool knowledge.
5. **SMIS (Semantic Media Integration Standard)**: All visual and media assets (crawled web images, generated PNGs, or videos) MUST carry a rich, context-inferred description directly inside standard Markdown Alt-text (`![alt](url "title")`), or wrapped inside standard semantic HTML elements (like `<figure>`, `<figcaption>`, `<details>`, `<summary>`) to ensure full visual-less accessibility, clean Markdown layouts, and native downstream LLM comprehension.
6. **Stream-Appending with Resume Support**: In P5, compile and append chapters one by one to `report.md`. Track progress in `KANBAN.md`. If a crash occurs, resume seamlessly from the first pending chapter.
7. **Non-blocking Git Integration**: Silent Git commits are restricted to **three primary lifecycle commits** and run silently if the Git CLI is active. If Git is unavailable, log a warning and continue without throwing an error.

---

## 📁 Reference Directory Index

- **[Pre-flight] Cognitive Checklist**: [pre_flight_cognitive_checklist.md](references/pre_flight_cognitive_checklist.md)
- **[P0] Setup, Probing, & Intake Initialization**: [p0_setup.md](references/phases/p0_setup.md)
- **[P1] Task Decomposition & KANBAN Setup**: [p1_taskboard.md](references/phases/p1_taskboard.md)
- **[P2] Subagent Dispatch & Recursive Exploration**: [p2_dispatch.md](references/phases/p2_dispatch.md)
- **[P3] Citation Washing & Semantic Media Audit**: [p3_wash_governance.md](references/phases/p3_wash_governance.md)
- **[P4] Outline Design & Visualization Planning**: [p4_outline.md](references/phases/p4_outline.md)
- **[P5] Segmented Drafting & Stream-Appending**: [p5_drafting_append.md](references/phases/p5_drafting_append.md)
- **[P6/P7] Review, Verification, & Project Packaging**: [p6_p7_review_verify.md](references/phases/p6_p7_review_verify.md)
- **[Enterprise] Specialized Corporate Analysis Overlay**: [enterprise_workflow.md](references/enterprise_workflow.md)
