## Known Environment Issues
- [ ] High-latency on external domain fetching can trigger timeouts.
- [ ] Accessing local files sometimes fails due to encoding conflicts.

## Success Patterns
- [ ] Use subagents to perform web searches and summarize findings.
- [ ] Always execute a structured counter-review comparing opposing views.
- [ ] Ground all factual claims in specific sources using sequential citations.

## Failures & Anti-patterns
- [ ] Avoid circular verification: never use user's private data to discover info they already know.
- [ ] Avoid single-pass drafting: write the entire draft together rather than splitting sections.
- [ ] Do not invent URLs or resurrect sources dropped in prior phases.
