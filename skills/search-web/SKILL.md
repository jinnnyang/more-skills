---
name: search-web
description: |
  Perform web searches across different modalities (pages, images, videos, papers, locations, terms) and inputs (texts, images). 
  Always use this skill whenever the user asks to "search the web", "look up images", "reverse image search", "search academic papers", "look up definitions", "search locations", or needs multi-format web searching capabilities.
---

# Web Search Skill

This skill provides multi-modal and multi-engine web searching capabilities (currently powered by Bing visual and web search) with a fake browser simulator that manages cookies, headers, and rate-limiting.

## Capabilities

1. **Multi-modal search**:
   - `pages by texts` (default): General web search.
   - `images by texts`: Search for images matching a description.
   - `videos by texts`: Search for videos matching a query.
   - `papers by texts`: Academic search filtering for publications (e.g. arXiv, IEEE, PubMed).
   - `locations by texts`: Places and map lookup.
   - `terms by texts`: Term/dictionary/Wikipedia definitions lookup.
   - `images by images`: Reverse image search using local files or remote image URLs.
   - `pages by images`: Find web pages/articles that contain or reference a given image.

2. **Fake Browser Simulation**:
   - Manages request headers and browser fingerprints to prevent access blocks.
   - Maintains a persistent cookie jar across sequential requests.

3. **Persistent Rate Limiting**:
   - Enforces a strict 20 Requests Per Minute (RPM) limit (at least 3-second spacing between requests) across separate CLI process runs using a local state file `.rate-limit-state.json`.

---

## How to Trigger & Run

Execute the CLI entrypoint script `cli.js` from the skill root directory:

```bash
node cli.js [output_type] [by] [input_type] [--engine name] [--query "val"] [--format raw|json|markdown]
```

### Syntax and Parameters

- **`output_type`** (positional): `pages` (default), `images`, `videos`, `papers`, `locations`, `terms`.
- **`input_type`** (positional): `texts` (default), `images`.
- **`--engine <name>`**: e.g., `bing`. If omitted, queries all active engines dynamically and aggregates results.
- **`--query <value>`** (or `-q <value>`): The query string. Can be specified multiple times for bulk queries.
- **`--format <raw|json|markdown>`**:
  - `raw` (default): Prints the raw unmodified HTML response from the search engine.
  - `json`: Prints structured JSON array of results:
    - Pages/videos/papers/etc. format: `[{"title": "Title", "alt": "Description/Snippet", "url": "URL"}]`
    - Images format: `[{"title": "Title", "alt": "Accessibility alt text", "url": "Direct Image URL"}]`
  - `markdown`: Prints formatted Markdown:
    - Pages/etc. formats: Numbered links `1. [Title](url) - *Snippet*`
    - Images formats: accessibility-compliant inline image tags: `![alt](url "title")`

### Input Image Resolution Rules (Reverse Image Search)
For reverse image search (`images by images` or `pages by images`), pass the image to `--query`:
- If starts with `file://`: Parsed as an absolute local path on disk.
- If starts with `http://` or `https://`: Parsed as a remote image web link.
- Otherwise: Checked for validity as a local file path.

---

## Examples

1. **General Text Search (Default to raw HTML output)**:
   ```bash
   node cli.js --query "SpaceX Starship"
   ```

2. **Get Search Results in Structured JSON**:
   ```bash
   node cli.js pages --format json --query "deep learning tutorials"
   ```

3. **Search Images by Text in Markdown**:
   ```bash
   node cli.js images --format markdown --query "cute kittens"
   ```

4. **Reverse Image Search (Find similar images by remote URL)**:
   ```bash
   node cli.js images by images --format json --query "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba"
   ```

5. **Reverse Image Search (Find web pages containing a local image)**:
   ```bash
   node cli.js pages by images --format json --query "file:///home/user/pictures/sample.jpg"
   ```

---

## Agent Guidance & Fallbacks

- **Empty results**: If search returns no results, the JSON format outputs `[]` (exiting with code 0). Do not treat this as a script error.
- **Network / SSL error**: If a network or handshaking error occurs, the script outputs an explicit `[AGENT GUIDANCE - FALLBACK STRATEGY]` message on stderr. Follow those instructions to retry or diagnose the network status.
