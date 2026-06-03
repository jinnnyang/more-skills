# Markdown Illustrator (Markdown文章配图与无障碍富化技能)

一个专为 AI Agent 设计的、统一的 Markdown 文章配图与排版排版技能。它能动态分析 Markdown 文章的结构 and 内容，设计风格一致的视觉调性（Visual Tone），定位配图锚点（POI），并在相应位置自动生成或引用嵌入高质量的视觉配图。同时支持对存量图片进行无障碍富化，自动利用 Agent 自身的视觉能力补全 `alt` 和 `title` 标签。支持 SVG 矢量图、Agent 原生绘图、OpenAI 兼容云端大模型，以及事实引用与网络截图引擎，并实现本地图片的自动关联复制。

---

## 🚀 核心特性

1. **存量图片无障碍化富化 (Alt/Title 补全)**：自动扫描 Markdown 中已有的图片，利用 Agent 自身的视觉读取能力，对缺乏描述的图片进行智能识别，补全 `alt` 描述和 `title` 标签。
2. **全局视觉一致性策划**：在配图前建立视觉调性看板（配色、风格类型），确保整篇文章所有新插图风格的统一性，避免多张图视觉割裂。
3. **多源配图引擎**：
   - **SVG 矢量图表**：编写深色主题（Dark-themed）系统架构图、流程图和时间线，自动编译渲染为高质量的双倍图（@2x PNG）。
   - **事实引用与网络配图**：针对新闻报道、官方声明、软件界面截图等强证据链场景，拉取或提示收集真实图片证据，确保内容的说服力。
   - **Agent 原生绘图** 与 **OpenAI 兼容 API**：生成极具美感、符合特定预设风格（如 Notion 线条画、微光玻璃态）的插画与封面图。
4. **智能素材收割与关联复制**：
   - 自动在本地限定目录下检索主题相关的已有 Markdown 文章，匹配收割已有的 `!\[alt\](url "title")` 图片资源。
   - 对使用的本地图片自动执行物理文件**关联复制**至目标文章的 `assets/` 目录下，保持文档排版包自包含。
5. **MITTS (多维文本透传) 与完整标签支持**：自动注入无障碍 alt 与 title，且 MITTS 规范块强制补充“图片来源与事实依据”，提高可读性与信度。
6. **Pre-flight 协同环境发现**：在执行前进行 Shell、Python 及渲染工具校验，安全避坑。

---

## 📁 目录结构

```
document-illustrator/
├── SKILL.md                 # 核心 Agent 指导词与绘图引擎选择规则
├── README.md                # 英文使用文档
├── README_zh-CN.md          # 中文使用文档
├── learnings.md             # 跨 Session 执行记忆与避坑指南
├── evals/
│   └── evals.json           # 包含 20 个测试 Case 的触发率评估测试集
├── scripts/
│   ├── openai_client.py     # 健壮的纯 Python HTTP API 客户端（生成/变体/编辑）
│   └── svg_to_png.py        # 兼容 Windows 的 SVG 转 PNG 命令行脚本（支持 npx/rsvg/inkscape）
└── references/              # 视觉排版规则与配色指南
    ├── svg/                 # 架构图、流程图和时序图的 SVG 编写模板
    ├── presets/             # 渐变玻璃态、Notion 线条画、扁平矢量风的 Prompt 预设
    ├── palettes/            # 语义化颜色配色方案
    └── workflows/           # 提示词拼装工作流
```

---

## 🛠️ 配置与环境设置

若要启用 OpenAI 兼容引擎（例如使用火山引擎的豆包 Seedream 绘图模型），请在项目根目录下的 `.env` 文件中添加以下配置：

```env
# 1. 专属 Base URL
DOCUMENT_ILLUSTRATOR_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3

# 2. API Key（填入您的火山引擎 Ark 控制台的真实密钥）
DOCUMENT_ILLUSTRATOR_API_KEY=your_real_api_key_here

# 3. 默认使用的模型名称
DOCUMENT_ILLUSTRATOR_MODEL_NAME=doubao-seedream-5.0-lite
```

---

## 🔍 Pre-flight 协同工具发现

在启动阶段，该技能会引导 Agent 显式地列出并检查当前环境中所有已注册的绘图、配图或图像生成相关的工具与技能。通过动态检查其参数结构，避免因平台差异导致硬编码参数报错，保证了跨 Agent 平台的自适应性。

---

## 💖 致谢与参考项目

在构建和整合该技能的过程中，我们衷心感谢以下开源项目、服务和技术带来的启发和支持：

- **[Document-illustrator-skill](https://github.com/op7418/Document-illustrator-skill)**：核心参考的底层技能实现，提供了文档配图逻辑、图表插入框架及初始工作流。
- **[gpt_image_playground](https://github.com/CookSleep/gpt_image_playground)**：为我们提供了图像生成测试沙盒设计、请求载荷格式及模拟客户端接口结构的参考。
- **[happy-figure](https://github.com/datawhalechina/happy-figure/tree/main)**：为本项目提供了精美图表布局规范、美学指导原则及图文呈现标准。
- **[baoyu-diagram](https://github.com)**：为本项目提供了极具美感的高级深色系 SVG 矢量排版规范、语义化组件配色方案，以及跨平台 Node/Python 混合渲染的工程设计思路。
- **[火山引擎 (Volcano Engine) 豆包 Seedream](https://www.volcengine.com)**：为我们提供了高性能、极具艺术风格的图像生成及变体模型能力，其特殊的 Base64 参考图传输规范直接启发并验证了我们的 API 客户端设计。
- **[resvg-js](https://github.com/yisibl/resvg-js)**：其提供的 `@resvg/resvg-js-cli` 工具是一款基于 Rust 开发的、极速的 SVG 转 PNG 转换器，使我们能够在 Windows、macOS 和 Linux 上无需安装臃肿的系统库即可实现像素级精准的渲染。
- **[OpenAI API 规范](https://platform.openai.com)**：定义了行业标准的图像生成、变体与编辑的 Multipart 数据交互格式，成为我们核心网络层协议的基石。
