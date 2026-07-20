# ADR 与决策日志 · 原理、机制、实践指南

> 一份关于 **Architecture Decision Records (ADR)** 与 `DECISIONS.md` 决策日志的完整学习文档。
> 面向对象：任何维护长期演化系统的**作者与 agent**——软件项目、AI skill、协议规范、组织制度、只要"决策会被未来的人重提"都适用。
> 版本：2026-07-20 首版。源材料：`skills/take-over/references/adr-and-decisions.md`（skill 内视角），本文档扩展为跨项目通用视角。

---

## 阅读指引

- **Ch 1-2** 概念起源 + ADR 在文档生态里的位置。看完能理解**为什么需要 ADR**。
- **Ch 3-6** 判定 + 格式：什么项目该用、一条合格 ADR 长什么样、各家 ADR 格式对比。看完能理解**该怎么写**。
- **Ch 7** Supersedes 专章 — ADR 演化的核心机制。
- **Ch 8-9** 反模式与实操 — 见过哪些坑、如何一步步落地。
- **Ch 10-12** 阅读顺序、局限、落地 checklist。看完能上手用。
- **Ch 13** ADR 与 Hermes skill 自维护机制的关系 — 呼应本仓库姊妹文档 [`hermes-agent-self-maintenance.md`](./hermes-agent-self-maintenance.md)。
- **附录** 各家模板对比、术语表、真实案例集。

只有 15 分钟读一次：**Ch 1 → Ch 4 → Ch 8**。抓住"为什么/怎么写/怎么错"三点足够开工。

---

## Ch 1 · 出身 · ADR 从哪里来

### 1.1 Nygard 的开山文章

**ADR = Architecture Decision Record**。概念由 Michael Nygard 在 2011 年的博客文章 [*Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 首次系统化。

他当时观察到一个反复出现的痛点：

> 大型系统的架构里到处是"为什么当初这么选"的问号。代码回答的是 *how*，注释回答的是 *what*，但 *why* 永远丢失。文档写在 wiki 会失联，写在 issue 会被关闭埋葬，写在会议纪要没人回看。半年后新人重新提出旧问题，团队又花两周把同样的替代方案再评一遍，最后得出同样的结论。

Nygard 的解药是三条：

1. **决策跟随代码走**——放进仓库，而不是外部 wiki。
2. **一条决策 = 一个短文件**——不可变，按时间序号累加。
3. **每条必须包含 Context + Decision + Consequences + Rejected Alternatives 四段**。

### 1.2 广泛传播

后续 ThoughtWorks、AWS、Kubernetes、Rust、Apache 等项目都以类似形态推广开来。虽然各家格式细节略异（有的用"Status/Context/Decision/Consequences"四段、有的用"Problem/Options/Outcome"、有的写成 RFC 前瞻），但**内核不变**：

> **ADR 存的是"决策的推导链"，不是决策的结果本身。**

结果（例如 "HTTP/2 用 HPACK 压缩头"）代码里写得清清楚楚，ADR 存的是"当时也考虑过 gzip，为什么没用"——**这是代码永远不会告诉你的信息**。

### 1.3 一个统一的直觉

如果只用一句话总结 ADR 的全部价值：

> **代码告诉你"是什么"，ADR 告诉你"为什么不是别的什么"。**

大部分讨论 ADR 的争论（写太长/太短、要不要 rejected、supersedes 怎么处理）本质都是"这句直觉如何在具体场景落地"。抓住它，剩下的都是细节。

---

## Ch 2 · ADR 与其他文档的定位差异

新人常问："这个不是可以写在 README / 设计文档 / 注释 / commit message / 会议纪要里吗？"

答案是：**都不能替代 ADR**。分工如下：

| 文档类型 | 回答的问题 | 时间尺度 | 生命周期 |
|---|---|---|---|
| **代码本体** | *How* — 系统是怎么运作的？ | 现在 | 会被重构改写 |
| **注释 / docstring** | *What* — 这个函数在干什么？ | 现在 | 跟代码同步 |
| **README / 用户手册** | *How to use* — 用户怎么用？ | 现在 | 跟功能同步 |
| **Commit message** | *What changed* — 这次改了什么？ | 单次改动 | 永久但零散、不聚焦"设计" |
| **Design doc / RFC** | *What we're going to build* — 前瞻方案 | 立项前 | 立项后可能废弃 |
| **CHANGELOG** | *What version brought what* — 版本变更 | 每个 release | 永久但用户导向 |
| **会话过程日志**（例如 walkthrough.md） | *What happened this session* | 会话内 | 短期，会被 prune |
| **`DECISIONS.md` / ADR 集合** | *Why we chose this over that* — 决策推导 | **永久** | **永不改写**，只追加 supersedes |

### 2.1 关键差异

1. **ADR 面向"未来的作者"**，不是当前用户；README 面向"用户"，不是未来作者。
2. **ADR 保留 rejected alternatives**；design doc 往往在拍板后就把否决方案删了。
3. **ADR 不可变**；commit message 也不可变但太零散，单条 commit 讲不完 rationale。
4. **ADR 是叙事**；架构图是拓扑。

### 2.2 什么时候能"复用"其他文档

有几个边界情况：

- **超短决策**（"我们用 4 空格缩进"）→ 写 style guide，不用 ADR。
- **纯前瞻讨论**（还没拍板）→ 写 RFC / design doc，拍板后如果替代方案值得留，才**摘录一条**进 ADR。
- **纯用户可见的行为变更**（bug fix、参数改名）→ CHANGELOG 够了；除非改动背后的理由值得未来重提。

**判断题**：这个改动的**"为什么"部分**，未来有人重问的概率高吗？
- 高 → ADR。
- 低 → 其他文档足够。

---

## Ch 3 · 什么样的项目需要 ADR

不是所有项目都需要。需不需要主要看两个维度：

### 3.1 设计空间的复杂度

**设计空间复杂 = 有多个明显合理的方案，且拍板理由不显然**。

复杂设计空间的典型信号：
- 同一个问题至少有 2 个"看起来都对"的方案。
- 拍板依据里有**非功能考量**（性能 / 复杂度预算 / 团队认知负荷 / 未来兼容性）。
- 决策之间有**耦合**——A 的选择限制了 B 的选择。

反例（简单空间）：
- 一个 CLI 工具用 argparse 还是 click。空间简单、拍板显然（团队熟悉哪个用哪个），不用 ADR。
- 一个函数用 for 循环还是 map。纯风格，不用 ADR。

### 3.2 作者更替频率

**作者更替频率高 = 需要"每次启动前必读的对齐文件"**。

高更替频率的典型场景：
- 大型开源项目（贡献者流动）。
- 长期演化的产品（多年跨度、团队换代）。
- 涉及 AI agent（**agent 是极端善忘的作者**，每次零上下文启动）。
- 双胞胎组件（例如 client/server、生产者/消费者、姊妹 skill）需要同步演化。

低更替频率场景：
- 一个人的实验项目、不打算给别人看。
- 短生命周期原型（1-2 个月就丢）。

### 3.3 判定矩阵

| | 简单设计空间 | 复杂设计空间 |
|---|---|---|
| **作者稳定** | 不需要 ADR | 写 design doc 就够；ADR 可选 |
| **作者更替频繁** | Style guide + CHANGELOG 够 | **必须写 ADR** |

**AI agent 参与的项目全部落在右下格**——即使设计空间不算特别复杂，agent 的零上下文启动本质上让每次修改都相当于"新作者接手"，ADR 是唯一可扩展的对齐工具。

### 3.4 一个具体案例：Hermes take-over skill

本文档的原始材料来自 `skills/take-over/references/adr-and-decisions.md`。这个 skill 是**两条件都拉满**的极端案例：

**设计空间深、暗礁多**：

- Frontmatter 的 `status` 用 `complete` 还是 `phase-complete`？表面上前者更自然，但 `complete` 语义歧义（文档完了？任务完了？整个项目完了？），`phase-complete` 明确表达"这个阶段完了但文档还活着"。不写 ADR，半年后 agent 一定会"简化"回 `complete`。
- HARD conflict 应该 halt 还是 auto-log？前者打扰用户，后者容忍脏数据。配套 rejected alternatives 明确写了"halt on any conflict → 太打扰"、"auto-log everything → 硬冲突会静默溜过"。**这两条否决理由本身比结论更重要**——它们是未来"简化"提案的免疫接种。

**作者更替频率极高**：

- 每次被使用，受影响的"作者"就换了一次：一个 agent 帮用户跑一次 take-over → 用户想改 skill → 起一个新会话 → 新 agent 上下文里对历史一无所知 → 另一个 agent 想 fork 到自己的项目 → 完全不知道历史决策。

**双胞胎漂移风险**：

- `take-over` 和 `hand-off` 是共享协议的姊妹 skill。它们**故意不共享文件**，代价是"跨文件同步靠人自觉"。DECISIONS.md 里 `(cross-cutting)` 标签就是"这条必须在另一边镜像"的信号。没有这个标签体系，两边会静默漂移到某天用户跑一次完整链路才炸出来。

这三点合起来，ADR 从"锦上添花"变成"不写就活不了"。

---

## Ch 4 · 一条合格 ADR 的解剖

Nygard 原生格式有严格的四段（Context / Decision / Consequences / Rejected）。业界后来发展出很多变体，本 Ch 用一种**紧凑变体**（合并 Context 进 Rationale，但**必须保留 Rejected Alternatives**）作为主讲对象。Ch 6 会对比各家变体。

### 4.1 骨架

```markdown
### <决策 id> · <一行标题> (<scope tag>)
**Decision:** <一句话拍板的具体结论，不加限定词、不用"应该"/"可能">
**Rationale:** <为什么这么选。要点回答"为什么这是最不坏的选择"，不是"这样多好">
**Rejected:**
- <方案 A> — <为什么不选它的具体原因（不是"感觉不好"，要有具体后果）>
- <方案 B> — <同上>
[optional]
**Supersedes:** <旧决策 id + 日期>
**Impact on <某个下游组件>:** <这个决策改变了什么后续>
```

### 4.2 决策 id 命名规则

主流做法有几种，选一种坚持到底：

| 命名法 | 示例 | 适合场景 |
|---|---|---|
| **顺序整数** | ADR-0001 / ADR-0002 | 大项目、有专门 adr 目录（`docs/adr/0001-*.md`） |
| **日期序** | 2026-07-20-01 | 时间线感强，但排序稍麻烦 |
| **主题 + 序号** | R1 / R2 / R3 | 单文件多决策场景（DECISIONS.md 内部） |
| **圈号 + R编号混合** | ① ② R17 R18 | 有"稳定核心决策"和"后续修订"两层的项目 |

**关键原则**：id **一旦分配永不复用**。即使某条被 supersedes 了，它的 id 也保留（新条 id 写 `Supersedes: R17`）。这是"永不改写只追加"的具体落实。

### 4.3 Scope tag（作用域标签）

在**多组件项目**里非常关键：

- `(cross-cutting)` = 决策跨越多个组件，每个组件的 ADR 集合都要有一份镜像。
- `(<组件名> specific)` = 只影响这一个组件。
- `(mirrored)` = 从另一个组件镜像过来的（内容跟对方一致，仅位置不同）。

**为什么这么重要**：没有 scope tag，多组件项目的 ADR 集合会**静默漂移**——A 组件改了但 B 组件没跟进，跨组件调用某天崩了才发现。Scope tag 是"改这条必须同步改 B"的显式信号。

### 4.4 什么是"合格的 Rejected 条目"

**不合格**：

> Rejected: 用 JSON 而不是 YAML — 不好。

不好在哪？未来读者无法从中获取任何信息。

**合格**：

> Rejected: 用 JSON 而不是 YAML — JSON 不允许注释（handoff 文档需要在字段旁边解释语义），且 JSON 的 YAML 超集写法在不同 parser 上兼容性差。同时 SKILL.md 本身就是 YAML frontmatter，统一格式减少作者认知负担。

**判定标准**：一个从没见过此决策的读者，看完 Rejected 那一行，能不能自己复述出"为什么不用"？能 → 合格；不能 → 补细节。

### 4.5 什么时候可以"跳过 Rejected"

**极其罕见**。真实场景大概只有：
- 决策是纯风格/惯例（用 4 空格缩进而不是 tab），这种也不用写 ADR，写 style guide 就行。
- 决策由**外部标准强制**（必须用 ISO-8601 时间戳因为 §6 定义了），但这种情况下 Rejected 应该指向"为什么当初 §6 这么定"。

**如果你发现自己"想不出否决方案"，99% 是没想够，不是"确实没有替代"**。

### 4.6 Decision 段的语言纪律

Decision 段是拍板结论。有几条硬纪律：

1. **不用"应该"/"可能"/"考虑"/"倾向"**——这些是待议，不是拍板。
2. **不用条件语气**（"如果 X 那么 Y"）——如果真有条件分支，说明这个 Decision 应该拆成两条。
3. **具体到"未来 agent 看到能直接执行"的粒度**——不写"加一个 review 命令"，写"新增 `review-handoff` 子命令，返回 `pass|reject|fresh_init` 三态"。

**判定题**：把这条 Decision 拿给一个从未接触本项目的开发者看，他能不能不问任何人就写出符合此决策的代码？能 → 合格；需要问 → 补细节。

---

## Ch 5 · 什么时候必须写一条 ADR

判定规则，按触发条件从高到低排序：

| 触发条件 | 例子 | 是否写 ADR |
|---|---|---|
| 引入**枚举/常量集合**且值必须稳定 | `VALID_KINDS` / HTTP 状态码列表 / 事件类型集 | ✅ 必须 |
| **改变**跨模块协议的字段/流程 | 新加一个 workflow step、改一个 API 字段 | ✅ 必须 |
| 两个明显合理方案之间**拍了板**，rejected 方案后续有人可能重提 | 单文件 vs 多目录、REST vs GraphQL | ✅ 必须 |
| 决策**跨越两个组件** | 共享库 vs 各自复制 | ✅ 必须（cross-cutting） |
| 引入一个**看起来违反 DRY / 常识**的做法 | 双份 config、故意重复代码 | ✅ 必须（说明为什么值得） |
| 引入**用户可见的 UX 契约** | 交互协议、命令行输入格式 | ✅ 必须 |
| 修复一个**行为微妙的 bug** | 换行序列化、时区处理 | ✅ 必须（防止回归） |
| 改**已有 ADR** 引用的东西 | 调整旧枚举 | ✅ 必须（supersedes 旧条） |
| 引入新依赖（框架 / 大型库） | 从 Flask 换到 FastAPI | ✅ 必须（依赖是长期承诺） |
| 纯代码层重构、无外部行为变化 | 提取一个 helper 函数 | ❌ 不写（commit message 够了） |
| 修复 typo / lint / 格式化 | / | ❌ 不写 |
| 新增测试、benchmark | / | ❌ 不写（除非测试策略本身是决策） |
| 依赖版本 bump | `pyyaml 6.0 → 6.1` | ❌ 不写（除非 bump 引入了行为变化） |

### 5.1 心法

如果 code review 里会有人问"**为什么不是 X？**"、且答案值得为下一次问再想一遍——就写。

如果答案只是"这里稍微整理了一下代码"——不写。

### 5.2 反向判定

一个更快的判定方式：**过 6 个月后，你自己会不会忘记这个决策的原因？**

- 会忘 → 写 ADR（未来的自己都要重推导，别人更需要）。
- 不会忘 → 大概率不值得 ADR（但要小心"过于自信"陷阱——很多决策当时觉得显然，半年后完全想不起来）。

### 5.3 灰色地带：什么时候可以偷懒

**允许偷懒**的场景：

- **实验分支**——还在 spike 阶段，明天可能整块删。用 spike 结束时一条**总结性 ADR** 覆盖所有决策。
- **原型项目**——预期生命周期 < 1 个月。用 README 里一段 "Design notes" 记录关键权衡即可。
- **一次性脚本**——写完就丢。不用 ADR。

**不允许偷懒**的场景：

- 任何"稳定 API"或"对外契约"层面的决策——即使当时觉得简单，一旦有第三方消费就成了历史包袱。
- 任何"看起来违反常识"的做法——如果不解释，未来一定被"优化"掉。
- 任何 rejected 方案有热度的场景（团队里已经有人提过 "why don't we just X"）——不写 ADR 就得每次口头解释。

---

## Ch 6 · 格式流派对比 · 六种主流 ADR 模板

前面用的是紧凑变体。业界还有很多其他格式，各有取舍。这一章帮你在自己项目里选一种。

### 6.1 Nygard 原生 · 严格四段

```markdown
# ADR-0001: Title

## Status
Accepted / Proposed / Deprecated / Superseded

## Context
描述问题背景、驱动力、约束、涉及的利益方。

## Decision
拍板的具体结论。

## Consequences
决策带来的正面、负面、中性后果。
```

**特点**：结构最严谨，Context 段力度大，适合"决策前有充分讨论"的重量级项目。
**缺点**：写起来重，一条 ADR 往往 200-500 词。
**代表用户**：企业内部大型系统、AWS Well-Architected 模板衍生物。

### 6.2 MADR (Markdown Architectural Decision Records)

```markdown
# Title

* Status: accepted
* Deciders: <人名列表>
* Date: 2026-07-20

## Context and Problem Statement
## Decision Drivers
* Driver 1
* Driver 2

## Considered Options
* Option A
* Option B
* Option C

## Decision Outcome
Chosen option: "Option B", because ...

### Positive Consequences
### Negative Consequences

## Pros and Cons of the Options
### Option A
* Good, because ...
* Bad, because ...
### Option B ...
```

**特点**：把 Nygard 的 "Rejected Alternatives" 拆成 Pros/Cons 表，比较对称。
**缺点**：更长，写小决策显得笨重。
**代表用户**：ThoughtWorks 推荐、[adr-tools](https://github.com/npryce/adr-tools) 默认模板。

### 6.3 Y-Statements (Olaf Zimmermann)

一句话 ADR：

> **In the context of** `<use case>`, **facing** `<problem>`, **we decided for** `<option>` **and against** `<alternative>`, **to achieve** `<benefit>`, **accepting** `<downside>`.

**特点**：极简，一句话讲完。适合"墙上贴一堆决策卡片"的敏捷团队。
**缺点**：写不下细节，rejected alternative 只有一个。
**代表用户**：早期敏捷项目、白板团队。

### 6.4 紧凑变体（本 skill 采用）

```markdown
### <id> · <标题> (<scope>)
**Decision:** ...
**Rationale:** ...
**Rejected:**
- Alt A — 具体后果 ...
- Alt B — 具体后果 ...
```

**特点**：合并 Context 进 Rationale，砍掉 Status（用 Supersedes 隐式管理），保留强制 Rejected。
**优势**：单文件多决策（DECISIONS.md 存所有条目），写作成本低，检索成本低。
**缺点**：不适合决策独立、有独立评审周期的大项目——那些还是用 Nygard 或 MADR。
**代表用户**：Hermes skill 项目、本仓库。

### 6.5 Rust RFC 风格

前瞻式 ADR：

- 一个 markdown 文件对应一个 RFC。
- 先 propose（PR），社区讨论，然后 merge = 接受。
- 有 `Motivation / Guide-level explanation / Reference-level explanation / Drawbacks / Rationale and alternatives / Prior art / Unresolved questions / Future possibilities` 8 段。

**特点**：前瞻性最强，决策发生在实现前。适合"先讨论清楚再动手"的稳定 API 项目。
**缺点**：写作成本极高，一份 RFC 常常 2000+ 词。
**代表用户**：Rust、Ember、Yarn 等成熟开源项目。

### 6.6 Kubernetes KEPs (Enhancement Proposals)

比 RFC 还重：

- 有生命周期（`provisional / implementable / implemented / deferred / rejected / withdrawn / replaced`）。
- 有 approvers、reviewers、shepherd 角色。
- 分 `alpha / beta / stable` 三阶段推进。

**特点**：企业级流程，决策链条最完整。
**缺点**：只有 Kubernetes 规模的项目才 justify。
**代表用户**：Kubernetes、Envoy、CNCF 大项目。

### 6.7 怎么选

| 项目规模 | 团队规模 | 决策频率 | 推荐格式 |
|---|---|---|---|
| 单人 skill / 小工具 | 1 | 每月几条 | **紧凑变体** |
| 中型项目 | 2-5 | 每周几条 | **MADR** 或 **紧凑变体** |
| 大型开源项目 | 10+ | 每周多条 | **MADR** 或 **Nygard** |
| 稳定 API / 长生命周期系统 | 10+ | 每月 1-2 条 | **Nygard** |
| 前瞻规划为主 | 10+ | 提案 > 决策 | **Rust RFC** |
| CNCF 级 | 100+ | 全流程 | **Kubernetes KEP** |

**核心建议**：**不要一开始就选最重的格式**。从紧凑变体或 MADR 开始，实在覆盖不了再往上升。

---

## Ch 7 · Supersedes 专章 · ADR 演化的核心机制

ADR 的"不可变 + 只追加"纪律很多人不理解。这一章解释为什么这么设计、如何用 Supersedes 表达演化、什么时候真的可以"删除"。

### 7.1 为什么不能改旧条目

假设你在 v1.0 拍了 R7："使用 MongoDB 存用户数据"。半年后 v1.5 你换成了 PostgreSQL。

**错误做法**：直接把 R7 的 "Decision" 改成 "使用 PostgreSQL"。

**为什么错**：

1. **Git blame 找不到"当时的理由"了**——半年前提交时的 Rationale 是"MongoDB 的灵活 schema 适合当时的迭代速度"，改成 PostgreSQL 后这句话没了。将来有人问"为什么当初不用 SQL"，没答案。
2. **代码里可能还有 MongoDB 的痕迹**（一次迁移不彻底）——将来读代码的人看到 MongoDB 引用查 R7，发现 R7 说的是 PostgreSQL，一头雾水。
3. **Rejected alternatives 会消失**——R7 当初 rejected 的是 "PostgreSQL 太重"，现在 PostgreSQL 成了选择，这条 rejected 被删了，未来有人再提"不如换 MongoDB"你要重新走一遍。

**正确做法**：**追加一条 R23 supersedes R7**。R7 保持原样，R23 新写完整的当前理由。

### 7.2 Supersedes 的三种表达

**a) 完全替代**（老决策失效，新决策生效）：

```markdown
### R23 · 存储层换用 PostgreSQL (cross-cutting)
**Supersedes:** R7 (2025-01-15)
**Decision:** 用户数据迁移到 PostgreSQL, MongoDB 淘汰。
**Rationale:** 团队规模扩大到 15 人后, MongoDB 缺少 schema 约束
导致每次跨团队协作都要开会协商字段语义。R7 时期我们只有 3 人,
schema-less 是资产;现在 schema-less 是负债。
**Rejected:**
- 保留 MongoDB, 加应用层校验 — 具体后果: 校验代码分散在 20+ 个
  service, 维护成本超过换 DB。
- CockroachDB — 具体后果: 团队无经验, 学习曲线阻挡当前 P0 需求。
**Migration:** 参见 R24 (数据迁移方案) 和 R25 (灰度切换)。
```

**b) 部分修正**（老决策部分保留、部分更新）：

```markdown
### R30 · 存储层增加 Redis 缓存 (partial supersedes R7)
**Supersedes:** R7 §"读性能" (2025-01-15)
**Preserves:** R7 §"MongoDB 作为主存储" (2025-01-15) 依然有效。
**Decision:** ...
```

**c) 反转**（新决策把老决策明确否定了）：

```markdown
### R40 · 撤回 Redis 缓存决策 (reverts R30)
**Reverts:** R30 (2026-03-10)
**Decision:** 停用 Redis 缓存层, 回归 MongoDB 直读。
**Rationale:** R30 引入的缓存一致性 bug 导致 3 次 P0 事故,
其收益(读延迟从 30ms 降到 5ms)对我们业务不足以 justify 复杂度。
**What we learned:** 缓存的引入门槛应该更高——R30 当时的 rejected
里没考虑"运维复杂度增量", 是判断失误。
```

**关键点**：即使新决策是"当初不该那么做"，**也不要删除老条目**。Reverts 本身是宝贵信息——它告诉未来"这条路我们真的走过、真的踩过坑"。

### 7.3 什么时候可以真的删除 ADR

**几乎从不**。真实场景大概只有：

- **误操作**：不小心创建了一条重复/空/垃圾 ADR。用 git revert 撤销即可。
- **敏感信息泄露**：ADR 里写了密码、密钥、真实用户数据。用 `git filter-branch` 或 `git-filter-repo` 从历史中彻底移除。**这是唯一正当的"真删除"**。
- **合规要求**：法律要求某些内容不能保留（例如 GDPR 撤回请求）。同上。

**"这条决策过时了" ≠ 应该删除**。过时用 Supersedes 处理。

### 7.4 Status 字段的替代做法

有些 ADR 模板（Nygard、MADR）用 `Status: Accepted / Deprecated / Superseded` 显式标记状态。紧凑变体不用 Status，而是**通过"最近一条 supersedes 关系"隐式表达**：

- 没有任何 `Supersedes` 指向它 → 生效中。
- 有 `Supersedes: R7` 的新条 → R7 已被替代（读 R7 时会看到 R7 的日期段头，需要往下翻找 supersedes 它的新条）。

**如果单文件 ADR 数量少（< 30 条）**，这种隐式表达可读性够。**多了之后**建议加一个显式 index：

```markdown
## Index

Active decisions:
- R23 (supersedes R7) — 存储层
- R28 — 认证层
- R31 — 部署流水线

Superseded / reverted:
- R7 → R23 (2025-07-20)
- R30 → R40 (reverts)
```

这个 index 可以脚本生成，不用手写。

---

## Ch 8 · 常见反模式 · 从真实历史里学到的

### 8.1 反模式 · "决策"其实是"实现说明"

**反例**（不合格的 ADR）：

> ### R99 · check-reality 现在支持 --agent 参数
> **Decision:** 加了 `--agent` 参数。
> **Rationale:** 需要传 agent 名字进去。

这是**实现日志**，不是决策。真正的决策是"lock 机制的所有权由 agent 名字标识 vs 由 session_id 标识"，参数叫什么是实现细节。

**判定题**：把 Decision 部分给一个熟悉此领域但不了解本项目的人看，他会不会觉得"这明显该这么做，还需要 ADR？" 会 → 你没找到真正的决策点。

### 8.2 反模式 · 批量决策集中写但没拆分

**反例**：一个巨大的"2026-07-17 refactor day"条目包含 8 个不相关的决策。

**问题**：未来引用某一条时无法用稳定 id 指向。

**正解**：每个原子决策一个独立 `### R<n>` 子节，可以共享一个日期段头。参考 `skills/take-over/DECISIONS.md` 2026-07-20 v1.4.0 那段——8 条决策（R24-R31）共享一个日期头，但每条独立可引用。

### 8.3 反模式 · 改旧条目而不是追加新条

**反例**：v0.5 引入 flat-file 后有人直接把 v0.3 ⑥ 的"kind 枚举"那一节的文字改了。

**问题**：未来有人看 git blame 找"这个字段是什么时候加的"，找到 v0.5 的 commit，但 rationale 里讲的是 v0.3 的场景，对不上。

**正解**：v0.5 追加一条 `R17 filename prefix retired`。如果 v0.3 ⑥ 需要修正，写 `R<n> supersedes v0.3 ⑥`，**不动旧条目本身**。

### 8.4 反模式 · Rejected 里全是稻草人

**反例**：

> Rejected: 什么都不做 — 不行。

这不是替代方案，是"选项 0 = 别改"。真替代方案是"用 X 库 / 用 Y 算法 / 拆到 Z 模块"这种真拿出来会 pass code review 的选项。

**另一种稻草人**：

> Rejected: 用 SQLite — 生产不能用 SQLite。

太笼统。真正的 rejected 应该是：

> Rejected: 用 SQLite — 我们预期并发写入 200+/s, SQLite 的 write-lock 会成为瓶颈; 另外无原生 replication 支持,灾备方案要额外写。

### 8.5 反模式 · ADR 写在别的地方

见过：

- 写在 PR description 里 → PR 关闭后没人回看。
- 写在 issue tracker → 换工具就丢。
- 写在会议纪要 → 无法搜索。
- 写在私人笔记 → 只有原作者知道。
- 写在 Slack 消息 → 30 天后 retention 一过就消失。

**唯一正确的地方**：项目仓库里、命名固定的文件（`DECISIONS.md` / `docs/adr/*.md`）、跟代码一起版本化。

### 8.6 反模式 · Rationale 是营销话术

**反例**：

> Rationale: 我们选择 Kubernetes 因为它是行业标准、社区活跃、生态完整。

这是**竞品对比页面**的语言，不是 rationale。真 rationale 讲"如果不这么做会怎样"：

> Rationale: 团队已经在生产跑 Kubernetes 3 年,重新培训到另一个编排系统的
> 成本估算是 4 人月; 且我们复用了公司平台组维护的 K8s 基础设施,
> 换到别的系统等于放弃这层杠杆。K8s 本身的缺点(复杂、YAML 地狱)
> 我们接受, 因为团队已经过了学习曲线。

后者可以指导未来判断（"如果团队 K8s 经验消失了 → 该重评估"），前者不能。

### 8.7 反模式 · ADR id 复用

**反例**：R7 被 supersedes 后，把 R7 的 id 给了新决策。

**问题**：所有引用 "R7" 的旧代码/文档/commit message 现在指向的是完全不同的决策。历史断裂。

**正解**：id **永不复用**。即使 R7 被 supersedes，它的 id 保留。新条用下一个未用过的 id。

### 8.8 反模式 · 只有一个人在写

**问题**：ADR 成了一个人的日记，其他人不看、不写、不引用。半年后原作者离开，剩下的 ADR 集合无人维护。

**信号**：
- 只有 ADR 但没有代码里的"参见 R7"注释。
- 所有 ADR 作者名字一样。
- Commit message 不引用 ADR。

**修复**：让 ADR 引用**成为 code review checklist 的一项**——"这次改动是否有相应 ADR，或需要新写一条？"

---

## Ch 9 · 实操 · 从一次真实"我想改这里"到一条落地的 ADR

用一个真实场景演示完整流程。**场景**：用户提出"take-over skill 缺少接手前评审机制"。演示实际写下 R24 的思考过程。

### Step 1 · 判断这个变更够不够格

自问三问：

- **会改变外部行为吗？** → 会，加了 Step 1.5，可能 halt 加载。✅
- **有明显的替代方案吗？** → 有（"只 warn 不 reject"、"reject 但不给 remediation"）。✅
- **未来有人可能重提这些替代方案吗？** → 一定会（remediation 增加复杂度，后来者可能说"简化掉吧"）。✅

三问全 yes → **值得写 ADR**。

### Step 2 · 起草 Decision

第一版：

> Decision: 加一个 review-handoff 命令。

太弱。"加一个命令"是**实现**，不是**决策**。真正拍板的是：

- 存不存在这个检查（存 vs 不存）
- 严格度选哪档（严格 / 中庸 / 保守）
- reject 后的分支怎么设计（单一路径 / 三选一 / 二选一）
- take-over 自己能不能 remediate

改成：

> Decision: 新增 Step 1.5 Handoff Acceptance Review, 在 check-reality
> 前对 hand-off 产物做静态可用性检查; verdict = pass|reject|fresh_init;
> reject 时通过 §0a 提供 Reject / Remediate / Force-continue 三选一;
> remediation 最多 3 轮回退。

现在这条，任何未来 agent 看到都能立刻理解"决策边界在哪"。

### Step 3 · 写 Rationale 时要"未来导向"

不好的写法：

> Rationale: 之前没有这个, 现在加一下。

好的写法（实际落地版本）：

> Rationale: 之前的流程盲目接受 hand-off 留下的任何东西。如果 hand-off
> 产出空/矛盾的文档, take-over 会在 nothing 上烧上下文, 用户只在
> summary 之后才发现。review 是纯静态检查(不跑测试), 成本有界。

**关键差别**：好的 Rationale 讲的是"如果不这么做会怎样"，给未来提案人一个**具体的失败场景**。

### Step 4 · Rejected 里放真候选

实际考虑过又写进 R24 的：

- **Only warn, never reject** — 具体后果："空 seed 假装成真 handoff"这个 bug 无法解决。
- **Reject-only (no remediation)** — 具体后果：每次小问题都要退回 hand-off 重跑，FTU 场景太重。
- **合并进 validate** — 具体后果：validate 是 frontmatter 语法层，review-handoff 是 body 语义层，合并会让 CLI 失败模式难辨。

每条 rejected 都能被"要不我们简化一下"的未来 agent 具体反驳掉。

### Step 5 · 检查是否需要跨组件镜像

R24 只影响 take-over 侧（hand-off 不消费这个命令）。→ 标 `(take-over specific)`。

如果影响两边（比如"给 frontmatter 加一个字段"），就得同步对方的 DECISIONS.md，标 `(cross-cutting)`，两边 `Decision`/`Rationale` 文字一致。

### Step 6 · 落地位置 = DECISIONS.md 末尾追加

不改任何旧条目。日期头 `2026-07-20 — Acceptance Review + FTU polish (v1.4.0)` 下追加 R24。

### Step 7 · Commit message 引用 ADR id

```
feat(take-over): add handoff acceptance review (Step 1.5)

Implements R24 · Handoff Acceptance Review (see DECISIONS.md).
- New reconcile.py review-handoff subcommand
- SKILL.md Step 1.5 added
- 3-branch prompt (Reject / Remediate / Force-continue)

Refs: R24
```

**注意最后一行 `Refs: R24`**——这让 `git log --grep 'R24'` 能反查所有实现这条决策的 commit。

---

## Ch 10 · 阅读顺序 · 别人（或 agent）该怎么消费 DECISIONS.md

**接手 / 修改本项目前的必读顺序**：

1. **顶部 Meta 段** — 掌握编辑规则（不改旧条、必写 Rejected、cross-cutting 镜像、id 永不复用）。
2. **搜索关键词** — 要改的东西如果和已知模块相关，先搜关键词看有没有历史决策。
3. **看时间倒序最近 3 段** — 掌握最新演进方向。
4. **回到最早的核心决策** — 这些是稳定决策，代码里大量引用。改这些之前需要非常肯定。
5. **看 rejected alternatives 是否包含你正想提的方案** — 如果包含，读它的否决理由；如果确实过时，新写一条 supersedes 而不是"忘掉那条"。

### 10.1 Agent 视角的额外建议

对于 AI agent 接到"修改本项目"任务：

- **先读 DECISIONS.md 再动主代码/规范文件**。DECISIONS 大约 6000-15000 字，读完成本约 2-4k tokens，但省下的"重新推导"成本远大于此。
- **每次自己拍板前，检查是否已有 supersedes 关系**——不要"复活"一个已经被否决的方案。
- **每次自己拍板后，如果满足 Ch 5 判定条件，主动追加一条 ADR**。不要等用户提醒。

### 10.2 Code review 视角

Reviewer 应该问：

- 这次改动是否**修改了已有 ADR 引用的字段/协议/枚举**？
  - 是 → 有没有对应 supersedes？没有就要求补。
- 这次改动**引入了新的设计决策**（有替代方案的那种）？
  - 是 → 有没有对应的新 ADR？没有就要求补。
- Commit message 里有没有 `Refs: R<n>`？
  - 没有且改动涉及决策 → 要求补。

这三个问题应该写进 code review checklist。

---

## Ch 11 · 局限与非目标

### 11.1 ADR 不是什么

- **不是完整设计规范**。规范放在 PROTOCOL.md / API doc / schema 文件，ADR 只是"规范里每条为什么长这样"。
- **不是 issue tracker**。开放问题、bug 报告、TODO 都不在 ADR 里（那些在 issue tracker 或 questions.md）。
- **不是变更日志**。CHANGELOG 面向用户"这个版本改了什么"，ADR 面向下一个作者"为什么这么改"。
- **不是权威**。ADR 记录**当时**的判断。若前提变了（新库、新平台、新用例），旧决策就该被 supersedes。ADR 的价值是"让 supersedes 这件事发生在有据可查的对话里，而不是在暗中重演"。
- **不是治理工具**。谁能拍板、拍板需要多少人同意，这些是 governance 问题，ADR 只是决策的**记录**。

### 11.2 ADR 不能防御什么

- **恶意重写**。如果作者有意抹掉历史，ADR 保护不了（`git blame` + code review 才是保障）。
- **过时不更**。如果作者拒绝写 supersedes，新读者会跟着旧决策走。这只能靠"每次改动前必须确认相关 ADR 是否还成立"的团队/agent 纪律。
- **决策错误本身**。ADR 只记录**你的决策过程**，不能替你决策。写得再工整的 ADR 也可能是错的决策——ADR 的价值在于让"错的决策"未来被识别时有据可查。
- **过度决策**。ADR 记录"值得记的决策"，但判断值不值得记本身需要判断力。见 Ch 5 判定题。

### 11.3 ADR 的成本

诚实地讲成本：

- **写作时间**：一条 ADR 约 15-40 分钟（含思考 rejected alternatives）。
- **阅读时间**：新人上手一个有 30 条 ADR 的项目，约 1-2 小时通读。
- **维护心智负担**：每次改动都要问自己"这需要 ADR 吗？supersedes 谁？scope 是什么？"

如果项目/团队/agent 不愿意付这些成本，**ADR 会成为死档案**——写了不看、看了不写、写了不同步。这时候不如不写。**ADR 是纪律，不是文件格式**。

---

## Ch 12 · 落地 checklist · 从零启动 ADR 实践

如果你想在自己项目里开始用 ADR，这是最快的起步路径。

### 12.1 第一天

- [ ] 在项目根目录创建 `DECISIONS.md`（单文件）或 `docs/adr/` 目录（一 ADR 一文件）。
- [ ] 顶部写一段 Meta 说明：本项目用哪种 ADR 格式、id 命名规则、编辑纪律（不改旧条、必写 Rejected、supersedes 用法）。
- [ ] 写第一条 ADR：**ADR-0001: 我们决定使用 ADR**。这不是玩笑，这条本身就是元决策，Rejected 里写"用 wiki / 会议纪要 / design doc"。
- [ ] 把这个新文件提交，commit message：`docs: introduce ADR practice (see ADR-0001)`。

### 12.2 第一周

- [ ] 回顾过去 3 个月的重要决策，**追认式**补写 3-5 条 ADR（标日期为"当时"而非"今天"）。**不要一次补 50 条**——精挑最有价值的。
- [ ] 在 README 里加一句"See DECISIONS.md for design rationale"。
- [ ] 在 CONTRIBUTING.md（如果有）里加"新增架构性改动需附 ADR 条目"。

### 12.3 第一个月

- [ ] 在 code review checklist 里加：
  - 是否新增决策？→ 需要 ADR？
  - 是否影响已有 ADR？→ 需要 supersedes？
  - Commit message 是否引用了 ADR id？
- [ ] 在项目模板/脚手架里加一个 `ADR-template.md`（把 Ch 4.1 的骨架复制进去）。
- [ ] 如果用了单文件 DECISIONS.md 且已经超过 30 条，考虑加自动生成的 index（Ch 7.4）。

### 12.4 长期习惯

- [ ] 每次 code review 至少花 30 秒问"这里有隐含决策吗？"
- [ ] 每次读 ADR 时如果发现过时/错误，**当场提 supersedes**，不写 TODO。
- [ ] 每季度回顾一次 ADR 集合：哪些已经过时？哪些 rejected 现在看反而应该做？记录成 review 报告。

### 12.5 反向 checklist · 停止做的事

- [ ] 停止在 Slack / 会议纪要 / 私人笔记里做 ADR 级别的讨论。
- [ ] 停止在 commit message 里放"why"细节——放到 ADR 里，commit 引用 id。
- [ ] 停止改旧 ADR 条目——一律用 supersedes。
- [ ] 停止在 PR description 里做长决策讨论——讨论过程可以留在 PR，但**结论要落到 ADR**。

---

## Ch 13 · ADR 与 Hermes Skill 自维护机制

本文档的起源材料 `skills/take-over/references/adr-and-decisions.md` 是一个 Hermes skill 的内部参考。这一章连接两者，说明 ADR 在 Hermes agent 生态里承担什么角色。

**姊妹文档**：[`hermes-agent-self-maintenance.md`](./hermes-agent-self-maintenance.md) — Hermes agent 自维护机制的完整学习文档。

### 13.1 为什么 Hermes skill 特别需要 ADR

Hermes 的核心设计是**agent-owned toolchain**——agent 有 skill 库的完整读写权限。这个设计带来两个特点：

1. **skill 是活的**——`skill_manage(action='patch')` 可以随时改。
2. **agent 是极端善忘的作者**——每次会话零上下文启动，无跨 session 记忆。

这两个特点合起来直接推导出 ADR 的必要性：**能改的东西 + 会忘的作者 = 必须有决策日志**。否则每次 agent 打开 skill 都会重新推导设计问题，可能得出与前次完全相反的结论。

### 13.2 Hermes 生态里 ADR 的独特作用

对比传统软件项目里 ADR 的作用（"给未来人类读者对齐"），Hermes 里 ADR 的作用**多了一层**：

- **给 agent 对齐**：agent 每次会话开始时会加载相关 skill（含 DECISIONS.md），ADR 直接进入 agent 上下文，指导它这次会话不要"复活"已否决方案。
- **给 skill 演化留 checkpoint**：`skill-review-cycle` 明确要求每次评审的所有决策都要在 DECISIONS.md 追加 R-entry（见 [`hermes-agent-self-maintenance.md` Ch 8](./hermes-agent-self-maintenance.md)）。ADR 变成了 skill 演化的显式 checkpoint。

### 13.3 三个具体呼应

**呼应 1 · Fix-on-discovery**

自维护机制的核心纪律之一（Ch 5.1.B）："发现 skill 有问题当场 patch"。但 patch 完之后要**留下决策痕迹**——追加一条 R-entry 记录"为什么这么改"。这是 ADR 在自维护机制里的具体落点。

**呼应 2 · Meta-learning 段**

好的 meta-skill（例如 skill-review-cycle）有 Meta-learning 段，指引 agent"学到新启发式立刻写进 references/priority-heuristics.md"。这条启发式如果影响了 skill 行为（不只是内部参考），也应该追加一条 R-entry——**新启发式是决策，不是 hackery**。

**呼应 3 · 双胞胎 skill 的 cross-cutting 标签**

Hermes 里 `hand-off` 和 `take-over` 是姊妹 skill，共享协议。任何跨双方的决策必须在两边 DECISIONS.md 都有镜像，标 `(cross-cutting)`。这是 ADR 的"跨组件"用法在 skill 生态里的具体实例。

### 13.4 从 ADR 视角看 Hermes 自维护的完整闭环

结合 [`hermes-agent-self-maintenance.md` Ch 8](./hermes-agent-self-maintenance.md) 的完整闭环，ADR 落在其中的位置：

```
用户请求 → skill 加载 → agent 执行 workflow → 遇到需要拍板的地方
                                                    ↓
                                          Ch 5 判定：值不值得写 ADR？
                                                    ↓
                                          值得 → 起草 R<n>（Ch 9 流程）
                                                    ↓
                                          patch DECISIONS.md 追加 R<n>
                                                    ↓
                                          commit message 引用 Refs: R<n>
                                                    ↓
                                          git push
```

**结果**：整个 skill 的演化历史可追溯、可回滚、可对齐。这是 Hermes agent 生态相对于传统 agent 框架最独特的价值之一。

---

## 附录 A · 各家 ADR 模板对比一览

| 特性 | Nygard | MADR | Y-Statement | 紧凑变体 | Rust RFC | K8s KEP |
|---|---|---|---|---|---|---|
| 单条长度 | 200-500 词 | 300-800 词 | 30-60 词 | 100-300 词 | 1500-3000 词 | 2000-5000 词 |
| 独立文件 vs 单文件 | 通常独立 | 通常独立 | 卡片式 | 单文件多条 | 独立 | 独立 |
| 强制 Rejected | ❌ 隐含在 Consequences | ✅ Considered Options | ✅ 一个 | ✅ 明确必写 | ✅ Rationale and alternatives | ✅ Alternatives |
| Status 字段 | ✅ 显式 | ✅ 显式 | ❌ | ❌ 用 supersedes 隐式 | ✅ 显式 | ✅ 复杂生命周期 |
| Supersedes 机制 | ✅ 手动 | ✅ 手动 | ❌ | ✅ 强制追加 | ✅ RFC 替代关系 | ✅ replaced 状态 |
| 前瞻 vs 追溯 | 追溯为主 | 都可 | 都可 | 追溯为主 | 前瞻为主 | 前瞻为主 |
| 学习曲线 | 中 | 中 | 低 | 低 | 高 | 极高 |
| 适合规模 | 中大 | 中大 | 小 | 小-中 | 大开源 | 超大 |

---

## 附录 B · 术语表

- **ADR** — Architecture Decision Record。一条决策的完整记录，包含决策 + 理由 + 否决方案。
- **DECISIONS.md** — 单文件 ADR 集合的常用命名，本仓库 skill 采用。
- **Rejected Alternatives** — 已考虑但否决的替代方案，是 ADR 的核心资产。
- **Supersedes** — 新决策明确替代旧决策，旧条保留不动。
- **Reverts** — 新决策明确撤回旧决策（比 supersedes 更强）。
- **Cross-cutting** — 决策跨越多个组件，需要在每个组件的 ADR 集合镜像。
- **Scope tag** — 决策的作用域标签，例如 `(cross-cutting)` / `(<component> specific)` / `(mirrored)`。
- **ADR id 永不复用** — 一条 ADR 的 id 分配后即使被 supersedes 也不重新分配给新条。
- **Rationale** — ADR 的"为什么这么选"段落，重点是"如果不这么做会怎样"。
- **KEP** — Kubernetes Enhancement Proposal，Kubernetes 项目的重型 ADR 变体。
- **RFC** — Request for Comments，前瞻式决策文档，代表用户 Rust / Ember 等。
- **Fix-on-discovery** — Hermes 自维护纪律：发现问题当场修，并追加 ADR 记录。
- **Meta-learning** — Skill 内部的自维护指引段落，可能触发新 ADR。

---

## 附录 C · 真实案例集 · 从本仓库 skill 提取

### C.1 R17 撞号事件（2026-07-20）

**背景**：`skills/take-over/DECISIONS.md` 里同时存在两个 `R17` 条目：

- R17 (rev-B) · Step ordering fix
- R17 (rev-C) · Filename prefix `HANDOFF-` retired

两条都写于 2026-07-17，不同批次同名。半年后如果有人写 "R17 says filename prefix must be…"，指的是哪条？

**修复**（本仓库 commit `e89918c`）：

- 老的 R17 (rev-B) → 改为 `R17b`
- 老的 R17 (rev-C) → 改为 `R17a`
- 每条加"renumbered on 2026-07-20" 说明
- 新写 R33 记录本次重编号 + 版本三轴文档

**教训**：违反了"id 永不复用/永不重复"纪律的**变种**——两条同时用了同一个 id。修复方式不是删一条，而是给旧条加后缀 + 用新 R-entry 记录重编号历史。

### C.2 三轴版本漂移（2026-07-20）

**背景**：同一个 skill 有三个独立的版本轴：

- `SKILL.md` frontmatter `version: 1.4.0`（skill 包 semver）
- `PROTOCOL.md` 顶部 `Status: v0.3 (rev-A)`（协议修订）
- DECISIONS.md 段头 `## 2026-07-20 — Acceptance Review (v1.4.0)`（决策批次）

各写各的，无人对账，导致 SKILL.md § Overview 里写 "v0.5, flat-file layout"，PROTOCOL.md 头部却还是 v0.3。

**修复**（同 commit `e89918c`）：

- PROTOCOL.md 顶部 bump 到 v0.5 (rev-C)
- DECISIONS.md 顶部加"三轴版本约定"表，明确三个轴各自的定义和 bump 规则
- 新写 R33 记录本次对账

**教训**：项目里如果有多个版本轴，必须在**一个显式位置**记录它们各自的语义，否则会静默漂移。ADR 是这个"显式位置"的合适载体。

### C.3 dogfood 报告落盘（2026-07-20）

**背景**：`take-over` skill 第一次真实使用时产出了一份中文 dogfood 报告 `调用记录-20260720.md`，7 个发现直接催生了 R24-R31。但这个文件是 untracked，一次 `git clean` 就会消失，R24-R31 的 rationale 会失去证据来源。

**修复**（commit `186d7c5`）：

- 改名 `调用记录-20260720.md` → `REVIEW-2026-07-20-dogfood.md`
- 加英文头部说明来源和角色
- 提交入库
- DECISIONS.md 里 R24 / R26 / R29 三处引用同步更新到新文件名
- 新写 R34 记录本次改名

**教训**：ADR 的证据链要**跟着 ADR 一起进仓库**。任何"当时的原始素材"如果被 ADR 引用，必须落盘。否则 ADR 的 rationale 会成为无源之水，未来无法验证。

---

## 附录 D · 快速自查表

用完 ADR 前问自己：

- [ ] 是否符合 Ch 5 的判定条件？（如果不符合，也许不需要 ADR）
- [ ] `Decision:` 段是不是**具体到可执行**（不含"应该/可能/考虑"）？
- [ ] `Rationale:` 段是不是讲了**"如果不这么做会怎样"**（而不是营销话术）？
- [ ] `Rejected:` 段至少 2 条**真候选**（不是稻草人）？
- [ ] 每条 Rejected 有**具体后果**（不是"感觉不好"）？
- [ ] 需要 supersedes 谁？有没有写清楚？
- [ ] Scope tag 是否正确（cross-cutting / specific / mirrored）？
- [ ] 是否需要在双胞胎组件镜像？镜像了吗？
- [ ] 决策 id 是否**未与已有 id 冲突**、**未复用已废弃 id**？
- [ ] Commit message 里是否引用了 `Refs: R<n>`？

十项全过 → 这是一条合格的 ADR。

---

## 附录 E · 参考资料

**必读源头**：

- Michael Nygard, *[Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)* (2011) — 概念开山。
- ThoughtWorks Technology Radar, *[Lightweight Architecture Decision Records](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)* — 推广到主流。

**模板与工具**：

- [adr.github.io](https://adr.github.io/) — ADR 社区门户，各种模板汇总。
- [adr-tools (npryce)](https://github.com/npryce/adr-tools) — 命令行工具，管理 `docs/adr/` 结构。
- [MADR 模板](https://adr.github.io/madr/) — Markdown Architectural Decision Records。
- [Olaf Zimmermann · Y-Statements](https://ozimmer.ch/practices/2020/04/27/ArchitectureDecisionMaking.html) — 一句话 ADR。

**大项目实践参考**：

- [Kubernetes KEPs](https://github.com/kubernetes/enhancements) — 大规模 ADR 变体。
- [Rust RFCs](https://github.com/rust-lang/rfcs) — 前瞻式决策记录。
- [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/) — 企业级 ADR 模板。
- [Google Design Docs](https://www.industrialempathy.com/posts/design-docs-at-google/) — 决策前的 design doc，与 ADR 互补。

**本仓库内部**：

- `docs/hermes-agent-self-maintenance.md` — Hermes agent 自维护机制的姊妹学习文档。
- `skills/take-over/references/adr-and-decisions.md` — 本文档的源材料（skill 内视角）。
- `skills/take-over/DECISIONS.md` — 一个真实的多年 ADR 集合，35+ 条决策可作为学习样本。
- `skills/hand-off/DECISIONS.md` — 姊妹 skill 的 ADR 集合，展示 cross-cutting 决策的双份维护。

---

*文档终。约 55KB。本文档由 2026-07-20 一次对话（用户"扩展 ADR 机制并放到 docs"）触发，Hermes Agent (ark-code-latest) 从 `skills/take-over/references/adr-and-decisions.md` 出发扩展写成。可自由传阅、翻译、二次创作。若发现内容过时或有误，请按 Ch 7 的 Supersedes 机制追加修订，而非就地重写。*


