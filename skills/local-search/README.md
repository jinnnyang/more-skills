# local-search

Fast unified local file and full-text search on Windows, backed by [Voidtools Everything](https://voidtools.com) (filenames) and [AnyTxt](https://anytxt.net) (full-text content, including PDF/docx/pptx).

One CLI (`local-search`), six self-explanatory subcommands. Distributed as a `uv tool`; used by Hermes Agent skills or directly from the terminal.

**Chinese: see [README_zh-CN.md](./README_zh-CN.md).**

---

## ⚠️ Prerequisites (must be installed AND correctly configured)

**This skill only works when BOTH backends are installed, running, and configured as described below. It is not a filesystem walker; without the two indexes, every subcommand will exit with a `BackendUnavailable` error.**

### Platform support

- ✅ **Windows 10 / Windows 11** — tested and supported
- ❌ **Windows 7 / 8 / 8.1** — Everything runs, AnyTxt not officially supported, untested
- ❌ **macOS / Linux** — neither Everything nor AnyTxt has a first-party build; **do not use this skill there**

Everything and AnyTxt are Windows-native applications. Even on WSL / Wine the IPC pathways used here (Everything's IPC + AnyTxt's local HTTP server) do not reliably work. If you are not on Windows 10+, use `search_files` / `rg` / `find` instead.

### 1. Voidtools Everything

**Install:** Download from <https://voidtools.com/downloads/> (either the installer or the portable build).

**Configure — Service Mode MUST be enabled:**

Open Everything, go to **Menu → Tools → Options → General**, and turn on:

- **[✓] Everything Service** — makes Everything run as a Windows service, so an admin-level "master" instance stays alive across log-off / log-on.
- **[✓] Start Everything on system startup** — recommended
- **[✓] Run as administrator** *(only shown after Service is enabled)* — required for indexing NTFS volumes without per-file permission errors

**Also required: an interactive user-session instance.** Everything's IPC (which this skill uses via the `everyfile` Python package) only works within the same Windows session. If you enabled Service Mode but never launched the app, IPC calls will silently fail because the service runs in Session 0, while your interactive shell runs in Session 1+.

We ship an idempotent fixer to handle this:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts\ensure-everything-user-session.ps1"
```

Or simply launch Everything from the Start menu once — the tray icon should appear.

### 2. AnyTxt Searcher

**Install:** Download from <https://anytxt.net/download/> (Windows-only). AnyTxt is free but closed-source.

**Configure — the HTTP Search (Beta) service MUST be enabled:**

Open AnyTxt, go to **Menu → Options → General → Advanced** (may be labeled *设置 → 高级 → HTTP 搜索(Beta)* in Chinese), and turn on:

- **[✓] HTTP Search (Beta)** *(a.k.a. "HTTP 搜索 (Beta)" / "Remote Search Server")*
- Confirm the listening port is **`9920`** — this is the default and what `local-search` expects
- Bind address should remain **`127.0.0.1`** (localhost) for security

Click **Apply** and restart AnyTxt. Verify the endpoint is reachable:

```bash
curl -s http://127.0.0.1:9920 -d '{}' | head -c 100
# Any HTTP 200 (even with a JSON-RPC error body) confirms the service is up.
```

**Also required: at least one indexed folder.** AnyTxt only searches folders you've explicitly added to its index. Go to **Menu → Options → Index** and add the drives / directories you want searchable (Documents, Desktop, project folders, etc.). Wait for the initial index to complete — a status bar at the bottom shows progress.

### 3. Confirm everything is ready

Run `local-search doctor`:

```
─────────── local-search doctor ───────────
┌────────────────────┬────────┬─────────────────────────────────────┐
│ Check              │ Status │ Detail / Fix                        │
├────────────────────┼────────┼─────────────────────────────────────┤
│ Everything (files) │ ✅ OK  │ 26 ms — IPC OK, 4,102,043 files     │
│ AnyTxt (text)      │ ✅ OK  │ 1753 ms — HTTP OK, 231,824 files    │
└────────────────────┴────────┴─────────────────────────────────────┘
```

Both rows must be green. Red status lines include the exact fix hint (which service to start, which config toggle to flip).

---

## Software Requirements

- **Windows 10 or 11**
- **Python 3.11+**
- **[uv](https://astral.sh/uv)** for install / tool management
- **Voidtools Everything** (see above)
- **AnyTxt Searcher** (see above)

## Install

```powershell
# From a shell in this directory:
scripts\install.ps1
# or POSIX equivalent (git-bash / WSL running Windows Python):
bash scripts/install.sh
# or directly:
uv tool install --editable . --force
```

Then:

```
local-search --version    # 0.1.1
local-search doctor       # both backends OK
```

## Commands (at a glance)

| Command | Backend | Purpose |
|---|---|---|
| `files` | Everything | Filename / path / extension search |
| `text` | AnyTxt | Full-text content search (incl. PDF/docx/pptx) |
| `recent` | Everything | Recently modified files, sorted by mtime desc |
| `extract` | AnyTxt | Dump AnyTxt's already-extracted plain text |
| `sync` | AnyTxt | Force reindex a folder + verify |
| `doctor` | both | Health check with actionable fix hints |

See `SKILL.md` (agent-facing full reference) or `local-search <cmd> --help` for detailed options.

## Development

```bash
# Run all tests (offline; pure functions + mocks — no backend required)
uv run pytest tests/ -v

# Live smoke (requires Everything + AnyTxt running & configured per above)
local-search doctor
local-search files "*.py" -n 5
local-search text "hermes" -e md --count-only
```

### Project layout

```
local-search/
├── SKILL.md                         # agent-facing skill declaration
├── README.md                        # this file
├── README_zh-CN.md                  # Chinese translation of this file
├── REVIEW.md                        # v1 → v2 expert review (retained)
├── 2026-07-16_145318-…-skill.md    # v1 plan (retained, superseded)
├── 2026-07-16_local-search-skill-v2.md   # v2 plan (source of truth)
├── pyproject.toml
├── src/local_search/
│   ├── __init__.py
│   ├── cli.py                       # Click subcommand tree
│   ├── errors.py                    # BackendUnavailable / InvalidQuery
│   ├── filters.py                   # UnifiedFilters + backend translators
│   ├── formatters.py                # Row / ResultSet + md/json/csv
│   ├── everything.py                # Everything backend (everyfile IPC)
│   ├── anytxt.py                    # AnyTxt backend (HTTP JSON-RPC)
│   └── doctor.py                    # health checks
├── scripts/
│   ├── ensure-everything-user-session.ps1
│   ├── install.ps1
│   └── install.sh
└── tests/                           # 52 tests, all offline
    ├── test_filters.py
    ├── test_formatters.py
    ├── test_anytxt_parsers.py
    └── test_cli.py                  # CLI safety rails + path normalization
```

### Wire-check findings (locked in v0.1.1)

- AnyTxt `GetResult` returns rows as `list[tuple]` — column order declared by `output.field` array
- AnyTxt `GetResult.count` = current page size, NOT total; total must be fetched via a separate `Search` call
- AnyTxt path field is `file`, not `path` or `filePath`
- AnyTxt numeric fields (`fid`, `lastModify`, `size`) are all strings
- AnyTxt `filterDir=""` is server-rewritten to `"C:"` (only searches C drive)
- AnyTxt `SyncIndex` returns `{}` — verify with a follow-up `Search` if you need a count
- everyfile `cursor.count` = current page size; `cursor.total` = actual total match count
- everyfile exception class is `EverythingError(Exception)`
- everyfile sort key is `modified` (not `date_modified`), `ext` (not `extension`)

See `REVIEW.md` for the full v1 → v2 diff and expert-review commentary.

## Distribution & multi-agent registration

This skill lives at a shared source directory (e.g. `C:\Users\<you>\Documents\more-skills\skills\local-search\`). Register it to any Hermes Agent profile via a directory junction:

```powershell
mklink /J "C:\Users\<you>\.hermes\profiles\<profile>\skills\system-administration\local-search" ^
          "C:\Users\<you>\Documents\more-skills\skills\local-search"
```

Edits to the source appear in every registered profile instantly. `uv tool install --editable` puts the `local-search` CLI on PATH globally — registration only controls skill *discovery* by agents, not CLI availability.

## License

MIT
