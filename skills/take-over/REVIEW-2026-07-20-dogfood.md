# take-over Skill — Dogfood Report 2026-07-20

> **Type:** Original one-shot dogfood report captured immediately after take-over's first live use on this repo.
> **Relationship to `REVIEW-2026-07-20.md`:** This is the raw findings that motivated the R24–R31 batch in `DECISIONS.md` (2026-07-20, v1.4.0). The `REVIEW-2026-07-20.md` file next to it is a separate, later `skill-review-cycle` pass covering the state *after* v1.4.0 landed. Read this file for the "why" of R24–R31; read the sibling REVIEW for the "what remains".
> **Preserved as-is** on 2026-07-20 (originally filed as `调用记录-20260720.md`, renamed on commit to make its role explicit). Chinese original retained; not translated.

---

## Take-Over 本次调用回顾

### 一句话结论
**基本符合预期**。核心链路（bootstrap → list-scopes → init → yield）跑通了，无失败、无污染。但过程中暴露了 **7 个真实可改进点**，其中 2 个属于文档缺陷，3 个属于流程设计粗糙，2 个属于跨技能协作断层。

---

### 本次实际执行链路

| 步骤 | 动作 | 结果 |
|---|---|---|
| Bootstrap | `command -v uv && git` + `list-scopes` | ✅ 0 scopes |
| 分支决策 | 无历史 + 无 clarify 工具 → 编号列表回退 → yield | ✅ 按 skill 文本执行 |
| 用户选 1 | `reconcile.py init` | ✅ 4 个模板文件生成 |
| 收尾 | 报告 "Initialized empty session"，退出 take-over | ✅ 按 skill 明文（"Exit the take-over flow and greet the user"） |

Steps 1–6 全部跳过（skill 明文规定 init 分支不进后续步骤）。因此本次真正被"测试"的只是 Step 0。

---

### 不足之处（按严重度排序）

#### 🔴 严重：**Frontmatter 枚举知识没有随 skill 传递**

`init` 用 template 播种了 4 个文件，template 里 `status: in-progress`。但整个 take-over `SKILL.md` **从未告诉过 agent** `status` 字段的合法取值是 `['archived', 'blocked', 'in-progress', 'phase-complete']`。

后果：hand-off 阶段我把 `status` 改成 `complete`（凭常识猜的），`validate` 才报错。这是**必然会踩的坑**，因为 take-over 是每个新会话都要跑的第一个技能。

**建议**：init 后的 greeting 消息里附一句 "frontmatter status enum: …"，或者把它写进 template 的注释头，或者写进 `references/` 里一个 `frontmatter-fields.md`。

#### 🔴 严重：**Windows 路径 shell 语法陷阱不在文档里**

Skill 里 `uv run <SKILL_DIR>/scripts/reconcile.py …` 的示例用的是 Unix 风格路径。在 Windows msys/git-bash 下，把 `/c/Users/...` 传给 `uv run` **失败**（"系统找不到指定的路径"），必须切成 `C:\Users\...`。

我第一次调用就踩了这个（虽然是 hand-off 阶段踩的，但 take-over 的调用示例同样有风险）。

**建议**：skill 里加一行 Windows 备注："Windows/msys: pass native `C:\...` paths to `uv run`, not `/c/...`."

#### 🟡 中等：**"无历史但用户想工作" 的正常路径过度啰嗦**

用户在这次会话里**刚把技能复制到 `skills/make-soul` 并明确要重构**。这时 `list-scopes` = 0 是**必然的**——因为文件夹是空的、还没有 handoff 状态。skill 却弹出 3 选 1 让我问："初始化在这里 / 别处 / 退出？"

这是给"用户误触"设计的兜底，但对 90% 的正常情况来说是多余的提问。**用户既然明确调用了 take-over、又刚创建了工作目录，"在这里 init" 就是唯一合理选项**。

**建议**：可以增加一个启发式——如果 pwd 里没有 handoff 文档、但 pwd 里有非空的非 handoff 文件（说明用户在这里"做过东西"），默认在 pwd init，只发一次确认；如果 pwd 完全是空的，才三选一。

#### 🟡 中等：**init 后不引导 seed 内容**

Init 后 `context.md` 里是 `Brief overview: ` 空白占位，`task.md` 里是 `Define your task list here`。skill 说 "greet the user" 然后结束。

但**用户刚刚才明确说要"重构 make-soul"**——这个信息完全有能力被立刻写进 `context.md#Project Description` 和 `task.md`，让第一次 hand-off 有实际内容。我这次是靠自己主动做的（读文件 → 出评估 → 写 context/task），如果换一个不那么主动的 agent，第一次 hand-off出来的可能就是空模板。

**建议**：`Step 0 · Init 分支`补一步"Initial context seeding"——用户刚刚说的那句话（触发 take-over 的那条 user message）本身就是最好的 seed 材料，skill 应该明确说"init 之后，把用户当前的意图/目标写入 `context.md#Project Description` 和 `task.md#Now` 的第一条，再 greet"。

#### 🟡 中等：**clarify 回退协议的"编号列表 + yield" 定义不够严格**

skill 明文说：
> 必须将选项以 Markdown 编号列表的形式输出给用户，并立即中止当前轮次的执行（不继续生成文本、不调用其他工具），让出控制权 (Yield Turn) 以等待用户文本回复编号。

这条规则本身写得挺好，但实操里有 3 个歧义：
1. **能不能在编号前后加解释性文字？** 我这次加了一段说明（"当前工作区…没有找到"）。skill 没说清"不继续生成文本"是指编号列表之后不能生成，还是完全不能生成。
2. **回复"1"之后 agent 是否应该二次确认？** 用户说 1 = 在当前 scope init。我直接跑了 init，没再确认路径。这在别的分支（比如 hard conflict 的 "Trust Handoff Docs / Trust Git Reality"）可能就该二次确认。
3. **回退触发条件不清晰**。skill 说"如果您的运行环境中未注册此类结构化提问工具"——但 agent 怎么"知道"自己有没有注册？现在只能靠工具目录里搜不到 `clarify` 就默认没有。

**建议**：把回退规则单独拎一节，明确 "编号列表前可以有 ≤N 行说明性上下文；编号列表后必须直接 stop，不得再有文字/工具调用；用户回复合法编号后无需二次确认，直接执行；非合法回复才回到 clarify。"

#### 🟢 轻微：**"list-scopes 找不到 = 是否走 take-over" 的判定太模糊**

skill 说：
> - 如果用户明确要求恢复工作 → clarify
> - 如果用户初始 prompt 是**正常的、无关的**指令 → 静默退出

问题：**"正常的、无关的"这个判断由谁来做、依据什么？** 本次会话里用户是显式发出 `take-over` 骨架来触发这个技能的（`[IMPORTANT: The user has invoked the "take-over" skill…]`），意图非常明确。但如果换一种触发方式（比如某个 hook 自动在每个新会话开头运行 take-over），初始 prompt 可能就是"帮我改个 bug"这种毫无历史 handoff 意图的话——此时 agent 到底应不应该静默退出？skill 只给了原则，没给判据。

**建议**：显式条件——"如果本轮 user message 包含 `继续` / `接着` / `continue` / `handoff` / `take-over` 这类关键词，或存在 `[IMPORTANT: user invoked take-over]` marker，则视为显式请求；否则视为无关。"

#### 🟢 轻微：**跨技能协作断层：take-over 不"预告" hand-off**

Init 完成后的 greeting 只说 "Initialized empty session"，然后就没了。用户完全不知道**这次 init 意味着以后可以用 hand-off 保存进度**、**hand-off 的触发词是什么**。这是两个独立技能被硬拆之后的副作用。

**建议**：init 分支的 greeting 里加一句 "Progress will be saved next time you say `先到这` / `handoff` — that triggers the companion `hand-off` skill." 让协议的双向性对用户可见。

---

### 什么是符合预期的

为公平起见也列一下：

- ✅ `list-scopes` 输出结构清晰、JSON 可解析
- ✅ `init` 幂等且明确（初始化了 4 个文件，返回 `initialized` 列表）
- ✅ "无 clarify 工具就编号列表 yield" 的回退协议**存在**（很多 skill 根本没写这段），执行效果 OK
- ✅ Anthropic Skill 式 frontmatter 和 Hermes 扩展 metadata 并存，兼容性好
- ✅ `PROTOCOL.md` / `DECISIONS.md` 分离得干净，SKILL.md 只放"怎么用"，参考细节外置

---

### 优先级建议（如果你要改 take-over）

| # | 问题 | 改动 | 收益 |
|---|---|---|---|
| P0 | Frontmatter 枚举知识不传 | 加一个 `references/frontmatter-fields.md`，init 后 greeting 里带一句 | 消除必踩坑 |
| P0 | Windows 路径 | SKILL.md 里加 1 行备注 | 消除 shell 语法陷阱 |
| P1 | Init 分支不 seed 内容 | Step 0 里追加 "Initial context seeding" 半步 | 让首次 hand-off 有实际内容 |
| P1 | clarify 回退协议模糊 | 单独一节讲清 3 个歧义 | 让不同 agent 行为一致 |
| P2 | "无历史但要工作" 三选一啰嗦 | 加 pwd-非空启发式 | 减一次不必要提问 |
| P2 | "是否走 take-over" 判据 | 显式关键词列表 | 减少 agent 幻觉 |
| P3 | 跨技能协作预告 | greeting 加一句 hand-off 提示 | 用户能理解协议闭环 |

真正的"缺陷"其实只有 P0 那两个——其余更多是"够用但可以更好"。整体而言 take-over 是我这半年用过的、**协议感最强**的 skill 之一（scope/writer/session_id/atomic-write/lock/health analyzer 全部在场），本次踩的坑基本都是**边缘案例**，不是核心链路问题。