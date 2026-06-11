# Phase 3: Execution Loop

You are now executing the tasks defined in `task.md`.

## The Sync Loop (CRITICAL)

To prevent context drift and ensure visibility, you MUST follow this loop for EVERY task:
1. **Read/Claim**: Update `task.md` to mark the current task as In Progress (`[/]`).
2. **Execute**: Perform the code changes (using `write_to_file`, `replace_file_content`, etc.) or run the necessary commands.
3. **Verify locally**: Make sure the syntax is correct and the specific file compiles/lints.
4. **Mark Complete**: Update `task.md` to mark the task as Done (`[x]`).
5. **Next**: Move to the next `[ ]` task in the list.

**SYNC HEURISTIC**: For significant architectural changes, update `task.md` synchronously. However, for a sequence of minor, low-risk refactors (e.g., updating 3 variables in the same file), you may group them into a single logical step to avoid unnecessary write overhead.

## Handling Blockers & Architectural Pivots
If you encounter a major error, a missing dependency you didn't plan for, or realize the architecture plan is fundamentally flawed:
1. **Stop execution.**
2. **Clean the Workspace**: You MUST revert or stash any half-written, unapproved code (`git stash` or `git checkout -- .`) to prevent corrupting the project state.
3. **Mark the task**: Note the failure in `task.md`.
4. **Return to Planning**: Revert to **Phase 1: Planning**, write an addendum or update the plan, and explicitly request human approval for the pivot. Do not silently rewrite the entire architecture.
