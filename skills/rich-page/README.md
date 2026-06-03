# Rich Page Writing & Layout Skill

`rich-page` is a specialized workflow skill designed to assist agents in writing, drafting, and formatting high-quality articles, reports, blog posts, and WeChat Official Account essays with advanced layout design, text-to-image prompts, and structured content ratios.

---

## Core Features

1.  **Classic Content Ratios (631 & 361 Rules)**:
    -   **631 Track (Knowledge/Career/Growth/Tech)**: 60% Dry Content, 30% Hooks & Emotion, 10% Conversion.
    -   **361 Track (Emotional/Stories/Opinions)**: 30% Dry Content, 60% Hooks & Emotion, 10% Conversion.
2.  **Interactive Outline & Image Pacing (三段一图)**:
    -   Ensures visual breathing room by inserting one image for every ~3 paragraphs.
    -   Determines optimal visual styles, fixed color palettes (<= 3 colors), and aspect ratios (e.g. 16:9 for body, 2.35:1 for header).
3.  **Chunk-Based Drafting**:
    -   Writes articles section-by-section to ensure high-quality detail and logical coherence without dilution.
4.  **Prose Micro-Tuning**:
    -   Smooths out transition points at chunk boundaries during the final merging phase.
5.  **Automated Verification**:
    -   Bundles a `verify.js` tool to check word counts, image counts, image prompt alt-text length, and ratio compliance.

---

## File Structure

```
rich-page/
├── SKILL.md                  # Core skill instructions and phases
├── README.md                 # English documentation
├── README_zh-CN.md           # Chinese documentation
├── scripts/
│   ├── verify.js             # Automated layout & ratio verification script
│   └── grade_runs.js         # Benchmark grading helper script
├── references/
│   ├── styles/
│   │   └── feidieshuo-style.md # Baseline writing style profile
│   └── examples/
│       └── 杭州亚运会，是亏还是赚？.md # Reference finished article with paced images
└── evals/
    └── evals.json            # Target evaluation test cases
```

---

## Pacing & Alt-Text Prompt Guidelines
When placeholders are created for new images, the `alt` tag contains detailed composition, camera angle, subject, style, colors, and lighting instructions so it can serve directly as a text-to-image prompt (e.g., for DALL-E 3 or Midjourney).
-   **Header Image**: 900x383px. Key elements placed within the central 383x383px square safety zone.
-   **Body Images**: 900x500px (16:9). Consistent aspect ratio.

---

## Coordination With Other Skills

The `rich-page` skill is part of a complete writing, illustrating, formatting, and publishing ecosystem. The flow and logic connections between these skills are described below:

```mermaid
graph TD
    A[User Raw Input / Topic / Report] --> B[rich-page (Core Writer)]
    
    %% Prep phase
    SD[style-distiller] -.->|Extracts Style Profiles| S[references/styles/]
    S --> B
    
    DR[deep-research] <-->|Phase 1: Deep Fact Gathering & Research| B
    
    %% Core process
    B -->|Phase 2: Content Outline & Image Prompts| C[Draft Outline + Image Placeholders]
    
    %% Image Generation
    C --> DI[doc-illustrator]
    DI -->|Generates images from alt-text prompts| B
    
    %% Formatting
    B -->|Phase 5: Final Raw Markdown| PM[pretty-markdown]
    PM -->|Typographical cleanup & accessibility checks| D[Polished Markdown Document]
    
    %% Publishing
    D --> PW[post-to-wechat]
    PW -->|Publishes finished article| E((WeChat Official Account))
```

1.  **`style-distiller`**: Runs beforehand to extract and save writing style profiles (e.g. `feidieshuo-style.md`) into `references/styles/`. If multiple style configuration files exist in this directory, `rich-page` will recommend the best fit based on the topic and actively ask the user for confirmation.
2.  **`deep-research`**: Invoked by the agent in Phase 1 if the input report or user idea needs more facts or deep background research.
3.  **`doc-illustrator`**: In Phase 2 or 3, once images and prompt-ready alt-texts are planned, `doc-illustrator` handles the actual text-to-image generation.
4.  **`pretty-markdown`**: Runs post-draft to handle CJK-English spacing, typographic quotation marks, and format formatting.
5.  **`post-to-wechat`**: Takes the final polished markdown and publishes it directly to WeChat Official Accounts.
