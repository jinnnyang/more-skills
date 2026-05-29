# Deep Research (深度调研工程化技能说明文档)

`deep-research` 是 Antigravity 智能体框架中的核心调研与情报合成技能，用于生成格式受控、证据可追溯、来源可治理且具备多维交叉验证的高质量研究报告。

经过优化重构，本技能已升级为**工程化持续调研版本**，全面支持跨会话看板管理、多媒体佐证本地化、数据可视化工具发现与 Mermaid 回落机制，并规范了启动前的前置环境检查。

---

## 🛠️ 核心能力

1. **工程化项目管理**：引入独立项目目录与 Git 版本追踪。每个调研课题拥有一个独立的 kebab-case 格式的根目录（如 `rare-earth-export-control-study`）。
2. **状态看板持续追踪**：通过 `kanban/project_state.json` 实时序列化看板阶段、子代理任务分配、全局 Citation 注册表及多媒体库，支持调研中断与跨会话恢复。
3. **多媒体佐证本地化归档**：子代理利用标准 Markdown 语法标记网页原图，Lead Agent 在撰写报告前的专门阶段（P3）统一完成图片过滤、防盗链下载、本地 `assets/` 归档以及报告相对路径重写。
4. **图像 Alt 说明 LLM 友好化**：采集的多媒体佐证必须配备极其详尽的 `alt` 数据及趋势说明，帮助其他 LLM 在阅读 Markdown 报告时完美理解图片承载的真实信息。
5. **可视化绘图回落策略**：优先通过工具发现机制检测并调用注册的绘图技能（如 `canvas-design` 或 Python 绘图库）输出 PNG 并保存至 `assets/`；在无专门绘图技能时，自动回落为编写防错的 Markdown 内联 Mermaid 代码块。
6. **自动化环境与网络检查**：集成 `check_env.py`，在 P0 阶段自动测试网络延时、Git 可用性、目录写权限及必要 Python 第三方依赖。

---

## 📐 核心设计模式

### 1. 交互式 Intake 交互机制
在技能正式启动前，Lead Agent 会基于用户的研究诉求，自动推荐 **3 个左右的具体可选项**，包括：
- **研究主题**候选（Topic）
- **研究范围与边界**候选（Boundary）
- **项目根目录命名**候选（Project Name）
用户只需做选择题或微调，即可快速进入工程初始化。

### 2. 五大阶段 Git 自动提交生命周期
为确保长周期复杂调研的数据安全性，技能在以下关键卡点自动执行 Git 提交：
- **P1 阶段完毕**：`stage: plan-initialized`（大纲与看板已规划）
- **P2 阶段完毕**：`stage: research-notes-completed`（所有抓取 notes 均已写回 `findings/`）
- **P4 阶段完毕**：`stage: registry-outline-built`（Citations 洗白完毕且大纲与图表设计锁骨架）
- **P5 阶段完毕**：`stage: draft-report-written`（报告初稿撰写完毕）
- **P7 阶段完毕**：`stage: report-finalized`（完成最终纠错，多媒体与 Mermaid 完成定位渲染并归档）

---

## 📁 目录结构

当您新建一个调研项目时，技能将自动在您指定的目录下创建如下规范化工程：

```
[project-name]/               # 项目根目录 (kebab-case)
  ├── .git/                  # Git 版本库
  ├── assets/                # 本地化保存的图片、图表、供应链地图等媒体文件
  ├── findings/              # 存放子代理执行各任务返回的原始 findings 和 notes (task-*.md)
  ├── tasks/                 # 存放具体的任务定义、分配及过程记录 (task-*.md 的配置)
  ├── plan/                  # 存放调研计划、大纲及边界文件
  ├── kanban/                # 看板数据存放目录
  │     └── project_state.json # 看板管理、全局 Citation 注册表与多媒体注册表
  ├── README.md              # 项目总体说明（英文，主入口）
  └── README_zh-CN.md        # 项目总体说明（中文，主入口）
```

---

## 🚀 使用指南

### 1. 执行前置环境校验
Lead Agent 会在 P0 启动前自动执行该检查，您也可以手动在 `deep-research` 技能根目录下调用以排查依赖：
```bash
python scripts/check_env.py
```
*注：该脚本将测试对通用及学术站点（如 Bing、EuropePMC）的连接，验证 Git 是否可用以及是否具有工作区写权限。*

### 2. 启动全新调研项目
当您输入“帮我调研一下...”或“深度研究...”时：
1. 技能将启动 Interactive Intake 并为您提供 3 个项目命名及范围的建议。
2. 选定后，技能将在 `projects/` 下自动创建并初始化 Git。
3. 动态规划任务看板并记录在 `kanban/project_state.json`。

### 3. 恢复或迭代已中断的调研
如果运行意外中断，技能再次启动时会检查本地是否存在 `.git` 和 `kanban/project_state.json`：
1. 自动载入已完成的任务 Findings。
2. 仅对 `TODO` 或 `FAILED` 状态的子任务进行派发。
3. 无缝衔接后续的多媒体统一下载、洗白以及报告合成阶段。

---

## 📅 CHANGELOG (更新日志) 与版本切换

| 版本号 | 关键改进与里程碑 | 对应提交哈希 (Commit Hash) |
| :--- | :--- | :--- |
| **v2.5.0** (当前) | **工程化重构版**：引入工程化项目目录与 Git 版本追踪；集成跨会话 JSON 看板状态；建立多媒体收集、防盗链下载、LLM 友好 Alt 编写规范；引入图表生成技能优先与 Mermaid 回落机制；新增 P0 `check_env.py` 自动化检查。 | `当前修改` |
| **v2.4.0** | 修正来源可访问性政策：明确 circular verification 与 exclusive advantage 的界限；更新 Citations 注册表格式；发布 Counter-Review Team v2 版。 | `693c403` |
| **v2.0.0** | 引入企业级分析模式（Enterprise Research Mode），新增 SWOT 矩阵分析及三级质量管控。 | `064c73e` |
| **v1.0.0** | 基础深度调研技能版本。 | `ffda537` |

### 🔄 如何进行版本回退与代码审计

如果您在执行中需要回退至未优化前的 Legacy 版本：

*   **回退至 v2.4.0 版本（包含 Counter-Review Team v2 且无本次工程化改动的版本）**：
    ```bash
    git checkout 693c403 -- skills/deep-research/
    ```

*   **回退至 v2.0.0 企业调研初始版本**：
    ```bash
    git checkout 064c73e -- skills/deep-research/
    ```

*   **放弃所有本地优化，切回当前最新最稳定的仓库版本**：
    ```bash
    git checkout main -- skills/deep-research/
    ```
