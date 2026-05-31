# 调研笔记格式规范 (Research Notes Format Specification)

调研笔记是子代理与主代理（Lead Agent）之间传递客观事实证据的唯一媒介。报告中的每一条客观事实都必须在此笔记中找到依据。

---

## 1. 结构与存放命名
子任务的 findings 统一写入项目目录下的 `findings/` 目录：
```
[project-name]/
  └── findings/
        ├── task-a.md       # 子任务 A 笔记 (经济历史专家)
        ├── task-b.md       # 子任务 B 笔记 (供应链分析师)
        └── registry.md     # 废弃 (全局引文已统一合并至 KANBAN.md，不再独立建文件)
```

---

## 2. 子任务笔记格式模板 (`task-{id}.md`)

每一个子任务笔记必须严格按照以下 Markdown 格式输出：

```markdown
---
task_id: a
role: 经济历史分析师
status: complete
sources_found: 4
---

## 1. 来源信源 (Sources)

[1] Before AI skeptics, Luddites raged against the machine | https://www.nationalgeographic.com/history/luddites | Source-Type: secondary-industry | As Of: 2025-08 | Authority: 8/10
[2] Rage against the machine | https://www.cam.ac.uk/research/news/rage-against-the-machine | Source-Type: academic | As Of: 2024-04 | Authority: 8/10
[3] Luddite | https://en.wikipedia.org/wiki/Luddite | Source-Type: community | As Of: 2026-03 | Authority: 7/10

## 2. 调研发现 (Findings)

- 卢德运动于 1811 年 3 月 11 日在诺丁汉郡的阿诺德开始。[3]
- 卢德分子是技术精湛的工匠，而不是盲目反对技术的极端分子。[1][2]
- 在拥有1亿人口的英国纺织工业中，卢德分子总数从未超过几千人。[2]
- 英国政府进行了严厉镇压：1813年1月在约克郡处决了12名领导者。[3]
- 运动在军事镇压下于 1817 年基本熄灭。[1]

## 3. 多媒体佐证 (Media Assets)

- !["[1812年全英国纺织工人抗议与军警冲突的黑白雕版画。图中中央为熊熊燃烧的纺织机，四周是手持铁锤的工人和举枪射击的士兵。]"](https://www.nationalgeographic.com/luddite_riot.jpg "1812年Arnold地区暴动图") [1]

## 4. 深度阅读笔记 (Deep Read Notes)

### 来源 [1]: 国家地理 — 卢德分子与 AI
- 核心数据: 运动第一年内砸毁了价值近 10,000 英镑的织布机。
- 核心洞察: 卢德分子并非反对机器本身，而是抗议制造商利用新设备规避当时的标准学徒制度与法定劳动准则。
- 支持章节: 历史上的技术性失业章节。

### 来源 [2]: 剑桥大学学术专栏
- 核心数据: 卢德分子主要由高技能的“精英工匠”组成，拥有 7 年以上的学徒资历。
- 核心洞察: 运动是高度地方化的，没有大规模的全国组织。
- 支持章节: 工业革命工人阶级演变研究。

## 5. 局限与盲区 (Gaps)

- 未能找到因纺织机引入导致失业人数的准确量化历史数据。
- 缺乏非英语学界对该历史运动的平行评估报告。
```

---

## 3. 核心约束原则

1. **信源本地编号**：子任务笔记中的引用编号 `[n]` 是局部独立的（都从 `[1]` 开始）。主代理将在 P3 阶段整合后转化为全局统一的引文编号并登记在 `KANBAN.md` 中。
2. **单句发现**：`## 调研发现` 里的每一行必须是一句客观的陈述，且行尾**必须且仅能**以引文编号（如 `[1]`）作为支撑标记。
3. **图像 URL 指向**：`## 多媒体佐证` 中引用的图片 URL **必须是原始网页链接**，严禁使用虚假的本地或临时文件路径。
