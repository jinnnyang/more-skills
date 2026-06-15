---
name: deep-research
description: |
  Generates structure-controlled research reports featuring environment-aware tool discovery, citation governance, adaptive recursive depth exploration, and phased stream-appending compilation.
  This skill MUST be activated when the user requests "help me investigate", "deep research", "review report", "indepth analysis", "competitive study", "industry report", or any work requiring robust factual backing, counter-arguments, and multi-media illustrations.
---

# Deep Research (Knowledge-Centric Foraging Model)

This skill utilizes a **modular phased instruction architecture** driven by a **Zettelkasten (Lab Notebook) philosophy**. To prevent context bloat and downstream LLM output truncation, the workflow completely rejects mechanical linear execution. Instead, it relies on a dynamic, recursive "Breathing Foraging Loop" where discoveries continually reshape the research map.

The Lead Agent **MUST execute this workflow phase-by-phase**, and only load and strictly execute the corresponding sub-phase instructions when transitioning to that phase.

---

## 📐 Phased Lifecycle & Routing Map

```mermaid
stateDiagram-v2
    [*] --> PreFlight: 接收用户请求

    state PreFlight {
        [*] --> VerifyCognitive: 执行 Pre-flight 认知校验
    }

    PreFlight --> P0_Setup

    state P0_Setup {
        [*] --> InitWorkspace: 探测环境与历史
        InitWorkspace --> CreateRoots: 初始化 root artifacts (task.md, plan.md, brief.md, artifacts.md)
        CreateRoots --> Git1: Git Commit 1/3 (plan-initialized)
    }

    P0_Setup --> P1_CognitiveMap

    state P1_CognitiveMap {
        [*] --> MapUnknowns: 梳理未知领域与核心假设
        MapUnknowns --> InitBacklog: 生成初始动态待办 (tasks.md)
    }

    P1_CognitiveMap --> P2_ForagingLoop

    state P2_ForagingLoop {
        [*] --> Inhale: 提取最高优任务，派发探测子智能体
        Inhale --> Capture: 子智能体提取原子洞见 (findings/[date]-[topic].md)
        Capture --> Exhale: 主智能体回收洞见，更新全局认知地图 (walkthrough.md)
        Exhale --> Refine: 裁剪过期任务，繁衍新探索分支 (tasks.md)
        Refine --> [*]: 边界收敛/任务池清空
        Refine --> Inhale: 循环探测
    }

    P2_ForagingLoop --> P3_Wash

    state P3_Wash {
        [*] --> WashCitations: 运行 wash_citations.py
        WashCitations --> SMIS: 审计多媒体资源 (artifacts.md)
    }

    P3_Wash --> P4_Outline

    state P4_Outline {
        [*] --> DesignOutline: 规划 chapters/outline.md
        DesignOutline --> MapEvidence: 映射证据与图表
    }

    P4_Outline --> P5_Drafting

    state P5_Drafting {
        [*] --> DraftChapters: 分片撰写 chapters/*.md
        DraftChapters --> Merge: 运行 merge_chapters.py
        Merge --> Git2: Git Commit 2/3 (draft-written)
    }

    P5_Drafting --> P6_P7_Review

    state P6_P7_Review {
        [*] --> CounterReview: 运行对抗性审查 (review.md)
        CounterReview --> Verify: 校验引文与图表
        Verify --> Git3: Git Commit 3/3 (report-finalized)
    }

    P6_P7_Review --> [*]
```

---

## 🔀 Output Language Adaptation (CRITICAL)

- **Adaptive Core Rule**: While the internal prompts, checklists, and guides in this skill are written in standard **Silicon Valley English**, the language of the final generated outputs (including `task.md`, `findings/task-*.md`, the final `[topic-slug]-report-<timestamp>.md`, and all **media/HTML wrappers**) MUST dynamically adapt to the user's primary input language context.
- **Language Matching**:
  - If the user interacts primarily in **Chinese**, the generated research findings, reports, and image/media descriptions (SMIS) MUST be compiled in **Chinese**.
  - If the user interacts primarily in **English**, all outputs MUST be compiled in **English**.
  - Always respect explicit language descriptors or system configurations if provided.

---

## 🚀 Execution Core Principles

1. **Lazy Loading**: Only read a phase's reference file when transitioning into it. Do NOT clutter the context by loading unrelated phase instructions in advance.
2. **Knowledge-Centric Zettelkasten (Context Optimization)**: For large research projects, agents MUST drop older context to avoid memory overflow. The workspace is a living lab notebook: `findings/` stores atomic, semantically-named knowledge cards (e.g., `findings/2026-05-huzhou-hsr.md`), NEVER generic `task-a.md` files.
3. **Environment & History Probing**: In P0, discover active drawing/illustration skills (like `doc-illustrator`), fact-checkers, and historic projects in `$HOME/projects/`. Use Grill-Me interaction to align on audience, depth, and cross-domain references.
4. **The Breathing Foraging Loop**: In P2, the Lead Agent acts as an Explorer. It dispatches short-lived subagents to forage. Upon their return, the Lead Agent MUST synthesize their atomic findings into the cognitive map (`walkthrough.md`) and dynamically prune/spawn new tasks in `tasks.md`.
5. **SMIS (Semantic Media Integration Standard)**: All visual and media assets (crawled web images, generated PNGs, or videos) MUST carry a rich, context-inferred description directly inside standard Markdown Alt-text (`![alt](url "title")`), or wrapped inside standard semantic HTML elements (like `<figure>`, `<figcaption>`, `<details>`, `<summary>`) to ensure full visual-less accessibility, clean Markdown layouts, and native downstream LLM comprehension. **Agents MUST actively collect internet charts/diagrams and append them to `artifacts.md` via their original URLs. The `scratch/` directory is exclusively for temporary coding/drawing scripts, not binary images.**
6. **Stream-Appending with Resume Support**: In P5, compile chapters as individual files in `chapters/`, then merge into `[topic-slug]-report-<timestamp>.md`. Track progress in `task.md`. If a crash occurs, resume seamlessly from the first pending chapter.
7. **Non-blocking Git Integration**: Git commits follow a hybrid model: three primary lifecycle commits PLUS dynamic, event-driven semantic commits during the P2 foraging loop. Run silently if the Git CLI is active; if unavailable, log a warning and continue.

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
