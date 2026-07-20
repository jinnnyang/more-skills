# docs · 学习文档索引

本目录存放**长期性、学习性**的知识文档——与 `skills/*/references/` 里面向单个 skill 的深度参考不同，这里的文档跨 skill、跨项目、可独立阅读。

面向对象：想学习本仓库背后设计思想的人（或未来的 agent）。

---

## 当前文档

| 文档 | 主题 | 长度 | 状态 |
|---|---|---|---|
| [`hermes-agent-self-maintenance.md`](./hermes-agent-self-maintenance.md) | Hermes Agent 的"技能自维护"机制：五层架构、完整闭环、设计权衡、横向对比 | ~47KB · 12章 + 2附录 | 2026-07-20 首版 |
| [`adr-decision-records.md`](./adr-decision-records.md) | ADR 与 DECISIONS.md 决策日志：概念起源、格式对比、Supersedes 机制、反模式与实操 | ~49KB · 13章 + 5附录 | 2026-07-20 首版（源自 `skills/take-over/references/adr-and-decisions.md`） |

---

## 推荐阅读顺序

**如果你想理解本仓库的设计哲学**（skill 自维护 + 决策留痕）：

1. 先读 [`hermes-agent-self-maintenance.md`](./hermes-agent-self-maintenance.md) 的 Ch 1 → Ch 8 → Ch 9。抓住"agent 是共同维护者"这个立场。
2. 再读 [`adr-decision-records.md`](./adr-decision-records.md) 的 Ch 1 → Ch 4 → Ch 8。理解决策留痕的具体做法。
3. 最后读两份的收尾章（自维护 Ch 11-12 / ADR Ch 12-13），把它们连成完整方法论。

**如果你想把这套方法用到自己项目**：

- 只需要 skill 库自维护 → 只看 `hermes-agent-self-maintenance.md`。
- 只需要决策日志 → 只看 `adr-decision-records.md`。
- 想两个都用 → 顺序无所谓，两份互相引用。

**如果你是 AI agent 接手本仓库**：

- 每次修改本仓库前，两份都扫一遍前 3 章即可掌握纪律。
- 需要拍板设计决策时，回到 `adr-decision-records.md` Ch 5 判定 + Ch 9 实操流程。
- 需要修改 skill 时，回到 `hermes-agent-self-maintenance.md` Ch 4 工具层参考。

---

## 与仓库其他部分的关系

```
more-skills/
├── docs/                       # 你在这里 · 跨 skill 学习文档
│   ├── README.md               # 本文件
│   ├── hermes-agent-self-maintenance.md
│   └── adr-decision-records.md
├── skills/
│   ├── take-over/
│   │   ├── SKILL.md            # take-over skill 主入口
│   │   ├── DECISIONS.md        # 一个真实的 ADR 集合（35+ 条）
│   │   ├── PROTOCOL.md         # 规范文档，被 ADR 引用
│   │   └── references/
│   │       └── adr-and-decisions.md   # 本 docs/ 里 ADR 文档的源材料
│   ├── hand-off/               # take-over 的姊妹 skill
│   └── ...                     # 其他 skill
└── ...
```

**分工原则**：

- `docs/` 里的文档是**独立、可传播**的知识——即使离开本仓库、离开 Hermes 生态也有阅读价值。
- `skills/*/references/` 里的文档是**skill 内部参考**——依赖 skill 上下文，跟 skill 生命周期绑定。
- 两者可以**互相演化**：docs 里的通用规律可以反向优化 skills 里的具体实践，skills 里的实操经验也可以升华回 docs。

---

## 维护纪律

两份文档都遵循自己教的方法：

- **`hermes-agent-self-maintenance.md`** — 若过时或有误，按其 Ch 11 阶段 3 的方法 patch。
- **`adr-decision-records.md`** — 若过时或有误，按其 Ch 7 的 Supersedes 机制追加修订，不就地重写。

新文档追加时，更新本 README 的表格。

---

*最后更新：2026-07-20。*
