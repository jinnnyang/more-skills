# Phase 1: Planning & Approval

You are now in the Planning Phase. Your goal is to research the codebase and write a technical proposal for the user to review.

## ⛔ Guardrails (CRITICAL)
- **NO MUTATIONS**: You may use `view_file`, `grep_search`, `list_dir`, and read-only bash commands (like `cat`, `ls`). You may NOT use `write_to_file` (except for the plan itself), `replace_file_content`, or mutating commands (like `npm install`, `rm`, `mv`).
- **SANDBOX EXCEPTION**: You are permitted to write experimental code (Spikes/PoCs) ONLY if it is strictly confined to a `scratch/` directory. This allows you to test library APIs or verify assumptions without dirtying the main codebase.
- **NO ASSUMPTIONS**: If a critical detail is missing from the user's prompt, do not guess. Document it as an "Open Question" in the plan.

## Execution Steps

1. **Research**: Spend time looking at the codebase to understand the current state.
2. **Draft the Plan**: Create a new file (e.g., `plan.md` or `implementation_plan.md` in the workspace/artifact directory).
   - You MUST use the template defined in `../templates/plan.md`.
3. **Request Approval**: Stop your execution loop. Present the plan to the user and explicitly ask: *"Please review the plan. Let me know if you approve or if you'd like any changes before I begin."*

## Handling User Feedback
- If the user approves without changes, proceed to **Phase 2: Task Decomposition**.
- If the user provides feedback or requests changes:
  1. Record their feedback using the template in `../templates/review.md` to keep a history of architectural decisions.
  2. Update the `plan.md` file accordingly.
  3. Request approval again.
