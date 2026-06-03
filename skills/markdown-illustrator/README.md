# Markdown Illustrator Skill

A unified Markdown illustration and accessibility enrichment skill for AI agents. It dynamically analyzes Markdown article structure and content, designs cohesive visual tones, identifies Points of Interest (POI) anchors, and automatically generates, cites, or embeds high-quality visual aids. Additionally, it supports stock image accessibility enrichment, automatically using the Agent's native vision capabilities to describe existing images and populate missing `alt` and `title` tags. It supports SVG vector diagrams, native environment drawing, OpenAI-compatible APIs, fact-based web screenshot citations, and local asset copying.

---

## 🚀 Key Features

1. **Stock Image Accessibility Enrichment (Alt/Title Completion)**: Automatically scans existing images in the Markdown document, using the Agent's vision capabilities to describe their content and populate accurate `alt` descriptions and `title` tags.
2. **Global Visual Consistency Planning**: Establishes a visual tone and style board (colors, style tags) before new generation to ensure all illustrations in the same article look unified.
3. **Multi-Source Illustration Engines**:
   - **SVG Vector Diagram Engine**: Direct generation of dark-themed system architectures, flowcharts, and timelines, automatically compiled to high-fidelity `@2x PNG` assets.
   - **Fact-based Web Citation & Screenshot Engine**: Captures/references real-world screenshots (e.g., news bulletins, official notices, live application UIs) to back up factual claims.
   - **Agent Native & OpenAI-Compatible Engines**: Generates highly aesthetic, stylized concept illustrations and cover banner images using preset themes (e.g. Notion line art, glow glassmorphism).
4. **Asset Harvesting & Relational Copier**:
   - Scans specified directories for semantically relevant markdown files to harvest existing `!\[alt\](url "title")` images.
   - Automatically duplicates local images used as reference into the target document's `assets/` directory, maintaining a self-contained layout.
5. **MITTS Compliance & Quality Attributions**: Embeds semantic alt/title properties and appends structured MITTS (Multi-dimensional Image Textual Transmission) blocks requiring explicit `Image Source & Factual Basis` properties.
6. **Pre-flight Collaborative Discovery**: Validates Shell, Python interpreters, and SVG libraries dynamically for a reliable, zero-install workspace.

---

## 📁 Directory Structure

```
document-illustrator/
├── SKILL.md                 # Core instructions and engine selection rules
├── README.md                # Documentation (English)
├── README_zh-CN.md          # Documentation (Simplified Chinese)
├── learnings.md             # Cross-session operational memories
├── evals/
│   └── evals.json           # 20-case trigger evaluation suite
├── scripts/
│   ├── openai_client.py     # Robust pure Python HTTP client (Generations/Edits/Variations)
│   └── svg_to_png.py        # Windows-compatible SVG-to-PNG CLI wrapper (npx/rsvg-convert/inkscape)
└── references/              # Architectural layout rules & style palettes
    ├── svg/                 # Architecture, flowchart, and sequence SVG guides
    ├── presets/             # Gradient-glass, notion, and vector style prompts
    ├── palettes/            # Semantic color presets
    └── workflows/           # Prompt assembly guidelines
```

---

## 🛠️ Configuration and Environment Setup

To use the OpenAI-Compatible engine (e.g. Volcano Engine Doubao Seedream), add the following configurations to your `.env` file at the project root:

```env
# 1. API Base URL
DOCUMENT_ILLUSTRATOR_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3

# 2. API Key (Insert your real Volcano Engine Agent Plan credentials)
DOCUMENT_ILLUSTRATOR_API_KEY=your_real_api_key_here

# 3. Model Name to target
DOCUMENT_ILLUSTRATOR_MODEL_NAME=doubao-seedream-5.0-lite
```

---

## 🔍 Pre-flight Tool Discovery

On startup, this skill instructs the agent to dynamically query and check all registered tools and skills related to drawing or image generation in the active environment. It inspects argument structures dynamically, rather than assuming a hardcoded parameter specification, ensuring seamless cross-platform adaptability.

---

## 💖 Acknowledgements and References

We would like to express our gratitude and extend full credit to the following projects and technologies that inspired or were integrated during the consolidation of this skill:

- **[Document-illustrator-skill](https://github.com/op7418/Document-illustrator-skill)**: The primary reference implementation providing core document illustration logic and image embedding workflows.
- **[gpt_image_playground](https://github.com/CookSleep/gpt_image_playground)**: For playground testing paradigms, payload schemas, and mock API client structures.
- **[happy-figure](https://github.com/datawhalechina/happy-figure/tree/main)**: For aesthetic design guidelines, figure layouts, and presentation rules.
- **[baoyu-diagram](https://github.com)**: For the design patterns of beautiful dark-themed SVG vector layouts, semantic component palettes, and cross-platform Node/Python SVG rendering architectures.
- **[Volcano Engine (火山引擎) Doubao Seedream](https://www.volcengine.com)**: For providing high-performance, stylized image generation and variation capabilities, which guided our base64 reference-image payload structures and variations scripts.
- **[resvg-js](https://github.com/yisibl/resvg-js)**: For providing `@resvg/resvg-js-cli`, the blazing-fast Rust-powered converter that enables pixel-perfect SVG-to-PNG rendering across Windows, macOS, and Linux without native system library baggage.
- **[OpenAI API Specifications](https://platform.openai.com)**: For establishing the standard Image Generations, Variations, and Edits multipart payloads which serve as our core client API contract.
