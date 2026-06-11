---
name: pretty-markdown
description: Automatically format and clean Markdown files. This skill parses the markdown, uses a multimodal LLM to generate accessibility descriptions (alt and title texts) for images, infers missing programming languages for code blocks, and cleans typography (like CJK spacing). Use when a user wants to beautify, format, or improve the accessibility of a Markdown document.
---

# Pretty Markdown Formatter

This skill programmatically formats Markdown files using `md2ast` and an OpenAI-compatible multimodal LLM to enrich the file content without altering its core meaning or original links.

## What it does
1. **Accessibility Enrichment**: Scans all `image` nodes. If an image lacks a descriptive alt text or title, the script fetches the image (locally or remotely), sends it to an LLM, and generates an accurate description.
2. **Code Language Inference**: Scans all `code` blocks. If a block is missing a language marker (e.g., ````javascript`), it asks the LLM to infer the language based on the syntax.
3. **Typography Cleanup**: Automatically inserts spacing between CJK characters and English words/numbers, and converts straight quotes to typographic quotes.

## How to trigger it
Invoke this skill when you want to run the formatter. The script is fully autonomous.

1. Ensure `OPENAI_API_KEY` is available in the environment, or instruct the user to create a `.env` file in the skill directory (`<workspace>/skills/pretty-markdown/.env`) containing:
   ```env
   OPENAI_API_KEY=your_key
   OPENAI_BASE_URL=https://api.openai.com/v1   # Optional
   OPENAI_MODEL_NAME=gpt-4o                     # Optional
   ```
2. Execute the CLI script:
   ```bash
   node c:/Users/jinnn/Documents/more-skills/skills/pretty-markdown/cli.js <input.md> [output.md]
   ```
   *(If `[output.md]` is omitted, it overwrites the input file in-place).*

## Agent Guidance
The script will output `[AGENT GUIDANCE]` explicitly to `stdout`/`stderr` when it completes or fails. Follow those instructions closely:
- **On Success**: Let the user know the file has been successfully formatted and enriched.
- **On Error**: Read the fallback strategy in the error output to troubleshoot (e.g., missing API keys or invalid syntax).

## Next Step: Fact-Checking or Document Rendering
After this skill completes, you might suggest reviewing the factual accuracy of the markdown or converting it to another format.

```
Formatting complete! The markdown has been enriched with image descriptions and code languages.

Options:
A) fact-checker — Run fact verification on the newly formatted document
B) pdf-creator — Export the clean markdown to a PDF
C) No thanks — The formatted markdown is exactly what I needed
```
