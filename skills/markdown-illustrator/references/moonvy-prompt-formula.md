## 📂 二、 Moonvy OPS 结构化 Tag 拼装公式 (Structured Tag Assembly)

借鉴 [Moonvy OPS (Open Prompt Studio)](https://moonvy.com/apps/ops/) 的积木式标签分类系统，**严禁写冗长自然语言句子**。Agent 必须按以下六大标签分类、按固定顺序拼装英文 Prompt：

```
[1. Style Prefix], [2. Subject/Scene], [3. Environment], [4. Color/Lighting], [5. Composition], [6. Negative Prompt], [7. Parameters]
```

### 各标签分类与数据源映射

| 标签分类 | 在我方系统中的来源 | 示例 |
| :--- | :--- | :--- |
| **1. Style Prefix** | 读取 `references/styles/` 中选定流派的 Design Aesthetic 描述 | `notion style doodle, minimalist hand-drawn line art` |
| **2. Subject** | Agent 依据正文内容自由提炼核心概念、人物与隐喻动作 | `a paper crane unfolding back into a flat sheet` |
| **3. Environment** | 依据流派控制背景杂乱度，配合主体声明物理空间 | `on a clean white desk, minimalist space` |
| **4. Color/Lighting** | 读取 `references/palettes/` 的 Hex 色票，翻译为自然语言（见第三节） | `color palette of deep forest green and sage, warm cream background` |
| **5. Composition** | 声明镜头语言、构图与留白方式 | `centered composition, ample negative space, single focal point` |
| **6. Negative (--no)** | 系统强制注入的负向标签（见第六节） | `--no text, words, watermark, blurry` |
| **7. Parameters** | 读取 `references/canvas/` 规范，转换成后缀指令 | `--ar 16:9 --v 6.1 --style raw` |

### 正确 vs 错误示例对比

❌ **乱成一团的自然语言 Prompt（Agent 容易犯的错）**：
```
A nice flat style business illustration that shows a manager holding a magnifying glass
to check a big gear, the main colors should be dark blue and orange, and the background
is gray, I want it in 16:9 ratio.
```

✓ **符合积木式 Tag 结构的标准 Prompt**：
```
modern corporate flat vector illustration, a businessman holding a magnifying glass
inspecting giant interlocking gears, clean studio environment, deep navy blue and
vibrant safety orange, light warm gray background, centered composition with ample
negative space --no text, signatures, watermark, low quality, blurry --ar 16:9
```

---

## 📂 三、 色票自然语言映射规则 (Palette-to-Language Translation)

AI 绘图模型（Midjourney、DALL-E 3、Stable Diffusion 等）**无法直接理解 Hex 颜色值**（如 `#FF6B35`）。若直接将 Hex 写入 Prompt，模型会忽略或产生混乱。Agent 必须将 Spec 中的 Hex 色票翻译为**英文具象色彩描述**。

### 1. 映射公式

```
#HEX → [英文具象色彩名称 + 可选质感修饰]
```

在 Prompt 中以如下语法声明：
```
color palette of [主色描述] and [点缀色描述], [底色描述] background
```

### 2. 常用色票映射速查表

以下覆盖 `references/palettes/` 中代表性色票的 Hex → 自然语言映射：

| Palette 文件 | 角色 | Hex | AI Prompt 自然语言映射 |
| :--- | :--- | :--- | :--- |
| `ikb-blue` | Accent | `#002FA7` | `international klein blue` |
| `ikb-blue` | Background | `#FAFAF8` | `clean matte off-white` |
| `swiss-orange` | Accent | `#FF6B35` | `vibrant safety orange` |
| `forest-ink` | Primary | `#16251B` | `deep dark forest green` |
| `forest-ink` | Accent | `#2E6B4F` | `rich sage green` |
| `forest-ink` | Background | `#F5F1E8` | `warm natural cream paper` |
| `midnight-ink` | Background | `#0E0D0C` | `deep midnight black` |
| `midnight-ink` | Accent | `#D4A04A` | `warm golden amber` |
| `midnight-ink` | Primary Text | `#ECE2CF` | `aged paper cream` |
| `neon` | Background | `#2D1B4E` | `deep electric purple` |
| `neon` | Primary | `#FF1493` | `hot neon pink` |
| `neon` | Secondary | `#00FFFF` | `electric cyan` |
| `macaron` | Background | `#F5F0E8` | `soft warm cream` |
| `macaron` | Macaron Blue | `#A8D8EA` | `soft pastel sky blue` |
| `macaron` | Macaron Mint | `#B5E5CF` | `gentle mint green` |
| `macaron` | Accent | `#E8655A` | `warm coral red` |
| `ink-classic` | Paper | `#F3F0E8` | `aged warm parchment` |
| `ink-classic` | Ink | `#0A0A0B` | `deep carbon black ink` |
| `mono-ink` | Background | — | `pure monochrome, black and white only` |

### 3. Agent 自行推导规则

对于上表未覆盖的色票，Agent 应遵循以下翻译启发式：

1. **优先使用色票文件中已有的 Color Name 列**：如 `forest-ink.md` 中 `#2E6B4F` 已标注为 `Forest Green`，直接采用。
2. **附加质感修饰词**：根据流派附加材质感（如水彩风加 `washed`、油画风加 `impasto`、极简风加 `clean matte`）。
3. **底色声明**：始终显式声明背景色，如 `on a warm cream background` 或 `against deep midnight black`。

---

## 📂 四、 视觉双重曝光 — SVG + AI 叠加方案 (Visual Double Exposure)

当正文需要"文字与图形深度穿插"的海报效果（如案例中的艺术海报、节气海报、活动海报）时，直接命令 AI 生成整张图是不明智的——模型极易产生文字乱码或排版混乱。

**解决方案**：采用 **"视觉双重曝光"** 分工方案：

| 视觉元素 | 负责路径 | 原因 |
| :--- | :--- | :--- |
| **背景质感、光影、艺术图形、剪影** | Gen-AI (Path 3) | AI 擅长渲染质感、光影和风格化图形 |
| **标题、正文、日期、二维码、精确排版** | SVG Card (Path 2) | SVG `<foreignObject>` 可输出精准矢量文字，零乱码 |

### 执行流程

1. **AI 生成纯净背景**：在 Prompt 中**强制声明 `--no text, words, letters, labels`**，仅生成高审美的视觉图形、肌理（如皱纸质感、泼墨效果、复古波浪图案）。
2. **SVG 叠加矢量排版**：在 SVG 的 `<foreignObject>` 容器中，使用 CSS Grid/Flexbox 将中文/英文标题与日期精准地叠加在 AI 生成的背景图之上。

### 分工法则速查

| 需求 | 走 Gen-AI | 走 SVG/Mermaid |
| :--- | :--- | :--- |
| 写实质感（皱纸、泼墨、金属光泽） | ✓ | — |
| 复杂的艺术剪影、人物形象 | ✓ | — |
| 精确的中英文标题排版 | — | ✓ |
| 日期、期号、二维码、页码 | — | ✓ |
| 数据图表（折线/柱状/饼图） | — | ✓ (Mermaid) |
| 列表、步骤、流程说明 | — | ✓ (SVG/Mermaid) |

---

## 📂 五、 提示词模版库 (Prompt Template Library)

以下提供五类标准化模版，Agent 根据视觉图纸（Spec）中确定的配图类型直接套用：

### 模版 1：概念氛围插画 (Conceptual Illustration)

适用于：抽象隐喻、概念可视化、情感修饰图。

**结构公式**：
```
[Style Prefix], [subject performing metaphorical action],
[environment with controlled complexity],
color palette of [palette colors], [background color] background,
[composition directive]
--no text, words, letters, watermark, signature, low quality, blurry
--ar [ratio]
```

**填空示例**（Notion 风 + forest-ink 色盘）：
```
notion style doodle, minimalist hand-drawn line art, a robotic arm gently
pressing a wooden building block causing it to collapse into flat geometric dust,
on a clean minimal surface, color palette of deep forest green and rich sage green,
warm natural cream background, single concept focus, ample whitespace
--no text, words, letters, watermark, realistic, shading, gradients --ar 16:9
```

---

### 模版 2：写实摄影 (Photorealistic Photography)

适用于：产品展示、场景氛围、编辑类生活方式摄影。

**结构公式**：
```
photorealistic [shot type] of [subject], [action or expression],
set in [environment], illuminated by [lighting description],
[color temperature and palette], captured with [camera and lens details],
[depth of field and texture emphasis]
--no text, watermark, illustration, cartoon, drawing --ar [ratio]
```

**填空示例**（midnight-ink 色盘）：
```
photorealistic medium close-up of a vintage brass pocket watch resting on
weathered leather-bound journal, set in a dimly lit study, illuminated by
warm golden amber candlelight from the left, deep midnight black shadows
with aged paper cream highlights, captured with Sony A7IV 85mm f/1.4,
shallow depth of field with rich bokeh, visible leather grain texture
--no text, watermark, illustration, cartoon, drawing --ar 16:9
```

---

### 模版 3：资产 / 贴纸 (Asset / Sticker)

适用于：透明背景小元素、Icon 素材、装饰贴纸。

**结构公式**：
```
[style] sticker of [subject], featuring [key characteristics],
[color palette], [line style] outline, [shading style],
transparent background, die-cut sticker design
--no background, shadow, frame, text --ar 1:1
```

**填空示例**（macaron 色盘）：
```
cute kawaii sticker of a smiling coffee cup with steam curling upward,
featuring rounded soft edges, soft pastel sky blue and gentle mint green,
warm coral red accent on the cup handle, bold clean outline, flat shading,
transparent background, die-cut sticker design
--no background, shadow, frame, text --ar 1:1
```

---

### 模版 4：风格迁移 (Style Transfer)

适用于：将参考图/照片转换为指定艺术风格。

**结构公式**：
```
transform this image into [art style / artist reference] style,
preserve original composition, render with [stylistic elements description],
color palette of [palette colors]
--ar [ratio]
```

**填空示例**：
```
transform this photograph into traditional Chinese ink wash painting style,
preserve the original composition of the mountain landscape, render with
flowing brush strokes, ink splatter effects, and atmospheric mist,
color palette of deep carbon black ink and aged warm parchment
--ar 16:9
```

---

### 模版 5：海报 / 封面背景 (Poster / Cover Background)

适用于：纯背景图（无文字），后续由 SVG 叠加排版。参考"视觉双重曝光"方案。

**结构公式**：
```
[style] background for a poster design, [visual elements and textures],
[color contrast description], [composition and spatial structure],
abstract decorative pattern, no text content
--no text, words, letters, labels, writing, font, typography, signature
--ar [ratio]
```

**填空示例**（复古摇滚海报背景 + neon 色盘）：
```
retro distressed print texture background for a poster design, bold wavy
ink strokes with oil printing texture, strong contrast of hot neon pink
and deep electric purple, white ink splatter accents, layered composition
with horizontal band structure, abstract decorative pattern, no text content
--no text, words, letters, labels, writing, font, typography, signature
--ar 3:4
```

---

