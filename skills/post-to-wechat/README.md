# post-to-wechat - WeChat Styling, Illustration, and Publishing Pipeline

A unified, comprehensive WeChat publishing pipeline that handles article styling, cover and illustration asset generation, image size optimization, and drafting to WeChat Official Accounts (微信公众号).

Original scripts and concepts are adapted from [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills). Special thanks to **Google Gemini** for the refactoring, optimization, and consolidation.

---

## Why We Merged

Initially, the WeChat publishing workflow was fragmented across several separate, highly-coupled skills:
- `baoyu-markdown-to-html` (Styling & layout conversion)
- `baoyu-cover-image` (Cover image prompt design)
- `baoyu-article-illustrator` (In-article visual aids design)
- `baoyu-compress-image` (Asset size compression)
- `baoyu-post-to-wechat` (API and CDP publishing)

By consolidating these functions into a single `post-to-wechat` skill, we have created a seamless publishing pipeline. This:
- **Reduces Overhead**: Prevents context-switching and configuration duplication across multiple separate skills.
- **Simplifies Pipelines**: Allows upstream content agents to simply output Markdown and pass it to a single terminal skill that handles everything from asset generation to publishing.

---

## Core Optimizations

During the consolidation process, several key enhancements were made to optimize execution speed, robustness, and AI agent self-correction capabilities:

1. **Inline Skill Execution Context**
   - Configured the skill as an **Inline skill** (omitting `context: fork` in frontmatter). This gives the executing agent full access to invoke other registered image skills (e.g., Codex `imagegen`, `baoyu-imagine`) and execute system commands.
2. **Prioritized Image Tool Selection**
   - Explicitly instructs the executing agent to look up and prioritize existing/native image generation skills (`imagegen`, `baoyu-imagine`, or native `generate_image` tools) before prompting the user.
3. **Cover & Illustration Guardrails**
   - Enforces strict `2.35:1` (or `1:1`) aspect ratios for WeChat banner covers while maintaining flexible aspect ratios for internal readability illustrations (flowcharts, comparisons, timelines).
4. **Auto-Compression Pipeline**
   - Integrated an automated image compression flow. If cover or body images exceed WeChat's file limits (e.g., 2MB for covers), they are automatically compressed to WebP/PNG using `compress-image.ts` before upload, avoiding API failures.
5. **Cross-Session Memory (`learnings.md`)**
   - Standardized a [learnings.md](learnings.md) memory file to log known environment issues (such as WeChat IP whitelists, Chrome profile locks, or macOS terminal permissions) so executing agents learn from previous runs.
6. **Structured Agent Guidance on Failure**
   - Modified the CLI scripts to print structured `[AGENT GUIDANCE — FALLBACK STRATEGY]` directly to `stderr` upon crash. This tells the executing agent exactly how to recover (e.g., whitelisting IPs, restarting Chrome, or falling back to CDP browser paste).
7. **Consolidated & Self-Contained Configuration (`EXTEND.md`)**
   - Merged styling, accounts, and image generation preferences into a single, structured `EXTEND.md` schema. Prioritizes self-contained configuration and `.env` credentials inside the skill folder (`skills/post-to-wechat/`).
8. **Integrated ClawHub WeChat Writing Reference**
   - Consolidated 4 major WeChat reference guides (`markdown-syntax-guide.md`, `viral-writing-methodology.md`, `theme-catalog.md`, `wechat-publishing-guide.md`) directly under the `references/` folder to guide executing agents on styling and visual structures.
9. **API Direct Publishing & Status Polling**
   - Upgraded `wechat-api.ts` to support direct publishing with the `--publish` flag (submits drafts and polls status until completion or timeout) and direct status queries with the `--publish-status <publish_id>` flag.
10. **Clean Removal of Legacy `.baoyu-skills` Dependencies**
    - Fully refactored config loaders and dotenv resolvers to drop obsolete `.baoyu-skills` paths, making the setup clean and fully contained in the skill folder.

---

## Directory Structure

```
skills/post-to-wechat/
├── SKILL.md                  # Unified skill workflow definitions
├── README.md                  # English documentation
├── README_zh-CN.md            # Chinese documentation
├── learnings.md              # Cross-session knowledge base
├── scripts/                  # Bundled execution scripts
│   ├── package.json          # Consolidated third-party dependencies
│   ├── compress-image.ts     # Jimp/Sharp/CLI image optimizer
│   ├── markdown-to-html.ts   # Markdown to HTML converter
│   ├── md-to-wechat.ts       # Conversion helper (handles placeholders)
│   ├── wechat-api.ts         # API upload & publishing (with direct publish & polling)
│   ├── wechat-article.ts     # CDP browser paste automation
│   └── ...                   # CDP and clipboard helpers
└── references/               # Style galleries and guides
    ├── cover/                # Cover palette & presets
    ├── illustration/         # Diagram templates & prompt guidelines
    ├── publishing/           # API credentials & first-time setup flow
    ├── markdown-syntax-guide.md   # Markdown syntax helper (38 points)
    ├── theme-catalog.md           # 94 themes catalog index
    ├── viral-writing-methodology.md # Visual hierarchy rules & layout playbook
    └── wechat-publishing-guide.md   # WeChat API & platform limits manual
```

---

## Credits & Special Thanks

- **Google Gemini**: Refactoring, planning, and executing the consolidation, adding agent self-healing features, and structuring the pipeline.
- **JimLiu/baoyu-skills**: The excellent foundation scripts and styling templates for WeChat publishing. (Repository: [github.com/JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)).
