# Phase 6 & 7: 交叉校验、纠错与最终发布 (Review & Finalization)

本阶段指导智能体执行事实合理性检验、大纲与引文对账、Mermaid 及多媒体最终审计，以及项目版本封版归档。

---

## 1. 阶段六：单智能体对立观点审查 (Counter-Review)
彻底移除繁杂的多 Agent 虚构评审团队，收敛为主 Agent 单体（或 `self` 子代理）的自我对立审查：
1. **反方立场审查**：对报告的主要论断发起相反观点的合理性质疑，寻找可能存在偏见的证据点。
2. **核心漏洞排查**：
   - 找出仅依赖单一信源的高危断言，补强论据或调低置信度。
   - 排查过期的信源（如 3 年前的政策或 6 个月前的快速变化新闻）。
3. **编写核心争议章节**：在报告尾部追加：
   ```markdown
   ## 核心争议与不同解释 / Key Controversies
   - **争议 1:** [主张 A 与反向证据 B 对比] [n][m]
   ```

---

## 2. 阶段七：对账与格式校验 (Verify & Polish)
1. **引文编号核对**：检查正文引文 `[n]` 与参考文献列表是否完全匹配。
2. **多媒体与链接核对**：
   - 验证正文中所有的 Markdown 图片 `!["alt"](url "title")` 格式是否规范。
   - 审计 `alt` 文本是否足够详尽（要求概括出核心数据以对 LLM 友好）。
3. **Mermaid 语法复查**：
   - 仔细复核所有 Mermaid 代码块，必须遵循防错规范（节点文本使用双引号包裹，禁用复杂 HTML 标签，节点 ID 禁用中文和特殊符号）。

---

## 3. 看板结项与 README 汇总
1. **更新 README**：主 Agent 将调研的核心结论、信源分布及最终结论摘要更新至项目根目录的 `README.md` 与 `README_zh-CN.md`。
2. **状态标记**：将 `kanban/KANBAN.md` 中的状态更新为 `COMPLETED`。

---

## 4. 最终封版 Git 自动提交 (Git Archive Commit)
检查本地环境是否存在 Git，若可用，在项目根目录下执行自动提交：
```powershell
git add .
git commit -m "stage: report-finalized"
```
*如果 Git 命令执行失败，打印日志并警告，跳过该步。*

---

## 5. 进度汇报格式
`[P7 complete] Verification passed. README updated. Git Stage: report-finalized. Project status: COMPLETED.`
