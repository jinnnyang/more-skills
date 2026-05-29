# Skill Creator (Meta-Skill)

`skill-creator` is a meta-skill within the Antigravity agent framework designed to automate the creation, testing, iteration, evaluation, and optimization of other agent skills. It transforms the manual scripting of agent behaviors into an engineered, benchmarked, and self-improving development lifecycle.

---

## 🛠️ Core Capabilities

1. **Intelligent Capture & Interview**: Guides the agent through capturing user intent, designing task-focused prompts, and defining target capabilities.
2. **Iterative Evaluation**: Automates parallel runs (with-skill vs. baseline) to benchmark changes qualitatively and quantitatively.
3. **Interactive Review**: Exposes a web-based/static HTML Review Viewer (`generate_review.py`) showing comparative outputs, assertion pass rates, and timing.
4. **Trigger Optimization**: Optimizes skill metadata descriptions using an automated feedback loop (`run_loop.py`) to prevent under-triggering.
5. **Static Design Linting**: Restricts and enforces design consistency, environment check standards, and memory management rules before compiling.

---

## 📐 Key Design Patterns (Phase 2+)

The meta-skill instructs and enforces three key architectural patterns for all downstream skills:

### 1. Progressive Discovery (Pre-flight Checks)
Instead of executing fragile, hardcoded platform-probing scripts, agents utilize a three-stage native platform verification:
1. **Cognitive Pause**: Output a plan detailing what needs verification before executing commands (e.g., `Plan: 1. Identify OS. 2. Verify dependencies.`).
2. **Adaptive Probing**: Run native, lightweight commands (`ver`, `uname -a`, or `$PSVersionTable`) to establish coordinates.
3. **Contextual Resolution**: Dynamically use platform-specific locators (`which`, `where`, `Get-Command`) to verify required CLI binaries or environment credentials.

### 2. Differential Guidance Density (Agent Guidance)
Scripts output proactive steering instructions directly to `stderr` and JSON `"guidance"` keys:
- **Happy Path (Success)**: Minimal guidance (1-line maximum, e.g., `[AGENT GUIDANCE] SUCCESS. Next: parse result.json.`) to avoid cognitive noise.
- **Error/Degradation Path**: Detailed, structured alternative commands and fallbacks (`[AGENT GUIDANCE — FALLBACK STRATEGY]`) showing exactly how to recover.

### 3. Cross-Session Memory (`learnings.md`)
Maintains evolution history for stateless agents:
- **Auto-Load**: The execution framework injects the contents of `learnings.md` directly into the agent's context on start; the agent does *not* need to spend tool calls to read it.
- **Strict Structure**: Standardized into three sections: `## Known Environment Issues`, `## Success Patterns`, and `## Failures & Anti-patterns`.
- **Append-Write & Compression**: The agent appends new findings at wrap-up. If the file exceeds 50 lines / 2KB, `quick_validate.py` triggers an actionable compression warning directing the agent to merge duplicates and prune solved issues.

---

## 📁 Directory Structure

```
skill-creator/
├── SKILL.md                 # Enforces skill-writing rules & execution lifecycle
├── LICENSE.txt              # License information
├── agents/                  # Standard operating manuals for execution subprocesses
│   ├── grader.md            # Assertion checks evaluator
│   ├── analyzer.md          # Benchmark results & health auditor
│   └── comparator.md        # Blind A/B comparison evaluator
├── scripts/                 # Core automation tools
│   ├── quick_validate.py    # Design linter (Checks Pre-flight, learnings, and Guidance)
│   ├── run_eval.py          # Cross-platform stream evaluator (Windows compatible)
│   ├── package_skill.py     # Tarball packager (supports --dry-run)
│   ├── improve_description.py # Token-optimized description compressor
│   └── utils.py             # YAML and frontmatter parsing utility
└── eval-viewer/             # Human-in-the-loop comparison dashboard
    └── generate_review.py   # Standalone web & static HTML generator
```

---

## 🚀 Usage Guide

### 1. Design Validation
Run the static linter to check compliance with the schema and design guidelines:
```bash
python scripts/quick_validate.py <path-to-skill-directory>
```
*Design issues like missing pre-flight checks, absent learnings.md, or lack of `[AGENT GUIDANCE]` in scripts output warnings rather than failing the build (non-blocking validation).*

### 2. Running Evaluations
Verify skill capabilities against test cases (cross-platform non-blocking streaming output):
```bash
python scripts/run_eval.py --help
```

### 3. Packaging Skills
Package a skill directory for distribution:
```bash
python scripts/package_skill.py <path-to-skill-directory> [--dry-run]
```

---

## 📅 CHANGELOG & Version Switching

| Version | Key Changes & Milestones | Commit Hash |
| :--- | :--- | :--- |
| **v2.1.0** (Current) | Implemented Phase 2.1 refinements (learnings.md auto-load, compression templates, `claude` CLI state and network checks). | `266c4c7` |
| **v2.0.0** | Major architectural overhaul: Integrated Pre-flight checks, Agent Guidance protocols, and full Windows cross-platform compatibility (async stream daemon threads, encoding fixes). | `62ea459` |
| **v1.0.0** (Legacy) | Base setup & early script execution workflow before optimization patterns. | `b9e19e6` |

### 🔄 How to Switch Versions

To inspect or fall back to previous major versions, run the checkout commands below:

*   **Switch to Legacy `v1.x` (Before Agent Guidance & Windows compatibility overhaul)**:
    ```bash
    git checkout -b v1-legacy b9e19e6
    ```

*   **Switch to Initial `v2.0.0` (Before Phase 2 & 2.1 design refinement feedback)**:
    ```bash
    git checkout -b v2.0.0-initial 62ea459
    ```

*   **Return to the Latest Stable Version (`v2.1.0`)**:
    ```bash
    git checkout more
    ```
