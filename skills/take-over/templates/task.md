---
kind: task
version: 1
last_updated: {{TIMESTAMP}}
last_verified: {{TIMESTAMP}}
last_agent: {{AGENT}}
last_writer: migration
session_id: {{SESSION_ID}}
status: in-progress
---

<!--
Frontmatter enums (see references/frontmatter-fields.md for full details):
  kind         : context | task | walkthrough | questions | plan | review
  status       : in-progress | blocked | phase-complete | archived   (NOT 'complete')
  last_writer  : hand-off | take-over | user | migration

Checklist marker legend:
  `[ ]`  todo         `[/]`  in-progress
  `[x]`  done         `[!]`  agent-side blocker (waiting on tool/build, NOT a human question)

Human-answered blockers live in questions.md, not here.
-->

# Current Tasks

## Now
<!-- The first item under Now is what the next agent picks up. -->

## Next
<!-- Ordered list of what to do after Now. -->

## Done
<!-- Move completed items here to keep an audit trail; hand-off may prune later. -->
