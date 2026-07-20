---
kind: context
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
  last_updated / last_verified : ISO-8601 WITH timezone offset (e.g. 2026-07-20T14:30:00+08:00)
                                  last_verified may also be the literal "SKIPPED".
-->

# Project Invariants & Context

> [!NOTE]
> This file contains invariants, credentials locations, environmental variables, and project constraints that must never break. 
> This document is strictly additive-only. Add corrections as new dated entries at the bottom.

## Project Description
- Brief overview: 

## Invariants & Rules
- Key architectural rules: 

## Environment & Build
- Env variables: 
- Build/Test commands: 

## Invariant Corrections Log
- None.
