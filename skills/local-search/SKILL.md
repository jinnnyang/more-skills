---
name: local-search
description: Use when finding files by name/path or searching inside file contents on the local Windows machine. Faster than `search_files` / `ls -R` / `find` / ripgrep when the search would touch many directories, because it uses live indexes (Voidtools Everything for filenames, AnyTxt for full-text incl. PDF/docx/pptx). One CLI (`local-search`) with self-explanatory subcommands - `files` (filename/path/ext, sub-second across millions of files), `text` (full-text incl. PDF/docx/pptx/code, keyword highlighting), `recent` (recently modified files, human-friendly time windows like `1h`/`today`/`30min`), `extract` (turn PDF/docx/pptx into plain text using AnyTxt's index — instant, no marker-pdf/OCR needed), `sync` (force AnyTxt to reindex a folder after writing new files so agent can search them immediately), `doctor` (health-check both backends with actionable fix hints). Default output is a markdown table; `--format json`/`csv` for machine consumption. Windows only.
version: 0.1.1
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [search, files, filesystem, indexing, everything, anytxt, windows, pdf, docx, pptx, extract, grep, fulltext, ripgrep-alternative, local-search, index]
    related_skills: [ocr-and-documents, hermes-agent, hermes-windows-troubleshooting]
---

# local-search

Fast unified local file and full-text search on Windows, backed by **Voidtools Everything** (filenames, path, ext) and **AnyTxt** (full-text content + already-extracted PDF/docx/pptx text).

One CLI, six self-explanatory subcommands. All output is markdown-first for direct agent consumption; `--format json` for scripting.

## When to Use

Reach for `local-search` whenever a task involves *searching the local Windows filesystem*.

| Situation | Right command |
|---|---|
| "Where is that config file?" | `local-search files <name>` |
| "Which PDFs mention this term?" | `local-search text <term> -e pdf` |
| "What did I edit in the last hour?" | `local-search recent --within 1h` |
| "Read this PDF's text" | `local-search extract <path>` |
| "I just wrote files, agent can't find them" | `local-search sync <folder>` |
| "Search across ALL indexed drives quickly" | `local-search files` / `text` (no `-p`) |

**Prefer this skill over:**
- `search_files` tool — that walks the FS live and gets slow across many dirs
- `terminal` + `find` / `ls -R` — no index, orders of magnitude slower
- `terminal` + ripgrep — great for a known directory tree, but `local-search text` is faster when the tree is large and the file is already indexed by AnyTxt

**Prefer other tools when:**
- The path is deep inside `.venv` / `node_modules` / build artifacts (Everything indexes everything, may return more noise than a focused rg)
- You need multi-line pattern matches or code-aware search — use `ripgrep` / language-aware tools
- The file is NOT yet indexed and you can't afford a `sync` wait — read directly

## Relationship to `ocr-and-documents`

Both skills extract text from PDF/docx/pptx. Use `local-search extract` when:

- The file is **already indexed** by AnyTxt (free, instant, uses cached extraction)
- You just want plain text, not layout / page numbers / images

Use `ocr-and-documents` when:

- The file is **not indexed** or is a scan needing OCR
- You need precise layout, per-page control, or structured extraction

They're complementary. Try `local-search extract` first; fall back to `ocr-and-documents` when the file isn't indexed or the text quality is insufficient.

## Install

**One-time (or after updating this skill's source):**
```bash
cd C:\Users\jinnn\Documents\more-skills\skills\local-search
uv tool install --editable . --force
```

`uv tool install --editable` puts the `local-search` CLI on PATH globally while keeping the source live-editable — edits to `src/` take effect immediately.

**Verify:**
```bash
local-search --version    # → local-search, version 0.1.1
local-search doctor       # → both backends OK
```

## Commands

### `files` — filename / path / extension search (Everything)

```bash
local-search files "config"                             # anywhere named 'config'
local-search files "SKILL.md" -e md -n 5                # top 5 .md files
local-search files "test_.*\.py" --regex                # regex over filenames
local-search files "hermes" --match-path                # match against full path
local-search files "config" -p C:\dev --sort modified --desc
local-search files "*.py" --format json                 # machine-readable
```

Options: `-n LIMIT`, `--offset N`, `-p PREFIX_PATH`, `-e EXT[,EXT]`, `--sort {name,path,size,ext,modified,created,accessed}`, `--desc`, `--format {md,json,csv}`, `--regex`, `--match-path`, `--case`, `--whole-word`.

### `text` — full-text content search (AnyTxt)

```bash
local-search text "OpenAI API key"                      # snippets with **highlight**
local-search text "hermes" -e md -n 5                   # scope to markdown files
local-search text "faster-whisper" --count-only         # just the total (cheap)
local-search text "GPT" --no-snippet -n 50              # skip snippets for speed
local-search text "hermes" -p C:\Users\jinnn\Documents  # prefix-scope
```

Options: same `-n/--offset/-p/-e/--sort/--desc/--format` as `files`, plus `--snippet/--no-snippet`, `--count-only`.

### `recent` — recently modified files (Everything)

```bash
local-search recent --within 1h                         # last hour
local-search recent --within today                      # since midnight
local-search recent --within 30min -e py                # 30 min, .py only
local-search recent --within 7d -p C:\Users\jinnn\Desktop
local-search recent --within "dm:2026-07-01..2026-07-16"  # Everything native
```

Accepted `--within` values: `1h/hour`, `today/1d/day`, `1w/week`, `month/1mo`, `<N>min`, `<N><s|h|d|w>`, or any raw `dm:...` Everything syntax.

Sort is fixed to `modified desc` — that's the whole point of this command.

### `extract` — dump AnyTxt's already-extracted plain text

```bash
local-search extract "C:\path\to\file.pdf"                       # full text
local-search extract "file.pdf" --head 5000                      # first 5000 chars
local-search extract "file.pdf" --count-only                     # just size
local-search extract "file.pdf" --strip-page-marks -o out.txt   # clean + write
local-search extract 2879675253150734652                         # by FID (if you have one)
```

**Key insight**: this is nearly free because AnyTxt already extracted the text at index time. Use it for any indexed PDF/docx/pptx before reaching for marker-pdf / OCR.

Passing a filesystem path triggers a fast FID lookup. If the file isn't indexed, you'll get a `BackendUnavailable` with a `local-search sync ...` fix hint.

### `sync` — force AnyTxt to (re)index a folder

```bash
local-search sync C:\Users\jinnn\Desktop\my-new-folder
```

Blocks until done, then verifies by counting files under that folder. Reports "0 files indexed" if the folder isn't in AnyTxt's index configuration (Menu → Options → Index) — since AnyTxt's `SyncIndex` gives no feedback on its own, this is the only way to know.

### `doctor` — health check both backends

```bash
local-search doctor                # rich table (human)
local-search doctor --format json  # structured (scripting)
```

Reports each backend's connectivity, response time, and an actionable fix hint when broken. Exit code 0 iff both are OK.

## Common Pitfalls

1. **Everything is in Session 0** (service running under LocalSystem, not your interactive session) → `everyfile` IPC silently fails. `local-search doctor` detects this and points at the fixer script. Run:
   ```
   powershell -ExecutionPolicy Bypass -File "C:\Users\jinnn\Documents\more-skills\skills\local-search\scripts\ensure-everything-user-session.ps1"
   ```
   Idempotent — safe to run any time.

2. **AnyTxt `filterDir=""` only searches C drive.** The server rewrites empty `filterDir` to `"C:"`. If you have data on D/E/F drives, pass `-p D:\` explicitly (once per drive) to search there.

3. **AnyTxt only indexes what you tell it to.** If `local-search text` returns 0 results for something that clearly exists on disk, check AnyTxt Menu → Options → Index. `local-search sync <folder>` triggers indexing but only for folders already configured.

4. **`total` vs page size** — the JSON output includes `"truncated": true` when there are more matches than the current page. Bump `-n` or paginate with `--offset` to see more.

5. **Regex is Everything-flavored, not PCRE.** No lookahead / lookbehind. Use `.` `*` `+` `?` `[]` `|` `()`. The CLI now pre-validates with Python's `re.compile` — bad syntax (e.g. `test[`) fails fast with `[error] Invalid regex ...` instead of silently returning 0 hits. For serious regex power, pipe the output paths to `ripgrep`.

6. **AnyTxt full-text is slow relative to Everything.** Expect 500–2000 ms per query on a large index vs 20–150 ms for `files`. Use `text --count-only` when you just need a count — it's ~10x faster than `text --limit N`.

7. **PDF page markers**: `extract` output on PDFs contains `📄 P 1 ...📄 P 2 ...` markers between pages. Pass `--strip-page-marks` to remove them.

8. **Empty QUERY safety rail.** `files "" -n 1` used to return a random slice of the entire 4M-file index (usually a typo, never what was wanted). The CLI now refuses an empty QUERY unless `-p` or `-e` is present. Explicit `files "" -p C:\Users\me\Desktop` or `files "" -e py` still works.

9. **Large `--format json` output vs Hermes' terminal truncation.** `terminal` (and `execute_code`'s `terminal()` wrapper) caps stdout at ~20 KB and inserts a `[OUTPUT TRUNCATED — N chars]` marker in the middle of the JSON, breaking `json.loads` with `Invalid control character at ...`. When paging with `-n 500+` or dumping a whole scope, **redirect to a file** and read it back, don't parse stdout directly:
   ```bash
   local-search files "" -p D:\data --format json -n 5000 > out.json
   ```
   Then load `out.json` (300 KB parses fine with strict `json.load`).

10. **Windows path escaping in git-bash / MSYS shell.** Hermes' `terminal` runs bash on Windows, so a literal `C:\Users\name` inside a double-quoted string can trigger bash escape processing (`\U`, `\n`, `\t` are risky). Two safe forms:
    - Native, double-escape: `"C:\\Users\\jinnn\\Desktop"`
    - MSYS style: `/c/Users/jinnn/Desktop`

    Single-quoted `'C:\Users\jinnn\Desktop'` also survives, since bash doesn't process backslash escapes inside single quotes. When agents call this CLI via `execute_code`'s `terminal()`, use quadruple backslash in the Python string literal so the eventual bash argument has doubled backslashes.

11. **Duplicate hits from mirrored trees.** If the same content exists in multiple locations (e.g. `hermes-merge/…` + `hermes-backup/…` + `.hermes/profiles/iris/…`), every match appears 2-3× with identical size + mtime. There is no `--dedupe` flag yet — narrow with `-p` to the canonical location, or dedup on `(name, size)` in your consumer.

12. **Relative paths in `-p`.** Since v0.1.1 the CLI resolves `-p .`, `-p ~/Desktop`, and `-p ../foo` to absolute paths before sending to Everything/AnyTxt. Previously these silently returned 0 hits (both backends do prefix match on absolute paths).

13. **MSYS/git-bash path style (`/c/Users/...`) is auto-converted.** Since v0.1.1 the CLI recognizes `/c/Users/jinnn/Desktop` and rewrites it to `C:\Users\jinnn\Desktop` before path resolution. In earlier builds this silently became `C:\c\Users\...` (garbage) and returned 0 hits. Hermes' `terminal` runs bash on Windows, so this style is common — both `native "C:\\Users\\me"` and `msys "/c/Users/me"` now work.

14. **`~` inside DOUBLE quotes is NOT expanded by bash — use single quotes or `$HOME`.** The CLI expands `~` on its own (`Path.expanduser`), but bash gets first crack at the arg. `local-search files x -p "~/Desktop"` sends the literal string `~/Desktop` (which the CLI then expands correctly), while `local-search files x -p '~/Desktop'` also works — both are safe. But `-p ~/Desktop` (no quotes) is bash-expanded to your HOME before the CLI ever sees it, which also works. The risky case is nested quoting inside `execute_code`'s `terminal()` wrapper — prefer explicit `$HOME/Desktop` or an absolute path there.

15. **`text` and `text --count-only` refuse an empty QUERY.** Same rationale as `files ""` — a content search for the empty string on a 230 000-file index would take minutes and match everything. Pass an explicit phrase.

## Verification Checklist

After install, run in this order:

```bash
local-search --version                                  # → 0.1.1
local-search doctor                                     # → both ✅
local-search files "SKILL.md" -n 3                      # some md hits
local-search text "hermes" -e md --count-only           # some count
local-search recent --within 30min -n 3                 # recent files
```

If any step fails, the error message names the backend and includes a fix hint.

## Registration (per-agent)

This skill lives at `C:\Users\jinnn\Documents\more-skills\skills\local-search\` — a shared source location, NOT inside any single Hermes profile. To make it visible to a specific agent:

```
mklink /J "C:\Users\jinnn\.hermes\profiles\<profile>\skills\system-administration\local-search" ^
          "C:\Users\jinnn\Documents\more-skills\skills\local-search"
```

Junction points are hard-link-like on Windows: edits to the source appear instantly in every registered profile. `uv tool install --editable` already exposes the CLI globally, so registration is only for skill *discovery*, not CLI availability.
