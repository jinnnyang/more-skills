---
name: markdown-illustrator
description: >
  Use this skill to analyze and illustrate Markdown articles ("为文章配图", "文章插图排版"). It automatically cleans accessibility attributes of stock images, establishes consistent visual brand boards, and generates/embeds high-quality diagrams, flowcharts, illustrations, or fact-based citation screenshots. It supports stock image alt/title enrichment via Agent vision, dark-themed SVG vector diagrams, Agent Native image generation, OpenAI-compatible APIs, and fact-based web screenshot references. When local image resources are referenced, it automatically performs relational copying to target directories, ensuring self-contained articles.
---

# Markdown Illustrator

A unified document illustration, accessibility enrichment, and diagramming tool.

## 🚀 Execution Workflow

### Step 0: Pre-flight Check (Collaborative Condition Checking)
Before generating any image or writing code, the agent MUST perform environment discovery:
1. **Cognitive Pause**: Output a brief plain-text plan detailing what needs verification before executing commands (e.g. checking OS/shell, python location, API keys, and conversion tools).
2. **Platform Probing**: Run native checks (`ver` or `$PSVersionTable` on Windows, `uname` on Linux/macOS) to identify OS and Shell.
3. **Python Check**: Ensure the Python command does not resolve to the Windows Store stub (which causes silent failures or opens the App Store). Identify and use the path of a real system or Conda Python interpreter if the stub is detected in PATH.
4. **Tool and Skill Listing**: Explicitly **list and inspect all drawing, illustration, or graphic generation tools and skills** registered in the active environment (e.g. tools like `generate_image`, `create_artwork` or skills like `pretty-mermaid`), and verify their schemas. Also verify if `.env` contains `DOCUMENT_ILLUSTRATOR_API_KEY` to check if the OpenAI-Compatible engine is configured.
5. **SVG Converter Probe**: Check if `npx`, `rsvg-convert`, or `inkscape` are in PATH to confirm if SVG-to-PNG rendering is supported.

### Workflow Phases
```
[Input Document]
       │
       ▼
[Step 1: Stock Image Enrichment] ──► Scan existing images, view contents via Agent Vision, and enrich empty alt/title tags
       │
       ▼
[Step 2: Visual Strategy & POIs] ──► Establish Brand Board (style, colors) & identify Point of Interest (POI) anchors
       │
       ▼
[Step 3: Harvesting & Engine Sel] ─► Harvest candidates from existing MD files or select engine (SVG/Native/OpenAI/Fact-based)
       │
       ▼
[Step 4: Asset Plan] ──────────────► Plan layout, sources, prompts, filenames, sizes, and relational copier actions
       │
       ▼
[Step 5: Execute & Copier] ────────► Generate or copy assets:
       │                             - SVG: Write code -> convert via scripts/svg_to_png.py
       │                             - Agent Native: Call discovered native tool
       │                             - OpenAI-Compatible: Run scripts/openai_client.py
       │                             - Fact-based Citation: Search/screenshot and apply Relational Copy to target
       │
       ▼
[Step 6: Document Embedding] ──────► Insert Markdown with alt/title & append MITTS (with Source Attribution)
```

---

## 🎨 Four Drawing Engines & Sourcing

### 1. SVG Vector Diagram Engine (Default for Tech/Flows)
- **Best For**: Systems architecture, flowcharts, timelines, mind maps, structural tables.
- **Workflow**:
  1. Write a clean, self-contained dark-themed SVG following the **Design System** below.
  2. Save it to `{output_dir}/[slug].svg`.
  3. Run the conversion script to render a high-quality `@2x PNG`:
     ```bash
     python scripts/svg_to_png.py <output_dir>/[slug].svg <output_dir>/[slug].png [width]
     ```
     *(If conversion fails due to missing dependencies, keep the `.svg` and advise the user; browsers can render SVGs natively).*

#### SVG Design System
- **Background**: Deep Slate `#0f172a` with a subtle grid.
  ```svg
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a"/>
  <rect width="100%" height="100%" fill="url(#grid)"/>
  ```
- **Semantic Colors**:
  - **Primary/Cyan**: `rgba(8, 51, 68, 0.4)` / `#22d3ee` (User-facing, frontend, inputs)
  - **Secondary/Emerald**: `rgba(6, 78, 59, 0.4)` / `#34d399` (Services, backend logic, APIs)
  - **Tertiary/Violet**: `rgba(76, 29, 149, 0.4)` / `#a78bfa` (Database, storage, persistence)
  - **Accent/Amber**: `rgba(120, 53, 15, 0.3)` / `#fbbf24` (Cloud infrastructure, regions)
  - **Alert/Rose**: `rgba(136, 19, 55, 0.4)` / `#fb7185` (Errors, security, boundaries)
- **Typography**: JetBrains Mono or SF Mono with monospaced fallback:
  - Title: 16px, bold
  - Components: 11-12px, semi-bold
  - Descriptions/Sublabels: 9px, regular, color `#94a3b8`

---

### 2. Agent Native Engine
- **Best For**: Quick, general concept illustrations, cover images, mockups, or when no custom API keys are available.
- **Workflow**:
  1. **Discover Tool**: Dynamically inspect the list of registered tools in the current environment to identify the platform's native image generator (e.g. `generate_image`, `create_artwork`, or platform-specific equivalent). Review its arguments and schema details. Do not assume or hardcode a specific schema.
  2. Draft a descriptive prompt containing style modifiers (e.g. `gradient-glass`, `vector-illustration`, `notion`).
  3. Call the discovered native tool using its exact defined schema structure.
  4. Copy/move the generated image from the tool's output directory to the document's `{article_dir}/assets/` directory.

---

### 3. OpenAI-Compatible Engine (Requires Configuration)
- **Best For**: Photorealistic, stylized, high-fidelity illustrations, reference-based variation (ref-to-image), or image-mask edits.
- **Environment Check**:
  Reads the following environment variables (from `.env` or system variables):
  - `DOCUMENT_ILLUSTRATOR_BASE_URL` (default: `https://api.openai.com/v1`)
  - `DOCUMENT_ILLUSTRATOR_API_KEY` (required)
  - `DOCUMENT_ILLUSTRATOR_MODEL_NAME` (default: `dall-e-3`)
- **Workflow**:
  Run the bundled helper script to communicate with the OpenAI-compatible endpoint:
  
  **Generate (Text-to-Image)**:
  ```bash
  python scripts/openai_client.py --mode generate --prompt "Your detailed visual prompt" --output <output_dir>/[slug].png --size 1024x1024
  ```

  **Variation (Image-to-Image / Style Anchor)**:
  ```bash
  python scripts/openai_client.py --mode variation --image <path_to_anchor.png> --output <output_dir>/[slug].png --size 1024x1024
  ```

  **Edit (Inpainting / Masking)**:
  ```bash
  python scripts/openai_client.py --mode edit --prompt "Add a futuristic server rack in the empty area" --image <base.png> --mask <mask.png> --output <output_dir>/[slug].png
  ```

---

### 4. Fact-based Web Citation & Screenshot Engine
- **Best For**: Factual proofs, news screen captures, official notices, live user interfaces, or verified graphics that back up a claim.
- **Workflow**:
  1. Detect key arguments or claims in the text that benefit from real-world proof (e.g., "据央视新闻报道", "Apple 官方声明中指出").
  2. Perform a web search or browse to fetch the actual screenshot, diagram, or official image.
  3. Save the image to `{output_dir}/[slug].png`.
  4. Ensure a clear Source Attribution (e.g. `[图片来源：央视新闻]`) is included in the alt, title, and MITTS block.

---

## 🌾 Asset Harvesting & Relational Copier (素材收割与关联复制)

When illustrating articles, the agent MUST inspect the local workspace to reuse existing assets or perform copying to keep the output self-contained:
1. **Existing Asset Harvesting**:
   - Before generating new assets, scan nearby Markdown files (particularly under `skills/pretty-markdown/waiting/` or configured folders) that are semantically related to the article topic.
   - Use regular expressions to extract existing references: `!\[(?P<alt>.*?)\]\((?P<url>.*?)(?:\s+"(?P<title>.*?)")?\)`
   - If an existing image (remote or local) matches the needed POI concept, consider it as a candidate.
2. **Relational Copying**:
   - If you select an image located in a local directory (e.g., `../waiting/some_folder/image.png`), you MUST perform a physical file copy of that image to the destination's `{article_dir}/assets/` folder.
   - Update the Markdown link in the target document to use the relative path pointing to the copied file: `![Alt](assets/image.png "Title")`.
3. **Alt & Title Quality Rules**:
   - Never write empty alt or title attributes.
   - Format: `![Detailed description of the image content](assets/path.png "Brief title/source")`.

---

## 🖼️ Stock Image Accessibility Enrichment (存量图片无障碍化富化)

Before performing new illustrations, the agent MUST scan the input Markdown document for existing image nodes and enrich their metadata using its own vision capabilities:
1. **Target Identification**:
   - Find all `![alt](url "title")` image tags.
   - If the `alt` attribute is empty, placeholder-like, or shorter than 5 characters, or if the `title` attribute is missing, mark it for enrichment.
2. **Vision Analysis**:
   - For local images (e.g. `assets/image.png`), use the `view_file` tool to open and view the image.
   - For remote images, use web/browser tools to retrieve a visual description.
   - Use surrounding paragraph text to understand the context.
3. **Tag Enrichment**:
   - Write a descriptive, accurate, and concise `alt` text in the target language of the article.
   - Write a clear, short `title` text.
   - Do NOT run any external scripts or call extra models; perform the description generation directly using the agent's native vision capability.
   - Replace the tag in the Markdown file in-place: `![Detailed alt description](url "Concise Title")`.

---

## 📐 Step 6: Document Embedding & MITTS Specifications

When embedding any generated illustration (SVG, Agent Native, or OpenAI-Compatible) into a document or article, the agent MUST adhere to the **Multi-dimensional Image Textual Transmission Standard (MITTS)**. This ensures downstream LLMs and assistive technologies can fully comprehend the visual structure, data points, and analytical conclusions without seeing the image pixels.

### 1. Language Adaptation Rule (CRITICAL)
- **Primary Rule**: The language of the MITTS block MUST dynamically adapt to the primary language of the target document or the user's input context (e.g., if the document is written in Chinese, use Chinese for MITTS; if written in English, use English for MITTS; or follow any explicit language descriptors).

### 2. Embedding Structure
Immediately below the standard Markdown image tag, insert a blockquote with the following four-dimensional structure:

**For Chinese Output (自适应中文输出模式)**:
```markdown
![{图片描述}](assets/{图片别名}.png "{图片标题}")
> 💡 **图表多维文本透传 (LLM & 读屏友好)**：
> - **图表类型与核心主题**：[图表类型，如：系统架构流程图，展示从 Blogwatcher 采集到投资信号生成的全自动化流程]
> - **核心组件与关键数据/流向**：[主要组件与关键流向，如：包含：1. Blogwatcher 定时新闻抓取；2. 网页清洗与去噪；3. 转换为 Markdown 日报；4. read-all 本地分析提取信号；5. 输出为 JSON 数据库与看板提示]
> - **业务逻辑/核心趋势描述**：[业务逻辑描述，如：展示了非结构化数据向高价值结构化信号级联提纯的完整数据流向，表明各组件之间为解耦的本地化流式协作关系]
> - **推导结论与商业/技术价值**：[判断性结论，如：数据印证了本地化自动化流水线能够完全去除人工噪音，将整体分析延迟从小时级缩短至分钟级，是内容运营效率提升的典型示范]
> - **图片来源与事实依据**：[图片来源，如：央视新闻官方微博截图 / 自行截图 / 绘图引擎生成 / 引用自 waiting/ 目录下的 index.md 关联复制资源]
```

**For English Output (Adaptive English Output Mode)**:
```markdown
![{Image Description}](assets/{image_name}.png "{Image Title}")
> 💡 **Multi-dimensional Image Textual Transmission (LLM & Screen-Reader Friendly)**:
> - **Chart Type & Core Theme**: [Chart type and theme, e.g., System architecture flowchart showing the end-to-end automation from Blogwatcher scanning to investment signal generation]
> - **Core Components & Key Flows/Data**: [Major components and key flows, e.g., 1. Blogwatcher scan (ingestion) -> 2. Metadata parsing & noise filtering -> 3. Markdown daily report generation -> 4. read-all local parser execution -> 5. Investment Tracking Signals database update]
> - **Business Logic / Core Trend Description**: [Business logic description, e.g., Demonstrates a high-efficiency pipeline purifying raw unstructured news feeds into structured actionable insights, highlighting decoupled local-first services]
> - **Key Takeaways & Business/Technical Value**: [Conclusive takeaway, e.g., Proves that a local automated pipeline eliminates human selection noise and cuts analytical latency from hours to minutes, offering a premium pattern for local content operations]
> - **Image Source & Factual Basis**: [Image source and attribution, e.g., CCTV News official microblog screenshot / Local application UI screenshot / AI generated / Referenced and copied from waiting/ directory]
```

---

## 🛠️ Configuration & Storage Defaults

### Default Placement
- **Standard Mode**: Always write generated graphics to `{article_dir}/assets/`.
- **Snippet/Pasted Mode**: If the user pastes raw text in the chat directly, save illustrations to `./assets/` relative to the current working directory.
- **Markdown Insert**: Relative path `assets/[slug].png` (or `.svg`).

---

## 📝 Guide to Style Presets
When generating bitmap images (via Agent Native or OpenAI-Compatible), recommend one of these three primary styles to ensure visual harmony:

1. **Gradient Glass (`gradient-glass`)**: Modern tech-feel, transparent glass cards, soft neon glow, deep slate background. Best for dashboards and concept highlights.
2. **Notion Style (`notion`)**: Minimalist hand-drawn line art, black/white line thickness, intellectual. Best for tutorials and definitions.
3. **Vector Illustration (`vector-illustration`)**: Flat shapes, bold outlines, friendly pastel palette. Best for narratives and cover artwork.

---

## 🔧 Troubleshooting and Guidance

### API Key Missing
If the user requests the OpenAI-Compatible engine but `DOCUMENT_ILLUSTRATOR_API_KEY` is not found:
1. Alert the user that the key is missing.
2. Guide them on setting it in their `.env` file:
   ```env
   DOCUMENT_ILLUSTRATOR_API_KEY=your_key_here
   DOCUMENT_ILLUSTRATOR_BASE_URL=https://api.openai.com/v1
   DOCUMENT_ILLUSTRATOR_MODEL_NAME=dall-e-3
   ```
3. Offer to fall back to the **Agent Native** or **SVG** engines in the meantime.

---

## 🔗 Next Step: Image Compression & Publishing

After generating and embedding the illustrations, suggest the natural next pipeline step to the user:

```
Illustration generation complete!
Options:
A) Compress Images — Optimize generated PNG/SVG file size using the WeChat Publishing compressor (Recommended)
B) Publish to WeChat — Upload the illustrated article and cover directly to your WeChat Drafts
C) No thanks — Keep the current uncompressed local images
```
