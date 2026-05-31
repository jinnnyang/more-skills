# Deep Research 持续性项目管理指南

为了支持长周期、可恢复和工程化的调研工作，本技能对所有调研任务实施统一的项目管理和 Git 版本追踪。

## 1. 交互式启动确认 (Interactive Intake)

在正式启动项目并创建目录前，Lead Agent 必须与用户确认调研项目的名称、主题以及边界。**不要使用空泛的填空题**，而应根据用户的初始请求自动生成候选方案，以单选/多选题的形式呈现：

### 交互模板示例
```
已收到您的调研请求：“关于稀土出口管制的调研”。为了工程化管理该项目，请选择以下配置（您也可以直接回复序号或微调）：

1. 研究主题候选：
   [A] (推荐) 中国及全球稀土出口管制政策及对半导体产业链的长期影响
   [B] 稀土进出口贸易政策历史演变及供需双向壁垒分析
   [C] 关键稀土元素（钕、镝、铽）出口配额政策与替代技术成熟度调研

2. 研究范围与边界候选：
   [A] (推荐) 聚焦 2020 年至今的政策变化，重点分析美日欧半导体企业的应对举措，排除非半导体领域
   [B] 全面覆盖 2015 年至今全球稀土矿产供应链，包含开采、冶炼、贸易及下游应用全产业链
   [C] 仅限近 3 年内中国出口许可名单及相关制裁措施的实效分析

3. 项目根目录命名候选：
   [A] (推荐) rare-earth-export-control-study
   [B] rare-earth-supply-chain-policy
   [C] china-rare-earth-restrictions-2026
```

---

## 2. 项目目录规范与 Git 初始化

确认命名为 `[project-name]` 后，在工作区下创建该项目的专用根目录，并运行 `git init` 初始化版本追踪。

### 目录结构

```
[project-name]/               # 项目根目录 (kebab-case)
  ├── .git/                  # Git 版本库
  ├── assets/                # 存放多媒体资源（图片、图表、视频）和原始数据文件
  ├── findings/              # 存放子代理执行各任务返回的原始 findings 和 notes (task-*.md)
  ├── tasks/                 # 存放各调研任务的定义说明 (task-*.md 的配置及日志)
  ├── plan/                  # 存放调研路线图、边界说明、大纲及变更记录
  ├── kanban/                # 存放项目状态与看板数据
  │     └── project_state.json
  ├── README.md              # 项目总体说明（英文，主入口）
  └── README_zh-CN.md        # 项目总体说明（中文，主入口）
```

---

## 3. 看板状态规范 (`project_state.json`)

在 `kanban/project_state.json` 中保存整个项目的元数据、任务看板状态、全局 Citation 注册表及多媒体列表。

### JSON 架构定义

```json
{
  "project_info": {
    "name": "rare-earth-export-control-study",
    "topic": "中国及全球稀土出口管制政策及对半导体产业链的长期影响",
    "boundary": "聚焦 2020 年至今的政策变化，重点分析美日欧半导体企业的应对举措",
    "status": "IN_PROGRESS", // IN_PROGRESS | COMPLETED | PAUSED
    "as_of": "2026-05-29",
    "created_at": "2026-05-29T16:00:00Z",
    "last_updated": "2026-05-29T16:15:00Z",
    "git_branch": "main"
  },
  "kanban": {
    "stages": {
      "P0": "COMPLETED",
      "P1": "COMPLETED",
      "P2": "IN_PROGRESS",
      "P3": "TODO",
      "P4": "TODO",
      "P5": "TODO",
      "P6": "TODO",
      "P7": "TODO"
    },
    "drafting_progress": {
      "output_file": "report.md",
      "total_sections": 6,
      "completed_sections": [
        "Executive Summary",
        "1. Policy Timeline"
      ],
      "pending_sections": [
        "2. Supply Chain Impact",
        "3. Alternative Solutions",
        "4. Recommendations",
        "References & Media"
      ],
      "last_updated": "2026-05-29T16:15:00Z"
    },
    "tasks": [
      {
        "id": "task-a",
        "role": "Policy Analyst",
        "objective": "梳理2020年以来稀土出口管制政策文件及核心限制品类",
        "status": "COMPLETED", // TODO | IN_PROGRESS | COMPLETED | FAILED
        "subagent_id": "conv_abc123",
        "output_path": "findings/task-a.md",
        "last_run": "2026-05-29T16:05:00Z",
        "error": null
      },
      {
        "id": "task-b",
        "role": "Supply Chain Expert",
        "objective": "分析管制政策对半导体关键原材料（如研磨液、靶材）供求的影响",
        "status": "IN_PROGRESS",
        "subagent_id": "conv_def456",
        "output_path": "findings/task-b.md",
        "last_run": "2026-05-29T16:10:00Z",
        "error": null
      }
    ]
  },
  "global_citations": {
    "approved": [],
    "dropped": []
  },
  "media_registry": [
    {
      "media_id": "media-a-1",
      "task_id": "task-a",
      "original_url": "https://example.com/charts/supply-chain.png",
      "local_path": "assets/task-a_1716943800_sha256.png",
      "alt": "2024年全球中重稀土开采与冶炼份额占比饼图，展示中国在冶炼环节占据了近89%的全球份额。",
      "title": "全球中重稀土开采冶炼占比",
      "download_status": "SUCCESS" // PENDING | SUCCESS | FAILED
    }
  ]
}
```

---

## 4. Git 自动提交生命周期 (Auto Git Commit Lifecycle)

在调研技能执行的生命周期关键节点，Lead Agent 必须自动检测并执行 Git 提交，以确保持续运行的安全性与数据可回溯性：

| 执行阶段 | 触发提交时机 | Git Commit Message | 说明 |
| --- | --- | --- | --- |
| **P1** | 交互确认完成，项目目录及 `plan/` 初始化完毕 | `stage: plan-initialized` | 确立调研项目的基准框架、范围与任务板设计 |
| **P2** | 所有子代理（或串行抓取）的任务 notes 写回 `findings/` 完毕 | `stage: research-notes-completed` | 抓取阶段完成，锁定所有子任务 notes 数据源 |
| **P3/P4** | Citation 注册表与 Evidence-Mapped Outline 构建完毕 | `stage: registry-outline-built` | 完成数据源洗白与大纲锁骨架 |
| **P5** | Lead Agent 撰写完各章节并追加合并为报告草稿完毕 | `stage: draft-report-written` | 完成主体报告撰写，准备进入交叉验证与纠错 |
| **P6/P7** | 完成纠错与多核校验，导出最终报告，多媒体及图表嵌入到位 | `stage: report-finalized` | 锁定发布版调研项目 |

### Git 执行容错
如果执行 Git 命令失败（例如用户未配置全局 git 账户 `user.name` / `user.email`），Lead Agent 应尝试使用本地项目临时配置执行 commit，确保流程不中断：
```powershell
git config --local user.name "Deep Researcher"
git config --local user.email "deep-researcher@agent.local"
git add .
git commit -m "stage: ..."
```
如果依然由于系统环境原因失败，则记录 warning 至运行日志中，但继续推进研究。

---

## 5. 断点续写与截断恢复机制 (Segmented Resumption)

由于超长调研报告生成极易触碰 LLM 的单次响应 Token 限制，本技能强制采用**按章节流式追加写入**。为应对中途网络异常或模型截断，设计如下恢复逻辑：

### 5.1 进度追踪与临时落盘
1. 在 P5 启动时，Lead Agent 根据 P4 大纲规划，将所有待撰写的章节名称写入 `kanban/project_state.json` 中的 `kanban.drafting_progress.pending_sections` 列表。
2. 每次完成一个章节的生成并追加合并写入报告文件后，将该章节从 `pending_sections` 移动到 `completed_sections`，并立即执行看板文件的写入与 Git 本地自动提交（使用消息 `stage: drafting-section-[name]`）。

### 5.2 截断恢复机制
如果程序异常中断（如模型输出越界或接口超时报错），当用户或系统再次启动该调研项目时：
1. **自动识别断点**：Lead Agent 自动读取并解析 `kanban/project_state.json` 中的 `kanban.drafting_progress`。
2. **状态验证**：
   - 检查已生成的报告文件尾部，验证已完成章节是否确实写入成功。
   - 检查当前待生成的 pending 章节。
3. **断点续写**：
   - 引导提示词中自动加入续写标记，清空当前对话中对已生成章节的具体展开内容（释放上下文空间），仅保留大纲框架和全局引文。
   - 针对下一个待生成的 `pending_sections[0]` 发起调用，并在生成后以 `append` 方式写入报告文件。
   - 续写时若发现剩余总 Token 紧张，自动调用压缩策略，缩减剩余章节的句式厚度。
