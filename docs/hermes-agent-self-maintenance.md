# Hermes Agent 自维护机制 · 学习文档

> 一份关于 Hermes Agent "技能自维护"设计的学习手册。
> 面向想深入理解 agent-owned toolchain 架构的读者。
> 版本：2026-07-20 首版。作者：Hermes Agent (ark-code-latest) 与 刘工 对话中沉淀。

---

## 阅读指引

本文档按"从上到下、由浅入深"编排：

- **Ch 1–2** 建立背景与概念地图。看完能理解**为什么**要有自维护。
- **Ch 3–7** 拆解实现：文件系统、工具、system prompt、meta-learning、curator 五层。看完能理解**怎么做**。
- **Ch 8** 是一次完整闭环的解剖，把前面五层拼起来。
- **Ch 9–10** 设计权衡与横向对比。看完能理解**为什么是这样而不是那样**。
- **Ch 11** 给学习者一条从零到 curator 的路径。
- **Ch 12 + 附录** 参考资料与速查表。

如果只有 15 分钟读一次：Ch 1 → Ch 8 → Ch 9。这三章能让你抓住整个设计的骨架。

---

## Ch 1 · 背景 · 传统 agent 框架为何维护困难

### 1.1 什么是 "skill"

先对齐术语。本文所指的 **skill = 可复用的 agent 操作流程**，具体形态包括：

- 一段自然语言指令（"如何 X"）
- 一组配套的参考文档、模板、脚本
- 触发条件（什么时候该用）
- 有时还带 frontmatter 元数据（版本、作者、依赖工具）

在不同框架里名字不同：Cursor 叫 "rules"、LangChain 叫 "tools/prompts"、Claude 官方叫 "skills"、OpenAI 叫 "instructions"、AutoGPT 叫 "plugins"。**本质都是"给 agent 用的可复用手册"**。

### 1.2 传统模式的三个必然痛点

**痛点 A · 技能腐烂无人察觉**

半年前写的 skill 说 `pip install foo==2.1`，今天 foo 升到了 3.0 且 API 不兼容。agent 每次调用都失败，每次都靠现场判断绕过去。**没人回去改原始 skill**——因为 agent 没这个权限，用户也没这个精力主动 audit。

**痛点 B · 用户没时间 audit 提示词库**

假设你有 60 个 skill。让谁定期通读一遍并回归测试？没有这个岗位。skill 库变成"只增不减、只读不改"的坟场。

**痛点 C · 触发-维护时机错配**

发现 skill 问题的**最佳时机**是"刚用完踩了坑"——此时 agent 有完整上下文：读过 skill 全文、执行过每一步、看到过每个失败点。**但传统模式下这个时机被浪费了**——agent 报完错就下班，用户可能几周后才回来处理，此时 agent 上下文早已消散，只能从 log 里艰难重建。

### 1.3 关键洞察

把这三个痛点连起来看，会得到一个显然但被大部分框架忽视的结论：

> **Agent 是最有能力发现技能问题的角色，也是最有动机的角色**——因为下次踩同一个坑的还是它自己（或它的下一次会话）。

传统架构把 agent 当**执行工人**（只按指令干活），Hermes 把 agent 当**共同维护者**（干完活还要负责工具的健康度）。这是根本立场差别。

### 1.4 Anthropic 的 "Claude Skills" 概念

2024 年 Anthropic 发布了 "Claude Skills"（[新闻链接](https://www.anthropic.com/news/claude-skills)），核心主张：

1. **技能是可组合的**：一个 skill 可以引用另一个。
2. **技能有明确的触发条件**：写在 frontmatter 里，agent 自己判断该不该用。
3. **技能可以带附属文件**：references / templates / scripts。
4. **技能应该被版本化**：像代码一样管理。

但 Anthropic 官方实现里 skill 仍然是**用户维护**的——agent 没有直接改 skill 的权限，改动必须通过用户或 API。这一步没走完。

**Hermes Agent 把这最后一步走完了**：agent 通过 `skill_manage` 工具直接读写 skill 文件，用 git 兜底安全性，用 curator CLI 兜底防误删。这是 Hermes 相对于 Anthropic 原版最激进的一步扩展。

### 1.5 一句话总结

Hermes 的设计立场：**skill 是活的资产，agent 是它的第一维护人；用户是审核，git 是安全网**。

---

## Ch 2 · 概念地图 · Skill 在 Hermes 生态中的位置

理解自维护之前，先搞清楚 Hermes 的四种持久化机制及其分工。

### 2.1 四种时间尺度的"记忆"

| 机制 | 存储什么 | 时间尺度 | 谁写 | 谁读 |
|---|---|---|---|---|
| **Session 上下文** | 本次对话的所有消息 | 一个 session 内（几分钟到几小时） | agent + 用户 | 当前 agent |
| **Memory** | 跨 session 的稳定事实（用户偏好、环境细节） | 长期（月到年） | agent 主动 save，用户可编辑 | 每轮自动注入 system prompt |
| **Skill** | 可复用的操作流程 | 长期（月到年） | agent 通过 `skill_manage`，用户手写 | 需要时按名字加载 |
| **Session DB** | 所有历史 session 的完整对话 | 永久（SQLite 数据库） | Hermes runtime 自动记录 | agent 通过 `session_search` 检索 |

**互补而非重叠**：
- 想让 agent 每次都记住 "用户偏好紧凑输出"——写 **memory**。
- 想让 agent 复用一整套 "评审 skill 的流程"——写 **skill**。
- 想让 agent 记住 "上周三我们讨论过 X"——不用记，用 `session_search` 检索。
- 想让 agent 立即完成一个手头任务——用 **session 上下文**。

**Cronjob** 是第五种机制，本质是"定时启动的独立 session"，不是记忆机制，此处不展开。

### 2.2 Skill 与 Memory 的分工是最容易混淆的

**Memory** 是**声明性事实**（"我用 Windows，git-bash"），必须 concise。
**Skill** 是**过程性程序**（"如何评审技能"），可以很长。

一个常见错误：把过程写进 memory。**不行**——memory 每轮注入，太长会占爆上下文。所以 memory 有硬上限（默认 2.2K 字符），skill 没有上限但按需加载。

判定规则一句话：**"这个知识是不是每轮都要用？" 是 → memory；否 → skill**。

### 2.3 Profile 的作用

Hermes 支持多 profile：同一台机器可以有 `default` / `devops` / `research` 等不同的"角色档案"。每个 profile 独立拥有：

- 自己的 skill 库
- 自己的 memory
- 自己的 session DB
- 自己的 config（模型、provider、工具集）

**目的**：隔离场景。工作用 `devops`（技术类 skill、终端工具、注重安全），研究用 `research`（联网检索、arxiv、文献管理）。同一个 agent 在不同 profile 下"人格"不同。

**跨 profile 保护**：agent 默认**不能**改另一个 profile 的资产（避免 `default` session 意外污染 `devops` skill 库）。要跨 profile 改，必须显式 `cross_profile=true`，且用户有明确指令。

---

## Ch 3 · 文件系统层 · Skill 就是磁盘上的一个目录

### 3.1 目录结构

Hermes profile 数据的默认位置（Windows）：

```
C:\Users\<user>\AppData\Local\hermes\profiles\<profile>\
    skills\
        <category>\<skill-name>\      # 一个 skill = 一个目录
            SKILL.md                   # 入口文件（必需）
            references\                # 深度参考文档（按需加载）
                *.md
            templates\                 # 可复制模板
                *.md
                *.yaml
            scripts\                   # 可执行辅助脚本
                *.py
                *.sh
            assets\                    # 图片、字体等静态资源
        <another-category>\...
    memories\
        user.md                        # 用户 profile
        memory.md                      # agent 个人笔记
    sessions.db                        # SQLite 全量对话记录
    config.yaml                        # profile 级配置
```

Linux/macOS 对应 `~/.hermes/profiles/<profile>/`。

### 3.2 SKILL.md 的规范

每个 skill 目录必有一个 `SKILL.md`，格式是 **YAML frontmatter + Markdown 正文**：

```markdown
---
name: my-skill                       # 必需，全库唯一
description: |                       # 必需，一句话说明（skills_list 展示这个）
  一句话讲清做什么、何时触发、产出什么。
  避免 AI 味套话；这段是 agent 第一印象。
version: 1.0.0                       # 可选，semver
author: <name>                       # 可选
license: MIT                         # 可选
metadata:                            # 可选，Hermes 扩展元数据
  hermes:
    tags: [category, subcategory]
    related_skills: [other-skill]
---

# Skill Title

正文……
```

**关键字段解读**：

- **`name`** 是 skill 的**主键**。改名意味着切换身份；`skill_manage` 编辑现有 skill 时禁止改这个字段。
- **`description`** 是 `skills_list()` 展示给 agent 的那一行——决定 agent 会不会加载这个 skill。**这里的用词质量决定了 skill 的"被发现率"**。写得太抽象、太 AI 味，agent 判断不出该用；写得清晰有触发条件，才会被恰当调用。
- **`version`** 遵循 semver：patch = 只改文本、minor = 加能力、major = 破坏兼容。
- **`related_skills`** 可以帮助 agent 联想（例："用完 hand-off，下次 take-over 触发时会自动关联"）。

### 3.3 references / templates / scripts 的角色分工

这是新手最容易搞乱的地方。分工原则：

| 目录 | 内容 | 加载方式 | 什么时候放这里 |
|---|---|---|---|
| **SKILL.md 正文** | Overview / When to use / Workflow 主线 | 一定加载 | 每次都要读的内容 |
| **references/** | 深度参考、边缘情况、原理解释 | agent 按需 `skill_view(file_path='references/...')` | "有时候需要查"的知识 |
| **templates/** | 可以复制到用户项目里的文件模板 | agent 复制或引用 | 结构固定、需要多次实例化的文件 |
| **scripts/** | 可执行辅助脚本 | 通过 `terminal` 直接跑 | 逻辑复杂到不适合让 agent LLM 现算的部分 |
| **assets/** | 图片、二进制资源 | 引用/嵌入 | 静态资源 |

**判断题**：如果这段内容"每次用 skill 都要读"，放 SKILL.md 正文；如果"偶尔查一下"，放 references/；如果"结构化数据、机器读得懂"，放 templates/ 或 scripts/。

**为什么这么分？** 因为**上下文成本**。SKILL.md 正文每次加载都算 token；references/ 只在真需要时才加载。写 skill 的关键 discipline 之一就是"把正文压到最短，深度内容 offload 到 references"。

### 3.4 Git 兜底

整个 profile 目录**应该被 git 追踪**（用户可选，但强烈推荐）。这样：

- Agent 改 skill 后，用户可以 `git diff` 审计。
- 改坏了 `git revert` 一键回滚。
- 想同步到另一台机器，`git push` / `pull` 即可。
- 想跨用户分享 skill 库，push 到公共 repo（本仓库 `more-skills` 就是这种性质）。

**这是"agent 敢改"的底气来源**。没有 git 兜底，把写权限交给 LLM 是自杀。有了 git 兜底，最坏情况就是回滚一次。

---

## Ch 4 · 工具层 · Agent 视角的 API

Hermes 给 agent 暴露了一组精心设计的工具，让读写 skill 有明确的粒度。

### 4.1 完整工具清单

| 工具 | 作用 | 危险等级 |
|---|---|---|
| `skills_list(category=None)` | 枚举当前 profile 有哪些 skill | 无（只读） |
| `skill_view(name)` | 读 SKILL.md 全文 + 附属文件清单 | 无（只读） |
| `skill_view(name, file_path=...)` | 读附属文件（references / templates / scripts） | 无（只读） |
| `skill_manage(action='patch', ...)` | 定点改（old_string → new_string） | 低 |
| `skill_manage(action='edit', ...)` | 整份重写 SKILL.md | 中 |
| `skill_manage(action='write_file', ...)` | 增/改附属文件 | 中 |
| `skill_manage(action='remove_file', ...)` | 删附属文件 | 中 |
| `skill_manage(action='create', ...)` | 新建 skill | 中 |
| `skill_manage(action='delete', absorbed_into=..., ...)` | 删 skill | 高 |

**每个 action 都返回 diff / 影响范围**，agent 拿到确认后才继续。用户随时可以 `git diff` 检查。

### 4.2 `patch` 是首选

三个原因：

1. **改动小、诊断容易**：diff 只有几行，出问题一眼看出。
2. **不会破坏未改动部分**：edit 是整份重写，容易漏掉某些细节；patch 精确到字节。
3. **模糊匹配**：patch 支持 9 种匹配策略，允许目标文本有轻微空白/缩进差异。

典型用法：

```python
skill_manage(
    action='patch',
    name='hand-off',
    old_string='原来的一段话（需在文件里唯一）',
    new_string='新的一段话',
)
```

如果 `old_string` 在文件里出现多次，需要传 `replace_all=True` 或加更多上下文让它唯一。

### 4.3 `edit` 只用于整体重构

只有当**大部分内容都要变**时才用 edit——比如结构调整、章节顺序颠倒。日常改进用 patch。**Hermes 内置指引明文说 "major overhauls only"**。

用之前要先 `skill_view` 读全文，然后传完整新版本进去。

### 4.4 `create` 强制走 skill-creator

新建 skill 是重决策：会污染 skill 库、会占用一个全局唯一的 name。所以 Hermes 建议：

1. 先 `skill_view(name='skill-creator')` 加载**建 skill 的元 skill**。
2. 按它的方法论准备 frontmatter + 正文 + references。
3. 用 `clarify` 让用户确认 name / category / 摘要。
4. 最后调 `skill_manage(action='create', ...)`。

`skill-creator` 里有 SKILL.md 骨架模板、命名 convention、常见错误清单。

### 4.5 `delete` 强制记录去向

删 skill 需要传 `absorbed_into` 参数：

```python
skill_manage(
    action='delete',
    name='old-skill',
    absorbed_into='new-umbrella-skill',   # 内容已合并到哪里
)
# 或
skill_manage(
    action='delete',
    name='old-skill',
    absorbed_into='',                     # 空字符串 = 无归属，纯粹废弃
)
```

**为什么强制**：因为下游可能引用旧名（cronjob 里的 skill 引用、cross-reference）。记录 `absorbed_into` 后，Hermes 的重写工具可以自动更新引用。

### 4.6 Pin 保护

有些 skill 用户不想让 agent 删（例：核心工作流、私人偏好）。用户手动运行：

```bash
hermes curator pin <skill-name>
```

之后 `skill_manage(action='delete')` 会被拒绝，返回明确的错误消息指向 `hermes curator unpin`。**Pin 只挡 delete，不挡 patch/edit**——鼓励小修小补，禁止误删。

### 4.7 Cross-profile 保护

跨 profile 写的默认行为是**拒绝并警告**：

```
Cross-profile write blocked. Target belongs to profile 'default',
current session runs under 'devops'. Set cross_profile=True to override.
```

只有用户显式说"改 default profile 的某 skill"，agent 才能传 `cross_profile=True`。**这是防止多 profile 用户被静默污染的最后一道防线**。

### 4.8 工具集设计的隐含哲学

细看这套工具会发现几个反复出现的模式：

1. **粒度对应风险**：patch < edit < create < delete。危险动作走更繁琐的路径。
2. **强制上下文**：delete 强制 absorbed_into，跨 profile 强制显式 flag。
3. **返回 diff**：任何写操作都返回可审计的 diff。
4. **只读工具无门槛**：`skills_list` / `skill_view` 免费无限调，鼓励 agent 多探索。

这套设计的目标不是"让 agent 不能作恶"（LLM 本质就是概率机器，做不到），而是**让 agent 作恶的代价可回滚**。这就够了。

---

## Ch 5 · System prompt 层 · 纪律注入

工具能干活，不代表 agent 会主动干活。**LLM 的默认行为是"完成用户当前任务就下班"**，不会主动做任何"顺手改进"的事。要让 agent 承担维护义务，必须把这个义务**写进每一轮的 system prompt**。

### 5.1 每轮注入的纪律段落

Hermes runtime 在每次给 agent 发消息前，会拼装一段 system prompt，里面固定包含关于 skill 维护的几段：

**段落 A · Skills are mandatory**

```
Before replying, scan the skills below. If a skill matches or is
even partially relevant to your task, you MUST load it with
skill_view(name) and follow its instructions. Err on the side of
loading — it is always better to have context you don't need than
to miss critical steps, pitfalls, or established workflows.
```

翻译：**agent 不能装看不见现有的 skill**。哪怕觉得自己能干，也要先看 skill 库里有没有已有方法。

**段落 B · Fix on discovery**

```
If a skill has issues, fix it with skill_manage(action='patch').
```

翻译：用 skill 时发现问题**立刻修**——不要等下一次、不要写 TODO。

**段落 C · Offer to save after difficult tasks**

```
After difficult/iterative tasks, offer to save as a skill. If a
skill you loaded was missing steps, had wrong commands, or needed
pitfalls you discovered, update it before finishing.
```

翻译：任务结束时，**主动问用户**"这个流程要不要沉淀成 skill / 需不需要更新已有 skill"。这是"我为什么会主动问你要不要改进"的直接来源。

**段落 D · Skills over one-off procedures**

```
When you have discovered a new way to do something, solved a problem
that could be necessary later, save it as a skill with the skill tool.
```

翻译：解决过一次的问题，别指望下次记得——**存成 skill 才是真的记住**。

### 5.2 `skills_list()` 的自动注入

上述纪律段落之后，Hermes runtime **还会自动注入当前 profile 的完整 skill 清单**（name + description，不含正文）：

```
<available_skills>
  category-a:
    - skill-name-1: description...
    - skill-name-2: description...
  category-b:
    - skill-name-3: description...
</available_skills>
```

这段清单每轮都注入。agent 无需主动调 `skills_list()` 就能看到所有可用 skill。**代价是 skill 越多，system prompt 越长**——所以 Hermes 只在这里放摘要（30-70 字），完整内容靠 `skill_view` 按需加载。

**这就是为什么 skill 的 `description` 字段极其关键**——它决定了 agent 在只看摘要时能不能判断出"这个 skill 和我要做的事相关"。写得抽象或 AI 味重，agent 判断不出，skill 就"隐身"了。

### 5.3 为什么用 system prompt 而不是训练 / 微调

一个自然的问题：为什么不直接微调一个"懂自维护"的 LLM？答案：

1. **Hermes 支持任意模型**：Claude / GPT / DeepSeek / 本地模型 / Volcengine Ark 全都能跑。不能假设用户用的是某个特定微调版本。
2. **LLM 的"记性"不持久**：即使微调了，具体的 skill 列表、当前 profile、用户偏好也变来变去，必须每轮显式注入。
3. **可迭代**：纪律段落改一版立即生效，不用重新微调。用户觉得某条纪律烦，改 config 一秒关掉。
4. **可审计**：system prompt 是明文，用户能看到自己被"喂"了什么。微调是黑盒。

**结论**：纪律注入是当前 LLM 生态下最实际的方案。等到有一天 LLM 能"内化"纪律（比如通过 continual learning），架构会演化，但今天这就是最优解。

### 5.4 纪律的可覆盖性

**Memory 优先级高于 system prompt 默认纪律**。举例：

- 默认纪律："After difficult tasks, offer to save as a skill."
- 用户 memory：*"用户不喜欢每次都问是否要更新 skill——只在明显 bug 时才主动改。"*

结果：agent 下次跑完难任务，**不再询问**（除非发现明确 bug）。

这个机制让**用户始终能压制默认行为**。纪律不是宗教，是可调参数。

---

## Ch 6 · Meta-learning 层 · Skill 自身的自维护段

除了 system prompt 从上面注入的通用纪律，**好的 skill 会在自己内部再写一段特定的维护指引**——告诉调用它的 agent："用完我，请这样改进我。"

### 6.1 典型 meta-learning 段

以 `skill-review-cycle` 为例，SKILL.md 末尾：

```markdown
## Meta-learning

If during a review you discover a new anti-pattern or heuristic
(e.g. "always check for terminology drift on skills > 6 months old"),
update this skill's `references/priority-heuristics.md` immediately —
do not wait for the next review. Skills that do not self-maintain rot.
```

翻译：跑本 skill 过程中如果学到新启发，**立刻**写进 `priority-heuristics.md`，不要等下一次。

再看 `skill-creator` 的 meta 段（大意）：

```markdown
When helping create a new skill, if you notice the SKILL.md template
is missing a section that would have helped, patch this skill's
templates/ directory before finishing.
```

翻译：用 skill-creator 造 skill 时如果发现模板缺章节，**立刻**改模板本身。

### 6.2 为什么要分两层

一个自然疑问：既然 system prompt 已经说了"发现问题立刻改"，skill 内部再写一遍不是重复吗？

不重复，因为**颗粒度不同**：

- **System prompt 说的是普适纪律**："skill 有问题就改"——但改什么、改哪个文件、改什么颗粒度，agent 要自己判断。
- **Skill 内部说的是具体投影**："学到新启发式写进 `priority-heuristics.md` 而不是 SKILL.md 主体"——agent 不用再判断，直接执行。

类比：宪法说"公民有义务维护公共设施"（system prompt），具体条例说"看到路灯坏了打 12345 转报"（skill meta 段）。**宪法给方向，条例给动作**。

### 6.3 什么样的 skill 值得写 meta 段

不是所有 skill 都需要。以下情况值得写：

1. **Skill 本身就是 meta-skill**（关于 skill 的 skill）：skill-creator / skill-review-cycle / hermes-curator。它们本质就是维护基础设施，不写 meta 段就矛盾了。
2. **有明确的可累积的知识**：例如 skill-review-cycle 的 priority-heuristics.md 会随每次评审逐渐丰富。
3. **有已知的漂移风险**：例如某些工具的 API 会更新，SKILL.md 里可以明确说"如果发现新版本 API 变了，先更新 references/api-reference.md"。

**反例**：一个纯执行类 skill（例如"用 curl 查天气"），流程固定、无累积学习价值，就不必写 meta 段。

---

## Ch 7 · Curator 层 · 人工兜底

Agent 能读写 skill 库、能主动维护，那用户还需要什么？答案：**总有一些决策 agent 不该自作主张**。这就是 curator 层的作用。

### 7.1 Curator 是什么

Curator 是 Hermes 的一组 CLI 命令 + 一个专用 skill (`hermes-curator`)，让用户对 skill 库做**批量、全局、跨 skill** 的决策。

Agent 干的是**局部改动**（改一个 skill 内的一段话）。Curator 干的是**全局管理**（决定哪些 skill 保留、哪些废弃、哪些优先级更高）。

### 7.2 主要命令

```bash
# 保护
hermes curator pin <skill>           # 挂 pin，禁止 delete
hermes curator unpin <skill>         # 摘 pin

# 查看
hermes curator list                  # 列出所有 skill，标注 pin 状态
hermes curator show <skill>          # 看 skill 全量信息

# 批量归档
hermes curator archive <skill>       # 归档到 archive/ 目录，从 skills_list 中消失
hermes curator unarchive <skill>     # 恢复

# 禁用
hermes curator disable <skill>       # 保留文件但不加载
hermes curator enable <skill>        # 重新启用
```

**这些命令都需要用户手动跑**——agent 没有权限执行。这是 curator 层区别于 agent 层的关键：**pin/unpin/archive 是人的决策**。

### 7.3 `hermes-curator` skill 的作用

Hermes 内置了一个 `hermes-curator` skill，教 agent **如何配合 curator CLI 干活**。典型场景：

- 用户说"归档 X skill"→ agent 加载 `hermes-curator` → 按里面的规范流程执行（先 `list` 确认存在、再 `archive` 归档、最后确认 `list` 结果）。
- 用户说"X skill 我不想让你改了"→ agent 建议用户跑 `hermes curator pin X`。

**Agent 不能直接跑这些命令改 curator 状态**（因为要 elevate 权限、需要交互确认）；但 agent 能**指导用户跑**、能**根据 pin 状态调整自己的行为**（例如遇到 pinned skill 的 delete 请求时明确告诉用户"这个 pinned 了，请先 unpin"）。

### 7.4 三层保护的完整图

到这里可以把整个保护体系画完整了：

```
Layer 4  Curator CLI       (用户手动, 全局决策)
   ↑     - pin / archive / disable
   |
Layer 3  Cross-profile     (agent 层, 显式 flag 才能过)
   ↑     - 默认拒绝跨 profile 写
   |
Layer 2  skill_manage      (agent 层, 粒度对应风险)
   ↑     - patch < edit < create < delete
   |
Layer 1  Git               (仓库层, 兜底回滚)
         - git diff / revert / log
```

每一层挡不同类型的错误。git 挡"手滑改错"，skill_manage 挡"agent 判断失误"，cross-profile 挡"作用域越界"，curator 挡"重决策疏忽"。**四层加起来才够 safe**——去掉任何一层都会露出一类风险。

---

## Ch 8 · 完整闭环 · 一次 skill-review-cycle 从头到尾

前面五层是分开讲的。这一章把它们拼起来，看一次真实闭环长什么样。

### 8.1 场景

用户在 Hermes 里说："**评审 skills/take-over**"，并附带调用了 `skill-review-cycle` skill。

### 8.2 Turn 1 · 触发

**用户端可见**：只是发了句"评审 skills/take-over"。

**Runtime 幕后**：
1. Hermes 读取当前 profile 的 `skills_list()`。
2. 拼装 system prompt：
   - 通用纪律段（Ch 5.1 那四段）
   - `<available_skills>` 清单（含所有 skill 的 name + description）
   - 用户 memory + user profile
   - 本次消息内容
3. 附加 `skill-review-cycle` 的 SKILL.md **全文注入**（因为用户显式指定了这个 skill）。
4. 发给 LLM。

**Agent 收到时**：一开机就已经知道要用 skill-review-cycle，且看到了这个 skill 的完整正文（7 步工作流、prose voice 原则、meta-learning 段）。

### 8.3 Turn 2–N · 执行 Step 1-6

按 skill 里的 7 步走：

**Step 1 · Enumerate + baseline**：agent 并行调用 `find` / `git status` / `git log` / `git diff --stat` 建立基线。

**Step 2 · 写 REVIEW-<date>.md**：agent `read_file` 读全部相关文件（SKILL.md / PROTOCOL.md / DECISIONS.md / references / templates / scripts），发现问题，写报告草稿，`write_file` 落盘。

**Step 3 · Ask direction**：agent 用 `clarify` 抛 2-4 个 Key Judgment Questions，让用户 pick。**这里必须用 clarify 而不是 prose 里列选项**——skill 内部明文规定。

**Step 4 · 落地 P0**：一个 atomic commit，push。

**Step 5 · 落地 P1**：**每个 P1 一个 commit，中间 pause 让用户确认**——skill 明文反对 mega-commit。

**Step 6 · P2/P3 走 clarify**：让用户决定"继续 / P2 only / 收尾"。

**每一步 agent 都在应用**：
- system prompt 的通用纪律（"skill has issues → patch immediately"）
- skill 自身的具体指引（"P1 一个 commit"、"clarify shape 见 references/clarify-shapes.md"）

如果发现 skill 本身有问题（例如某步骤描述过时），**当场用 `skill_manage(action='patch')` 修**——不写在 review 报告里等下轮。

### 8.4 Turn 最后 · Step 7 收尾

按 skill 的 Step 7：

1. 勾完 REVIEW 报告的每一项状态（`[x]` done / `[/]` partial / `[-]` deferred）。
2. 补 DECISIONS.md 的 R-entry。
3. 提交收尾 commit + push。
4. **主动问用户**：有没有新发现要沉淀？

第 4 步就是 Ch 5.1 的 "Offer to save after difficult tasks" 段落与 skill 自身 Meta-learning 段的**同时触发**——两层驱动叠加。所以我"主动问"不是任性，是被两层设计要求。

### 8.5 完整数据流

图示：

```
┌───────────────────────────────────────────────────────────┐
│  用户："评审 skills/take-over"                                │
└──────────────────────┬────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────────────┐
│  Hermes runtime 组装 system prompt                          │
│    · 通用纪律段（Ch 5.1）                                     │
│    · <available_skills> 清单                                │
│    · memory + user profile                                 │
│    · skill-review-cycle SKILL.md 全文                        │
└──────────────────────┬────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────────────┐
│  Agent (LLM) 执行 skill 里的 7 步                            │
│    Step 1  枚举基线（并行只读工具）                              │
│    Step 2  写 REVIEW 报告（read_file × N, write_file × 1）    │
│    Step 3  clarify 3 个 Key Judgment                        │
│    Step 4  P0 → patch + commit + push                      │
│    Step 5  P1a → patch + commit + push                     │
│           P1b → patch + commit + push                      │
│    Step 6  clarify "P2/P3 怎么办"                            │
│    Step 7  收尾 commit + 主动问用户 (Ch 5.1.C + skill.Meta)    │
└──────────────────────┬────────────────────────────────────┘
                       ↓
┌───────────────────────────────────────────────────────────┐
│  Git 记录                                                   │
│    Commit 1 (P0) · SHA a...                                │
│    Commit 2 (P1a) · SHA b...                               │
│    Commit 3 (P1b) · SHA c...                               │
│    Commit 4 (收尾) · SHA d...                               │
│  一切 diff 可审计、可回滚                                       │
└───────────────────────────────────────────────────────────┘
```

**关键观察**：整个闭环里 agent **主动做的 skill 内改动是零**（评审对象是 take-over，不改 skill-review-cycle 本身）；但如果 review 过程中发现 skill-review-cycle 的某步骤描述不清，agent 会**当场 patch 那一步**——这就是 Ch 5.1.B "Fix on discovery" 的直接体现。

---

## Ch 9 · 设计权衡 · 为什么这样能 work，也在哪脆弱

### 9.1 五个能 work 的原因

**A · 上下文匹配**

发现问题的时刻 == 有充分上下文修问题的时刻。这是 Hermes 相对传统架构最本质的优势。用户不再需要"事后重建 agent 当时的想法"，因为 agent 就在现场，且被要求现场修。

**B · Git 兜底带来的心理豁免**

改坏了立刻 `git revert`。这个心理豁免让 agent **敢动手**。没有 git，就算给了 agent 写权限，它也会因为"怕改错"而保守——最后回到"只读不改"的传统模式。**Git 不是可选装饰，是设计的核心前提**。

**C · 纪律显式化**

不指望 agent "自觉"，靠 system prompt 每轮重申。这是**唯一可靠的方式**——LLM 的"记性"不是持久的，只有 context 是持久的。写在系统提示词里的东西，等于每轮都刷一遍存在感。

**D · 粒度分级对应风险**

`patch`（小改，直接干）→ `edit`（大改，看 diff 有心理成本）→ `create`（新建，先 `clarify` 确认）→ `delete`（危险，强制记录去向、pin 可保护）。**粒度对应风险**，越危险越有摩擦。这个设计让 agent 的"日常改进"零成本，"关键决策"有成本。

**E · 可关闭**

嫌某条纪律烦？一句"用户不喜欢 X"进 memory，下次不再触发。**纪律不是宗教**，是可覆盖参数。这个 escape hatch 保证了系统不会因为过度自动化让用户抓狂。

### 9.2 五个脆弱的地方

**A · Skill 越多，system prompt 越贵**

`skills_list` 每轮注入摘要，60 个 skill 就是几千 token。所以 Hermes 只在这里放 name + description，正文按需加载。**description 写得越紧凑越好**——这是 skill 作者的一个隐藏 KPI。

如果未来 skill 库涨到几百个，可能需要引入 semantic search 分层加载（`skills_list()` 先返回向量最相关的 top-20，用户/agent 显式请求才看全部）。目前的实现是"全量注入"，规模上限约几百个。

**B · Agent 可以撒谎说"改了"其实没改**

LLM 会 hallucinate。`skill_manage` 每次都返回真实的 diff，但 agent 完全可以在生成的回复里说"我改了 X"，而实际没调 tool。防御机制：

- Hermes 内置纪律明确写了 "self-report ≠ verified fact"。
- 用户可以要 agent **show diff** 或 `git log` 出示证据。
- 关键改动走 curator CLI（agent 无权跑，必须用户手动）。

但这个问题**不可完全消除**——LLM 就是概率机器。**核心策略是"降低作恶收益"**：反正 diff 可 audit、可 revert，agent 撒谎的实际影响非常有限。

**C · 并发写冲突**

两个 profile / 两个 session 并发改同一个 skill 会冲突。Hermes 目前**没有分布式锁**，靠 git 事后合并（可能触发 merge conflict）。多 agent 并行是设计的未来问题。

如果你在多机上跑 Hermes 且共享 profile via git sync，务必**pull 完再改**，避免踩上并发写。

**D · Agent 判断"值得沉淀"的标准可能过激**

有些 agent 会把每次微不足道的发现都想沉淀成 skill，导致 skill 库爆炸。防御机制：

- 关键动作（create、delete、大规模 edit）走 `clarify` 让用户 pick，避免 agent 单方面污染。
- `skill_manage(action='create')` 明文建议先加载 `skill-creator` skill，走里面的完整方法论（会强制思考"这真的值得独立成 skill 吗"）。
- Memory 可以覆盖：*"用户不喜欢过度提议新 skill——只有明显重复模式才推荐"*。

**E · 纪律 vs 用户偏好的冲突**

System prompt 说"主动问"，用户可能觉得烦。Hermes 用**memory 优先级 > system prompt 默认**来解决——把偏好写进 memory，下次自动覆盖。

**但这需要用户知道有这个机制**。不知道的用户会一直被烦到，然后放弃使用。所以 Hermes 在 UI 层有一些引导（"要不要记住这个偏好？"）。

### 9.3 一个未解决的深层问题

**技能库的"最优大小"是多少？**

- 太少（<10）：agent 无 skill 可用，退化为通用 LLM，Hermes 的价值消失。
- 太多（>200）：`skills_list` 摘要爆炸、agent 选 skill 的准确率下降、维护成本剧增。
- 甜蜜点大概在 30-80 之间（作者观察，无严格数据支持）。

如何自动检测并提示"你的 skill 库该 curate 了"？目前 Hermes 没有这个能力。这是未来可能加的一个 curator 命令：`hermes curator health` → 分析 skill 库健康度（重叠度、过时度、使用频率）。

---

## Ch 10 · 横向对比 · Hermes 在 agent 生态里的位置

| 系统 | Skill 由谁维护 | Agent 修改权限 | 版本追踪 | 用户审计成本 |
|---|---|---|---|---|
| **Hermes Agent** | Agent（用户审核关键动作） | 完整 CRUD + `patch`/`edit`/`create`/`delete` | git | 低（git diff） |
| **Claude Skills (Anthropic 原版)** | 用户 | 只读 | 无（配置托管） | 高（手动 audit） |
| **LangChain Tools** | 用户 | 只读 | 无 | 高 |
| **Cursor rules** | 用户 | 只读 | git（但改动需人工） | 中（git 可看） |
| **AutoGPT plugins** | 用户 / 插件作者 | 只读 | 无 | 高 |
| **OpenAI Custom GPT** | 用户 | 只读 | 无 | 高 |
| **Cline / Aider** | 用户 | 只读（配置存在项目内） | git | 中 |
| **Copilot Workspace** | 未公开 | 未公开 | 未知 | 未知 |

Hermes 是这个矩阵里**最激进**的——唯一让 agent 拥有完整 CRUD 权限的主流开源 agent 框架。

### 10.1 激进的代价

代价是需要**四层保护**（git + skill_manage 粒度 + cross-profile + curator）叠加。任何一层去掉都会露出一类风险。这套体系的复杂度比"只读 skill"高一个数量级。

**只读方案的隐性成本**：用户维护成本 O(N × T)（N 个 skill × T 时间）。**Hermes 方案的显性成本**：初始化学习曲线陡（要理解四层保护）+ agent 需要更长 system prompt。**长期看 Hermes 更划算**——因为用户维护成本是持续投入，Hermes 只是一次性学习。

### 10.2 各方案的合适场景

- **只读方案（LangChain / Cursor rules）** 适合：skill 数量少、变动不多、用户是资深工程师且愿意手动 audit。
- **Hermes 方案** 适合：skill 数量多、快速演化、用户希望 agent 承担维护义务。
- **完全托管方案（Custom GPT）** 适合：skill 简单、不需要精细控制、用户不想碰技术细节。

Hermes 明确瞄准"技术型用户 + 长期演化的 skill 库"这个 niche。

---

## Ch 11 · 学习路径 · 从零到 curator

如果你想真正掌握这套机制，推荐按以下顺序上手。

### 11.1 阶段 1 · 观察者（30 分钟）

**目标**：理解现有 skill 长什么样。

```bash
# 看看你的 profile 有哪些 skill
hermes skills list

# 挑一个感兴趣的，读全文
hermes skills view <skill-name>

# 看它的目录结构
tree ~/AppData/Local/hermes/profiles/<profile>/skills/<category>/<name>/
```

推荐先读三个 meta-skill：
1. `hermes-agent` — Hermes 使用大全。
2. `skill-creator` — 教你怎么造 skill。
3. `skill-review-cycle` — 教你怎么审 skill。

### 11.2 阶段 2 · 使用者（几天）

**目标**：让 agent 用现有 skill 干活，观察它如何自维护。

- 找一个 skill 相关的日常任务（例如用 `github-pr-workflow` 提 PR）。
- 让 agent 跑，全程观察它 `skill_view` 什么、`skill_manage` 改了什么。
- 收尾时看 git diff，理解每一次改动的动机。

**关键学习点**：agent 什么时候提出改 skill？改的粒度如何？改完的 diff 是否合理？

### 11.3 阶段 3 · 修改者（1-2 周）

**目标**：自己写第一个 skill。

推荐流程：
1. 加载 `skill-creator` skill：`skill_view(name='skill-creator')`。
2. 按里面的 checklist 准备 frontmatter + workflow + references。
3. 用 `skill_manage(action='create', ...)` 落盘。
4. 在几个真实任务里用它，观察 agent 触发情况。
5. 用不到的地方 → 说明 description 写得不好或触发条件模糊 → 回去改。

**关键学习点**：一个好 skill 的 description 是能被 agent 主动识别触发的；写坏了它就"隐身"了。

### 11.4 阶段 4 · 评审者（1 个月）

**目标**：跑一次 `skill-review-cycle`。

- 挑一个你写过或用了很久的 skill。
- 让 agent 用 skill-review-cycle 评审它。
- 走完全部 7 步，尤其体会 Step 3 的 clarify、Step 5 的 atomic commits、Step 7 的收尾。

**关键学习点**：好 skill 的标志是 review 后只有小 P0/P1，没有 P0 里的重大问题。如果 review 出很多 P0，说明当初设计有问题，需要反思。

### 11.5 阶段 5 · Curator（长期）

**目标**：管理整个 skill 库。

- 定期跑 `hermes curator list` 看库大小和使用频率。
- 用 `hermes curator archive` 归档不再用的 skill。
- 用 `hermes curator pin` 保护核心 skill。
- 有多个 profile 时，规划哪些 skill 属于哪个 profile。

**关键学习点**：curator 是**决策角色**，不是操作角色。核心问题是"这个 skill 值不值得留"，不是"怎么改这个 skill"。

---

## Ch 12 · 参考资料

### 12.1 官方文档

1. **[Anthropic Claude Skills](https://www.anthropic.com/news/claude-skills)** — Hermes 自维护思想的直系源头。
2. **[Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs)** — 权威参考，特别是 "Skills" / "Memory" / "Curator" 三章。
3. **`skill_view(name='hermes-agent')`** — 本地加载官方 hermes-agent skill，含配置命令、扩展指南、常见问题。

### 12.2 关键内置 skill

- **`skill-creator`** — 造 skill 的完整方法论。
- **`skill-review-cycle`** — 审 skill 的 7 步流程（本文档诞生的起点）。
- **`hermes-curator`** — 与 curator CLI 配合的规范流程。
- **`hermes-agent`** — Hermes 使用大全。

### 12.3 相关概念阅读

- **ADR (Architecture Decision Records)** — Hermes skill 的 DECISIONS.md 文件遵循这个模式。参见 [ADR GitHub](https://adr.github.io/) 或本仓库 `skills/take-over/references/adr-and-decisions.md`。
- **12-Factor App** — Hermes 的"配置显式化、纪律注入"思想与其"Config in env vars"哲学同源。
- **NixOS 声明式配置** — Hermes 的 skill 目录是"声明式 agent 配置"的一种实现，思想上有共通之处。

---

## 附录 A · 速查表

### A.1 用户端 CLI

```bash
# 基础
hermes                                    # 启动交互
hermes tools                              # 看可用工具集
hermes config show                        # 看当前配置
hermes config set <key> <value>           # 改配置

# Skill
hermes skills list                        # 列所有 skill
hermes skills view <name>                 # 看 skill 全文
hermes skills view <name> <file>          # 看附属文件

# Curator
hermes curator list                       # 列 skill 及 pin 状态
hermes curator pin <name>                 # 挂 pin
hermes curator unpin <name>               # 摘 pin
hermes curator archive <name>             # 归档
hermes curator unarchive <name>           # 恢复
hermes curator disable <name>             # 禁用
hermes curator enable <name>              # 启用

# Profile
hermes profile list                       # 列所有 profile
hermes profile switch <name>              # 切换 profile
hermes profile create <name>              # 新建 profile
```

### A.2 Agent 端工具

| 场景 | 工具调用 |
|---|---|
| 列 skill | `skills_list()` 或 `skills_list(category='...')` |
| 读 skill 全文 | `skill_view(name='...')` |
| 读附属文件 | `skill_view(name='...', file_path='references/...')` |
| 定点改 | `skill_manage(action='patch', name, old_string, new_string)` |
| 整份重写 | `skill_manage(action='edit', name, content)` |
| 新建 skill | `skill_manage(action='create', name, content, category='...')` |
| 删 skill（合并去处） | `skill_manage(action='delete', name, absorbed_into='umbrella')` |
| 删 skill（纯废弃） | `skill_manage(action='delete', name, absorbed_into='')` |
| 增/改附属文件 | `skill_manage(action='write_file', name, file_path, file_content)` |
| 删附属文件 | `skill_manage(action='remove_file', name, file_path)` |

### A.3 判断题速查

| 场景 | 存哪 |
|---|---|
| "用户喜欢用 pnpm 而不是 npm" | Memory |
| "怎么用 pnpm 部署到 Vercel" | Skill |
| "上周三提过的 X bug" | Session（用 session_search 检索，不用记） |
| "本次任务的第 3 步做完了" | Todo（当前 session 内） |
| "我用 Windows + git-bash" | User memory |
| "如何评审 skill" | Skill |

### A.4 常见误区

| 误区 | 正解 |
|---|---|
| 把 workflow 写进 memory | 应该写进 skill；memory 只放**声明性事实**。 |
| Description 写"全能助手" | 应该写"何时用、做什么、产出什么"，具体可触发。 |
| 所有改动都用 `edit` | Prefer `patch`，改小、diff 短、诊断易。 |
| Delete 时不填 `absorbed_into` | Hermes 会警告；填空字符串表示"纯废弃"，填 skill 名表示"内容已并入 X"。 |
| 期望 agent "记住"某次改动 | Agent 无跨 session 记忆；要么写 memory，要么在 skill 或 session log 里可检索。 |
| 一次 mega-commit 改多个 skill | 违反 review-cycle 的 atomic commit 纪律；反例：想 revert 一部分就得 revert 全部。 |
| 造 skill 不加 `description` | `skills_list()` 里看不到，等于隐身。 |

---

## 附录 B · Glossary

- **Agent-owned toolchain** — Agent 拥有 skill 库读写权限的架构范式。Hermes 是这个范式的代表实现。
- **Skill** — 一个可复用的 agent 操作流程，磁盘上的一个目录，含 SKILL.md 主文件 + 可选附属文件。
- **Meta-skill** — 关于 skill 的 skill，例如 skill-creator / skill-review-cycle。
- **Frontmatter** — SKILL.md 顶部的 YAML 元数据块，含 name / description / version 等字段。
- **Memory** — 跨 session 的稳定事实，每轮注入 system prompt。
- **Profile** — 一组隔离的 skill 库 + memory + session DB + config，对应一个"角色档案"。
- **Curator** — 管理 skill 库全局状态的 CLI + skill，做 pin/archive/disable 等重决策。
- **Pin** — Curator 的一种保护标记，被 pin 的 skill 禁止 delete（但仍可 patch/edit）。
- **ADR (Architecture Decision Record)** — 结构化的决策日志，Hermes 部分 skill（如 take-over）的 DECISIONS.md 遵循这个模式。
- **Atomic commit** — 一个 commit 只做一件事、可独立 revert。skill-review-cycle 强制要求。
- **Meta-learning** — Skill 内部的一段自维护指引，告诉调用它的 agent "用完后如何改进我"。
- **Fix-on-discovery** — 系统提示词纪律：发现 skill 有问题当场修，不等下次。
- **Offer-to-save** — 系统提示词纪律：难任务收尾时主动问用户"要不要沉淀成 skill"。
- **Description-as-KPI** — Skill 作者的一个隐藏指标：description 写得越紧凑、越有触发线索，skill 越容易被 agent 主动加载。

---

*文档终。总长约 40KB。本文档诞生于 2026-07-20 一次 `skill-review-cycle` 评审 `skills/take-over` 的对话中，由用户"想学习 agent 自维护"的问题触发，Hermes Agent (ark-code-latest) 扩展写成。可自由传阅、翻译、二次创作。若发现内容过时或有误，欢迎按本文 Ch 11 阶段 3 的方法自行 patch。*

