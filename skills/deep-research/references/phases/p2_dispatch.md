# Phase 2: 子任务分发与抓取 (Dispatch & Investigate)

本阶段指导主智能体（Lead Agent）将拆解后的子任务分发给专门的子代理进行网络检索与文献抽取，或在单体降级模式下顺序执行。

---

## 1. 双轨执行机制 (Execution Modes)

### 模式 A：子代理模式 (With Subagents - 推荐)
1. **并发分发**：将 Group A 的独立子任务同时分发给 `research` 子代理进行网络搜索，最多并发 3 个任务。
2. **加载专有 Prompt**：分发时为子代理装载 [subagent_prompt.md](../subagent_prompt.md) 作为其系统提示词。
3. **前置依赖等待**：Group A 执行完毕并写回 notes 后，再将依赖于前置结论的 Group B 任务分发出去（Group B 子代理可读取 Group A 的 notes 作为背景输入）。

### 模式 B：单体降级模式 (Degraded Mode - 无子代理时)
- 主代理（Lead Agent）亲自扮演各个子任务的“领域专家”，顺序执行网络搜索。
- **上下文防护**：每完成一个子任务，必须将该任务对应的原始网页大文本搜索结果从 Lead Agent 的历史会话中清理丢弃，仅在 `findings/task-*.md` 中保留提炼后的 notes，以控制主代理的 Context 占用。

---

## 2. 信源治理标记规范 (Source Governance)
无论是子代理还是主代理，在收集信源时必须对每一行数据标注以下元数据属性，格式参见 [research_notes_format.md](../research_notes_format.md)：
1. **信源可访问性分类 (Accessibility)**：
   - `public`: 公开源，任何人无需注册/付费即可获取（如新闻网站、学术论文、WHOIS公开字段等）。
   - `semi-public`: 半公开源，需要注册或受限访问（如 LinkedIn 个人主页、Gartner 免费预览等）。
   - `exclusive-user-provided`: 用户专属授权源，仅在第三方竞争对手调研中**鼓励使用**（如用户提供的 Crunchbase Pro 导出数据、付费 API 接口）。
   - `private-user-owned`: 用户自有私有源。**严禁在自身调研中使用**，防范循环校验（即严禁通过访问用户的私有账号来发现用户本来就已知的企业内部数据）。
2. **信源类型标签 (Source Type)**：
   - `official` (官方源) / `academic` (学术源) / `secondary-industry` (行业分析源) / `journalism` (新闻源) / `community` (社群源) / `other` (其他源)。
3. **时效性戳记 (As Of)**：
   - 必须包含信源发布时间（格式为 YYYY-MM-DD）。
4. **权威度评分 (Authority)**：
   - 对信源进行 1 至 10 分主观打分。

---

## 3. 信息黑箱与非公开实体处理
如果调研对象无任何公开网络足迹（如虚设子公司、小众实体）：
- 严禁调用用户的私有凭证去补充公开调研数据。
- 必须诚实记录对 WHOIS、工商登记、主流媒体的检索失败尝试。
- 在 `findings/` 中记录为：`UNABLE TO VERIFY ENTITY EXISTENCE`（无法从公开外部视角证实实体存在），置信度标为 `N/A`。

---

## 4. 严格的信息密度控制 (Token Budget)
为了防范大文本撑爆上下文，对 `findings/task-*.md` 强制限制：
- **Findings (核心发现)**：最多 10 条事实，每条事实必须是**单句事实陈述**，并附带引用文献编号。
- **Deep Read Notes (深度文献笔记)**：仅对 DEEP 类型任务，最多阅读 2-3 篇全文，且针对每篇文献的笔记**严格控制在 4 行以内**。

---

## 5. 阶段归档与看板更新
当所有子任务的笔记汇总写回至 `findings/` 目录下后，Lead Agent 在看板 `kanban/KANBAN.md` 中标记所有子任务为已完成，并更新阶段进度至 P3。

*注：本阶段不需要触发 Git 自动提交。*

