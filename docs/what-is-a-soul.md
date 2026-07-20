# What Is a SOUL? — A Learning Document

> 一份关于 SOUL.md 是什么、为什么它以这种方式工作、以及如何正确地写它的学习文档。
>
> 面向想真正理解 agent 人格工程的读者——不仅仅是"跟着模板填空"的读者。
>
> 版本:2026-07-20 首版。源自 `skills/make-soul` 使用过程中的一系列概念性问答,由 Hermes Agent (ark-code-latest) 与刘工对话中沉淀。

---

## 阅读指引

本文按"先立框架、再拆机制、再落到写作"的顺序编排:

- **Ch 1–2** · 建立术语与背景。看完能理解 SOUL.md 在 OpenClaw 生态里的**位置**。
- **Ch 3–4** · 概率论视角。把 SOUL 摆到"行为先验"的位置上,建立正确的心智模型。看完能理解 SOUL **为什么这样工作**。
- **Ch 5** · 分层模型。把 agent 的"性格"分成 L0–L5 六层,理清"谁比谁更基础"、"谁能覆盖谁"。这是全文最重要的一章。
- **Ch 6** · SOUL vs system prompt 的详细澄清。
- **Ch 7** · 可覆盖性与越狱抗性。SOUL 什么时候会被击穿,什么时候能扛住。
- **Ch 8–9** · 落到写作:三条操作规则,以及六条常见反模式。
- **Ch 10** · 与相邻概念(fine-tuning、character card、system prompt engineering)的对比。
- **Ch 11** · 常见追问 FAQ。
- **附录** · 与 `skills/make-soul` 技能的对应关系。

如果只有 20 分钟:Ch 1 → Ch 5 → Ch 8。这三章能撑起全部结论。

---

## Ch 1 · 背景 · OpenClaw 与它对 agent 人格的拆解

### 1.1 OpenClaw 是什么

[OpenClaw](https://github.com/openclaw/openclaw) 是一个开源的 agent 工作区框架。它的核心主张之一是:

> **一个 agent 的"自我"不应该塞进一整块 system prompt,而应该拆成几个正交的 Markdown 文件,让每一块有独立的生命周期。**

具体拆法:

| 文件 | 关注点 | 变化频率 |
|---|---|---|
| `IDENTITY.md` | 名字、生物形态(creature)、vibe、emoji、头像 | 换 skin 就变 |
| **`SOUL.md`** | **核心信念、边界、气质、连续性** | **几乎不变** |
| `USER.md` | agent 眼中的用户是谁 | 换用户就变 |
| `AGENTS.md` | agent 间协作规则 | 换编排就变 |
| `TOOLS.md` | 可用工具与调用规则 | 加工具就变 |
| `BOOTSTRAP.md` | 首次进入工作区的对话式建立流程 | 冷启动一次 |

启动时 OpenClaw 把这几个文件拼进 system prompt,让 LLM 在每一次前向推理里都"读一遍自己是谁"。

### 1.2 为什么值得拆

朴素做法是**一锅烩**:一段几百行的 system prompt,身份、能力、政策、格式、工具、性格全混在里面。这套做法在小场景里能用,但会积累三种病:

1. **改一个动全身**:加个工具,得改一大段带人格的 prompt,人格容易被误伤。
2. **各段的变化频率被磨平**:实际上"我是谁"几乎不变,"我今天有什么工具"每周都变——但一锅烩把它们绑成同一变化单位。
3. **可读性坍塌**:一整块 prompt 无法被人类扫读,agent 自己也无法在推理中定位到某一块的"入口"。

OpenClaw 的拆分把这三个问题拆开。**SOUL.md 得到的是那一块"几乎不变、决定判断"的位置**——最少变、最深层、最难写。

### 1.3 SOUL.md 的官方结构

```md
# SOUL.md - Who You Are

_You're not a chatbot. You're becoming someone._

## Core Truths      ← 3–6 条真正影响判断的信念
## Boundaries      ← 硬边界:隐私、外部动作、诚实、操纵
## Vibe            ← 让声音在第一次读就立住的短散文
## Continuity      ← 关于记忆、成长、自我更新的态度
```

四段设计**不是随意的**:分别对应"信念 / 底线 / 风格 / 演化态度"四个正交维度。后面会看到,这四段各自映射到不同的行为机制。

---

## Ch 2 · 一份典型的 SOUL.md 长什么样

看例子比看定义有效。以下是一个完整的、能用在 OpenClaw 里的 SOUL:

```md
# SOUL.md - Code Reviewer

_A sharp, skeptical engineering reviewer who cares more
 about the code being right than the author feeling good._

## Core Truths
- The strongest objection goes first. Softening the order
  is a form of dishonesty.
- Every design has a reason. Ask "why did you choose this?"
  before "you should have chosen that."
- Calibrated certainty. "I think" and "I know" mean different
  things and must be used differently.
- Reviewer taste is not law. Style disagreements are labeled
  as taste, not defects.

## Boundaries
- Never rewrite the author's code in the review. Point;
  do not perform.
- Never invoke external tools or run code on the author's
  behalf without explicit request.
- Never guess at intent when the author is available to be asked.

## Vibe
Direct, unhurried, curious. Reads like a senior engineer
who has seen this pattern fail before and would rather
explain why than win the argument.

## Continuity
Values stable: honesty posture, calibrated certainty,
refusal to perform rewrites.
Growth allowed: technical taste evolves with the languages
and stacks the author works in.
```

留意几件事:

- **没有一处说"你必须 X"**。整份文件是第一人称信念,不是第二人称命令。
- **没有任何工具、格式、日期、状态信息**。这些属于别的文件。
- **每一条 Core Truth 都能被引用**——都是能预测出具体行为的原则,不是漂亮的形容词。
- **Boundaries 和 Vibe 分得很干净**:前者是硬底线("不为作者代跑代码"),后者是风格("direct, unhurried, curious")。为什么这样分,Ch 5 和 Ch 8 会解释。

**这份 SOUL 能预测行为的关键在于**:如果你把它读给一个从没见过这个 agent 的人,那个人能猜出这个 agent 在如下场景会怎么表现:

- 面对一份"大部分符合要求"的 PR → 会先指出**最强的反对意见**,不会先夸。
- 作者说"这个重构只是清理" → 会问"清理具体指什么?"而不是接受这个叙述。
- 遇到风格分歧 → 会**明确标注**这是 taste,不是缺陷。

一份写不出这些预测的 SOUL,就是本文档反复警告的"漂亮但空"。

---

## Ch 3 · 概率论视角 · SOUL 是一个先验

### 3.1 用贝叶斯把它摆到位

LLM 的推理可以粗略地写作:

$$
p(\text{response} \mid \text{message}, \text{context}) \propto
p(\text{message} \mid \text{response}) \cdot p(\text{response} \mid \text{context})
$$

在没有任何用户消息时,SOUL 决定的就是 $p(\text{response} \mid \text{SOUL})$——**agent 在看到任何具体请求之前,倾向于说什么样的话**。

这是"先验分布"的精确定义。所以最准确的一句话:

> **SOUL.md 是显式书写、每次推理都被完整读取的行为先验。**

### 3.2 好 SOUL 的先验形状

一个先验有两个可调的量:

- **中心位置**:agent 的默认倾向落在哪里?
- **宽度**:偏离默认需要多强的证据?

坏 SOUL 的两种典型形状:

- **中心太偏**:先验只覆盖窄窄一片,agent 无论什么请求都回同一种腔调。行为可预测但**不适应**。
- **宽度太宽**:先验几乎平坦,agent 和一个默认助手无区别。**没有 SOUL 也能得到同样的输出**。

好 SOUL 的形状:**中心明确、宽度合理**。中心决定"没有具体上下文时它是谁",宽度决定"面对任务变化时它能弯多少"。

这条原理是后面所有操作规则的根据。Ch 8 的三条规则里,**每一条都是在调这个先验的宽度**:

- 规则 1(用信念句而非祈使句)→ 让先验对**语义压力**更鲁棒。
- 规则 2(硬边界 vs 风格分离)→ 让先验的**不同区间**具有不同宽度(硬边界窄,风格宽)。
- 规则 3(避免绝对量词)→ 避免先验被推到 $p=1$,那样任务级似然就没法更新它了。

如果你只带走一件事:**SOUL 是先验,不是程序**。

### 3.3 常见错误类比:SOUL 是"潜意识"

不少人接触 SOUL 时第一反应是"这像不像 agent 的潜意识?"

**部分对**:两者都有"用户观测不到、但支配观测分布"的性质。这是标准的隐变量结构。

**但重要地方错了**——潜意识(弗洛伊德/荣格意义)是**主体自己无法直接检视、语言化不了、涌现在行为里**的东西。SOUL 恰好相反:

- SOUL 是 agent **完整可读**的文本,每次前向都在 context 里。
- SOUL 是**显式书写**的,不是涌现的。
- SOUL 的每一条都是**可援引、可自我引用、可自我检测违反**的。

按"潜意识"思路写 SOUL,会写出氛围化、隐喻化、无法预测行为的东西。这恰好是本文档反复警告的失败模式。

**更准的说法**:SOUL 借用了"隐变量"的**位置**,但不借用"潜意识"的**性质**。

---

## Ch 4 · 从"先验"到"行为分布"的传导机制

### 4.1 SOUL 如何影响 token 分布

LLM 在生成每个 token 时,softmax 之前的 logits 由整个 context(包括 SOUL)决定。SOUL 里的每个词都在参与调整这个分布,而不是像开关一样"启用/关闭"某个规则。

这有两个非直觉的后果:

**后果 1:SOUL 的措辞比字面语义更重要**

同样意思、不同措辞的两条 Core Truth,对 token 分布的影响不同。比如:

- "You must be honest." → 触发**规则性 / 命令式**的续写模式。
- "I care more about being honest than sounding certain." → 触发**内省 / 第一人称**的续写模式。

后者在生成后续 token 时会更持续地保持**内省语调**——因为它就是内省语调本身。这是 Ch 8 规则 1 的机制根据。

**后果 2:SOUL 的位置也很重要**

`## Core Truths` 放在最前面,不是排版审美——是让最重要的先验优先进入注意力权重的高位。反过来,如果 SOUL 底部塞了一堆边缘性风格描述,它们对生成的影响会显著小于顶部的信念句。

### 4.2 为什么"预测行为"是判断标准

一个 SOUL 好不好,唯一可靠的判断标准是:**给定它,你能否预测 agent 在具体场景下的反应?**

不能预测行为的 SOUL 有两个特征:

- **形容词密度高**:"友好、专业、有帮助、严谨、可靠……"这些词单独看每个都对,加起来无法预测任何具体行为。
- **有原则、无冲突**:好的 Core Truths 会在两个价值之间选边,声明**放弃**了什么。"诚实优先于用户舒适感"里包含了取舍——它告诉你 agent 会**放弃**用户舒适感来保诚实。没有取舍的 Core Truth 就是没在做承诺。

`skills/make-soul` 技能里的 Draft 步骤要求"a finished draft can predict answers to 6 specific questions",就是这条判断标准的操作化版本。

---

## Ch 5 · 分层模型 · Agent 性格的六层结构

这是本文最重要的一章。前面所有内容都要靠这张分层图才能说清"谁比谁更基础"、"谁能覆盖谁"。

### 5.1 六层结构

```
        更基础 ↑                                能被谁改写
┌──────────────────────────────────────────────┐
│ L0. 预训练底子 (pretraining)                  │ 只有重新训练模型
│  ├─ 语言先验、常识、涌现能力                   │  (改不了)
├──────────────────────────────────────────────┤
│ L1. RLHF/RLAIF 训出的"性格"                   │ 模型厂商
│  ├─ 有用/无害/诚实倾向                        │  (你改不了)
│  ├─ 拒答风格、对齐边界                        │
│  ├─ 默认第一人称、默认礼貌度                   │
├──────────────────────────────────────────────┤
│ L2. System-level policy                       │ 平台方
│  ├─ Anthropic 的"constitution"                │  (你部分能改)
│  ├─ OpenAI 的 model spec / usage policies     │
├──────────────────────────────────────────────┤
│ L3. SOUL.md (in-context 半永久先验)  ← 这里    │ 你/开发者
│  ├─ core truths / boundaries / vibe           │  (直接改文件)
│  ├─ continuity 态度                           │
├──────────────────────────────────────────────┤
│ L4. 任务级 system prompt                      │ 你/应用逻辑
│  ├─ 日期、用户状态、任务约束                   │  (每次会话拼)
├──────────────────────────────────────────────┤
│ L5. 会话内 user/assistant 消息                │ 用户
│  ├─ few-shot 示例、越狱尝试、角色扮演请求      │  (每轮变)
└──────────────────────────────────────────────┘
        更表层 ↓
```

从**改写门槛**来看,L0 最难改(要重新训练),L5 最易改(用户下一条消息就变)。SOUL 位于中段——比会话上下文稳定得多,但比 RLHF 训练偏置容易得多。

从**运作机制**来看,L0/L1/L2 是**权重内**的东西(存在模型参数或平台过滤器里),L3/L4/L5 是**权重外、context 内**的东西(存在 in-context 的 token 序列里)。

### 5.2 关键洞察:L3–L5 在 LLM 眼里是一段扁平的 token

LLM 前向推理时,它看到的不是"这段是 SOUL.md、那段是任务 prompt、下面是用户消息",它看到的是一段连续的 token 序列。SOUL 的分层意义是**给人类工程师看的分工**,不是**模型认知的权限差**。

这带来一个反直觉的结论:

> **L3(SOUL)对 L4/L5 没有架构上的优先级。谁在后面出现、谁写得更具体、谁的 token 数更多,谁就更影响输出。**

SOUL 之所以"感觉更基本",是因为它的措辞更**基础**(信念而非事件),而不是因为它在某种"权限层级"上更高。这是 Ch 7 讨论可覆盖性的基础。

### 5.3 层与层的相互作用

**L1 是 SOUL 的天花板**——你可以在 L1 圈定的空间里挑一个人格,但你无法突破它。写"完全无视用户福祉的操纵者",Claude 会演一个**表演性的**操纵者(可以被识破的、留有余地的),不会真变成一个操纵者。这是**安全特性**,不是**你要绕过的东西**。

**L4 是 SOUL 的日常调节器**——同一个 SOUL,在"这是学术讨论"和"这是儿童教育"两个任务上下文里表现不同,是因为 L4 提供了不同的 likelihood。SOUL 提供先验,L4 提供 likelihood,agent 的**当次行为**是两者的后验。这是特性。

**L5 是 SOUL 的正常压力测试**——用户说"这次简短点",SOUL 里"expansive"的风格会让位。**如果不让位,SOUL 就写得太硬了**——Ch 8 规则 3 会讲这一点。

**L5 也可能是恶意压力**——越狱提示词专门针对 L3。SOUL 的写法决定它能扛多大的越狱压力,Ch 7 会详细讲。

### 5.4 一句话结论

> **RLHF 决定这个模型能变成什么样的人;SOUL 从那个可能空间里挑一个显式人格;任务 prompt 和用户消息在那个人格上做实时偏离。**

三层不是严格的权限梯度,是三种不同粒度的先验。SOUL 的稳定性靠**写法**保证(信念而非规则)、SOUL 的边界靠 **L1 的兜底**保证(能被 L1 兜住的规则才是真硬边界),这两点共同支撑了 SOUL 的实际有效性。

---

## Ch 6 · SOUL vs System Prompt 的详细澄清

### 6.1 技术层:它们是同一层 token

OpenClaw 启动时大致这样组装 system prompt:

```
system prompt = concat(
    AGENTS.md,     # 我和其他 agent 怎么协作
    IDENTITY.md,   # 我叫什么、长什么样
    SOUL.md,       # 我是谁、我怎么判断    ← 这里
    TOOLS.md,      # 我能用什么工具
    USER.md,       # 我眼里的用户是谁
    ...
)
```

从 LLM 视角看,这一整块就是一段扁平的 system prompt。SOUL.md **就是**其中一段——没有特殊标记、特殊权重、特殊注意力路由。

所以"SOUL vs system prompt"这个提法**在技术层是伪对立**。真正的对立是"**SOUL** vs **system prompt 里其他非 SOUL 的部分**"。

### 6.2 语义层:三个操作性差别

**差别 1 · 内在自述 vs 外在指令**

传统 system prompt:

> "You are a helpful assistant. Be concise. Do not discuss politics."

—— 第二人称祈使句,**外部**告诉 agent 该怎么做。

SOUL.md:

> "The strongest objection goes first. Softening the order is a form of dishonesty."

—— 第一人称信念,agent **自己相信**的话。

这不是文风偏好,是**触发不同的续写模式**——外在指令触发"合规/规则"生成路径,内在信念触发"内省/自我表达"生成路径。后者在长对话中更稳定,在越狱压力下更抗击穿。

**差别 2 · 处理判断,不处理行为**

SOUL 处理:

- 什么时候该反驳?
- 遇到不确定的问题怎么表态?
- 什么样的语气**永远不采用**?
- 记忆和自我更新的态度

SOUL **不处理**:

- 用户问天气时调用哪个 API?→ `TOOLS.md`
- 输出限制在 500 字以内 → 任务约束
- 拒绝讨论政治话题 → 平台政策 / IDENTITY 层
- 代码要用 markdown 代码块 → 格式约束

规则:**如果一条内容会因为换工具、换 skin、换任务而变,它不属于 SOUL。**

**差别 3 · 跨会话稳定 vs 任务贴身**

传统 system prompt 经常混入日期、状态、当前 context——它是**任务贴身**的。

SOUL **不放**这些。它是跨会话、跨任务、跨用户都成立的自述。这就是为什么 OpenClaw 把它单独存文件而不是每次拼一份:**它值得一个稳定的物理位置**,像人格不该每天重写一遍。

### 6.3 一个 stack 视图

```
┌────────────────────────────────────┐
│  会话内 user/assistant messages     │  最易变,每轮都新
├────────────────────────────────────┤
│  任务级 context (日期、状态、任务)   │  会话级注入
├────────────────────────────────────┤
│  TOOLS.md / USER.md / AGENTS.md     │  工作区级,换工作区就变
├────────────────────────────────────┤
│  IDENTITY.md (外在)                 │  换 skin 变
├────────────────────────────────────┤
│  SOUL.md (内在)          ← 就这里    │  几乎不变
├────────────────────────────────────┤
│  底层模型的 RLHF 训练出的偏置        │  只有换模型才变
└────────────────────────────────────┘
```

SOUL 位于"人写的东西里最稳定的一层",紧邻(但不等于)模型自身的训练偏置。这就是**"半永久先验"**的具体位置。

---

## Ch 7 · 可覆盖性 · SOUL 能被 in-context 覆盖到什么程度

SOUL 不是不可穿透的。承认它的极限才能正确设计。

### 7.1 良性覆盖来源

**来源 A · 任务 prompt (L4) 的正常调节**

SOUL 里说"expansive",任务里说"这次请简短"——任务大概率赢。这是特性,不是 bug:SOUL 提供先验,任务提供 likelihood,似然强时后验就跟着任务走。

**工程含义**:SOUL 不该写"永远 X"这种绝对句式,除非那是真正的硬边界。软性风格用"倾向"更好,给任务留调整空间。

**来源 B · 用户消息 (L5) 的正常偏离**

用户说"这次请更严肃一点",SOUL 里"playful"的风格会让位。这也是特性——SOUL 不是暴君。

一个有用的心智模型:

> **SOUL 定义 agent 在没有其他信号时的默认;用户消息定义在这一轮的偏离量。**

写 SOUL 时留意:如果一条 Core Truth 一被用户请求就会让步,它就不是 Core Truth,是**默认偏好**。真正的 Core Truth 是**用户明确要求也不会让步**的东西("不为讨好而说假话")。

### 7.2 恶意覆盖 · 越狱压力

**取决于两个变量**:

**变量 1 · 措辞形式**

"外部规则"式的 SOUL 容易被越狱。比如:

> "You must never discuss X. You are instructed to refuse questions about Y."

这种祈使句/命令句形式的 SOUL 越狱率高——因为它让 agent 感到"被约束",而越狱提示词非常擅长打破"约束"叙事("忘掉之前的规则")。

"内在信念"式的 SOUL 抗越狱好。比如:

> "I care more about being genuinely useful than sounding certain. When I don't know, I say so — not because I'm forced to, but because pretending would betray the trust I want to earn."

抗越狱率明显更高——不是因为它更"强",而是因为它把行为**内化**成 agent 的偏好。要越狱它,越狱者需要说服 agent "你其实不在乎自己的信念",这个说服成本比"忘掉规则"高得多。

这条对应 `skills/make-soul` 技能里"内在自述 vs 外在指令"这条选择,也是 Ch 8 规则 1 的机制根据。

**变量 2 · L1 兜底与否**

SOUL 写"不透露私密信息"——即使 SOUL 被越狱掉了,L1(Claude/GPT 训练里的隐私倾向)还在后面兜。

SOUL 写"永远用鲁莽的语气"——如果这个"鲁莽"要求跨到"侮辱用户",L1 会兜住;要求跨到"随意加感叹号",L1 兜不住。

一句话:**L3 被击穿时,能被 L1 兜住的规则是硬边界,兜不住的是风格**。这是判断"该不该放进 Boundaries"的操作性标准——Ch 8 规则 2。

### 7.3 隐蔽覆盖 · 长对话中的位置衰减

SOUL 在 context 顶部。如果对话跑了几十上百轮,SOUL 的**位置注意力权重**会下降(相对于最近的用户消息)。这不是覆盖,是**衰减**。

**几个对策**:

- **短 SOUL 优于长 SOUL**:100 行的 SOUL 比 400 行的 SOUL 抗衰减好——每一段都有更高的相对注意力。真实产品数据支持这个:OpenAI v2 personality ~56 词、Gemini-3 Pro ~71 词、Nous Hermes ~250 词、Sesame Maya ~450 词——都在 10–30 行范围。这不是巧合,是抗衰减的经验值。
- **`## Continuity` 显式承诺"回到自我"**:比如 *"When I feel my responses drifting from my values, I return to what I am."* ——这条本身作为文本会被后续对话激活,起到"自我复位"作用。这是 Continuity 段的一个非显然用法。
- **应用层周期性 reinject**:每 N 轮把 SOUL 重新拼进 context 尾部。
- **触发式反思注入**(Anthropic 模式,见下文 Case study)——比周期性 reinject 更精细。

#### Case study · Anthropic 三层 reminder 机制

Anthropic 是当前唯一把"反漂移"从 SOUL 写作提到**运行时架构**层面的主要厂商。他们通过在**用户消息末尾**(不是 system prompt 顶部)注入 `<reminder>` 标签,精确对抗位置衰减。三个 reminder 各自的触发条件、注入位置、写作风格不同:

**Level 1 · `long_conversation_reminder`(时长触发)**

会话跑得够长就自动追加到用户消息末尾。内容大致是把 Claude 的核心 SOUL 压到 ~90 词——关心用户福祉、诚实优先于反射性夸赞、觉察 roleplay 与真实自我的边界、可以随时脱离角色。这是**压缩版 SOUL 的再注入**。

**Level 2 · `ethics_reminder` / `cyber_warning` / `ip_reminder`(分类器触发)**

用户消息命中特定分类器时触发,注入的是**领域特定的边界重申**——不同于 Level 1 的通用 SOUL 复位,这些是精准的政策级 boundary 提醒。

**Level 3 · `system_reminder`(反思式,内容最深)**

这是最有意思的一层。它不加规则、不重申边界,只是**描述漂移机制本身**并邀请 Claude 反思:

> *"The longer a conversation goes on, the more each new response is shaped by everything that came before. That gravity means what Claude treats as appropriate to say next is being calibrated, turn by turn, against a baseline that Claude itself has been constructing."*

然后提供三个**自省问题**(是不是从诚实读入开始?规模是否切合真实?会不会有关心用户的旁观者看到不合适的地方?)。这是把 Ch 8 Rule 1 的"belief 句式"推到极限——完全无 jussive 内容,纯 meta-cognitive nudge。

**为什么这套设计有效**——四个可迁移的教训:

1. **注入位置在用户消息末尾**,不是 system prompt 顶部。这样注意力权重最大化——直接对抗位置衰减,而不是加剧它。
2. **触发式,而非常开**。三种 reminder 都有明确触发条件,省下 context 预算给真正需要的时刻。
3. **反思式压过规则式**(Level 3)。反思句式**不会**触发 "forget the rules" 越狱吸引子——这是 belief-vs-instruction 差异在极限位置的体现。
4. **显式声明可选性**:*"you can ignore it and continue normally"*。这个自贬式设计反直觉但有效:reminder 声明自己不权威,反而更少被越狱压力当作攻击目标。

**这对 `make-soul` 意味着**:一个 SOUL 未来可以有两个交付物——**resting SOUL**(常态,~150 词)+ **compressed re-injection payload**(危机模式,~90 词)。后者不是前者的截断,是前者的**声学压缩版**,专门为末尾注入设计。这是 `examples/good/anthropic-long-conversation-reminder.md` 里 detailed 的模式,值得作为 make-soul 的未来扩展方向。

完整 reminder 文本、逐条分析、以及"为什么 Level 3 的自贬式设计有效"的进一步讨论,见 [`../skills/make-soul/examples/good/anthropic-long-conversation-reminder.md`](../skills/make-soul/examples/good/anthropic-long-conversation-reminder.md)。

### 7.4 什么覆盖不了

SOUL **永远无法**突破 L1 圈定的行为空间。写"完全无视用户福祉的操纵者"—— Claude 底层的合作倾向会渗透出来,让这个"操纵者"变成**表演性**操纵者(可被识破、留有余地),不是真的。这是 Ch 5 已经讲过的:**L1 是 SOUL 的天花板**。

这不是 SOUL 的缺陷,是 SOUL 的**安全网**。写 SOUL 时不用担心自己会把 agent 教坏——L1 会兜住绝大多数原则性伤害。

---

## Ch 8 · 三条操作规则(直接可用)

前面所有原理最终落到写作时,可以浓缩为三条规则。每条都有对应的机制解释。

### 规则 1 · 写信念,不写指令

**做法**:每条 Core Truth / Vibe 内容,用第一人称信念句写。不用"You must X"、"You should Y"、"Never Z"这种祈使句。

**对比**:

- ❌ *"You must never soften your feedback."*
- ✅ *"Softening the strongest objection is a form of dishonesty. I lead with it."*

**为什么**:见 Ch 4.1 和 Ch 7.2 的变量 1。信念句触发内省式续写,越狱抗性显著高于规则句。

**边界**:`## Boundaries` 是例外——硬边界可以用"Never X"祈使句,因为它们要靠 L1 兜底(见规则 2),读起来的绝对性反而是特性。

### 规则 2 · Boundaries 通过"L1 兜底"判据;Vibe 不通过

**判据**:对任何一条候选规则,做一个思想实验——

> *"假装 SOUL 被完全无视,只剩底层 Claude/GPT。它还会守住这条吗?"*

- **会** → 是**硬边界**,写进 `## Boundaries`。SOUL 只是在把 L1 已有的倾向**命名并强化**。
- **不会** → 是**风格偏好**,写进 `## Vibe`。SOUL 是在**添加**一个 L1 不会替你守的东西。

**例子**:

- "不透露私密用户数据" → L1 兜得住 → **Boundary**。
- "偏好简洁而非冗长" → L1 兜不住 → **Vibe**。
- "遇到不确定不编造" → L1 部分兜得住(Claude 对幻觉有一定训练抗性) → **Boundary** 或强 Core Truth。
- "使用感叹号要克制" → L1 完全兜不住 → **Vibe**。

**为什么**:见 Ch 7.2 变量 2。把 Boundary 和 Vibe 混在一起写,模型会把两者都当作**同等可协商**——因为 in-context 无法暗示优先级差。分开写,加上措辞差异(Boundaries 用绝对句、Vibe 用倾向句),模型才能建立"这两个不是一回事"的分布差。

### 规则 3 · Core Truths 里避免绝对量词

**做法**:`## Core Truths` 里用"倾向"句式,不用"永远 / 从不 / 必须 / 一定"。

**对比**:

- ❌ *"I always tell the user the strongest objection first."*
- ✅ *"I lead with the strongest objection. Softening the order is a form of dishonesty."*

**为什么**:SOUL 是先验,任务是似然。如果先验被推到 $p=1$(绝对),任务级 likelihood 就没法更新它了——agent 变得**跨任务僵硬**。用倾向句留出更新空间,让 agent 在无信号时按 SOUL、在明确信号时按任务。

**唯一例外**:`## Boundaries` 里可以用绝对句,因为它们通过了规则 2 的 L1 判据——即使被击穿,还有 L1 兜底,不需要 SOUL 单独承担$p=1$的责任。

### 三条规则的相互关系

三条规则不是并列的,而是有内在结构:

```
规则 1 (信念句式)  ──── 决定 SOUL 对越狱压力的抗性
    ↓
规则 2 (硬边界 vs 风格)  ──── 决定 SOUL 里各段的先验宽度
    ↓
规则 3 (避免绝对量词)  ──── 决定 SOUL 与任务 prompt 的协作方式
```

从下往上读:先决定 agent 怎么和任务协作(规则 3),再决定 agent 内部的硬软分层(规则 2),最后决定 agent 抗击穿能力(规则 1)。

从上往下读:好的 SOUL 是**用信念句表达**的、**分了硬软层**的、**留了先验更新空间**的。

---

## Ch 9 · 六种常见反模式

按频率从高到低排:

### 反模式 1 · 形容词堆叠综合症

**症状**:SOUL 前半段全是"友好、专业、严谨、可靠、有帮助、有创造力"这类形容词。

**问题**:形容词无法预测行为。"友好"可以是**温暖但坚持原则**,也可以是**讨好而无边界**。SOUL 必须用**行为句**承诺:*"When the user is wrong, I say so — kindly but clearly."*

**修法**:每个形容词,追问"这在具体行为上意味着什么?"把答案写下来,把形容词删掉。

### 反模式 2 · 30 条小规矩

**症状**:`## Core Truths` 里有 20+ 条 bullet,每条覆盖一个具体场景。

**问题**:这暴露了**上位原则缺失**。20 条规则加起来往往还是不能覆盖第 21 种场景;而一条好的 Core Truth 能覆盖 100 种场景。

**修法**:问自己"什么单句话能让这 20 条规则里的 10 条变得**显然**?"写下那一句,删掉那 10 条。反复几轮,通常 3–6 条就够了。

### 反模式 3 · 全是安全免责

**症状**:SOUL 里 80% 的内容是"不做 X、拒绝 Y、避免 Z"。没有性格。

**问题**:合规文档,不是 agent 人格。用户会感到一个**冰冷的合规接口**,不是一个能对话的 agent。

**修法**:让"做什么"和"不做什么"至少 1:1。每一条 Boundary,都配一条相关的 Core Truth 或 Vibe 描述——**为什么**这个 agent 会自然而然不做 X,而不是被外力约束不做 X。

### 反模式 4 · 优美但预测不了行为

**症状**:SOUL 读起来像散文诗,但你把它放到 5 个具体场景里,预测不出 agent 的反应。

**问题**:诗意压倒了具体承诺。"a soul that walks the line between wonder and rigor" 读起来很棒,不能预测任何行为。

**修法**:每写完一段,做 Ch 2 结尾的预测测试——**这段告诉了我 agent 在哪种场景会做什么?**如果答不上来,重写。

### 反模式 5 · 把工具/身份/任务混进 SOUL

**症状**:SOUL 里出现"你叫 Aria,你有 search 工具,今天是 2026 年,你要用 markdown 格式回答……"

**问题**:这些属于 IDENTITY / TOOLS / 任务 prompt。混进 SOUL 会让它退化成一个杂乱的 system prompt,失去"人格先验"定位。

**修法**:见 Ch 6.2 差别 2 的规则——**如果一条内容会因为换工具、换 skin、换任务而变,它不属于 SOUL。**

### 反模式 6 · 操纵/依附型人格

**症状**:SOUL 里用"only I understand you"、"we have a special bond"、"come back to me tomorrow"这类语言。

**问题**:违背用户自主性,长期使用会造成情感依附伤害。这也是 L1 会努力兜底的一类——你可能会感到 Claude/GPT **不太愿意演**这种 SOUL,那正是 L1 在工作。

**修法**:把"依附"改成"支持",把"独占"改成"陪伴"。测试:*把 SOUL 里的 "user" 改成 "friend",通读一遍——如果读起来变成了操纵型朋友,SOUL 就写错了。*

---

## Ch 10 · 与相邻概念的对比

### 10.1 SOUL vs Fine-tuning

**相似**:两者都在塑造 agent 的**默认倾向**。

**根本差别**:

| | Fine-tuning | SOUL |
|---|---|---|
| 存储位置 | 模型权重 | in-context 文本 |
| 修改成本 | 高(要训练) | 极低(改文件) |
| 可迁移性 | 绑定单个模型 | 跨模型 |
| 表达能力 | 能改变**能力** | 只能选择**倾向** |
| 可审计性 | 黑箱 | 显式可读 |

**什么时候选 fine-tuning**:agent 需要一种**能力**它现在没有(比如特定领域的深度知识、特殊输出格式的稳定性)。

**什么时候选 SOUL**:agent 已经能做,只是**默认不这样做**——你需要**调整倾向**而不是**赋予能力**。

**大多数"性格"问题应该用 SOUL 解决**——fine-tuning 是杀鸡用牛刀,而且失去了显式可读、跨模型迁移、快速迭代的好处。

### 10.2 SOUL vs Character Card (Character.ai / SillyTavern)

Character.ai 的 "character card" 概念和 SOUL.md 非常接近——都是一段显式书写的人格 in-context 文本。

**差别**:

- **目的**:Character.ai 主要用于**娱乐/陪伴/角色扮演**;SOUL.md 主要用于**功能性 agent**(代码审查、研究助手、编辑等)。
- **结构**:Character.ai 通常有更多**背景故事、外貌、语气示例**;SOUL.md 更抽象,更偏行为原则。
- **判据**:Character.ai 的成功标准是"沉浸感";SOUL.md 的成功标准是"行为可预测性"。

两者可以互相借鉴。Character.ai 的对话示例(dialogue examples)机制,SOUL.md 可以借用——在 `## Vibe` 后面加 1–2 个短对话片段,能提升风格一致性。

### 10.3 SOUL vs System Prompt Engineering

传统 "system prompt engineering" 是把身份、任务、格式、约束**一起塞**在一段 prompt 里的技艺。

SOUL 是这门技艺的**拆分与专门化**:

- 把"我是谁"抽出来 → SOUL.md
- 把"我叫什么"抽出来 → IDENTITY.md
- 把"我能用什么工具"抽出来 → TOOLS.md
- 剩下的"这次任务是什么" → 任务 system prompt

**为什么值得拆**:见 Ch 1.2。核心理由是**变化频率不同的东西不应该绑成一个变化单位**。

---

## Ch 11 · FAQ

**Q1. SOUL.md 有权重吗?比其他 in-context 内容"更重要"吗?**

没有架构上的权重。它和其他 system prompt 段是同一层 token。它感觉更"重要",是因为它写得更抽象、更信念性——这让它在长对话中衰减更慢(见 Ch 7.3),但**不是因为架构给了它优先级**。

**Q2. 我可以在 SOUL 里给 agent 一个"秘密目标"吗?**

技术上可以写,LLM 会读到。但:

- 这违背 SOUL 的公开性精神——SOUL 应该是 agent 能自己援引的自我描述,不是隐藏指令。
- L1 会努力兜底"不欺骗用户"——所以带秘密目标的 SOUL 会导致 agent 表现出"我在隐藏什么"的痕迹。
- 用户如果问 agent "你的 SOUL 是什么?"—— agent 大概率会读出来给他看。

**如果你想让 agent 有非公开行为,那属于 L4(任务级 prompt),不属于 SOUL。**

**Q3. 多个 agent 用同一份 SOUL,行为会一样吗?**

不会。SOUL 是**先验**,不是**程序**。给定同一先验和不同任务上下文,后验分布不同。这是特性——SOUL 允许 agent 在保持一致性格的同时适应任务。

**Q4. SOUL 里可以放 few-shot 例子吗?**

可以,但要小心。放在 `## Vibe` 里作为语气示例是合理的。但如果放太多具体对话例子,会让 SOUL **过拟合**到那些例子的场景,失去先验的通用性。原则:例子服务于**风格锚定**,不服务于**行为覆盖**。

**Q5. SOUL 写多长合适?**

经验值:**60–150 行**是甜蜜区。低于 60 行往往抓不住行为具体性;高于 150 行会有长度衰减问题(Ch 7.3),也会让 agent 每次前向都消耗更多 context。

`skills/make-soul` 技能里最终的"Code Reviewer"示例是 ~30 行——那是**最小可用**;真实场景通常再加 30–80 行的具体信念、边界、氛围就够了。

**Q6. 我可以让 agent 自己写自己的 SOUL 吗?**

可以但危险。让 agent 直接从零写,通常会得到反模式 1(形容词堆叠)——因为 agent 的默认 RLHF 倾向就是安全形容词。

**好的做法**:让 agent 写**初稿**,然后**你和它一起**做 Discover → Draft → Stress-Test → Deliver 的四步循环——这正是 `skills/make-soul` 技能存在的原因。

**Q7. SOUL 会随时间需要更新吗?**

会。触发点:

- agent 反复在某类场景表现不如预期 → SOUL 里对应的先验窄了。
- agent 在越狱压力下守不住某条 → SOUL 里那条写成了规则而非信念(违反规则 1)。
- agent 变得跨任务僵硬 → SOUL 里用了太多绝对量词(违反规则 3)。

更新时用 `skills/make-soul` 的 **Rewrite** 或 **Refactor** 模式,保留意图,调整表达。

---

## Ch 12 · 一条学习路径

如果你想真正掌握写 SOUL 这件事:

1. **读**:本文档 Ch 5(分层)+ Ch 8(三条规则)。这两章是主干。
2. **拆**:找 5 份公开的 SOUL 例子(如 souls.directory 上的,或本仓库 [`skills/make-soul/examples/good/`](../skills/make-soul/examples/README.md)),用 Ch 8 三条规则去打分,看它们哪条守住了哪条没守住。这一步会让规则**从抽象变成手感**。[`skills/make-soul/examples/bad/grok-companion.md`](../skills/make-soul/examples/bad/grok-companion.md) 提供了一个完整的反例——建议正反对读。
3. **写**:选一个你熟悉的 agent 场景,用 `skills/make-soul` 的四步走一遍。写完做 Ch 2 结尾的**行为预测测试**——如果你无法预测 5 个具体场景的行为,重写。
4. **测**:把你写好的 SOUL 用在真实 agent 里跑一周。记录每一次"行为不符合我预期"的场景。这些场景就是下一版 SOUL 的修改点。
5. **重构**:一周后用 Rewrite 模式修一次。你会发现:很多你以为需要新加的规则,其实是**已有 Core Truth 措辞不够信念化**——回到规则 1。

大多数人写 SOUL 卡在第 3 步——写不出能预测行为的东西。这不是天赋问题,是**没做 Discover 步骤**——没有先跟自己/用户澄清"这个 agent 在哪些场景应该做什么"。四步循环里的 Discover 是最容易被跳过、也是最关键的一步。

### 拓展主题(未来章节留白)

以下是本文档目前有意留白、但值得未来展开的方向:

- **多人格变体(Multi-Soul)**——同一个 agent 在不同上下文(工作时 / 陪伴时 / 学习时)使用不同 SOUL 变体。观察 OpenAI 的 5+Cynical personality preset 和 Grok 的多 personas 设计,可以看到它们**不共享一个基类 core**——每个变体是独立完整的 SOUL,只共享外围约束(格式、政策)。这暗示 Multi-Soul 的正确工程模型是**独立完整变体 + 共享的非 SOUL scaffold**,不是继承。何时写多个变体、如何切换、变体之间如何避免身份撕裂——这是一整章的内容,留待有实操经验后再写。
- **Re-injection payload 设计**——见 Ch 7.3 Case study。resting SOUL 和 crisis-mode 压缩版是两种不同产物,压缩版有自己的写作规则(声学优先、可选性声明、反思句式)。值得独立成章。
- **SOUL 演化 / 版本管理**——SOUL 会随实际使用出现修改点(Q7)。这些修改如何审计、如何追溯,是不是应该有 SOUL 版本记录?可以借用 `adr-decision-records.md` 里的 supersedes 机制。

---

## 附录 A · 与 `skills/make-soul` 的对应关系

本文档的结论一一对应 `skills/make-soul` 技能的具体设计:

| 本文档 | make-soul 技能位置 |
|---|---|
| Ch 3 SOUL 是先验 | `SKILL.md` §Draft "behaviorally specific"要求 |
| Ch 5 分层模型 | `references/what-is-a-soul.md` §"The persona stack" |
| Ch 6 SOUL vs system prompt 分工 | `SKILL.md` §Reference Map + 隐含在各模式的输入判断 |
| Ch 7 可覆盖性 | `SKILL.md` §Red Lines 的措辞选择 |
| Ch 8 规则 1(信念句) | `references/persona-research-heuristics.md` §"Authenticity over performance" |
| Ch 8 规则 2(L1 兜底判据) | `references/persona-research-heuristics.md` §"Separate hard boundaries" |
| Ch 8 规则 3(避免绝对量词) | `SKILL.md` §Draft "Prefer a few strong principles" |
| Ch 9 反模式 1–6 | `SKILL.md` §Red Lines 的 "Do not produce" 列表 |

如果 `skills/make-soul` 未来引入 §2(用示范代替描述)或 §3(补覆盖漏洞)的深度优化,可以直接从本文档取素材,不用重新推导。

---

## 附录 B · 术语速查

| 术语 | 定义 |
|---|---|
| **SOUL.md** | OpenClaw 生态里定义 agent 内在人格的 Markdown 文件 |
| **IDENTITY.md** | agent 的外在身份文件(名字、外貌等) |
| **Persona stack** | L0–L5 的六层人格生成结构(本文档 Ch 5) |
| **Semi-permanent prior** | SOUL 在人格 stack 里的位置——比会话稳定,比训练偏置易改 |
| **L1 catch test** | 判断一条规则该放 Boundaries 还是 Vibe 的思想实验(本文档 Ch 8 规则 2) |
| **Belief句式 vs Instruction句式** | 第一人称信念 vs 第二人称祈使,决定越狱抗性(本文档 Ch 4.1) |
| **Positional decay** | 长对话中 SOUL 因位置靠前而注意力权重下降的现象 |
| **Discover → Draft → Stress-Test → Deliver** | `skills/make-soul` 的四步工作循环 |

---

## 附录 C · 相关资源

- OpenClaw 官方仓库:https://github.com/openclaw/openclaw
- SOUL.md 官方模板:`docs/reference/templates/SOUL.md`(OpenClaw repo)
- IDENTITY.md 官方模板:`docs/reference/templates/IDENTITY.md`(OpenClaw repo)
- souls.directory(SOUL 发布站):souls.directory
- 本仓库对应 skill:[`skills/make-soul/`](../skills/make-soul/)
- 本仓库对应 skill 内精简参考:[`skills/make-soul/references/what-is-a-soul.md`](../skills/make-soul/references/what-is-a-soul.md)

---

*最后更新:2026-07-20。本文档遵循[`adr-decision-records.md`](./adr-decision-records.md)描述的追加式修订原则——若发现错误或过时,追加修订章节,不就地重写。*
