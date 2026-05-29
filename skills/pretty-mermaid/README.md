# `pretty-mermaid` Skill

> [!WARNING]
> This skill is being migrated to `more-skills` and will no longer be maintained as a standalone repository. Please use the version inside the [more-skills](https://github.com/jinnnyang/more-skills) repository.

Draw beautiful Mermaid diagrams (class, sequence, state, ER, XY charts, etc.) with syntax checking and SVG/PNG export capabilities.

## Features

- **Unified CLI Entry**: Run all validations and image exports via the root-level `cli.js`.
- **Automatic Setup**: Installs required NPM packages dynamically on first run.
- **Direct String Processing**: Support for passing Mermaid code directly via `--code` argument (avoids manual temporary file writing and cleanup in your workspace).
- **Expanded References**: Detailed drawing guides for flowcharts, sequence diagrams, class diagrams, state diagrams, ER diagrams, and XY charts.

## Prerequisites

- **Node.js**: Must be installed on the system.

## Command-Line Interface Usage

The primary entry point is the root `cli.js`.

```bash
node cli.js [options]
```

### Options:
- `-c, --code <code>`      Direct Mermaid code string to process.
- `-i, --input <file>`     Path to a `.mmd` file to process.
- `-o, --output <file>`    Path to save the generated output. Infers format (`.svg` or `.png`) from file extension.
- `-t, --theme <theme>`    Theme selection (e.g. `zinc-light` (default), `zinc-dark`, `tokyo-night`, `dracula`, `github-light`, `github-dark`).
- `-v, --validate-only`    Validates Mermaid syntax and exits. Does not generate any output image.

### Examples:

1. **Verify Syntax Only**:
   ```bash
   node cli.js --validate-only -c "graph TD; A[\"Start\"] --> B[\"Stop\"]"
   ```

2. **Render directly to PNG**:
   ```bash
   node cli.js -c "graph TD; A[\"Start\"] --> B[\"Stop\"]" -o output.png -t tokyo-night
   ```

3. **Render from an `.mmd` file**:
   ```bash
   node cli.js -i diagram.mmd -o output.svg
   ```

## References
- [Flowchart Reference](references/flowchart.md)
- [Sequence Diagram Reference](references/sequence.md)
- [Class Diagram Reference](references/class.md)
- [State Diagram Reference](references/state.md)
- [ER Diagram Reference](references/er.md)
- [XY Chart Reference](references/xychart.md)
