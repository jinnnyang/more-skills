# Phase 6 & 7: Adversarial Review, Verification, & Finalization

This phase guides the Lead Agent through conducting factual integrity validation, citation auditing, visual/MITTS compliance checks, compiling README summaries, and executing the final repository version commit.

---

## 1. Phase 6: Adversarial Counter-Review (Self-Review)
To avoid consensus bias, the Lead Agent (or a spawned `self` subagent) MUST conduct a rigorous, adversarial review of the drafted report:
1. **Adversarial Audit**: Intentionally challenge the report's primary claims. Identify potential biases, assumptions, or oversights.
2. **Vulnerability Mitigation**:
   - Locate high-risk assertions supported by only a single source. Strengthen the evidence or adjust the confidence rating downward.
   - Audit outdated references (e.g., policy updates older than 2 years or rapid news feeds older than 6 months in fast-moving domains).
3. **Controversies Compilation**: Draft and append the `## Key Controversies & Adversarial Views` section at the end of the report to present the balanced counter-arguments.

---

## 2. Phase 7: Verification & Formatting Polish (Verify & Polish)
1. **Citation Registry Audit**: Cross-verify that all inline citation tags `[n]` in the text map perfectly to the bibliography list at the end of the report.
2. **Visual & SMIS Audit (MANDATORY)**:
   - Verify that all Markdown image tags `![alt](url "title")`, semantic HTML `<figure>` wrapper trees, and Mermaid blocks are formatted correctly.
   - **Audit SMIS Compliance**: Ensure that every single visual and video element has a fully expanded, context-inferred, and highly analytical description embedded natively inside standard Markdown Alt-text (Pattern A) or standard semantic HTML figcaptions/summaries (Pattern B) in the correct adaptive language.
   - **Verify HTML Integrity**: Check that all semantic inline-HTML tags (like `<figure>`, `<figcaption>`, `<details>`, `<summary>`) are correctly opened and closed, and use standard HTML tags (like `<b>`, `<i>`, `<a>`) rather than Markdown formatting inside them to ensure stable rendering.
3. **Mermaid Anti-Error Check**: Re-parse and double-check all inline Mermaid syntax. Confirm that all complex node text is wrapped in double quotes and that no HTML tags are present within the Mermaid graph definitions.

---

## 3. Project Packaging, Brief & README Summaries
1. **README Updates**: Synthesize the core findings, domain parameters, citation breakdown, and conclusion highlights. Save/overwrite this summary in Silicon Valley English to the root directory's `README.md` and `README_zh-CN.md`. Note that `README.md` serves as a general introduction to the repository, project setup, and how to read the files.
2. **Brief Updates (Current Results Summary)**:
   - Open `brief.md` and update **Status** to `Completed`.
   - Update **Last Updated** with the current date.
   - Under **Executive Summary**, write a concise 1-2 paragraph static snapshot summarizing the *current results and final conclusions* of the research project. Ensure this remains distinct from `README.md` (which is about the project structure/goals).
   - Under **Key Discoveries**, list the final verified key discoveries.
   - Under **Current Roadblocks**, write "None (Resolved)" or list any outstanding research gaps for future work.
3. **Task Status Update**: Mark all phases as completed in `task.md`.

---

## 4. Final Silent Git Archive Commit 📌 [Silent Git Commit 3/3]
If the Git CLI is active in the environment, run the final packaging commit silently to freeze the project state:
```powershell
git add .
git commit -m "stage: report-finalized"
```
*If the Git command fails or Git is missing, log a warning and complete the task without blocking.*

---

## 5. Phase Completion Reporting Format
`[P7 complete] Verification passed. README updated. Git Stage: report-finalized. Project status: COMPLETED.`
