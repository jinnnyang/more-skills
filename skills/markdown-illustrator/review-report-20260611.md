# 🔍 `markdown-illustrator` Skill Review

A comprehensive quality review of the [markdown-illustrator](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator) skill — a 6-step pipeline for automatically illustrating Markdown articles with AI-generated images, Mermaid diagrams, SVG knowledge cards, and retrieved media.

---

## Executive Summary

The `markdown-illustrator` skill is **architecturally excellent** — one of the most sophisticated skill designs I've seen. It implements a clean 6-step closed-loop pipeline with progressive disclosure, clear data contracts between steps, and an impressive reference library (14 color palettes, 27 art styles, 3 canvas specs). The dual-use of the evaluation guide at Steps 1 and 6 creates a natural quality feedback loop.

However, the skill has **three categories of issues** that need attention before it's ready for distribution:

| Priority | Issue | Impact |
|----------|-------|--------|
| 🔴 Critical | Path numbering inconsistency in Guide 2 | Agent misroutes **every image** — Maps Gen-AI to Path 1 instead of Path 3 |
| 🔴 Critical | 11 hardcoded Linux paths + 8 hardcoded Windows paths | Breaks installation on any other machine |
| 🟡 High | Tool naming confusion (pretty-mermaid / beautiful-mermaid / mermaid-tool.ts) | Agent doesn't know which tool to call |
| 🟡 High | No dependency auto-detection | Scripts fail silently without `node_modules`, `mmdc`, etc. |
| 🟡 High | Image budget conflict: 5MB (Guide 1) vs 10MB (Guide 4a) | Contradictory constraints |
| 🟢 Medium | Guide size (2 guides near 500-line limit), learnings.md format, missing fallbacks | Reduces agent reliability in edge cases |

---

## Skill Metrics

| Metric | Value |
|--------|-------|
| SKILL.md | 115 lines / 7.8 KB |
| Guide files | 8 files, 2,033 lines / ~120 KB |
| Reference files | 44 files, 2,246 lines |
| Scripts | 2 TypeScript files + package.json |
| Total (excl. node_modules) | ~4,900 lines / 472 KB |
| Palettes | 14 (dune, forest-ink, ikb-blue, macaron, neon, ...) |
| Art styles | 27 (3d-clay, blueprint, chalkboard, editorial, ...) |
| Canvas specs | 3 (rednote cover, standard inline, wechat cover) |

---

## Per-File Analysis

### [SKILL.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/SKILL.md) — Pipeline Controller

**Rating: ⭐⭐⭐⭐ (Architecture: ⭐⭐⭐⭐⭐, Portability: ⭐⭐)**

The orchestrator is clean and readable. The Mermaid flowchart at the top gives immediate visual understanding of the pipeline. Each step has clear "指令" (instruction), "动作" (action), and "退场条件" (exit condition).

> [!CAUTION]
> **11 hardcoded absolute paths** (`/home/twait-halek/Documents/more-skills/...`) in `file://` links. These break portability entirely. Should use relative paths like `guides/1. image-text-evaluation-guide.md` instead.

> [!WARNING]
> The Pipeline Handoff section (lines 112–114) is sparse. Per skill-creator best practices, it should suggest natural next-step skills via a structured recommendation format.

---

### [1. image-text-evaluation-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/1.%20image-text-evaluation-guide.md) — Quality Evaluation (146 lines)

**Rating: ⭐⭐⭐⭐⭐**

Excellent dual-purpose guide used at both Step 1 (diagnosis) and Step 6 (re-evaluation). Defines a 5-dimension scoring rubric (图文匹配度, 配图密度, 图表多样性, 视觉层次, 信息编码) with concrete examples at each 1–5 level. The dual-mode design with separate "首次评估" and "终审" sections is clean.

- ✅ Clear entry/exit conditions
- ✅ Concrete scoring examples
- ✅ Smart reuse pattern (Steps 1 & 6)

---

### [2. illustration-spec-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/2.%20illustration-spec-writing-guide.md) — Visual Spec Planning (160 lines)

**Rating: ⭐⭐⭐⭐**

The "三维解耦" (3-dimension decoupling: platform × domain × identity) approach is creative and produces well-targeted visual recommendations. Includes a user confirmation checkpoint, which is good interactive design.

- ✅ Interactive user confirmation built in
- ✅ References to palettes/styles/canvas directories all valid
- 💡 Could explain *why* the 3-dimension decomposition works (helps the agent internalize the reasoning instead of just following steps)

---

### [2. illustration-spec-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/2.%20illustration-spec-writing-guide.md) — Visual Spec Planning (160 lines)

**Rating: ⭐⭐⭐ (downgraded due to critical bug)**

The "三维解耦" approach is creative. However, this guide contains the skill's most critical bug.

> [!CAUTION]
> **Path numbering inconsistency — will cause every image to be misrouted.**
>
> - **Step 4 (lines 77–81)** correctly maps: Path 1 = Charts/Flowcharts (Mermaid), Path 2 = Cards (SVG), Path 3 = Decorative (AI), Path 4 = Reality
> - **Step 5 (lines 88, 92–94)** INCORRECTLY maps: Path 1 = Gen-AI, Path 2 = Mermaid, Path 3 = SVG, Path 4 = Reality
> - **Output template (line 147)** also INCORRECT: `路径 1-生成图 / 路径 2-结构化图 / 路径 3-矢量图 / 路径 4-下载图`
>
> This means an agent following Step 5 will write "路径 1" for Gen-AI images in the plan.md, but Guide 3's router maps Path 1 → Mermaid. **Every image gets routed to the wrong generator.**

- ✅ Interactive user confirmation built in
- ✅ References to palettes/styles/canvas directories all valid
- ❌ **Critical path numbering bug** (Step 5 and output template)
- 💡 Could explain *why* the 3-dimension decomposition works

---

### [3. illustration-routing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/3.%20illustration-routing-guide.md) — Routing/Dispatch (129 lines)

**Rating: ⭐⭐⭐⭐**

Clear 4-path routing decision tree mapping illustration slots to generation methods. Examples help but the decision boundaries between paths are somewhat fuzzy.

- ✅ Clear routing logic
- ❌ 1 hardcoded absolute path (line 54)
- 💡 Could sharpen the heuristics for distinguishing "knowledge card vs. Mermaid diagram" — the current examples help but a more explicit decision matrix would reduce ambiguity

---

### [4a. ai-image-generation-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4a.%20ai-image-generation-guide.md) — AI Image Generation (449 lines)

**Rating: ⭐⭐⭐⭐**

The most detailed guide. The "Moonvy 提示词公式" (prompt formula) for structured prompt engineering is the crown jewel of this skill — excellent domain knowledge that would take users significant time to develop independently.

- ✅ Excellent prompt engineering methodology
- ✅ Concrete examples with before/after
- ⚠️ **At 449 lines, approaching the 500-line recommended limit**. The prompt formula reference (~150 lines) could be extracted to `references/moonvy-prompt-formula.md` to reduce guide size.
- ⚠️ **No tool availability check** — assumes `generate_image` or equivalent is available. Should include detection and fallback guidance.
- ⚠️ **Image budget conflict**: States single image ≤5MB and total ≤10MB, but Guide 1 says total ≤5MB. Needs unification.

---

### [4b. mermaid-diagram-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4b.%20mermaid-diagram-writing-guide.md) — Mermaid Diagrams (331 lines)

**Rating: ⭐⭐⭐⭐**

Comprehensive Mermaid syntax reference covering 13+ diagram types with theming. Well-integrated with the Sankey bug workaround from `learnings.md`.

- ✅ Syntax examples for each diagram type
- ✅ Theming integration with palette references
- ⚠️ References `mermaid-tool.ts` for validation but no auto-detection of `npx tsx` or `node_modules`
- ⚠️ **Frontmatter name mismatch**: frontmatter says `name: mermaid-chart-writing-guide` but filename says `mermaid-diagram-writing-guide`
- ⚠️ **Tool naming confusion**: Guide references "pretty-mermaid CLI" and `cli.js` but the actual tool is `mermaid-tool.ts` which imports `beautiful-mermaid`. Three different names for the same thing.

---

### [4c. svg-card-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4c.%20svg-card-writing-guide.md) — SVG Knowledge Cards (482 lines)

**Rating: ⭐⭐⭐⭐**

Detailed guide with multiple complete SVG card templates (hero card, comparison table, timeline, stats dashboard). Excellent styling guidance with palette integration.

- ✅ Multiple complete working examples
- ✅ Accessibility considerations
- ⚠️ **At 482 lines, this is the longest guide and nearly at the limit.** Consider extracting SVG templates into `assets/svg-templates/` to reduce guide size.

> [!CAUTION]
> **8 hardcoded Windows paths** (`file:///C:/Users/jinnn/Documents/more-skills/...`) on lines 19, 20, 30, 31, 430, 431, 432, 433. These appear to be from a different developer's machine and will not resolve on the current Linux system. All should be converted to relative paths.

- ⚠️ References `guizang-social-card-skill` (line 8) — an external skill dependency not defined anywhere. Legacy reference?
- ⚠️ SVG templates embed Google Fonts via `@import url(...)` — requires internet access at render time, no offline fallback mentioned.

---

### [4d. media-search-retrieval-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4d.%20media-search-retrieval-guide.md) — Media Search & Retrieval (232 lines)

**Rating: ⭐⭐⭐**

Guides local asset harvesting and web search with quality scoring. The local/web asset comparison decision process is clear.

- ✅ Clear local vs. web decision process
- ⚠️ Assumes web search tool availability without checking
- ⚠️ "多模态视觉质检" assumes the agent can analyze images — depends on model capabilities
- ⚠️ **Candidate log naming inconsistency**: Local harvester writes to `cand-local-images.md`, but unified contract expects `[article].cand.md`
- ⚠️ Embeds a simplified copy of `harvest-assets.ts` inline (~70 lines) — creates maintenance drift risk vs. the actual script
- 💡 Should include fallback guidance when web search or image analysis isn't available

---

### [5. image-assembly-validation-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/5.%20image-assembly-validation-guide.md) — Assembly & Validation (104 lines)

**Rating: ⭐⭐⭐⭐**

The bottom-up assembly algorithm (inserting from highest line number first to avoid line drift) is a smart engineering choice. Clean and concise.

- ✅ Smart assembly algorithm
- ✅ File existence validation
- ⚠️ References `mmdc` (mermaid-cli) without installation/detection check
- 💡 The "双轨制 Alt 合规性" concept could use a concrete example

---

### Scripts

#### [harvest-assets.ts](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/scripts/harvest-assets.ts) (7,250B)

**Rating: ⭐⭐⭐⭐** — Well-structured workspace scanner. Keyword-based filename matching works but is limited (misses generically-named images).

#### [mermaid-tool.ts](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/scripts/mermaid-tool.ts) (10,355B)

**Rating: ⭐⭐⭐⭐** — Solid Mermaid validation/rendering implementation using JSDOM + resvg-js. All dependencies declared in `package.json`.

> [!IMPORTANT]
> Neither script includes `[AGENT GUIDANCE]` output sections. Per skill-creator best practices, script outputs should guide the agent's next decision at key junctures.

---

### Reference Library

**Rating: ⭐⭐⭐⭐⭐**

The reference library is the hidden gem of this skill:
- **14 palettes** — each with hex codes, usage guidance, Mermaid theme snippets, and gradient stops
- **27 art styles** — each with prompt fragments, SVG styling rules, and visual design principles
- **3 canvas specs** — platform-specific safe zones and dimensions

The reference files are consistently formatted and provide "ready-to-use" fragments. This is a major strength.

---

### [learnings.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/learnings.md)

**Rating: ⭐⭐⭐**

Contains genuinely useful operational knowledge (Sankey diagram Unicode bug, radar/venn chart version requirements). However:

> [!WARNING]
> Doesn't follow the recommended three-section format:
> ```markdown
> ## Known Environment Issues
> ## Success Patterns  
> ## Failures & Anti-patterns
> ```
> Current format uses custom headers. Should be restructured for consistency.

---

## Proposed Changes (Priority-Ordered)

### 🔴 P0: Fix Hardcoded Paths

#### [MODIFY] [2. illustration-spec-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/2.%20illustration-spec-writing-guide.md)
Fix the path numbering in Step 5 (lines 88, 92–94) and the output template (line 147) to match the correct mapping used everywhere else:
- Path 1 = Mermaid (structured diagrams)
- Path 2 = SVG (knowledge cards)
- Path 3 = Gen-AI (decorative illustrations)
- Path 4 = Reality/Retrieval

#### [MODIFY] [SKILL.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/SKILL.md)
Replace all 10 absolute `file:///home/twait-halek/...` paths with relative paths.

#### [MODIFY] [4c. svg-card-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4c.%20svg-card-writing-guide.md)
Replace all 8 `file:///C:/Users/jinnn/...` Windows paths with relative paths.

#### [MODIFY] [3. illustration-routing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/3.%20illustration-routing-guide.md)
Fix 1 hardcoded absolute path on line 54.

---

### 🟡 P1: Fix Tool Naming Confusion

#### [MODIFY] [4b. mermaid-diagram-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4b.%20mermaid-diagram-writing-guide.md)
- Fix frontmatter `name` from `mermaid-chart-writing-guide` to `mermaid-diagram-writing-guide`
- Replace all references to "pretty-mermaid CLI" and `cli.js` with `mermaid-tool.ts`
- Clarify that `beautiful-mermaid` is the npm package used internally by `mermaid-tool.ts`

---

### 🟡 P2: Add Dependency Auto-Detection

#### [MODIFY] [SKILL.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/SKILL.md)
Add a "Step 0: Environment Check" before Step 1:
```markdown
### 步骤 0：环境检测 (Environment Detection)
在启动管线前，自动探测运行环境：
1. 检查 Node.js 是否可用：`which node`
2. 检查 scripts/node_modules 是否存在，不存在则 `cd scripts && npm install`
3. 检查图像生成工具可用性（generate_image 或其他绘图工具）
4. 检查网络搜索工具可用性
5. 向用户报告环境状态和可用的生成路径
```

---

### 🟡 P3: Unify Image Budget

Reconcile the contradictory total image budgets:
- Guide 1 says total ≤ 5MB
- Guide 4a says total ≤ 10MB

Pick one and update both guides.

---

### 🟢 P4: Guide Size Optimization

#### [MODIFY] [4a. ai-image-generation-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4a.%20ai-image-generation-guide.md)
Extract the Moonvy prompt formula reference (~150 lines) into a new file:

#### [NEW] `references/moonvy-prompt-formula.md`
Move the prompt formula specification here, keeping only a summary and `view_file` pointer in the guide.

#### [MODIFY] [4c. svg-card-writing-guide.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/guides/4c.%20svg-card-writing-guide.md)
Extract SVG template examples into `assets/svg-templates/`, keeping only 1–2 representative examples inline.

---

### 🟢 P5: Restructure learnings.md

#### [MODIFY] [learnings.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/learnings.md)
Restructure to use the recommended three-section format while preserving the valuable Sankey and Radar/Venn bug documentation.

---

### 🟢 P6: Add Script Output Guidance

#### [MODIFY] [harvest-assets.ts](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/scripts/harvest-assets.ts)
#### [MODIFY] [mermaid-tool.ts](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/scripts/mermaid-tool.ts)
Add `[AGENT GUIDANCE]` sections to script outputs at success/error paths.

---

### 🟢 P7: Enhance Pipeline Handoff

#### [MODIFY] [SKILL.md](file:///home/twait-halek/Documents/more-skills/skills/markdown-illustrator/SKILL.md)
Expand the Pipeline Handoff section with structured "Next Step" suggestions:
```markdown
## Next Step

After the markdown-illustrator pipeline completes:
- If the article is for a public blog → suggest `pretty-markdown` for final formatting
- If the article contains Mermaid diagrams → suggest `pretty-mermaid` for enhanced rendering
- If the article needs to be exported → suggest `pdf` or `pptx` for output conversion
```

---

## Open Questions

> [!IMPORTANT]
> **Q1**: `beautiful-mermaid` is imported by `mermaid-tool.ts` but the guides call the tool "pretty-mermaid" — should the npm package name or the guide references be updated?

> [!IMPORTANT]
> **Q2**: Should the skill description remain Chinese-only, or would a bilingual (Chinese + English) description improve triggering accuracy for multilingual users?

> [!IMPORTANT]
> **Q3**: Which of the proposed changes (P0–P7) would you like me to implement? I'd recommend starting with **P0 (path numbering + hardcoded paths)** since these are the critical blockers — P0 alone would fix the most impactful bugs.

> [!NOTE]
> **Q4**: Guide 4c references a `guizang-social-card-skill` — is this still relevant, or should the reference be removed?

> [!NOTE]
> **Q5**: Guide 4d embeds a simplified copy of the `harvest-assets.ts` script inline. Should this be removed in favor of just referencing the actual script?

---

## Verification Plan

### Automated Checks
```bash
# After P0: verify no hardcoded paths remain
grep -r "/home/twait-halek" skills/markdown-illustrator/ --include="*.md"

# After P1: verify scripts run after auto-install
cd skills/markdown-illustrator/scripts && npm install && npx tsx harvest-assets.ts --help
```

### Manual Verification
- Install the skill in a fresh environment to confirm portability
- Run the pipeline on a test article to validate the full 6-step flow
