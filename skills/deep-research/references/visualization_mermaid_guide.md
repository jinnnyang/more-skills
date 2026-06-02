# Deep Research Data Visualization & Diagram Fallback Guide

To clearly present complex data, processes, and industry relationships, the Lead Agent MUST introduce high-quality visual diagrams. This guide defines the visual tool discovery, fallback policy, Mermaid coding standards, and the **Semantic Media Integration Standard (SMIS)**.

---

## 1. Diagram Fallback & Tool Discovery Policy

When a diagram or illustration is planned (e.g., system architecture, pricing line charts, process workflows), follow this two-tier routing workflow:

```mermaid
graph TD
    Start["Diagram Needed (Architecture / Flow / Data)"] --> Scan["Scan environment for drawing skills"]
    Scan --> CheckTools{"Specialized skill available?<br>(e.g., doc-illustrator / matplotlib)"}
    
    CheckTools -- Yes --> DrawSkill["Priority 1: Invoke doc-illustrator"]
    DrawSkill --> OutputImage["Generate high-fidelity PNG/SVG"]
    OutputImage --> SaveAssets["Save to relative assets/ or images/"]
    SaveAssets --> EmbedMD["Embed Markdown image tag<br>+ Apply SMIS Standard"]
    
    CheckTools -- No/Failed --> MermaidFall["Priority 2: Fallback to inline Mermaid.js"]
    MermaidFall --> RenderMD["Render raw Mermaid code block in report<br>+ Apply SMIS Standard"]
```

### 1.1 Priority 1: Specialized Illustration (doc-illustrator)
- Scan for active drawing skills (like `doc-illustrator`) or Python libraries (`matplotlib`, `seaborn`).
- Invoke `doc-illustrator` using its assembled prompt and guidelines to output a high-fidelity image file.
- Save the asset under `assets/` or `images/` within the project root directory.
- Embed the image in `report.md` using the standard Markdown image link wrapped in SMIS Pattern A (descriptive Alt-text) or Pattern B (semantic `<figure>` HTML wrapper).

### 1.2 Priority 2: Mermaid Inline Fallback
- If `doc-illustrator` is missing or fails, write a raw Mermaid.js text diagram directly inline in the Markdown report.
- Protect all node text with double quotes and use unique simple IDs.
- Wrap the Mermaid block inside a semantic `<figure>` HTML structure, or write a descriptive caption using `<figcaption>` below it to provide high context.

---

## 2. Mermaid Anti-Error Syntax Guidelines

Mermaid parsers are highly sensitive. To prevent rendering failure, strictly adhere to these rules:

### ⚠️ Rule 1: Always Wrap Complex & Chinese Labels in Double Quotes
Labels containing spaces, brackets, special punctuation, or non-ASCII characters (e.g., Chinese) **MUST** be wrapped in double quotes.
- ❌ **Incorrect**: `A[Global rare earths (China 89%)] --> B`
- ✅ **Correct**: `A["Global rare earths (China 89%)"] --> B`

### ⚠️ Rule 2: Use Unique, Monospaced Node IDs
Keep node IDs simple (e.g., `A`, `B`, `step1`, `process2`). Do not use spaces, Chinese, or special characters in the ID.
- ❌ **Incorrect**: `中国稀土["China Rare Earth"] --> 冶炼加工["Refining"]`
- ✅ **Correct**: `china["China Rare Earth"] --> process["Refining"]`

### ⚠️ Rule 3: Strictly Prohibit HTML Tags
For maximum cross-platform compatibility, do not embed raw HTML tags like `<br>`, `<b>`, or `<div>` inside labels. Use clean text and let the renderer handle wrapping, or use double quotes with explicit line breaks if supported.

---

## 3. Semantic Media Integration Standard (SMIS)

To ensure reports are fully accessible to screen readers and downstream LLMs that have no vision capabilities, every single visual element (PNG, SVG, or Mermaid) or video asset **MUST** carry a rich, context-inferred, and highly analytical description. Use **Pattern A** (simple/compact visuals) or **Pattern B** (complex visuals/videos) in the target adaptive language.

### 3.1 Pattern A: Simple/Compact Visuals (Standard Markdown Alt-Text)
Embed the rich description directly inside the standard Markdown image `alt` attribute. This is extremely compact and native.

#### Format:
`![【类型：图表类型；核心主题：描述主题】从原网上下文与图表分析，关键数据为...，由此推断出关键结论为...](图片原始 Web URL "自解释标题")`

#### Chinese Example:
`![【折线图：2020-2025年全球氧化镝出口价格走势】2022年价格达到32万美元/吨的高值，2024年回落并稳定在22万美元/吨，整体价格随出口配额呈现强周期性波动。由此推断，供应链对管制配额高度敏感，海外买方企业需在2026年配额再次调整前通过多年度固定价格采购协议锁定成本。](https://example.com/charts/dysprosium-price.png "2020-2025年全球氧化镝价格折线图")`

#### English Example:
`![[Line Chart: 2020-2025 Global Dysprosium Oxide Export Price Trend] Prices peaked at $320k/ton in 2022 and stabilized at $220k/ton in 2024, exhibiting high cyclical volatility driven by export quota adjustments. Conclusively, the supply chain is highly vulnerable to policy changes; buying entities must secure long-term, fixed-price procurement agreements before 2026 to mitigate risk.](https://example.com/charts/dysprosium-price.png "2020-2025 Global Dysprosium Oxide Price")`

### 3.2 Pattern B: Complex/Structural/Video Visuals (Semantic HTML Wrappers)
Use standard semantic inline-HTML elements. This allows beautiful rendering, structural layouts, and handles complex media (like collapsible video transcripts or long charts).
* **CRITICAL HTML RULE**: Inside HTML block wrappers, you MUST use standard HTML tags (e.g. `<b>`, `<i>`, `<a href="...">`) instead of Markdown formatting (`**`, `*`, `[]()`) to guarantee parser stability.

#### Chinese Example:
<figure>
  <img src="https://example.com/workflow/license-audit.png" alt="【流程图】两部委出口许可证双向申报与合规审查流向" />
  <figcaption><b>图 1.2: 稀土出口两部委合规审查流程图</b> — 原网页条款指出，企业需依次经过企业申报、省商务厅初审、商务部与海关总署终审三大关卡，平均审批周期为60个工作日。这表明合规门槛将显著提高，跨国企业需提前 60 天以上规划物流。 <a href="https://example.com/policy/details">[1]</a></figcaption>
</figure>

#### English Example:
<figure>
  <img src="https://example.com/workflow/license-audit.png" alt="[Flowchart] Dual-Ministry Export Licensing & Compliance Process" />
  <figcaption><b>Figure 1.2: Dual-Ministry Export Licensing Compliance Flowchart</b> — Official regulations state that enterprises must clear three gates: dual-ministry declaration, provincial pre-audit, and final joint approval by MOFCOM and GACC, with an average processing window of 60 business days. This indicates a heightened compliance barrier; multinational buyers must expand logistical lead times by 60+ days. <a href="https://example.com/policy/details">[1]</a></figcaption>
</figure>

#### Collapsible Video/Transcript Example:
<details>
  <summary>🎬 <b>视频佐证：稀土配额管理政策解读视频</b></summary>
  <p>视频详细梳理了商务部和海关总署对重稀土出口配额的核验流程。关键镜头展示了2026年即将推行的电子口岸双核验界面（08:45）。由此推论：配额申领的信息化程度提升将压缩贸易商的政策擦边球空间，合规审查漏检率将降至接近于零，促使跨国车企必须与持牌国企进行对接。具体规范参见 <a href="https://example.com/video/details">视频官方文字实录</a>。</p>
</details>

---

## 4. Standard Diagram Templates for Reference

### 4.1 SWOT Quadrant Chart
```mermaid
quadrantChart
    title SWOT Strategic Positioning
    x-axis "External Opportunities" --> "External Threats"
    y-axis "Internal Weaknesses" --> "Internal Strengths"
    quadrant-1 "Aggressive Expansion (SO)"
    quadrant-2 "Defensive Strategy (ST)"
    quadrant-3 "Vulnerability Minimization (WT)"
    quadrant-4 "Turnaround Options (WO)"
    "Strong R&D and Tech Accumulation" : [0.7, 0.8]
    "Low Manufacturing Costs" : [0.8, 0.6]
    "Tightening Environmental Regulations" : [0.6, 0.3]
    "Geopolitical Compliance Friction" : [0.9, 0.2]
    "Key Semiconductor Tools Blocked" : [0.2, 0.4]
```

### 4.2 Industry/Supply Chain Flowchart
```mermaid
flowchart LR
    subgraph Mining["Ingestion / Inflow"]
        raw1["Blogwatcher Scan (Daily Feed)"]
    end
    subgraph Refining["Processing / Refinement"]
        ref1["Metadata Ingestion & Noise Filtering"]
        ref2["Markdown Report Formatting"]
        raw1 --> ref1 --> ref2
    end
    subgraph Downstream["Analysis / Insight Extraction"]
        device1["read-all Local Parser Core"]
        ref2 --> device1
    end
    subgraph Target["Outputs / Actions"]
        semic["Investment Signals Output"]
        ev["JSON Signal Database Update"]
        device1 --> semic
        device1 --> ev
    end
```
