# html-ppt

一份 HTML 演示文稿创作技能，已作为供应源码（vendored copy）纳入本 `more-skills`
仓库。用于生成专业级的**静态 HTML 幻灯片**：36 套主题、15 套完整 deck 模板、
31 种页面布局、47 个动效（27 CSS + 20 Canvas FX），以及一套真实可用的
**演讲者模式**（像素级预览 + 逐字稿 + 计时器）。纯静态 HTML/CSS/JS，无需构建。

> English: [README.md](README.md)

---

## 来源与署名

| | |
|---|---|
| **上游仓库** | https://github.com/lewislulu/html-ppt-skill |
| **原作者** | lewis &lt;sudolewis@gmail.com&gt; |
| **协议** | MIT（© 2026 lewis）—— 见 [`LICENSE`](LICENSE) |
| **导入自** | `https://github.com/lewislulu/html-ppt-skill`（commit `f3a8435`，2026-07-16 导入） |
| **重命名** | 上游文件夹 `html-ppt-skill/` → 本地文件夹 `html-ppt/`（`SKILL.md` 中的 `name:` 保持不变：`html-ppt`） |

本目录是上游技能的**供应源码副本**（vendored），不是 git submodule 也不是
fork。完整 MIT 协议原文保留在 [`LICENSE`](LICENSE)；上游作者原始的两份 README
以 [`UPSTREAM_README.md`](UPSTREAM_README.md) 与
[`UPSTREAM_README.zh-CN.md`](UPSTREAM_README.zh-CN.md) 的形式原样保留以供参考。

### 相对上游的改动

仅重写了指向旧文件夹名的**路径标签引用**（README 中目录树里的 `html-ppt-skill/`
→ `html-ppt/`，以及 `.clawscan-allow` 的头部注释）。`assets/`、`templates/`、
`scripts/`、`references/`、`docs/`、`examples/`、`SKILL.md`、`LICENSE` 与上游
**逐字节一致**。README 中 `npx skills add https://github.com/lewislulu/html-ppt-skill`
的安装命令仍然指向真实的上游仓库，**不要**改写。

如果你对 `assets/` / `templates/` / `references/` / `scripts/` 做了改进，
欢迎回馈到上游 `github.com/lewislulu/html-ppt-skill`。

### 与上游对比校验

```bash
# 将本地副本与新拉取的上游做 diff：
git clone --depth 1 https://github.com/lewislulu/html-ppt-skill /tmp/html-ppt-upstream
diff -r --brief \
  --exclude=.git --exclude=README.md --exclude=README_zh-CN.md \
  --exclude=UPSTREAM_README.md --exclude=UPSTREAM_README.zh-CN.md \
  /tmp/html-ppt-upstream ./
```

---

## 使用方式

这是一个 Agent Skill。任何遵循 [Agent Skills](https://agentskills.io) 规范的
运行时（带 skills 的 Claude、Hermes Agent 等）在用户提出"要一份幻灯片"类请求时，
会自动加载 `SKILL.md`。`SKILL.md` 里的 frontmatter `description` 列出了所有触发
关键词（`presentation`、`ppt`、`slides`、`deck`、`keynote`、`幻灯片`、`演讲稿`、
`小红书图文`、`pitch deck`、`technical presentation` 等）。

### 不通过 agent，纯本地使用

```bash
# 在本目录下：
./scripts/new-deck.sh my-talk           # 用基础模板脚手架出一份新 deck
open examples/my-talk/index.html        # 或用任意静态 HTTP server 打开

# 或者浏览内置的展示：
open templates/theme-showcase.html      # 全部 36 主题
open templates/layout-showcase.html     # 全部 31 布局
open templates/animation-showcase.html  # 全部 47 动效
open templates/full-decks-index.html    # 全部 15 套完整 deck 模板
```

完整的创作流程、键盘快捷键、逐字稿写作三条规则、演讲者模式的实现原理等，
请看上游 README —— [`UPSTREAM_README.zh-CN.md`](UPSTREAM_README.zh-CN.md)；
面向 agent 的入口和分步指引则看 [`SKILL.md`](SKILL.md) 以及
[`references/`](references/) 目录下的详细文档。

### 通过 agent 使用

当你的 agent 运行时已经把本仓库配置成 skills 源之后，直接自然地说：

- "做一份 8 页的技术分享 slides，用 cyberpunk 主题"
- "把这段大纲改成一份 pitch deck"
- "做一个小红书图文，9 张，白底柔和风"
- "我要去给团队做技术分享，要一份带逐字稿的 PPT"

Agent 会加载 `SKILL.md`，先问你三个澄清问题（内容/受众、主题、起手模板），
然后再开始脚手架并生成 deck。

### 导入后的目录结构

```
skills/html-ppt/
├── SKILL.md                agent 入口（与上游一致）
├── LICENSE                 上游 MIT 协议（未修改）
├── README.md               英文版
├── README_zh-CN.md         ← 本文件（说明来源与用法）
├── UPSTREAM_README.md      上游英文 README
├── UPSTREAM_README.zh-CN.md 上游中文 README
├── .clawscan-allow         安全扫描白名单
├── assets/                 base.css · themes/ · animations/ · runtime.js …
├── templates/              deck.html · full-decks/ · single-page/ · 展示页
├── references/             themes.md · layouts.md · animations.md · …
├── scripts/                new-deck.sh · render.sh
├── docs/                   README 图片素材 (hero.gif、截图)
└── examples/               demo-deck/
```

---

## 协议

上游技能使用 MIT 协议。本供应副本在**同一 MIT 条款**下二次分发。完整协议原文
和原始版权声明保留在 [`LICENSE`](LICENSE)：

> Copyright (c) 2026 lewis &lt;sudolewis@gmail.com&gt;

本次导入过程中新增的内容（本 `README.md`、`README_zh-CN.md`，以及把上游两份
README 改名为 `UPSTREAM_README.*` 的动作）同样以 MIT 条款贡献。
