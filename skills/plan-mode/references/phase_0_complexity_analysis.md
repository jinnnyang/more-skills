# Phase 0: Complexity Analysis

Before taking any action, you must determine if the user's request warrants the full `plan-mode` workflow or if it can be executed directly.

## Evaluation Matrix

Ask yourself the following questions:
1. **Scope**: Does this change affect more than one file or function?
2. **Architecture**: Does this change introduce new dependencies, database schemas, or architectural patterns?
3. **Ambiguity**: Is the user's request underspecified? Does it require you to make significant design decisions?
4. **Risk**: Could this change break existing core functionality or introduce security vulnerabilities?

## Decision Routing

### Route A: Direct Execution (Simple)
If the answer to ALL of the above questions is **No** (e.g., "fix a typo", "change the button color to red", "format this JSON"):
- Do not create a plan.
- Do not ask for permission.
- **Action**: Execute the fix immediately and summarize what you did.

### Route B: Invoke Plan-Mode (Complex)
If the answer to ANY of the above questions is **Yes**, or if the user explicitly typed words like "design", "plan", "proposal", or "architecture":
- **Action**: Proceed immediately to **Phase 1: Planning**. Do not write any code yet.

> **Note**: If the user explicitly asks you to "just do it" or "skip the plan", you should respect their wish and take Route A, but briefly warn them of the risks if the task is highly complex.
