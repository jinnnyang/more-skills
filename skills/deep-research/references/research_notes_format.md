# Research Notes Format Specification

Research notes (`task-{id}.md`) are the primary vehicle for transferring objective, structured facts and evidence from subagents to the Lead Agent.
Every factual claim in the final generated report must be traceable back to these notes.

---

## 1. Directory Structure & Naming Defaults
All subagent notes are stored in the project's relative `findings/` directory:
```
[project-name]/
  └── findings/
        ├── task-a.md       # Notes from Task A subagent (e.g., Policy Analyst)
        ├── task-b.md       # Notes from Task B subagent (e.g., Supply Chain Expert)
        └── (Note: registry.md is obsolete; citations are managed in KANBAN.md)
```

---

## 2. Subagent Note Template (`task-{id}.md`)
Every subagent note file MUST strictly follow this Markdown structure:

```markdown
---
task_id: a
role: Economic Historian
status: complete
sources_found: 3
---

## 1. Sources

[1] Before AI skeptics, Luddites raged against the machine | https://www.nationalgeographic.com/history/luddites | Source-Type: secondary-industry | As Of: 2025-08 | Authority: 8/10
[2] Rage against the machine | https://www.cam.ac.uk/research/news/rage-against-the-machine | Source-Type: academic | As Of: 2024-04 | Authority: 8/10
[3] Luddite | https://en.wikipedia.org/wiki/Luddite | Source-Type: community | As Of: 2026-03 | Authority: 7/10

## 2. Research Findings (Findings)

- The Luddite movement began on March 11, 1811, in Arnold, Nottinghamshire. [3]
- Luddites were highly skilled artisans, not blind technophobes. [1][2]
- The number of active Luddites in the British textile industry (with 100M population size) never exceeded a few thousand. [2]
- The British government suppressed the movement brutally: executing 12 leaders in York in January 1813. [3]
- Under military suppression, the movement had largely extinguished by 1817. [1]

## 3. Media Assets (Media)

*(List harvested media assets using the SMIS specifications. Select Pattern A or Pattern B based on complexity. If no high-value media are found, leave this section empty)*

### Pattern A Example (Simple Visual):
- ![【黑白版画：1812年Arnold地区卢德运动暴乱冲突】画面中央是燃烧的织布机，四周是举枪射击的士兵与手持铁锤的工匠，展现了早期手工劳动力与早期工业机器生产的剧烈社会冲突。原网页上下文指出当时织工捣毁新机器并非单纯反对技术本身，而是反抗工厂借新机器废除学徒制和法定工资。核心结论：抗争源于早期纺织工人的生存权与行业手艺自主权受到剥夺。](https://www.nationalgeographic.com/luddite_riot.jpg "1812 Arnold Riot") [1]

### Pattern B Example (Complex/Details Visual):
<figure>
  <img src="https://www.nationalgeographic.com/luddite_riot.jpg" alt="【版画】1812年Arnold地区卢德运动暴乱冲突图" />
  <figcaption><b>图 1.1: 1812年Arnold地区卢德运动织工暴动黑白版画</b> — 原网配文指出织工由于机器引入导致生计受阻与地方民兵爆发武装冲突。印证了卢德运动核心在于保护生存权，而非反智或反创新。 <a href="https://www.nationalgeographic.com/luddite_riot">[1]</a></figcaption>
</figure>

## 4. Deep Read Notes (Deep Read Notes)

### Source [1]: National Geographic - Luddites and AI
- Core Data: Luddites destroyed textile machinery worth nearly £10,000 in their first active year.
- Core Insight: Luddites were not protesting technology itself, but rather manufacturers using new machines to bypass established apprenticeship rules and legal wage standards.
- Supporting Sections: Historical context of technological unemployment.

### Source [2]: Cambridge Academic Research Feature
- Core Data: Luddites consisted of elite, highly skilled weavers with over 7 years of apprenticeship.
- Core Insight: The movement was localized and lacked a centralized national coordinating committee.
- Supporting Sections: Industrial Revolution working-class studies.

## 5. Gaps & Limitations (Gaps)

- Could not locate precise quantitative historical records on the exact number of workers displaced by looms in 1811.
- Lack of non-English academic literature evaluating this movement.
```

---

## 3. Core Constraints & Principles

1. **Local Citation Numbers**: Citation numbers `[n]` in each `task-{id}.md` are independent and start from `[1]`. The Lead Agent will compile, de-duplicate, and assign them global numbers in the main `KANBAN.md` during Phase 3.
2. **Single-Sentence Findings**: Every line in `## Research Findings` **MUST** be a single, standalone objective statement and end with one or more citation indicators (e.g., `[1]`).
3. **Image URL Integrity**: Image URLs in `## Media Assets` **MUST** be the original webpage links. Dummy, temporary, or local file links are strictly prohibited during the gathering phase.
4. **Adaptive Output Language**: The output of subagent notes (Findings, Gaps, SMIS media wrappers) MUST match the target output language requested by the Lead Agent.
