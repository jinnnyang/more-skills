## Known Environment Issues
- [ ] Needs a working Node.js runtime. If `node` or `npm` command is missing on Windows, prompt user to add Node to PATH.
- [ ] Mocking DOM via JSDOM is lightweight but does not support full web component lifecycle hooks. Avoid utilizing highly experimental or newer third-party Mermaid plugins that require browser-specific visual computations (like layout bounding boxes) during parsing.

## Success Patterns
- [ ] Prefer `--code` over `--input` for short to medium size diagrams to avoid workspace pollution and skip file deletions.
- [ ] Always check syntax first using `--validate-only` before prompting for rendering, which saves resources and keeps the flow clean.
- [ ] Wrap all labels or displayed text (nodes, states, relationships) in double quotes to prevent syntax errors with brackets, parenthesizes, colons, or other special characters.

## Failures & Anti-patterns
- [ ] Do not omit the diagram preamble (e.g. `graph TD`, `sequenceDiagram`) as this triggers a parser error.
- [ ] Avoid running commands directly from `scripts/` folder; always use the root wrapper `node cli.js` for automatic dependency resolution.
