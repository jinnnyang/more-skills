# Priority heuristics

> How to decide P0 vs P1 vs P2 when reviewing a skill. Applied in Step 2 of the workflow. Update this file whenever a real review teaches you a signal you didn't have a name for yet.

## The one-line test

For each candidate optimization, ask what would happen if the review did nothing about it. The answer usually maps cleanly onto a priority:

| Answer | Priority |
|---|---|
| New users can't get past the first screen without loading references. | **P0** |
| Correctness or maintainability regresses silently. There's no test guarding this. | **P1** |
| It works, but it's embarrassing, inconsistent, or harder to reason about than it should be. | **P2** |
| A power user or a Windows CRLF quirk trips over it once a month. | **P3** |

## Positive signals for P0 (first-screen ergonomics)

- SKILL.md introduces a technical enum or JSON field before the reader has a mental model of the skill.
- The "happy path" of the workflow requires reading `references/` — it should be visible from SKILL.md alone.
- The user has to hop between three or more files to answer "how do I run this once?"
- Version tags and rev labels are used inconsistently across files (`v0.5-rev-C`, `rev-F`, `1.4.0` all showing up in one skill).
- **The `description:` block in SKILL.md's YAML frontmatter reads like AI product copy.** `skills_list()` shows this string to the agent *before* it decides whether to load the skill, so its tone lands earlier than SKILL.md L1. When you review a skill, read the frontmatter first — not last. (Learned the hard way on `hand-off` 2026-07-20: the humanize pass rewrote SKILL.md body and every reference, but missed the frontmatter until end-of-cycle sanity check. Fix landed as commit `590a61c` on `hand-off/SKILL.md`.)

## Positive signals for P1 (correctness and maintainability)

- **No tests** on pure-logic functions that encode important product decisions — classifiers, thresholds, parsers. Refactoring anything in this state is a footgun.
- **Terminology drift.** The same concept is called different things in SKILL.md, PROTOCOL.md, and the scripts.
- **A recently-added feature that hasn't run in the wild.** Thresholds are guesses, no calibration log, no way to know if it's calibrated to reality.
- **Silent side effects.** A "read-only preflight" that quietly writes to disk breaks its own contract; that's a P1 correctness bug in disguise.
- **Undocumented interaction contract.** SKILL.md says "batched clarify" without showing the JSON shape, and different sessions end up inventing divergent UIs.

## Positive signals for P2 (nice-to-have polish)

- Reference docs missing a concrete example that would save the next agent five minutes.
- An aggressive classifier or tag system that adds cognitive load without proportional benefit, but no direct evidence yet that it's harming anyone.
- A large single-file script (1000+ lines) that could be split — but tests exist and the file has clear sections, so splitting is preference more than need.

## Positive signals for P3 (housekeeping)

- CRLF / LF warnings on every commit.
- Wording nits in trigger docs.
- One-word typos in comments.
- `.gitattributes` or `.gitignore` gaps.

## Anti-signals — don't elevate

Push these down to P3 or to "Rejected Alternatives" when you spot them:

1. **"It would be nicer if..."** with no user pain cited. That's a design preference, not a review finding.
2. **"We could add feature X."** Reviews are for tightening what exists, not for adding capabilities. If X is genuinely needed, open a separate design doc for it.
3. **"The code is complex."** Complexity on its own isn't a defect. Complexity plus no tests plus planned changes is a P1. Complexity plus tests plus stable behavior is a **Do NOT Change**.
4. **"Personal style differences."** Semicolons, quote style, one-liner versus multi-line — the linter or formatter handles those. Reviews shouldn't.
5. **"Missing something I'd add."** Resist the urge to project your own writing style onto stable content. If it belongs anywhere, it belongs in "Rejected Alternatives".

## Meta-signals about the review report itself

A review report has problems when:

- Any single priority band has eight or more items. That's a dump, not a ranking. Split by a second criterion (impact × cost) and push the low-ROI ones down to P2 or P3.
- There's no "Rejected Alternatives" section. You're not showing your work; readers can't tell what you considered and dismissed.
- There's no "Do NOT Change" section. You'll refactor something stable during landing without meaning to.
- No P0 or P1 item cites a `file:line`. That means the ranking is opinion, not observation.
- There are no "Key Judgment Calls". You're pretending decisions have obvious answers when they don't.

## Update this file when

- A real review discovers a signal you didn't have language for.
- A priority you assigned turns out wrong in retrospect — a P0 that should have been P2, or the other way around.
- A category of anti-signal shows up twice across different reviews.
