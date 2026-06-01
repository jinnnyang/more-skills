# post-to-wechat - 微信排版、插图与发布流水线技能

一个统一且完整的微信文章发布流水线技能，涵盖文章排版美化、封面及正文插图生成、图片体积自动压缩，以及直接发布/草稿保存至微信公众号后台（支持 API 及 Chrome CDP 浏览器模拟操作）。

本项目的基础脚本与设计理念改编自 [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)。特别感谢 **Google Gemini** 进行的代码重构、架构优化及技能整合。

---

## 为什么要合并技能？

在最初的设计中，微信发布的整个工作流零散分布在几个高耦合的独立技能中：
- `baoyu-markdown-to-html` (格式与排版转换)
- `baoyu-cover-image` (文章封面 prompt 设计)
- `baoyu-article-illustrator` (正文可读性插图设计)
- `baoyu-compress-image` (图片体积优化压缩)
- `baoyu-post-to-wechat` (API 与浏览器 CDP 发布)

由于这些步骤在实际发布中是强前后依赖的，将它们合并为一个统一的 `post-to-wechat` 技能可以带来如下优势：
- **降低上下文开销**：避免智能体在多个零散技能之间频繁切换，消除配置文件的重复定义与读取摩擦。
- **简化上游智能体设计**：内容生产类智能体（上游）只需输出 Clean Markdown，然后交由本技能这一个终端节点，即可一次性完成从“配图生成 -> 自动压缩 -> HTML渲染 -> 公众号后台保存”的全流程。

---

## 核心优化点

在整合过程中，基于 `/skill-creator` 的最佳实践，我们对技能执行的健壮性、速度和智能体自我纠错能力进行了深度优化：

1. **Inline 运行上下文（非隔离）**
   - 技能 frontmatter 中去除了 `context: fork`。配置为 **Inline 运行**，使得执行该技能的智能体能够无缝调用环境中已注册的其他图片生成技能（如 Codex 的 `imagegen`、`baoyu-imagine` 技能）并执行本地命令。
2. **图片生成技能优先级策略**
   - 明确指导智能体在生成配图和封面时，必须优先检测并调用本地已注册的图像技能（如 `imagegen`）或原生图片工具（如 `generate_image`），只有在无可用工具时才向用户求助，严禁使用 SVG/HTML 代码硬画替代位图。
3. **封面与插图比例控制**
   - 强制封面图使用微信官方的 `2.35:1`（首图）或 `1:1` 比例；同时放开正文插图（流程图、对比图、时间线等）的比例限制，使其自适应内容排版。
4. **自动压缩与体积优化管道**
   - 在发布上传步骤前集成了自动图片压缩。如果生成的封面或正文插图文件体积超出微信接口限制（如封面限制 2MB，正文大图限制 1MB），脚本会在上传前自动运行 `compress-image.ts` 将其压缩转换为 WebP/PNG，彻底避免接口报错。
5. **跨会话记忆库 (`learnings.md`)**
   - 规范了 [learnings.md](learnings.md) 文件，用于沉淀已知环境陷阱（如微信 API 的 IP 白名单报错、Chrome Profile 文件锁占用、macOS 终端模拟输入权限等）以及运行成功/失败模式。
6. **结构化智能体报错引导 (`[AGENT GUIDANCE]`)**
   - 修改了主要 CLI 脚本，当运行遭遇报错（如 Token 过期、IP 限制、Chrome 未启动等）时，直接向 `stderr` 打印结构化的自愈指南 `[AGENT GUIDANCE — FALLBACK STRATEGY]`，便于智能体在无需人工干预的情况下进行参数自调和降级自愈。
7. **统一且内聚的配置文件 (`EXTEND.md`)**
   - 合并了排版风格、微信账号密钥和图片后端设置至统一的 `EXTEND.md`。配置与 `.env` 密钥默认优先存放在技能目录本身 (`skills/post-to-wechat/`) 下，实现完全内聚和自包含。
8. **融合 ClawHub 微信专业写作知识库**
   - 在 `references/` 目录下集成了 38 个 Markdown 语法知识点（`markdown-syntax-guide.md`）、爆款推文结构与评分模型（`viral-writing-methodology.md`）、94 种排版主题目录（`theme-catalog.md`）以及公众号官方 API 发布限制（`wechat-publishing-guide.md`），用于指导 Agent 排版与配图设计。
9. **支持 API 直接群发与状态轮询**
   - 微信 API 脚本（`wechat-api.ts`）已全面支持直接发布功能。通过 `--publish` 参数可以将草稿直接群发给粉丝，并在命令行自动轮询等待结果；也可通过 `--publish-status <publish_id>` 单独查询发布进度。
10. **彻底清理历史 `.baoyu-skills` 依赖**
    - 重构了所有配置文件和 `.env` 查找逻辑，彻底去除了历史遗留的 `.baoyu-skills` 隐藏文件夹查找，配置完全高内聚在技能目录下。

---

## 目录结构

```
skills/post-to-wechat/
├── SKILL.md                  # 统一的技能工作流指令集
├── README.md                  # 英文说明文档
├── README_zh-CN.md            # 中文说明文档
├── learnings.md              # 跨会话运行经验知识库
├── scripts/                  # 合并后的执行脚本
│   ├── package.json          # 整合后的第三方包依赖配置
│   ├── compress-image.ts     # 图片压缩 CLI 工具
│   ├── markdown-to-html.ts   # Markdown 转换为 styled HTML 工具
│   ├── md-to-wechat.ts       # 转换辅助脚本（处理占位符）
│   ├── wechat-api.ts         # 通过微信 API 上传与草稿箱发布（并支持直发与状态查询）
│   ├── wechat-article.ts     # 通过 CDP 浏览器模拟粘贴发布
│   └── ...                   # CDP 协议与系统剪贴板交互辅助文件
└── references/               # 样式画廊与规范指南
    ├── cover/                # 封面生成配色、风格与维度参考
    ├── illustration/         # 正文插图类型、模版与 prompt 指南
    ├── publishing/           # 秘钥配置、API 规范及冷启动配置流
    ├── markdown-syntax-guide.md   # Markdown 38个知识点语法手册
    ├── theme-catalog.md           # 94种排版主题分类库
    ├── viral-writing-methodology.md # 微信黄金排版原则与写作方法论
    └── wechat-publishing-guide.md   # 微信接口与限制规范
```

---

## 鸣谢与致谢

- **Google Gemini**：规划并执行了全套技能的重构合并，设计并实现了智能体自愈、自动图片压缩管道以及知识库的规范化。
- **JimLiu/baoyu-skills**：本项目中优秀的微信文章排版样式模板、CDP 模拟粘贴以及基础的接口操作脚本。（开源仓库地址：[github.com/JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)）。
