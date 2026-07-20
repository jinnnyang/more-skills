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

# Project Invariants & Context

> [!NOTE]
> This file contains invariants, credentials locations, environmental variables, and project constraints that must never break. 
> This document is strictly additive-only. Add corrections as new dated entries at the bottom.
>
> **Provenance-tag every invariant** (see PROTOCOL §11a). Prefix each bullet with `[git:<sha>]`, `[user:<YYYY-MM-DD>]`, `[test:<name>]`, `[inferred:<session-id>]`, or `[unknown]`. Untagged bullets erode the multi-hop trust health score. If you don't know the source, `[unknown]` is honest — do NOT fabricate a `[git:*]` tag.

## Project Description
- Brief overview: 

## Invariants & Rules
- Key architectural rules (example: `- [git:abc1234] Auth tokens are JWT with 24h expiry.`): 

## Environment & Build
- Env variables (example: `- [user:2026-07-17] DATABASE_URL is read from .env.local`): 
- Build/Test commands: 

## Invariant Corrections Log
- None.
