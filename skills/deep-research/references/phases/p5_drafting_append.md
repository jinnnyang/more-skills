# Phase 5: Phased Section Drafting & Appending (Loop-Append & Checkpoint Resume)

This phase guides the Lead Agent in compiling and drafting the long-form research report section-by-section, invoking drawing skills, and appending files stream-by-stream while maintaining strict checkpoints.

---

## 1. Context Optimization & Preparation
To prevent context bloat and downstream LLM output truncation (avoiding single-response `max_output_tokens` limits):
- **Memory Optimization**: **DO NOT** keep previously written draft chapters in active context.
- **Lazy Loading**: For each section, load only: the core report outline (`chapters/outline.md`), the specific subagent findings notes (`findings/task-*.md`) linked to this chapter, and the washed Global Citation Registry (`citations.md`).
- **Goal**: Maintain a tight, high-focus context window for the LLM to write a single premium, dense chapter (400-800 words) at a time.

---

## 2. Drafting & Visual Embedding Rules

For each pending section in `task.md`, execute the drafting block:
1. **Contextual Anchoring**: Never insert an image or diagram out of nowhere. Precede every media asset with a clear narrative transition or hook (e.g., *"As shown in the system architecture workflow below, the process flow is..."*).
2. **Specialized Illustration Integration (doc-illustrator)**:
   - If `doc-illustrator` is available, invoke it using its exact documented prompt-assembly and calling interface to generate the planned PNG (e.g., `assets/workflow_pipeline.png`).
   - Wrap and embed the generated PNG using **SMIS specifications** (Pattern A for simple layouts, Pattern B for complex layouts).
3. **Harvested Web Evidence Integration (Supporting Evidence)**:
   - The Lead Agent **MUST actively reference and embed** the multimedia evidence (images, charts, videos, or transcripts) registered in the root `artifacts.md` file.
   - For any relevant media block registered in `artifacts.md`, copy its SMIS-compliant block (either Pattern A or Pattern B) and insert it into the chapter file.
   - Precede each embedded media block with a clear narrative transition or hook that explicitly cites or refers to the visual evidence.
   - **All relevant evidence listed in `artifacts.md` MUST be referenced and integrated in the report's body text (e.g. `report-<timestamp>.md` or chapter files) to provide clear factual backing.**
   - **Pattern A (Simple/Compact Visuals)**: Embed as a standard Markdown link with a highly descriptive, context-inferred Alt text containing data, metrics, and business takeaways:
     `![【类型：图表类型】[数据事实描述](结合课题的推断性结论)](图片 Web URL "自解释标题")`
   - **Pattern B (Complex/Video/Transcripts)**: Embed as standard semantic inline HTML wrappers:
     ```html
     <figure>
       <img src="图片 Web URL" alt="【类型：图表类型】[数据事实描述](推断性结论)" />
       <figcaption><b>图 {序号}: {自解释标题}</b> — {上下文关键事实佐证与深度业务推导}</figcaption>
     </figure>
     ```
     Or for collapsible video transcripts:
     ```html
     <details>
       <summary>🎬 <b>视频佐证：{视频标题}</b></summary>
       <p>{视频画面与核心事实的详尽描述。若需超链接，请使用 <a href="链接">链接文本</a>}</p>
     </details>
     ```
   - **CRITICAL HTML Rules**: Within inline-HTML wrappers, you MUST use standard HTML tags (e.g., `<b>`, `<i>`, `<a href="...">`) instead of Markdown formatting (`**`, `*`, `[]()`) to ensure stable rendering across all Markdown engines.
4. **Mermaid Fallback**: If fallback was selected, write a clean, double-quote-protected inline Mermaid.js code block. You may wrap the Mermaid code block inside a `<figure>` and `<figcaption>` tag structure to add a clean description below it.
5. **Language自适应 (Language Adaptive)**: The language of both the chapter text and all media description wrappers (Alt texts, figcaptions, summaries) MUST dynamically match the target adaptive language (Chinese for Chinese, English for English).

---

## 3. Chunk-then-Merge & Task Checkpoints
1. **Isolated Drafting**: Write each freshly generated chapter to its own file in a `chapters/` directory (e.g., `chapters/01_intro.md`, `chapters/02_market.md`). Ensure the file names contain the chapter sequence number so they sort correctly.
2. Update `task.md`: mark the drafted section as `[x]`.
3. Print a single-line progress log: `[P5 drafting] section {index}/{total}: [SectionName] saved to chapters.`
4. Do NOT perform Git commits on every single chapter. Keep commits restricted to the three main lifecycle nodes.

---

## 4. Active Checkpoint & Refresh Mechanism
To prevent the LLM's context window from swelling and causing token exhaustion (e.g., the "Session compressed" issue) while writing long reports:
1. **Batch Drafting Limit**: The Lead Agent MUST NOT attempt to draft the entire report in one continuous session. It should draft a batch of chapters (e.g., 2 or 3 chapters) and then explicitly stop.
2. **State Persistence**: After the batch, the Lead Agent MUST save progress to `walkthrough.md` and check off completed sections in `task.md`.
3. **Context Refresh via Self-Subagent**: To resume, the Lead Agent MUST spawn a fresh clone of itself (using the `invoke_subagent` tool with `TypeName: "self"`) to draft the next batch. The bloated parent process then terminates.
4. **Crash Recovery**: If execution is unexpectedly cut off:
   - When reactivated, the Lead Agent or newly spawned subagent reads `task.md`.
   - List files in `chapters/` to verify they match the completed sections.
   - Load the first `Pending Section` and resume drafting.

---

## 5. Report Compilation Completion & Git Commit
Once all outline chapters and the `## 参考文献 / References` section are fully drafted in the `chapters/` directory:
1. **Merge**: Execute `python scripts/merge_chapters.py` from the project root to automatically concatenate all draft chapters sequentially into the final `report-<timestamp>.md`.
2. **Update brief.md**:
   - Open `brief.md` and change the **Status** to `Reviewing`.
   - Update **Last Updated** with the current date.
   - Synthesize a draft **Executive Summary** representing the compiled research results.
   - Ensure the **Key Discoveries** section matches the core findings of the newly compiled report.
   - Note any remaining review concerns under **Current Roadblocks**.
3. Mark Phase 5 as completed in `task.md`.
4. Execute the silent Git commit:
   ```bash
   git add .
   git commit -m "stage: draft-report-written"
   ```
   *If the Git CLI is unavailable, log a warning and bypass without throwing an error.*
