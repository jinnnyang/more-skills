# Zettelkasten Atomic Insight Format Specification

Research notes (Atomic Knowledge Cards) are the primary vehicle for transferring objective, structured facts from the Explorers (subagents) to the Lead Agent's Cognitive Map.
Every factual claim in the final generated report must be traceable back to these atomic notes.

---

## 1. Directory Structure & Semantic Naming
All subagent discoveries are stored in the project's relative `findings/` directory.
**Files MUST NOT be named after task IDs.** They MUST use highly descriptive, semantic filenames capturing the core topic.
```
[project-name]/
  └── findings/
        ├── 2026-05-huzhou-high-speed-rail.md    # Atomic insight on HSR opening
        ├── 2026-06-national-sales-downturn.md   # Atomic insight on sales data
        └── (Note: registry.md is obsolete; citations are managed in citations.md)
```

---

## 2. Atomic Insight Template (`[YYYY-MM-DD]-[topic].md`)
Every atomic insight file MUST strictly follow this Markdown structure:

```markdown
---
topic: {3-4 word summary of the insight}
role: {Role that discovered this}
sources_found: 3
---

## 1. Sources

[1] Before AI skeptics, Luddites raged against the machine | https://www.nationalgeographic.com/history/luddites | Source-Type: secondary-industry | As Of: 2025-08 | Authority: 8/10
[2] Rage against the machine | https://www.cam.ac.uk/research/news/rage-against-the-machine | Source-Type: academic | As Of: 2024-04 | Authority: 8/10
[3] Luddite | https://en.wikipedia.org/wiki/Luddite | Source-Type: community | As Of: 2026-03 | Authority: 7/10

## 2. Research Findings (Findings)

- The Luddite movement began on March 11, 1811, in Arnold, Nottinghamshire. [3]
- Luddites were highly skilled artisans, not blind technophobes. [1][2]
- The number of active Luddites in the British textile industry never exceeded a few thousand. [2]

## 3. Media Assets (Media)

*(List harvested media assets using the SMIS specifications. Select Pattern A or Pattern B based on complexity. If no high-value media are found, leave this section empty)*

### Pattern A Example (Simple Visual):
- ![【黑白版画：1812年Arnold地区卢德运动暴乱冲突】原网页指出当时织工捣毁新机器并非单纯反对技术本身，而是反抗工厂借新机器废除学徒制。核心结论：抗争源于早期纺织工人的生存权受到剥夺。](https://www.nationalgeographic.com/luddite_riot.jpg "1812 Arnold Riot") [1]

## 4. Deep Read Notes (Deep Read Notes)

### Source [1]: National Geographic - Luddites and AI
- Core Data: Luddites destroyed textile machinery worth nearly £10,000 in their first active year.
- Core Insight: Luddites were not protesting technology itself, but rather manufacturers using new machines to bypass established apprenticeship rules and legal wage standards.

## 5. Gaps & Limitations (Gaps)

- Could not locate precise quantitative historical records on the exact number of workers displaced by looms in 1811.
```

---

## 3. Core Constraints & Principles

1. **Atomic Principle**: One file = One coherent topic or insight cluster. Do not mix completely unrelated discoveries into a single file.
2. **Local Citation Numbers**: Citation numbers `[n]` in each file are independent and start from `[1]`. The Lead Agent will compile, de-duplicate, and assign them global numbers in the root `citations.md` file during Phase 3.
3. **Single-Sentence Findings**: Every line in `## Research Findings` **MUST** be a single, standalone objective statement and end with one or more citation indicators (e.g., `[1]`).
4. **Image URL Integrity**: Image URLs in `## Media Assets` **MUST** be the original webpage links. Dummy, temporary, or local file links are strictly prohibited during the gathering phase.
5. **Adaptive Output Language**: The output of subagent notes MUST match the target output language requested by the Lead Agent.
