# html-ppt

An HTML presentation authoring skill vendored into this `more-skills` collection.
Produces professional static-HTML slide decks with 36 themes, 15 full-deck
templates, 31 page layouts, 47 animations (27 CSS + 20 canvas FX), and a real
presenter mode (pixel-perfect preview + speaker script + timer). No build step,
pure static HTML/CSS/JS.

> 中文版：[README_zh-CN.md](README_zh-CN.md)

---

## Source & attribution

| | |
|---|---|
| **Upstream repository** | https://github.com/lewislulu/html-ppt-skill |
| **Original author** | lewis &lt;sudolewis@gmail.com&gt; |
| **License** | MIT (© 2026 lewis) — see [`LICENSE`](LICENSE) |
| **Imported from** | `https://github.com/lewislulu/html-ppt-skill` (commit `f3a8435`, imported 2026-07-16) |
| **Folder renamed** | upstream folder `html-ppt-skill/` → local folder `html-ppt/` (skill `name:` in `SKILL.md` is unchanged: `html-ppt`) |

This directory is a **vendored copy** of the upstream skill, not a submodule
and not a fork. The full MIT license text is preserved verbatim in
[`LICENSE`](LICENSE); the upstream author's original README files are kept
side-by-side as [`UPSTREAM_README.md`](UPSTREAM_README.md) and
[`UPSTREAM_README.zh-CN.md`](UPSTREAM_README.zh-CN.md) for reference.

### What was changed vs upstream

Only path-label references to the old folder name were rewritten (`html-ppt-skill/`
→ `html-ppt/` in doc file-tree diagrams and the `.clawscan-allow` header
comment). All `assets/`, `templates/`, `scripts/`, `references/`, `docs/`,
`examples/`, `SKILL.md`, and `LICENSE` are byte-identical to upstream. The
`npx skills add https://github.com/lewislulu/html-ppt-skill` install-command
lines still point at the real upstream repository — do not rewrite them.

If you improve anything under `assets/` / `templates/` / `references/` /
`scripts/`, please consider contributing it back upstream at
`github.com/lewislulu/html-ppt-skill`.

### Verifying against upstream

```bash
# Diff the vendored copy against a fresh clone of upstream:
git clone --depth 1 https://github.com/lewislulu/html-ppt-skill /tmp/html-ppt-upstream
diff -r --brief \
  --exclude=.git --exclude=README.md --exclude=README_zh-CN.md \
  --exclude=UPSTREAM_README.md --exclude=UPSTREAM_README.zh-CN.md \
  /tmp/html-ppt-upstream ./
```

---

## Usage

This is an Agent Skill. Any agent runtime that follows the
[Agent Skills](https://agentskills.io) spec (Claude with skills, Hermes Agent,
etc.) will load `SKILL.md` when the user asks for a slide-based deliverable.
The `SKILL.md` frontmatter description lists the triggering keywords
(`presentation`, `ppt`, `slides`, `deck`, `keynote`, `幻灯片`, `演讲稿`,
`小红书图文`, `pitch deck`, `technical presentation`, …).

### Try it locally without an agent

```bash
# From this folder:
./scripts/new-deck.sh my-talk           # scaffold a fresh deck
open examples/my-talk/index.html        # or start any static HTTP server

# Or browse the built-in showcases:
open templates/theme-showcase.html      # all 36 themes
open templates/layout-showcase.html     # all 31 layouts
open templates/animation-showcase.html  # all 47 animations
open templates/full-decks-index.html    # all 15 full-deck templates
```

Complete authoring workflow, keyboard shortcuts, the 3 rules of speaker-script
writing, and the presenter-mode design are documented in the upstream README —
see [`UPSTREAM_README.md`](UPSTREAM_README.md) or, for the agent-facing
dispatcher and step-by-step guide, [`SKILL.md`](SKILL.md) plus files under
[`references/`](references/).

### Loading via an agent

Once your agent runtime has this repository configured as a skills source,
just ask naturally:

- "做一份 8 页的技术分享 slides，用 cyberpunk 主题"
- "turn this outline into a pitch deck"
- "做一个小红书图文，9 张，白底柔和风"
- "我要去给团队做技术分享，要一份带逐字稿的 PPT"

The agent will load `SKILL.md`, ask the three clarifying questions
(content / audience, theme, starting template), then scaffold and author
the deck.

### Directory layout (post-import)

```
skills/html-ppt/
├── SKILL.md                agent-facing dispatcher (unchanged from upstream)
├── LICENSE                 upstream MIT license (unchanged)
├── README.md               ← this file (integration + attribution)
├── README_zh-CN.md         中文版本
├── UPSTREAM_README.md      upstream English README
├── UPSTREAM_README.zh-CN.md upstream 中文 README
├── .clawscan-allow         security-scan false-positive allowlist
├── assets/                 base.css · themes/ · animations/ · runtime.js …
├── templates/              deck.html · full-decks/ · single-page/ · showcases
├── references/             themes.md · layouts.md · animations.md · …
├── scripts/                new-deck.sh · render.sh
├── docs/                   readme assets (hero.gif, screenshots)
└── examples/               demo-deck/
```

---

## License

The upstream skill is MIT-licensed. This vendored copy is redistributed under
the same MIT terms. The full license and original copyright notice are
preserved in [`LICENSE`](LICENSE):

> Copyright (c) 2026 lewis &lt;sudolewis@gmail.com&gt;

Any additions to this vendored copy (this `README.md`, `README_zh-CN.md`, and
the upstream-README renames) are contributed to the same MIT terms.
