# Skill Creator (元技能说明文档)

`skill-creator` 是 Antigravity 智能体框架中的**元技能**（Meta-Skill），用于自动化创建、测试、迭代、评估和优化其他 Agent 技能。它将手动编写技能行为的过程转变为可工程化、可度量且具备自我迭代能力的开发生命周期。

---

## 🛠️ 核心能力

1. **意图捕获与访谈引导**：引导 Agent 提取用户真实意图、设计面向任务的 Prompt 提示词，并定义具体交付指标。
2. **迭代评估**：自动运行对比测试（使用技能 vs 基础基线），以定性和定量的方式全面评估技能改动。
3. **人机协同评审**：生成基于 Web 或静态网页的评审看板（`generate_review.py`），直观对比输出数据、断言通过率和时间开销。
4. **触发描述优化**：通过自动反馈闭环（`run_loop.py`）对 SKILL.md 中的描述进行多轮演进，有效解决 Agent 的“漏触发”痛点。
5. **设计规范静态 Lint**：在技能打包前，对环境检查规范、内存管理以及输出指引模式进行静态分析校验。

---

## 📐 核心设计模式 (Phase 2+)

本技能在设计和校验流程中强制推广以下三种关键架构模式：

### 1. 渐进式探索 (Progressive Discovery / Pre-flight Checks)
避免在技能脚本中硬编码复杂的环境探测脚本，提倡“LLM 充当主驾驶”的自适应核查：
1. **认知停顿 (Cognitive Pause)**：在执行任何命令前，以普通文本规划核查步骤（例如 `Plan: 1. Identify OS. 2. Verify dependencies.`），避免过拟合特定推理标签。
2. **自适应环境试探 (Adaptive Probing)**：优先执行原生轻量命令（`ver`、`uname -a` 或 `$PSVersionTable`）快速确立当前环境坐标系。
3. **按需定位验证 (Contextual Resolution)**：在确立环境后，动态使用对应平台原生命令（`which`、`where` 或 `Get-Command`）寻找特定工具或验证环境变量。

### 2. 差异化指引密度 (Differential Guidance Density)
脚本将下一步的行动决策指引直接输出至 `sys.stderr` 以及输出 JSON 中的 `"guidance"` 字段：
- **Happy Path (成功路径)**：指引保持极简（控制在 1 行以内，例如 `[AGENT GUIDANCE] SUCCESS. Next: parse result.json.`），消除认知噪音。
- **Error/Degradation Path (错误/降级路径)**：提供详尽的结构化替代命令、前置检查以及降级策略（`[AGENT GUIDANCE — FALLBACK STRATEGY]`）。

### 3. 跨会话记忆 (`learnings.md`)
为无状态 Agent 提供持续进化的能力：
- **无感加载 (Auto-Load)**：框架在加载技能时自动将 `learnings.md` 的内容拼接至上下文，Agent 启动时**无需**花费任何工具调用去读取。
- **严格三段式结构**：必须按以下三段组织：`## Known Environment Issues`（已知环境问题）、`## Success Patterns`（成功模式）、`## Failures & Anti-patterns`（失败教训）。
- **硬性体积约束**：当文件行数超过 50 行或 2KB 时，`quick_validate.py` 会抛出 Warning 并输出精简 Prompt 模板，指导 Agent 合并重复报错、清除已解决的环境条目，最多保留 10 条精简内容。

---

## 📁 目录结构

```
skill-creator/
├── SKILL.md                 # 约束技能编写原则与执行生命周期的指令文件
├── LICENSE.txt              # 开源许可证
├── agents/                  # 流程子任务标准手册 (Grader, Analyzer, Comparator)
│   ├── grader.md            # 断言评级器指南
│   ├── analyzer.md          # 运行瓶颈分析及设计审计指南
│   └── comparator.md        # 盲测对比评测指南
├── scripts/                 # 自动化核心脚本
│   ├── quick_validate.py    # 静态设计 Linter (校验 Pre-flight、learnings、Guidance)
│   ├── run_eval.py          # 跨平台非阻塞 Stream 评测器 (兼容 Windows 挂起问题)
│   ├── package_skill.py     # 技能打包器 (支持 --dry-run)
│   ├── improve_description.py # Token 优化的描述压缩器
│   └── utils.py             # 统一 YAML 及 frontmatter 解析工具
└── eval-viewer/             # 评测数据看板生成模块
    └── generate_review.py   # 独立静态 HTML 看板生成器
```

---

## 🚀 使用指南

### 1. 设计规范校验
运行静态 Linter 检查目标技能是否符合基础规范及最佳设计模式：
```bash
python scripts/quick_validate.py <技能目录路径>
```
*如果缺失 Pre-flight 检查、缺少 learnings.md 或脚本中没有 `[AGENT GUIDANCE]` 模式，脚本将以 `WARNING` 形式警告输出，不会中断或阻塞构建流程。*

### 2. 启动基准评估
使用跨平台非阻塞管道对测试集进行并行/串行测试评估：
```bash
python scripts/run_eval.py --help
```

### 3. 技能打包
将测试无误的技能文件夹打包为分发格式：
```bash
python scripts/package_skill.py <技能目录路径> [--dry-run]
```

---

## 📅 CHANGELOG (更新日志) 与版本切换

| 版本号 | 关键改进与里程碑 | 对应提交哈希 (Commit Hash) |
| :--- | :--- | :--- |
| **v2.1.0** (当前) | 落实 Phase 2.1 细节微调（实现 learnings.md 自动加载、内嵌精简算子警告提示、新增 `claude` CLI 状态自检及网络探针）。 | `266c4c7` |
| **v2.0.0** | 架构重大重构（整合 Pre-flight 渐进探索机制、Agent Guidance 密度策略、Windows 平台兼容性修复如非阻塞 Stream 守护线程与 GBK/UTF-8 字符集兼容）。 | `62ea459` |
| **v1.0.0** (历史) | 技能创建、测试与评估的基础流水线版本（优化前）。 | `b9e19e6` |

### 🔄 如何进行版本切换与代码审计

如果您需要对比不同重大版本或回退至旧版运行，请在工作区下运行以下命令：

*   **切换至优化前 Legacy `v1.x` 版本 (无 Agent Guidance / 无 Windows 兼容性)**：
    ```bash
    git checkout -b v1-legacy b9e19e6
    ```

*   **切换至初始重构版 `v2.0.0` (经历 Phase 2 & 2.1 细节调优之前的最初重构版)**：
    ```bash
    git checkout -b v2.0.0-initial 62ea459
    ```

*   **切回当前最新最稳定的 `v2.1.0` 版本**：
    ```bash
    git checkout more
    ```
