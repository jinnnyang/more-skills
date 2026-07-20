# ADR 与 DECISIONS.md · 原理、机制、实践指南

> 面向对象:未来来修改本 skill(或任何采用相同模式的 skill / 项目)的 agent 与人类作者。
> 读完你会知道:ADR 是什么、为什么它是"设计的备忘链"而不是"技术日记"、什么时候必须写一条、怎么写一条、什么时候可以不写、这个 skill 自己的历史里有哪些真实教训。

---

## 1. 出身:ADR 从哪里来

**ADR = Architecture Decision Record.** 概念由 Michael Nygard 在 2011 年的博客文章 [*Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 首次系统化。他当时观察到一个反复出现的痛点:

> 大型系统的架构里到处是"为什么当初这么选"的问号。代码回答的是 *how*,注释回答的是 *what*,但 *why* 永远丢失。文档写在 wiki 会失联,写在 issue 会被关闭埋葬,写在会议纪要没人回看。半年后新人重新提出旧问题,团队又花两周把同样的替代方案再评一遍,最后得出同样的结论。

Nygard 的解药是三条:
1. 决策**跟随代码走**(放进仓库,而不是外部 wiki)。
2. 一条决策 = 一个短文件,**不可变**、按时间序号累加。
3. 每条必须包含 **Context + Decision + Consequences + Rejected Alternatives** 四段。

后续 ThoughtWorks、AWS、Kubernetes、Rust RFC、Apache 项目都以类似形态推广开来,统称 "ADR",格式细节各家略异,但**内核不变**:

> **ADR 存的是"决策的推导链",不是决策的结果本身。**

结果(HTTP 2 用 HPACK)代码里写得清清楚楚,ADR 存的是"当时也考虑过 gzip,为什么没用" —— 这是代码永远不会告诉你的信息。

---

## 2. ADR 与其他文档的区别 · 一张定位图

新人常问:"这个不是可以写在 README / 设计文档 / 注释 / commit message / walkthrough 里吗?"

它们**都不能替代 ADR**,分工如下:

| 文档类型 | 回答的问题 | 时间尺度 | 生命周期 |
|---|---|---|---|
| **代码本体** | *How* — 系统是怎么运作的? | 现在 | 会被重构改写 |
| **注释 / docstring** | *What* — 这个函数在干什么? | 现在 | 跟代码同步 |
| **README / 用户手册** | *How to use* — 用户怎么用? | 现在 | 跟功能同步 |
| **Commit message** | *What changed* — 这次改动了什么? | 单次改动 | 永久,但零散、不聚焦"设计" |
| **Design doc / RFC** | *What we're going to build* — 前瞻的方案 | 立项前 | 立项后可能废弃 |
| **`walkthrough.md`(handoff)** | *What happened this session* — 会话过程 | 会话内 | 短期,会被 prune |
| **`DECISIONS.md`(ADR)** | *Why we chose this over that* — 决策推导 | **永久** | **永不改写**,只追加 supersedes |

关键差异:
- **ADR 面向"未来的作者"**,不是当前用户;README 面向"用户",不是未来作者。
- **ADR 保留 rejected alternatives**;design doc 往往在拍板后就把否决方案删了。
- **ADR 不可变**;commit message 也不可变但太零散,单条 commit 讲不完 rationale。
- **ADR 是叙事**;架构图是拓扑。

一个简明记忆法:**代码告诉你"是什么",ADR 告诉你"为什么不是别的什么"**。

---

## 3. 为什么这个 skill 需要 ADR(而不是简单的 CHANGELOG)

普通库/工具需不需要 ADR,取决于**设计空间的复杂度**和**作者更替频率**。本 skill 两个维度都拉满:

### 3.1 设计空间深、暗礁多

看几个例子(都来自本 skill 真实历史):

- **Frontmatter 的 `status` 用 `complete` 还是 `phase-complete`?** 表面上前者更自然,但 `complete` 语义歧义(文档完了?任务完了?整个项目完了?),`phase-complete` 明确表达"这个阶段完了但文档还活着"。这是 v0.3 ⑥ 拍的板。不写 ADR,半年后 agent 一定会"简化"回 `complete`。

- **HARD conflict 应该 halt 还是 auto-log?** 前者打扰用户,后者容忍脏数据。第 ④ 号决策拍的是"HARD halt + SOFT log + AMBIGUOUS→HARD",配套 rejected alternatives 明确写了"halt on any conflict → 太打扰"、"auto-log everything → 硬冲突会静默溜过"。这两条否决理由本身比结论更重要 —— 它们是**未来"简化"提案的免疫接种**。

- **`_shared/` 目录 vs 各 skill 独立自足?** 2026-07-17 从 `_shared` 迁到独立自足,原因是"每个 skill 必须可独立 install",看起来违反 DRY,但 rejected 里写清了 "hybrid main/shim" 和 "auto-sync 脚本" 的问题(Windows 符号链接、build 步骤等),否则未来一定有人提"还是合并回去吧,重复太多"。

这些决策的**否决理由**才是资产。结论谁都能推出来,难的是记住"我们已经试过了,别再来"。

### 3.2 作者更替频率极高

本 skill 每次被使用,受影响的"作者"就换了一次:
- 一个 agent 帮用户跑一次 take-over。
- 用户想改 skill → 起一个新会话 → 新 agent 上下文里对历史一无所知。
- 另一个 agent 想 fork 这个 skill 到自己的项目 → 完全不知道历史决策。

**LLM agent 是极端善忘的作者**。它不会像人类一样"隐约记得三个月前讨论过",它每次都是零上下文启动。DECISIONS.md 就是那个"每次启动前必读的对齐文件"。

### 3.3 双胞胎 skill 的漂移风险

`take-over` 和 `hand-off` 是共享协议的姊妹 skill。它们**故意不共享文件**(2026-07-17 决策),代价是"跨文件同步靠人自觉"。DECISIONS.md 里 `(cross-cutting)` 标签就是"这条必须在另一边镜像"的信号。没有这个标签体系,两边会静默漂移到某天用户跑一次完整链路才炸出来。

---

## 4. 一条合格 ADR 的解剖

原生 Nygard 格式有严格的四段(Context / Decision / Consequences / Rejected)。本 skill 用的是**紧凑变体**,舍弃了 Context 段(合并进 Rationale)但**必须保留 Rejected Alternatives**。

### 4.1 骨架

```markdown
### <决策 id> · <一行标题> (<scope tag>)
**Decision:** <一句话拍板的具体结论,不加限定词、不用"应该"/"可能">
**Rationale:** <为什么这么选。要点回答"为什么这是最不坏的选择",不是"这样多好">
**Rejected:**
- <方案 A> — <为什么不选它的具体原因(不是"感觉不好",要有具体后果)>
- <方案 B> — <同上>
[optional]
**Supersedes:** <旧决策 id + 日期>
**Impact on <某个下游组件>:** <这个决策改变了什么后续>
```

### 4.2 决策 id 命名规则(本 skill 惯例)

- **早期核心决策**:圈号 ①②③④⑤⑥,跨 skill 稳定,`SKILL.md`/`PROTOCOL.md` 可以直接引用"§9b ④"这种坐标。
- **后续修订**:`R<数字>`(R2, R3, ..., R31)。按追加顺序编号,同一日期批次可共用日期头。
- **Scope tag**:`(cross-cutting)` = 必须在双胞胎 skill 都写;`(take-over specific)` = 只在这;`(mirrored)` = 从对方镜像过来的。

### 4.3 什么是"合格的 Rejected 条目"

**不合格**:
> Rejected: 用 JSON 而不是 YAML — 不好。

不好在哪?未来 agent 无法从中获取任何信息。

**合格**:
> Rejected: 用 JSON 而不是 YAML — JSON 不允许注释(handoff 文档需要在字段旁边解释语义),且 JSON 的 YAML 超集写法在不同 parser 上兼容性差。同时,SKILL.md 本身就是 YAML frontmatter,统一格式减少 agent 认知负担。

**判定标准**:一个从没见过此决策的 agent,看完 Rejected 那一行,能不能自己复述出"为什么不用"?能 → 合格;不能 → 补细节。

### 4.4 何时"跳过 Rejected"

**极其罕见**。真实场景大概只有:
- 决策是纯风格/惯例(用 4 空格缩进而不是 tab),这种也不用写 ADR,写 style guide 就行。
- 决策由**外部标准强制**(必须用 ISO-8601 时间戳因为 §6 定义了),但这种情况下 Rejected 应该指向"为什么当初 §6 这么定"。

如果你发现自己"想不出否决方案",99% 是**没想够**,不是"确实没有替代"。

---

## 5. 什么时候必须写一条 ADR

判定规则(取自本 skill 真实实践,按触发条件排序):

| 触发条件 | 例子 | 是否写 ADR |
|---|---|---|
| 引入一个**枚举/常量集合**且值必须稳定 | `VALID_KINDS` / `VALID_STATUS` | ✅ 必须(v0.3 ⑥) |
| **改变**跨模块协议的字段/流程 | 增加 Step 1.5 acceptance review | ✅ 必须(R24) |
| 两个明显合理方案之间**拍了板**,rejected 方案后续有人可能重提 | flat-file 还是 `HANDOFF-` prefix | ✅ 必须(R17) |
| 决策**跨越两个 skill** | `_shared/` 迁独立自足 | ✅ 必须(cross-cutting) |
| 引入一个**看起来违反 DRY / 常识**的做法 | 双份 `reconcile.py` | ✅ 必须(说明为什么值得) |
| 引入**用户可见的 UX 契约** | Yield-Turn Fallback Protocol | ✅ 必须(R26) |
| 修复一个**行为微妙的 bug** | 双换行序列化 bug | ✅ 必须(R13) |
| 改**已有 ADR** 引用的东西 | 修改 `kind` 枚举 | ✅ 必须(supersedes 旧条) |
| 纯代码层重构、无外部行为变化 | 提取一个 helper 函数 | ❌ 不写(commit message 够了) |
| 修复 typo / lint / 格式化 | / | ❌ 不写 |
| 新增测试、benchmark | / | ❌ 不写(除非测试策略本身是决策) |
| 依赖版本 bump | `pyyaml 6.0 → 6.1` | ❌ 不写(除非 bump 引入了行为变化) |

**心法**:如果 code review 里会有人问"为什么不是 X?"、且答案值得为下一次问再想一遍 —— 就写。如果答案只是"这里稍微整理了一下代码" —— 不写。

---

## 6. 常见失败模式 · 从本 skill 历史里学到的

### 6.1 反模式:"决策"其实是"实现说明"

**反例(不好的 ADR)**:
> ### R99 · check-reality 现在支持 --agent 参数
> **Decision:** 加了 `--agent` 参数。
> **Rationale:** 需要传 agent 名字进去。

这是**实现日志**,不是决策。真正的决策是"lock 机制的所有权由 agent 名字标识 vs 由 session_id 标识",实现细节(参数叫什么)不需要 ADR。

### 6.2 反模式:批量决策集中写但没拆分

**反例**:一个巨大的"2026-07-17 refactor day"条目包含 8 个不相关的决策。
**问题**:未来引用某一条时无法用稳定 id 指向。
**做法**:每个原子决策一个 `### R<n>` 子节,可以共享一个日期段头。

见本 skill 2026-07-20 v1.4.0 那段 —— 8 条决策(R24-R31)共享一个日期头,但每条独立可引用。

### 6.3 反模式:改旧条目而不是追加新条

**反例**:v0.5 引入 flat-file 后有人直接把 v0.3 ⑥ 的"kind 枚举"那一节的文字改了。
**问题**:未来有人看 git blame 找"这个字段是什么时候加的",找到 v0.5 的 commit,但 rationale 里讲的是 v0.3 的场景,对不上。
**正解**:v0.5 追加一条 `R17 filename prefix retired`,如果 v0.3 ⑥ 需要修正,写 `R<n> supersedes v0.3 ⑥`,不动旧条目本身。

### 6.4 反模式:Rejected 里全是稻草人

**反例**:
> Rejected: 什么都不做 — 不行。

这不是替代方案,是"选项 0 = 别改"。真替代方案是"用 X 库 / 用 Y 算法 / 拆到 Z 模块"这种真拿出来会 pass code review 的选项。

### 6.5 反模式:ADR 写在别的地方

见过:
- 写在 PR description 里 → PR 关闭后没人回看。
- 写在 issue tracker → 换工具就丢。
- 写在会议纪要 → 无法搜索。
- 写在私人笔记 → 只有原作者知道。

**唯一正确的地方**:项目仓库里、命名固定的文件(`DECISIONS.md` / `docs/adr/*.md`)、跟代码一起版本化。

---

## 7. 实操:从一次真实"我想改这里"到一条落地的 ADR

场景:今天用户提出"take-over 缺少接手前评审机制"。演示我实际写 R24 的思考过程。

### Step 1 · 判断这个变更够不够格

自问三问:
- 会改变外部行为吗?→ 会,加了 Step 1.5,可能 halt 加载。 ✅
- 有明显的替代方案吗?→ 有("只 warn 不 reject"、"reject 但不给 remediation")。 ✅
- 未来有人可能重提这些替代方案吗?→ 一定会(remediation 增加复杂度,后来者可能说"简化掉吧")。 ✅

→ **值得写 ADR**。

### Step 2 · 起草 Decision

第一版:

> Decision: 加一个 review-handoff 命令。

太弱。"加一个命令"是**实现**,不是**决策**。真正拍板的是:
- 存不存在这个检查(存 vs 不存)
- 严格度选哪档(严格 / 中庸 / 保守)
- reject 后的分支怎么设计(单一路径 / 三选一 / 二选一)
- take-over 自己能不能 remediate

改成:

> Decision: 新增 Step 1.5 Handoff Acceptance Review,在 check-reality 前对 hand-off 产物做静态可用性检查;verdict = pass|reject|fresh_init;reject 时通过 §0a 提供 Reject / Remediate / Force-continue 三选一;remediation 最多 3 轮回退。

现在这条,任何未来 agent 看到都能立刻理解"决策边界在哪"。

### Step 3 · 写 Rationale 时要"未来导向"

不好的写法:
> Rationale: 之前没有这个,现在加一下。

好的写法(实际落地的版本):
> Rationale: 之前的流程盲目接受 hand-off 留下的任何东西。如果 hand-off 产出空/矛盾的文档,take-over 会在 nothing 上烧上下文,用户只在 summary 之后才发现。review 是纯静态检查(不跑测试),成本有界。

**关键差别**:好的 Rationale 讲的是"如果不这么做会怎样",给未来提案人一个具体的失败场景。

### Step 4 · Rejected 里放**真候选**

我实际考虑过又写进 R24 的:
- Only warn, never reject — 具体后果:"空 seed 假装成真 handoff"这个 bug 无法解决。
- Reject-only (no remediation) — 具体后果:每次小问题都要退回 hand-off 重跑,FTU 场景太重。
- 合并进 validate — 具体后果:validate 是 frontmatter 语法层,review-handoff 是 body 语义层,合并会让 CLI 失败模式难辨。

每条 rejected 都能被"要不我们简化一下"的未来 agent 具体反驳掉。

### Step 5 · 检查是否需要跨 skill 镜像

R24 只影响 take-over 侧(hand-off 不消费这个命令)。→ 标 `(take-over specific)`。

如果影响两边(比如"给 frontmatter 加一个字段"),就得同步 `hand-off/DECISIONS.md`,标 `(cross-cutting)`,两边 `Decision`/`Rationale` 文字一致。

### Step 6 · 落地位置 = DECISIONS.md 末尾追加

不改任何旧条目。日期头 `2026-07-20 — Acceptance Review + FTU polish (v1.4.0)` 下追加 R24。

---

## 8. 阅读顺序:一个 agent 该怎么消费 DECISIONS.md

**每次修改本 skill 前的必读顺序**:

1. **顶部 Meta 段** — 掌握编辑规则(不改旧条、必写 Rejected、cross-cutting 镜像)。
2. **搜索关键词** — 你要改的东西如果和 `frontmatter` / `conflict` / `scope` / `remediation` 等关键词相关,先搜。
3. **看时间倒序最近 3 段** — 掌握最新演进方向。
4. **回到最早的 ①②③④⑤⑥** — 这些是稳定决策,`SKILL.md`/`PROTOCOL.md` 大量引用。改这些之前你要非常肯定。
5. **看 rejected alternatives 是否包含你正想提的方案** — 如果包含,读它的否决理由;如果确实过时,新写一条 supersedes 而不是"忘掉那条"。

**agent 提示词层面的建议**:接到"修改 take-over"任务时,先读完 `DECISIONS.md` 再动 `SKILL.md`。DECISIONS 大约 6000 字,读完成本 ≈ 2-3k tokens,但省下的"重新推导"成本远大于此。

---

## 9. 局限与非目标

ADR **不是**:
- **不是完整设计规范**。规范在 `PROTOCOL.md`,ADR 只是"规范里每条为什么长这样"。
- **不是 issue tracker**。开放问题、bug 报告、TODO 都不在 ADR 里(那些在 `PROTOCOL.md §13` 或 `questions.md`)。
- **不是变更日志**。CHANGELOG 面向用户"这个版本改了什么",ADR 面向下一个作者"为什么这么改"。
- **不是权威**。ADR 记录**当时**的判断。若前提变了(新库、新平台、新用例),旧决策就该被 supersedes。ADR 的价值是"让 supersedes 这件事发生在有据可查的对话里,而不是在暗中重演"。

ADR **不能防御**:
- **恶意重写**。如果作者有意抹掉历史,ADR 保护不了(git blame + code review 才是保障)。
- **过时不更**。如果作者拒绝写 supersedes,新 agent 会跟着旧决策走。这只能靠"每次改动前必须确认相关 ADR 是否还成立"的团队/agent 纪律。

---

## 10. 参考资料

**必读源头**:
- Michael Nygard, *[Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)* (2011) — 概念开山。
- ThoughtWorks Technology Radar, *[Lightweight Architecture Decision Records](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)* — 推广到主流。

**大项目实践参考**:
- Kubernetes KEPs (Kubernetes Enhancement Proposals) — 大规模 ADR 变体。
- Rust RFCs — 更前瞻(决策发生在实现前)。
- AWS Well-Architected — 企业级 ADR 模板。

**本 skill 内部相关**:
- `DECISIONS.md` — 本 skill 自己的 ADR 日志。
- `PROTOCOL.md` — 引用 ADR 编号的规范文档(如 `§9b ④`)。
- `references/frontmatter-fields.md` — 由 ADR ⑥ 派生的枚举参考。
- `../hand-off/DECISIONS.md`(若已安装)— 姊妹 skill 的镜像日志,cross-cutting 决策的另一份。

---

*最后修订:2026-07-20。若本文档过时,请追加一条 ADR 说明变化,并在此文档尾部添加 supersedes 指针,不要就地重写。*
