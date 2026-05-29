---
name: pretty-mermaid
description: Draw beautiful Mermaid diagrams (class, sequence, state, ER, XY charts, etc.) with syntax checking and SVG/PNG export capabilities. Use this skill whenever the user requests a diagram or when your response includes Mermaid code.
---

# When to use
- When the user explicitly requests a diagram (e.g., flowchart, sequence diagram, class diagram, state diagram, ER diagram, XY chart).
- When you need to use a diagram to illustrate complex logic, architecture, or processes.
- When you need to export Mermaid code to a beautiful image (SVG or PNG).

# When NOT to use
- When the user only needs a simple text list or table.
- When the user explicitly requests a different diagramming tool (e.g., PlantUML, Graphviz).

# Prerequisites
- **Node.js**: Must be installed on the user's system.
- **Automatic Setup**: The skill's root `cli.js` will automatically check for and install all required Node.js dependencies on its first execution. You do not need to run `npm install` manually.

# Workflow

1. **Select Diagram Type and Load Reference**
   - Choose the appropriate diagram type based on the user's request.
   - **MUST** read the corresponding reference file to understand syntax rules and see beautiful examples:
     - Flowchart: `references/flowchart.md`
     - Sequence Diagram: `references/sequence.md`
     - Class Diagram: `references/class.md`
     - State Diagram: `references/state.md`
     - ER Diagram: `references/er.md`
     - XY Chart: `references/xychart.md`
   - *Note: Any text that needs to be displayed MUST be enclosed in double quotes, and internal names for nodes/participants should be self-explanatory.*

2. **Validate Mermaid Code**
   - You can validate your Mermaid syntax directly using the code string without saving it to a temporary file:
     ```bash
     node <pretty-mermaid-path>/cli.js --validate-only --code "YOUR_MERMAID_CODE"
     ```
   - If the code is extremely large, you can save it to an absolute temporary path (e.g. `/absolute/path/to/temp.mmd`) and validate it:
     ```bash
     node <pretty-mermaid-path>/cli.js --validate-only --input /absolute/path/to/temp.mmd
     ```
   - If validation fails, check the detailed output, modify the syntax based on the error message/guidance, and re-validate until it passes.

3. **Preview and Confirm**
   - Output the validated Mermaid code to the user as a markdown code block for preview.
   - Proactively ask the user if they need any modifications, and cooperate with them to adjust the diagram until they confirm it's correct.

4. **Export Image (Optional)**
   - After user confirmation, ask if they want to export the diagram as an image, and what format (SVG or PNG) and theme they prefer.
   - Supported themes: `zinc-light`, `zinc-dark`, `tokyo-night`, `dracula`, `github-light`, `github-dark`.
   - Export directly from a code string:
     ```bash
     node <pretty-mermaid-path>/cli.js --code "YOUR_MERMAID_CODE" -o /absolute/path/to/output.png -t tokyo-night
     ```
   - Or export from a saved file:
     ```bash
     node <pretty-mermaid-path>/cli.js --input /absolute/path/to/temp.mmd -o /absolute/path/to/output.png -t tokyo-night
     ```
   - Inform the user where the image file has been saved.

5. **Complete Task**
   - If you created any temporary `.mmd` files in Step 2/4, **proactively delete them** to keep the workspace clean. If you used the `--code` parameter directly, no cleanup is needed!
   - Complete the task once the final assets are delivered.

# Examples

**Scenario: User asks for a simple login flowchart**

1. Read `references/flowchart.md` to understand the guidelines.
2. Formulate the Mermaid flowchart:
   ```mermaid
   graph TD
       start["Start"] --> input["Input Credentials"]
       input --> validate{"Validate"}
       validate -->|"Success"| home["Go to Home"]
       validate -->|"Fail"| error["Show Error"]
       error --> input
   ```
3. Run syntax validation:
   ```bash
   node c:/Users/jinnn/Documents/more-skills/skills/pretty-mermaid/cli.js --validate-only --code "graph TD; start[\"Start\"] --> input[\"Input Credentials\"]; input --> validate{\"Validate\"}; validate -->|\"Success\"| home[\"Go to Home\"]; validate -->|\"Fail\"| error[\"Show Error\"]; error --> input"
   ```
4. Output the code block for the user to preview.
5. User confirms and requests a PNG using the `tokyo-night` theme.
6. Run export:
   ```bash
   node c:/Users/jinnn/Documents/more-skills/skills/pretty-mermaid/cli.js --code "graph TD; start[\"Start\"] --> input[\"Input Credentials\"]; input --> validate{\"Validate\"}; validate -->|\"Success\"| home[\"Go to Home\"]; validate -->|\"Fail\"| error[\"Show Error\"]; error --> input" -o c:/Users/jinnn/Documents/more-skills/login.png -t tokyo-night
   ```
7. Inform the user of the saved PNG and complete the task (no temp files were created, so no cleanup is required!).

# Troubleshooting
- **`npm: command not found`**: Ensure Node.js is installed.
- **Dependency Installation Fails**: If the automatic setup fails, fall back to running `npm install` inside the `scripts` directory manually.
- **Syntax Check Fails**: Pay close attention to the error diagnostics printed by `cli.js`. Ensure all text inside node shapes, state labels, or ER relations are enclosed in double quotes.
