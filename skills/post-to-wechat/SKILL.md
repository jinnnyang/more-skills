---
name: post-to-wechat
description: WeChat publishing pipeline. Generates cover images (2.35:1) and readability-enhancing article illustrations (infographics, diagrams, timelines) using existing image generation skills. Converts Markdown to styled WeChat HTML (with themes, colors, and bottom citations), and uploads/posts drafts or directly publishes to WeChat Official Accounts via API or Chrome CDP. Use when user wants to post/publish to WeChat (微信公众号), format markdown for WeChat (微信排版/转HTML), or generate covers/illustrations for a WeChat article (公众号配图/封面).
version: 2.0.0
metadata:
  openclaw:
    homepage: https://github.com/JimLiu/baoyu-skills#post-to-wechat
    requires:
      anyBins:
        - bun
        - npx
---

# post-to-wechat - WeChat Styling, Illustration, and Publishing Pipeline

This skill handles the entire WeChat publishing workflow, from cover/illustration asset generation and page styling, to uploading and creating/publishing drafts on WeChat Official Accounts (微信公众号).

---

## 📖 Reference Knowledge Documents (Mandatory Reading)

Before formatting articles, creating illustrations, or launching publishing runs, the agent **MUST** review the following references under the `references/` directory to adhere to WeChat's design guidelines:

1. **[markdown-syntax-guide.md](references/markdown-syntax-guide.md)**: 38 Markdown syntax points (Basic + Extended + Advanced) to ensure HTML rendering compliance.
2. **[viral-writing-methodology.md](references/viral-writing-methodology.md)**: Structuring rules (Hook types, Gold-standard 5-part layout, CTA interactive ending blocks, and the 70/100 quality score threshold).
3. **[theme-catalog.md](references/theme-catalog.md)**: 94 rendering themes categorized by scenario (Business, Tech, Retro, Classic). Choose a style matching the article topic and supply it to the compilation scripts.
4. **[wechat-publishing-guide.md](references/wechat-publishing-guide.md)**: Platform technical limits (e.g. image width limit of 677px, aspect ratios, error code tables, and security principles).

---

## 💻 System Requirements & Script Execution

`{baseDir}` = this SKILL.md file's directory. 
Resolve `${BUN}`: prefer `bun`; fallback to `npx -y bun`; else suggest installing Bun.
Run `bun install` in `{baseDir}/scripts/` before executing scripts for the first time.

| Script | Purpose |
|--------|---------|
| `scripts/markdown-to-html.ts` | Converts markdown to WeChat-ready HTML (retains local images/links) |
| `scripts/compress-image.ts` | Compresses/optimizes images to WebP/PNG formats to fit upload sizes |
| `scripts/wechat-api.ts` | Uploads content, creates drafts, and publishes via WeChat API (Recommended) |
| `scripts/wechat-article.ts` | Pastes content and uploads images via Chrome CDP automation |
| `scripts/wechat-browser.ts` | Creates image-text (图文) posts via Chrome CDP |

---

## ⚙️ Configuration (EXTEND.md)

The skill loads account credentials, theme presets, and image preferences from `EXTEND.md` directly under the skill directory (self-contained):
* `{baseDir}/EXTEND.md`

### First-Time Setup (BLOCKING)

If `EXTEND.md` is not found, the agent **MUST** run the guided setup flow using the `AskUserQuestion` tool before proceeding with any other workflows:
1. Refer to the setup questions and guide at `references/publishing/config/first-time-setup.md`.
2. Prompt the user with all setup choices in a single interactive call.
3. Write the generated `EXTEND.md` to `{baseDir}/EXTEND.md`, print a confirmation, and then load the configurations.

### Schema Template

```yaml
# WeChat accounts configuration
accounts:
  - alias: my-account       # Identifier used in --account <alias>
    name: "My Official Account"
    default: true
    publish_method: api     # api or browser
    default_author: "Author"
    app_id: "wx..."         # (Optional) For API publishing
    app_secret: "..."       # (Optional) For API publishing

# Default layout and styling preferences
default_theme: default      # default, grace, simple, modern, or any of the 94 catalog themes
default_color: orange       # Classic presets: blue, green, vermilion, orange, etc.

# Readability image generation settings
image_generation:
  preferred_backend: auto   # auto, imagegen, baoyu-imagine, ask
  auto_compress: true       # Compresses oversized images before upload
  max_cover_size_mb: 2.0    # Max file size limit for cover images
```

---

## 🧠 Strategic Operations & Content Planning (WeChat Native)

Before drafting or formatting, the agent acting in an operational or publisher role **MUST** adhere to the following top-level strategies designed specifically for the WeChat ecosystem:

### 1. Subscriber Persona & Dynamic Tagging
- Maintain detailed subscriber personas. Utilize WeChat's tag management to segment users based on behavior (e.g., interacted with a specific poll, activated mini-programs) for targeted future broadcasts.

### 2. Content Pillars & 60/30/10 Golden Ratio
- **Core Pillars**: Establish 4-5 core content themes mapped to the WeChat custom menu, acting as a mini-homepage index.
- **60% Value Content (干货)**: Focus on deep insights and practical value to capture "Search" (微信搜一搜) long-tail traffic and trigger social recommendations (看一看).
- **30% Interactive & Community (互动)**: Use comment hooks, polls, and "Star/在看" reminders to boost account engagement weight in the WeChat timeline algorithm.
- **10% Brand & Promotion (推广)**: Contextually embed Mini-program cards or promotional links without disrupting the reading flow.

### 3. Business Metrics Optimization Targets
- **Open Rate (打开率) 30%+ (CRITICAL THRESHOLD)**: **A mediocre or poor cover image will drastically reduce readers' interest in clicking (打开率), directly destroying the article's traffic potential.** The cover image is the single most critical factor in the user's split-second decision to tap. You MUST treat the cover design as a premium psychological hook, matching a high-impact title to trigger intense curiosity, emotional resonance, or professional aspiration. Always utilize a stunning, high-end 6-dimensional palette and design (2.35:1 ratio).
- **Read Completion Rate (完读率) 50%+**: Strictly enforce mobile-friendly readability (Golden 3-second hook, generous line spacing, visual breathing room, $\le 3$ lines per paragraph).
- **Mini-program Activation (小程序激活率) 40%+**: Contextually embed Mini-program cards at the exact moment the user's pain point is activated, minimizing click paths.

### 4. Boundaries & Security (Red Lines)
- The strategy/publisher agent strictly handles top-level planning, formatting, and invoking publishing APIs. It does **NOT** manually operate the account frontend, store payment details, or handle highly sensitive resources. 

---

## 🎨 Workflow 1: Premium Cover Design & In-Article Illustration Generation

Before formatting the article, analyze the markdown to identify opportunities to generate visual aids (cover and in-article illustrations) to enhance readability and maximize traffic potential.

### 🚨 The "Click-or-Die" WeChat Cover Principle (CRITICAL)
*   **The 0.5-Second Filter**: In the WeChat feed, users decide whether to read your article in under 0.5 seconds. The cover image occupies **80% of the visual space** in their timeline. A cheap, generic, or AI-hallucinated low-quality cover guarantees a dead article.
*   **High-End Visual Metaphors**: Never use boring stock photos, cluttered corporate graphics, or standard flowcharts as covers. Instead, design a clean visual metaphor that reflects the article's soul (e.g., an elegant minimal key unlocking a glowing digital vault, rather than a generic photo of a computer).
*   **Aesthetic Discipline**: Maintain generous whitespace (40-60% breathing room), a single strong visual anchor (centered or offset left), and absolute typographical clarity. Avoid text collisions with background details.

### WeChat Visual Hierarchy Rules (Mandatory)
*   **Paragraph Limit**: Every paragraph **MUST** be $\le 3$ lines on mobile screens, with a full blank line separator.
*   **Image Density**: Insert a subheading (`###`) and a supporting illustration/diagram approximately every **300 to 400 words**.
*   **Footer Links**: WeChat blocks external hyperlinks. All external links must be converted to footnotes (handled automatically by our compiler).

### Rules for Image Tool Selection (Critical Priority)
When rendering cover or in-article illustrations, the agent **MUST** prioritize available tools in this order:
1. **Registered Image Skills**: Check for registered skills like Codex `imagegen` or `baoyu-imagine`. If found, call it using the `Skill` tool.
2. **Native Tooling**: Check if the agent environment exposes a native image generation tool (e.g., `generate_image`). If so, invoke it directly.
3. **Prompt and Ask**: If no image generation skill or tool is registered, ask the user how to generate the image (do **not** write raw SVG or HTML art as a replacement).

### Step 1.1: Generate Cover Image (6-Dimensional Design & Psychological Hook)
Leverage the advanced cover generation frameworks located in `references/cover/` to craft a premium, high-impact masterpiece.
1. **Establish the Visual Metaphor & Psychological Hook**: Analyze the core thesis of the article. Determine a high-end visual metaphor and a psychological trigger (curiosity, gain, awe, or professional pride) that fits.
2. **Determine 6 Dimensions**: Analyze the article to select the appropriate combination of:
   - **Type**: hero, conceptual, typography, metaphor, scene, minimal
   - **Palette**: warm, elegant, cool, dark, earth, vivid, pastel, mono, retro, duotone, macaron
   - **Rendering**: flat-vector, hand-drawn, painterly, digital, pixel, chalk, screen-print
   - **Text**: none, title-only, title-subtitle, text-rich
   - **Mood**: subtle, balanced, bold
   - **Font**: clean, handwritten, serif, display
3. **Cover Dimensions**: Must use **2.35:1 aspect ratio** (or `--aspect 2.35:1`) for WeChat top-banner cover images, or **1:1** for secondary covers.
4. **Write Prompt**: Consult `references/cover/base-prompt.md` and save the structured image generation prompt to `{article_dir}/prompts/cover.md` before invoking the generator.
5. **Generate & Auto-Compress**: Call the image generator. If the output image file size exceeds `max_cover_size_mb` (default 2.0MB), compress it using the compressor script:
   ```bash
   ${BUN} {baseDir}/scripts/compress-image.ts {article_dir}/cover.png -f png -q 80
   ```

### Step 1.2: Identify and Generate In-Article Illustrations
1. **Scan Article**: Find sections, processes, comparisons, or data listings in the markdown where a diagram would improve reader comprehension (aiming for the 300-word density rule).
2. **Select Type & Style**:
   - **infographic**: for metrics and data.
   - **flowchart**: for processes or steps.
   - **framework**: for architectural components or models.
   - **comparison**: for side-by-side choices.
3. **Write Prompts**: Save each illustration prompt to `{article_dir}/prompts/{number}-{type}-{slug}.md`.
4. **Generate & Save**: Call the image generator and save images under `{article_dir}/imgs/`.
5. **Insert to Markdown**: Insert standard Markdown image blocks at the corresponding positions:
   ```markdown
   ![[Diagram description]](imgs/{number}-{type}-{slug}.png)
   ```

---

## 📝 Workflow 2: Layout & Styling (Markdown to WeChat HTML)

Once cover and illustration files are embedded in the markdown file, convert it to styled HTML ready for WeChat.

```bash
${BUN} {baseDir}/scripts/markdown-to-html.ts <markdown_file> --theme <theme> [--color <color>] [--cite]
```

### Conversion Settings
1. **Theme**: Resolve theme using this precedence: CLI `--theme` → `EXTEND.md` `default_theme` → `default`. Available: `default`, `grace`, `simple`, `modern`, or any matching theme name from `theme-catalog.md`.
2. **Color**: Resolve color using: CLI `--color` → `EXTEND.md` `default_color` → default theme color.
3. **Citations (`--cite`)**: Enable only if the user explicitly requests link citations or if the theme calls for it. Converts external URLs to numbered footnotes.

---

## 📤 Workflow 3: Distribution & Publishing to WeChat

Upload the styled article and assets to create drafts or directly publish in the WeChat Official Account Platform.

### Method A: API Publishing (Recommended)

Requires `app_id` and `app_secret` configured in `EXTEND.md` or as environment variables `WECHAT_APP_ID`/`WECHAT_APP_SECRET` (loaded from `{baseDir}/.env` or `<cwd>/.env`).

```bash
# Upload and save as a Draft (Default & Safe)
${BUN} {baseDir}/scripts/wechat-api.ts <file> --theme <theme> [--color <color>] [--cover <cover_path>] [--account <alias>] [--no-cite]

# Directly publish draft live to followers immediately
${BUN} {baseDir}/scripts/wechat-api.ts <file> --theme <theme> [--cover <cover_path>] [--account <alias>] --publish

# Query status of a specific publish job ID
${BUN} {baseDir}/scripts/wechat-api.ts --publish-status <publish_id> [--account <alias>]
```

*Note: For API drafts/posts, a cover image (`--cover`) is strictly required.*

### Method B: Browser CDP Automation (Fallback)

Use this when API keys are not available. It will open Chrome via CDP, prompt the user to scan the login QR code if needed, and paste the HTML content into the WeChat editor.

```bash
${BUN} {baseDir}/scripts/wechat-article.ts --markdown <markdown_file> --theme <theme> [--color <color>] [--account <alias>] [--no-cite]
```

### Image-Text (图文) Short Post Publishing

For quick posts consisting of plain text and multiple images (up to 9):

```bash
${BUN} {baseDir}/scripts/wechat-browser.ts --markdown <markdown_file> --images <images_dir> [--submit]
```

---

### 📝 Automated Logging for Data Feedback Loop

After ANY successful API publish or draft creation, the agent **MUST** write the structured publish results (including PostId, media_id, web links, status, and any error messages) to a local JSON log file in a designated directory (e.g., `publish-logs/YYYY-MM-DD-post.json` or as defined by the project). 
This guarantees a closed-loop data pipeline where a Data Assistant agent can later fetch 24h/7d analytics to optimize the 60/30/10 ratio and publish times.

---

## 📊 Completion Report Format

Upon completing a publishing pipeline run, output a structured summary:

```
WeChat Publishing Complete!

Article Information:
• Title: [Title]
• Author: [Author]
• Theme: [Theme name] | Color: [Color]
• Cover Image: [Local path] (Compressed: Yes/No)
• In-Article Illustrations: [N images generated and inserted]

Publishing Status:
✓ Draft saved to WeChat Official Account / Published Successfully
• Method: [API | Browser CDP]
• Account: [Account Alias]
• Media ID: [media_id] (API draft only)
• Publish ID: [publish_id] (API publish only)
• WeChat Link: [Web Link] (if available)
```
