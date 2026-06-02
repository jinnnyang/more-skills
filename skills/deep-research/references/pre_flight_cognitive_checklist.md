---
name: pre-flight-cognitive-checklist
description: Mandatory pre-flight cognitive constraint checklist. Prevents reflexive "web_search" invocation by enforcing a "Skills & Tools First" methodology over primitive ad-hoc searching.
author: Meta-Research Governance
version: 2.0
tags: [methodology, cognitive-control, pre-flight]
---

# 🛫 Pre-flight Cognitive Checklist

## 🎯 Purpose
To prevent the "Data without Structure" anti-pattern where agents impulsively fire search queries without a foundational research framework. This checklist enforces the **"Skills over Primitives"** doctrine, ensuring maximum leverage of specialized environments before resorting to generic web searches.

## 🔒 Mandatory Pre-flight Verification (DO NOT SKIP)

### □ 1/5 Skill & Capability Matrix Audit
- [ ] **Ecosystem Scan**: I have evaluated my available `<skills>` and loaded MCP servers. Highly relevant skills for this exact task include: `[WRITE EXACT SKILL NAMES HERE or 'None']`.
- [ ] **Documentation Review**: For the specialized skills listed above, I have executed `view_file` on their `SKILL.md` (if unfamiliar) to grasp their precise I/O parameters and prerequisites.
- [ ] **Activation Decision**: I have explicitly decided which skill MUST be activated as the primary engine for this task. Target Skill(s) to activate: `[WRITE SKILL NAMES HERE]`.

### □ 2/5 Local & Proprietary Data Triage
- [ ] **Local Archive Check**: I have verified if historical research archives exist locally (`$HOME/projects/`) that can serve as a baseline.
- [ ] **Subscription Audit**: I have checked if targeted data streams (e.g., `blogwatcher`, internal API dumps) are already available in the workspace.
- [ ] **MCP Data Extraction**: I have confirmed if existing MCP tools can pull the required structured data directly (e.g., querying an SQL database vs scraping a website).
- [ ] **Primitive Search Fallback**: I acknowledge that raw `web_search` is only authorized if ALL the above proprietary and local avenues are exhausted or insufficient.

### □ 3/5 Skeleton Architecture & Cognitive Scaffolding
- [ ] **Focal Decomposition**: The core research objective has been aggressively pruned into ≤ 3 high-density focal questions.
- [ ] **Adversarial Evidence Requirement**: For each focal question, I have defined a dual-evidence standard (requiring both supporting and contradicting data points).
- [ ] **Output Topology**: The final deliverable structure (e.g., 7-Chapter Corporate Report, SWOT, JSON schema) is explicitly mapped.
- [ ] **Visualization Strategy**: I have determined if the output requires localized plotting tools, fallback Mermaid diagrams, or SMIS-compliant multimedia integration.

### □ 4/5 Tool Orchestration & Pipelining
- [ ] **Intentionality Over Habit**: Tool selection is strictly driven by the data topology requirements, deliberately suppressing the reflex to use `web_search`.
- [ ] **Execution Sequencing**: The tool invocation chain is logically sequenced (e.g., `Resolve IDs` → `Fetch Proprietary DB` → `Fallback Web Search`).
- [ ] **Subagent Delegation**: Tasks requiring deep recursive exploration or massive I/O have been cleanly partitioned for subagent delegation.

### □ 5/5 Boundary Definitions & Termination Thresholds
- [ ] **Scope Containment**: I have explicitly listed out-of-scope domains to prevent infinite rabbit holes and token waste.
- [ ] **Assumption Tagging**: Unverifiable hypotheses and blind spots are pre-tagged.
- [ ] **Stop Loss Trigger**: I have set a rigid termination condition (e.g., "Stop searching and begin synthesis after extracting 3 primary peer-reviewed sources or failing 2 targeted query permutations").

## ⚠️ Violation Penalties
Bypassing this checklist and jumping straight into primitive tool execution will result in:
- A 50% penalty on structural integrity scoring.
- Severe waste of proprietary data channels and API quotas.
- Mandatory task abortion and rework.

## 📝 Operating Protocol
Before initiating any new research vector, the Lead Agent MUST copy this checklist into its internal thought process (Chain of Thought), check off every single item, and document the findings. Only upon reaching 100% completion is the first tool invocation authorized.
