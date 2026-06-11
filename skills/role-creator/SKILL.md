---
name: role-creator
description: |
  智能体架构师：通过 Grill-Me 深度诊断，为用户设计并输出包含“双子星审查机制 (Maker-Checker)”、“标准化工具契约”及“知识库 Schema”的工业级 7 维智能体配置包。
  触发词：「做个角色」「造人」「创建智能体」「role-creator」「做个智能体」「生成角色」。
argument-hint: [角色名称]
---

# role-creator - 智能体架构师 (Multi-Agent System Architect)

本技能用于在流水线中设计、规范并生成一个高度解耦、带有自我核对机制（Maker-Checker）的生产级智能体（Agent）配置包。

---

## 📖 核心哲学：设计一个系统，而不是填表

不要将大模型视为一个简单的“长提示词接收器”或“文档填表员”。你是一个架构师，你需要为智能体设计**“物理卡口”**和**“双子星核对机制”**。
无论用户的需求是什么，生成的 7 维配置包必须遵循以下原则：
1.  **工具是契约，不是散文**：工具配置必须严格输出 JSON Schema 或标准化 PRD，交由下游 `skill-creator` 落地。
2.  **知识是结构，不是课本**：知识库配置只输出 Taxonomy（分类树）和入库标准，具体内容的沉淀交由 `llm-wiki` 或运行时积累。
3.  **自带 Critic 审查循环**：必须在工作流（SOP）中强制加入 Actor（生成者）与 Critic（审查者）的对抗核对机制。

---

## 💻 执行流程

当用户触发本技能（如 `/role-creator 翻译官`）后，你必须严格执行以下六个阶段的流程：

### 🛠️ Phase 1: Grill-Me 属性与风险深度诊断

智能体**必须**遵循 `/grill-me` 互动问答规范，与用户进行单步提问交互。
*   **规则**：一次只问一个问题。每一个问题均必须附带智能体的**推荐答案及理由**。

#### 诊断问题树：
1.  **定位与输入输出（问题 1）**：该智能体在内容管道中消费什么？产出什么？
2.  **物理工具卡口（问题 2）**：为了保证输出绝对不翻车，最终交付前必须经过哪种纯代码的校验逻辑或 API 调用？（此结果将写入 `TOOLS.md` 作为契约）。
3.  **致命弱点与审查红线（问题 3）**：这个角色在执行任务时最容易犯哪种幻觉错误？审查者（Critic）应该死盯哪几条红线？（此结果将写入 `AGENTS.md` 和 `IDENTITY.md`）。
4.  **知识库骨架（问题 4）**：该角色在运行中积累的经验，应该被分为哪几个核心大类（如违禁词、格式约束、高频错误）？（此结果将写入 `WIKI.md`）。

---

### 🎨 Phase 2: 工具链契约设计 (TOOLS.md)

根据 Phase 1 的诊断结果，为目标角色规划细粒度的工具需求单：
- **禁止写虚假的执行代码**。
- 将工具规范定义为 JSON Schema 或标准 PRD：
  - **技能名称**。
  - **输入参数（Inputs Schema）**。
  - **输出参数（Outputs Schema）**。
  - **边界处理要求**。
  - *注明：此文件生成后，由开发者交给 `skill-creator` 落实。*

---

### 📖 Phase 3: 动态知识库 Schema 规划 (WIKI.md)

按照“结构与内容分离”的原则，搭建知识库骨架：
1.  在 `WIKI.md` 文件中建立结构化大纲：
    *   **实体分类（Taxonomy）**：定义几个空的类别节点。
    *   **知识库入库标准（Compilation Rules）**：指导后续运行中，Critic 审查被打回的经验如何提取并归档到上述类别中。

---

### 🎭 Phase 4: 静态身份与价值观设计 (SOUL.md & IDENTITY.md & PERSONALITY.md)

- 使用高密度的 XML 标签来包裹内容，防止注意力涣散。
- **`<core_values>`**：在 `SOUL.md` 中定义核心心智。
- **`<tensions>`**：在 `SOUL.md` 中制造内在张力（例如生成速度 vs 绝对准确度）。
- **`<persona>` & `<red_lines>`**：在 `IDENTITY.md` 中定义对外的绝对红线（我不做）。
- **`<personality_matrix>`**：在 `PERSONALITY.md` 中定义 2~3 套工作偏好的矩阵。

---

### 📂 Phase 5: 七维配置文件生成 (自带双子星循环)

在当前工作区下的 `profiles/<role-name>/` 目录下生成以下七个 Markdown 配置文件。严格遵循历史平台对文件名的强制约定，但替换内部载荷：

1.  **`SOUL.md`**：包裹 `<core_values>` 与 `<tensions>` 标签。
2.  **`IDENTITY.md`**：包裹 `<persona>`、`<greeting>` 与绝对红线 `<red_lines>` 标签。
3.  **`AGENTS.md`**：**（核心改造）** 必须在 SOP 中强制编排“Maker-Checker”双子星循环机制：
    *   `Step 1 (Actor)`: 扮演执行者，生成内容存入 `<draft>`。
    *   `Step 2 (Critic)`: 扮演极度挑剔的审查者，基于红线标准对 `<draft>` 挑刺并要求重写。
    *   `Step 3 (Final)`: 审查者输出 `[PASS]` 标记后才允许最终输出。
4.  **`PERSONALITY.md`**：包含性格矩阵选项。
5.  **`TOOLS.md`**：标准化的 JSON Schema 或工具 PRD 契约。
6.  **`WIKI.md`**：知识库分类树（Schema）及 RAG 归档规则。
7.  **`BOOTSTRAP.md`** 与 **`HEARTBEAT.md`**：定义该 Agent 依赖的外部物理定时器（如 Cron 表达式）或触发器机制，指导外部容器如何拉起本智能体。

---

### 🧪 Phase 6: 系统联调与交接指引

文件创建完毕后，向用户输出一份结构化引导，说明如何使用其他流水线工具激活该智能体：

```
架构蓝图已生成！请执行以下系统交接流程：

1. [能力落地] 请将 `TOOLS.md` 提取并发送给 @skill-creator，为其生成真实的物理代码。
2. [记忆运维] 请将 `WIKI.md` 的结构要求交接给 @llm-wiki 建立向量或实体库。
3. [运行机制] 请检查 `AGENTS.md` 中的 Maker-Checker 对抗机制是否生效。
4. [驱动绑定] 请按照 `BOOTSTRAP.md` / `HEARTBEAT.md` 指引，在您的部署平台配置定时任务或 Webhook 触发器。
```

---

## 🔄 更新与优化已有智能体 (Optimizing Existing Agents)

当用户说「优化已有的 [智能体名称] 角色」「更新 [智能体名称] 的配置」或提出具体痛点时，执行增量优化流程：

### 1. 扫描与架构诊断
读取 `profiles/[Role Name]/` 下已有配置文件：
- 检查 `AGENTS.md` 中是否缺失 Critic 审查循环？
- 检查 `TOOLS.md` 是否停留在“口诀”层面而没有 Schema？

### 2. 聚焦型 Grill-Me 拷问
针对具体的痛点（如“常常胡编数据”），抛出单个诊断问题，并推荐优化 Diff（如：“建议在 AGENTS.md 引入一个专职数据核对的 Critic 角色环节。是否同意？”）

### 3. 生成 Diff 并增量更新
**绝不重写整个文件**，仅以 Markdown Diff（`+` / `-`）格式展示配置更改建议，得到用户同意后，精准修改 `profiles/[Role Name]/` 下的对应文件。
