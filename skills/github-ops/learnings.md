## Known Environment Issues
- [ ] Windows Git/credentials helper popup can freeze programmatic CLI subprocesses. Use environment variables (e.g. `GITHUB_TOKEN`) to authenticate.

## Success Patterns
- [ ] Use `NOJIRA:` prefix in PR titles when bypassing JIRA integration checks.
- [ ] Programmatically format outputs into JSON using `--json` option when processing datasets.

## Failures & Anti-patterns
- [ ] Avoid running commands that trigger interactive prompts (e.g., raw `gh auth login` without flags) in background subagents.
- [ ] Do not commit changes directly to the main branch; always create a feature branch first.
