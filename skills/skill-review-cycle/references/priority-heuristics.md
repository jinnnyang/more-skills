# Priority Heuristics

> How to decide P0 vs P1 vs P2 when reviewing a skill. Applied by Step 2 of the workflow. Update this file whenever a real review teaches you a new signal.

## The one-line test

For each candidate optimization, ask: **"If we do NOTHING about this, what breaks?"**

| Answer | Priority |
|---|---|
| "New users can't get past the first screen without loading references." | **P0** |
| "Correctness or maintainability regresses silently. There's no test guarding this." | **P1** |
| "It works but is embarrassing / inconsistent / harder to reason about than it should be." | **P2** |
| "A power user or Windows CRLF quirk trips over it once a month." | **P3** |

## Positive signals for P0 (first-screen ergonomics)

- SKILL.md introduces a technical enum or JSON field before the reader has a mental model of the skill.
- The workflow's "happy path" requires reading `references/` — it should be visible from SKILL.md alone.
- The user has to hop between 3+ files to answer "how do I run this once?".
- Version tags / rev labels used inconsistently across files (e.g., `v0.5-rev-C`, `rev-F`, `1.4.0` all in one skill).

## Positive signals for P1 (correctness / maintainability)

- **No tests** on pure-logic functions that encode important product decisions (classifiers, thresholds, parsers). Refactoring is a footgun.
- **Terminology drift**: the same concept is called different things in SKILL.md vs PROTOCOL.md vs scripts.
- **Feature added recently that hasn't run in the wild** — thresholds are guesses, no calibration log.
- **Silent side effects** — a "read-only preflight" that quietly writes to disk breaks its own contract.
- **Undocumented interaction contract** — SKILL.md says "batched clarify" without showing the JSON shape, letting different sessions invent divergent UIs.

## Positive signals for P2 (nice-to-have polish)

- Reference docs missing a concrete example that would save agents 5 minutes.
- Overly aggressive classifier / tag system that adds cognitive load without proportional benefit — but no evidence yet that it's actually harmful.
- A large single-file script (1000+ lines) that could be split — but tests exist and the file has clear sections.

## Positive signals for P3 (housekeeping)

- CRLF/LF warnings on every commit.
- Wording nits in trigger docs.
- One-word typos in comments.
- `.gitattributes` / `.gitignore` gaps.

## Anti-signals (do NOT elevate)

Skip or push down to P3 / "Rejected Alternatives" when you spot these:

1. **"It would be nicer if..."** with no user pain cited — that's a design preference, not a review finding.
2. **"We could add feature X"** — reviews are for tightening what exists, not adding new capabilities. If X is genuinely needed, open a separate design doc.
3. **"The code is complex."** — complexity by itself isn't a defect. Complexity + no tests + planned changes = P1. Complexity + tests + stable = **Do NOT Change**.
4. **"Personal style differences."** — semi-colons, quote style, one-liner vs multi-line — the linter / formatter handles these, not a review.
5. **"Missing something I'd add."** — restrain the urge to project your own writing style. Rewrites of stable content go into "Rejected Alternatives".

## Meta-signals about the REVIEW report itself

Your review report is bad if:

- ≥ 8 items in a single priority band → you didn't rank; you dumped. Split by second criterion (impact × cost) and demote low-ROI ones to P2/P3.
- No "Rejected Alternatives" section → you're not showing your work.
- No "Do NOT Change" section → you'll accidentally refactor something stable during landing.
- No file:line citation on any P0/P1 item → you're editorialising, not reviewing.
- No "Key Judgment Calls" → you're pretending decisions have obvious answers when they don't.

## Update this file when

- A real review discovers a new signal you didn't have language for.
- A priority you assigned turned out wrong in retrospect (P0 that should have been P2, or vice versa).
- A category of anti-signal shows up twice in different reviews.
