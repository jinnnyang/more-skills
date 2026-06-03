---
name: rich-page
description: Write, draft, and format high-quality articles, reports, blog posts, and WeChat Official Account essays with advanced layout design, text-to-image prompts, and content structuring. Use this skill whenever the user wants to write a comprehensive article, convert a technical/dry report into an engaging story or essay, refine article outlines, plan image pacing and alt-text, or apply writing style profiles (like `feidieshuo-style.md`).
---

# Rich Page Writing & Layout Skill

This skill guides the agent through an interactive, high-quality, structured writing and layout planning workflow. It enforces classic content ratios (631/361 rules), chunk-based drafting, micro-tuned transitions, and strict image pacing.

---

## 1. Core Principles & Content Ratios

Before starting, classify the article's category to determine the structural ratio:

*   **Knowledge/Career/Growth/Tech Track (631 Rule)**:
    *   **60% Dry Content (干货)**: Core knowledge points, actionable steps, data, diagrams, case studies.
    *   **30% Hooks & Emotion (钩子+情绪)**: Hooks at the start of sections, suspense, painful realities, quotes, gold-sentence highlights.
    *   **10% Conversion (转化)**: End-of-article summary, call-to-action (likes, shares, subscriptions, comments).
*   **Emotional/Story/Opinion Track (361 Rule - Inverse)**:
    *   **30% Dry Content (干货)**: Key takeaways, lessons learned, or focal summary.
    *   **60% Story & Emotion (故事+情绪)**: Rich scenarios, personal anecdotes, emotional hooks, narrative drama.
    *   **10% Conversion (转化)**: Relatable summary, call-to-action.

---

## 2. Step-by-Step Writing Workflow

### Phase 1: Input Analysis & Style Determination
1.  **Analyze Input**: Read the user's raw idea, technical draft, or report. Identify the core theme, target audience, and primary message.
2.  **Determine Track**: Select either the **631 Track** or the **361 Track** based on the topic.
3.  **Select Style & Template**: Scan the `references/styles/` directory for available style files.
    *   If multiple styles exist, analyze the user's input topic/intent and **actively recommend one specific style** that fits the content best (explaining why).
    *   **Actively ask the user** which style they want to proceed with, presenting the list of available styles.
4.  **Determine Writing Language**: Set the default writing language to be the same as the selected style template (e.g., Chinese for `feidieshuo-style.md`). Confirm both style choice and language selection with the user before starting.

### Phase 2: Outline Refinement & Image Pacing Plan
1.  **Draft the Outline**: Create a detailed section-by-section outline. Distribute the word counts matching the chosen ratio (e.g. for a 2000-word article, map out 1200 / 600 / 200 words).
2.  **Pacing Images (三段一图)**: Plan to insert one image for every ~3 paragraphs (or every 1-2 mobile screens).
    *   For a 2000-word article, plan **4-5 images** (including a header image).
    *   **Image Types Selection**:
        *   **Explanatory (说明图)** (20%-30%): Mindmaps, charts, graphs to visualize dry content.
        *   **Emotional/Story (情绪/故事图)** (20%-30%): Photos, custom illustrations to match hooks/feelings.
        *   **Decorative (修饰图)** (50%-60%): High-quality abstract/scenic backgrounds to break text blocks.
    *   **Image Syntax & Prompt Language**: Prepare images using an HTML comment for the prompt and standard markdown for the image.
        *   If referencing existing local/web resources: Use the actual URL.
        *   If requesting new assets: Separate the AI prompt from the accessibility description. Put the AI generation instructions in an HTML comment (`<!-- PROMPT: ... -->`) above the image. The `alt` text inside the image tag `![alt]` must focus exclusively on **rich semantic accessibility** (tailored to the image type: e.g., describing character dynamics, data trends, or landscape moods) without technical noise like "vector style" or "lighting".
        *   *Prompt Language Rule*: Determine whether the AI image prompts (in HTML comments) should use:
            *   *Option 1 (Default)*: The same language as the style template / article.
            *   *Option 2*: English (expert AI prompt engineering style, optimized for Midjourney/DALL-E 3).
            *   *Option 3*: Custom language specified by the user. (Note: Accessibility `alt` texts should always remain in the article's language).
    *   **Image Dimensions**:
        *   **Header Image**: 900x383px (2.35:1). Core visual elements must be in the central 383x383px safety zone. Keep overlay text minimal.
        *   **Body Images**: 900x500px (16:9) or custom. Ensure all body images share the exact same aspect ratio for visual consistency.
        *   **GIFs**: Keep file size < 1MB. Total page image weight must be < 5MB.
3.  **Confirm with User**: Present the structured outline, image placement plan, and language preferences (both article language and image prompt language) to the user. Do not proceed until approved.

### Phase 3: Chunk-Based Drafting
To maintain high-quality details and logical coherence, write the article section-by-section (chunk-by-chunk) rather than generating the entire text in a single prompt.
1.  Apply the selected style constraints (e.g., short paragraphs <= 4 lines, CJK spacing, specific phrasing).
2.  Maintain the dry-to-hook ratio within each section.
3.  Embed the planned image placeholders `![alt](url "title")` at the exact designated transition points.

### Phase 4: Merging & Prose Micro-tuning
1.  **Merge Chunks**: Combine the generated drafts into a single markdown file.
2.  **Micro-tune Transitions**: Review the boundary junctions between sections. Rewrite sentences at these boundaries to ensure smooth, natural flow and logical connectivity.
3.  **Color & Layout Review**: Ensure the visual design is clean (no more than 3 colors in formatting/diagrams, consistent styling, no messy formatting).
4.  **Format Verification**: Run automated verification checks or review against checklist guidelines.

### Phase 5: Downstream Verification
Upon completing the draft:
1.  Run typography spacing (add space between CJK and English/numbers).
2.  Proactively offer to run `pretty-markdown` to double-check formatting, linting, and accessibility alt-text:
    ```bash
    node c:/Users/jinnn/Documents/more-skills/skills/pretty-markdown/cli.js <input.md> [output.md]
    ```

---

## 3. Image Generation & Accessibility Guide
When planning new image placeholders in Phase 2, strictly separate the AI prompt from the semantic accessibility text.

**1. AI Prompt (HTML Comment)**
Focus on visual rendering instructions for AI generation. Format: `<!-- PROMPT: [style/medium] depicting [subject] from [camera angle/perspective]. The composition features [placement details]. The lighting is [light type] with a color palette of [color names]. [Detailed visual context]. -->`

**2. Accessibility Alt-Text (The `alt` attribute)**
The goal is to **paint a vivid picture in the blind person's mind** that matches the image's purpose:
- **For character/story images**: Describe *who* is there, *what* they are doing, spatial relationships (e.g., who is standing on the left/right, implying power dynamics), and facial expressions.
- **For charts/diagrams**: Describe the core data trend, comparison, or structural takeaway.
- **For decorative/abstract images**: Describe the core subject, physical layout, and emotional tone.
Exclude all technical aesthetic terms (no mentions of "vector", "lighting", "camera angle").

**3. Title (The `title` attribute)**
Use this for a very brief, high-level summary of the image's function or topic.

Example:
```markdown
<!-- PROMPT: A minimal flat vector illustration depicting a business team celebrating a success from a front perspective. The composition features three stylized characters raised-hand high-five in the center. The lighting is bright and even with a color palette of deep blue, bright orange, and soft gray. Clean white background. -->
![在办公室场景中，三名商业人士正在击掌庆祝。站在正中间的女性高管面带自信的微笑，她的手势最高，主导着整个庆祝动作；而站在她左侧和右侧的两名男性下属则身体微微前倾，面带钦佩地看向她，体态暗示了他们在团队中的辅助角色。](./assets/milestone.png "团队里程碑")
```

---

## 4. Checklist & Avoidance List
- [ ] Are paragraphs short and readable? (Under 4 lines each)
- [ ] Does the word count split match the target ratio (631 vs 361)?
- [ ] Is image placement paced at approximately "三段一图" (one image per 3 paragraphs)?
- [ ] Do new images separate AI prompts (HTML comments) from semantic accessibility alt-texts?
- [ ] Are the accessibility alt-texts appropriately rich for their image type (e.g., character dynamics, data trends) and free of technical visual noise?
- [ ] Are all body images matching the same aspect ratio (e.g., 16:9)?
- [ ] Have the chunk transition points been micro-tuned for smoothness?
- [ ] Did you avoid using stock watermark-like images or mixed illustration styles?
