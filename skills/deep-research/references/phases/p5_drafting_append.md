# Phase 5: 分章节流式追加写作与恢复 (Loop-Append & Checkpoint Resume)

本阶段指导智能体如何采用分章节流式追加方式写入超长调研报告，并在中间截断时自动恢复续写。

---

## 1. 写作大纲拆分与看板登记 (P4 衔接)
在大纲设计阶段（P4），Lead Agent 必须将所有的报告章节标题，登记在 `kanban/KANBAN.md` 的 `## 4. 报告写作进度` 章节中：
```markdown
## 4. 报告写作进度
- **已完成章节**:
  (暂无)
- **待完成章节**:
  - [ ] Executive Summary
  - [ ] 1. 政策文件梳理与准入要求
  - [ ] 2. 半导体关键材料供需链冲击
  - [ ] 3. 替代材料技术与成熟度评估
  - [ ] 4. 供应链风控应对建议
```

---

## 2. 分章节流式生成与追加循环 (Loop-Append)
针对 `待完成章节` 列表中的每一个项目，顺序执行以下操作：

### 2.1 上下文空间清理 (Context Optimization)
- **释放记忆**：**禁止**将前述章节的详细文本内容一直堆积在当前会话的上下文记忆中。
- **加载项控制**：每次只载入“大纲框架 + 当前章节特定的任务 findings 原始笔记 + 全局引用注册表”。
- **目标**：保证 LLM 的单次响应专注于编写当前章节，防止触发最大输出 Token 限制。

### 2.2 章节撰写与格式要求
- 严格标记引用引文 `[n]`。
- 图像嵌入：使用 Markdown 标准格式 `!["[极其详尽的 alt 趋势解析数据，供 LLM 理解该图片]"](https://original-url.png "标题")` 进行嵌入。
- 图表回落：若回落为内联 Mermaid，必须严格执行防错指南（文本一律用双引号包裹）。
- 章节字数控制：单章控制在 400-800 字。

### 2.3 追加写入与看板更新
1. 将当前生成的章节内容，使用文件**追加写入**（`Append`）合并到 `report.md` 尾端。
2. 修改 `kanban/KANBAN.md`：将当前章节移至 `已完成章节` 区域并标记为 `[x]`。
3. **不要进行单章 Git 提交**，仅在内存和 KANBAN.md 中保持标记即可。
4. 输出单章节状态日志：`[P5 drafting] section {index}/{total}: [SectionName] complete.`

---

## 3. 中断与断点恢复机制 (Checkpoint Resume)
如果程序在生成 Section 3 时由于网络或 token 耗尽崩溃退出：
1. **重新载入**：当技能再次启动时，Lead Agent 自动读取 `kanban/KANBAN.md`。
2. **断点比对**：
   - 检查 `已完成章节` 列表。
   - 检查 `report.md` 的内容是否完整到已完成章节的末尾。
3. **断点续写**：
   - 重新构建上下文：清理前两个章节的展开会话，直接定位到 `待完成章节` 里的第一项。
   - 发起续写请求，继续向 `report.md` 尾部追加。

---

## 4. 报告初稿完工与 Git 自动提交
当所有待完成章节全部拼接完毕，并追加合并了 `## 参考文献` 之后：
1. 更新 `kanban/KANBAN.md` 看板，标记阶段五已完成。
2. 在项目根目录下执行自动提交：
   ```powershell
   git add .
   git commit -m "stage: draft-report-written"
   ```
   *如 Git 不可用，打印日志警示，直接跳过。*

---

## 5. 进度汇报格式
`[P5 complete] Segmented draft report completed and merged. Git Stage: draft-report-written.`
