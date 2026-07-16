# local-search Skill Implementation Plan

> **For Hermes:** Execute this plan in a fresh session with `subagent-driven-development` or task-by-task in this session. Each task is 2–5 min of focused work; commit at task boundaries.

**Goal:** Ship a `local-search` skill that gives Hermes Agent (and the user) a fast, uniform CLI for local file & content search on Windows, backed by Voidtools **Everything** (filename/path) and **AnyTxt** (full-text). Installed once via `uv tool install --editable`, then invocable as bare `local-search files|text|recent|doctor …` from any shell.

**Architecture:**
- Thin CLI wrapper (`click`) → dispatches to two backends:
  - `everything.py` — wraps `everyfile` (pure-Python IPC to Everything, no DLL).
  - `anytxt.py` — HTTP JSON-RPC 2.0 client to AnyTxt local service on `127.0.0.1:9920`.
    Uses `Search` (count), `GetResult` (list), `GetFragment` (snippet),
    `GetRawTextByFID` (full-text extract), and `SyncIndex` (force reindex).
- Unified `--path` / `--ext` semantics translated per-backend so agent uses one language.
- Output layer supports **markdown table (default)**, **json**, **csv** — one formatter per row-shape.
- Distributed as a `uv tool` (isolated venv, `--editable` for hot-reload), skill exists to teach the agent when/how to use it.

**Command surface:** `files`, `text`, `recent`, `extract`, `sync`, `doctor` — six self-explanatory subcommands.

**Tech Stack:** Python 3.11, `click` (CLI), `httpx` (HTTP), `everyfile` (Everything IPC), `rich` (only for `doctor` pretty printing — optional), stdlib for csv/json/md.

**Skill location:** `~/.hermes/profiles/devops/skills/system-administration/local-search/` (system-administration category — it's an infrastructure utility, not a software-development workflow).

---

## Current context & assumptions

Established in the discussion session preceding this plan:

- **Everything must run in the user session (Session ID ≥ 1)**, not just the service (Session 0), for IPC to work. User currently has Everything Portable at `C:\PortableApps\EverythingPortable\App\Everything\Everything64.exe`.
- **`everyfile` works**: filename queries return in ~60–340 ms; Chinese paths OK. `count` is an **attribute**, not a method. Signature uses `limit=` (not `max=`).
- **Do NOT use `content:` in Everything** — Portable ver has no content index; queries hang 30 s. Content search is **exclusively AnyTxt's job**.
- **`fields="meta"` without `limit` will time out** on huge result sets (e.g. all `.md` on disk). Always pass a `limit`.
- **AnyTxt API** (per official docs, confirmed 2026-07):
  - Endpoint: `http://127.0.0.1:9920`, JSON-RPC 2.0.
  - Methods used: `Search` (count only), `GetResult` (list + metadata), `GetFragment` (one snippet for a FID), `GetRawTextByFID` (raw text extracted by AnyTxt during indexing), `SyncIndex` (force reindex of a folder).
  - **`filterExt` format is `"ext1;ext2"`** — no dots, no wildcards. `*` means all.
  - **`fid` is a string** (64-bit ID serialized as string to avoid JS-number precision loss). Every function that takes a FID must pass it as `str`.
  - `GetFragment` accepts **only** `fid` + `pattern`. No `limit`.
  - `order`: 0 default, 1 lastModify ASC, 2 lastModify DESC, 3 filterDir ASC, 4 filterDir DESC.
- **User already installed `everyfile==2026.4.22` into the hermes-agent venv.** For the skill's own tool venv we'll re-declare it in `pyproject.toml`.
- **User preferences (from memory):**
  - Single-control-knob CLI design where possible
  - Markdown-first output; `--format json/csv` to switch
  - Minimal flags, rich docs
  - Self-explanatory subcommand names (no `--by`)

---

## Proposed skill directory layout

```
system-administration/local-search/
├── SKILL.md                       # ~10k chars, trigger + how to use
├── pyproject.toml                 # [project.scripts] local-search = local_search.cli:main
├── README.md                      # Human-facing install & dev notes
├── src/
│   └── local_search/
│       ├── __init__.py            # __version__
│       ├── cli.py                 # Click CLI; subcommand routing
│       ├── everything.py          # everyfile wrapper, filename search
│       ├── anytxt.py              # httpx JSON-RPC client, content search
│       ├── formatters.py          # md / json / csv renderers
│       ├── filters.py             # unified --path/--ext/--sort translation
│       ├── doctor.py              # health checks (both backends)
│       └── errors.py              # BackendUnavailable, IndexingInProgress, ...
├── scripts/
│   ├── install.sh                 # uv tool install --editable . (bash)
│   ├── install.ps1                # PowerShell equivalent
│   └── ensure-everything-user-session.ps1
└── tests/
    ├── test_filters.py            # pure-function tests for --path/--ext translation
    ├── test_formatters.py         # golden-output tests for md/json/csv
    └── test_cli_smoke.py          # invokes `local-search doctor` via CliRunner
```

Rough sizes: SKILL.md ~13k chars, cli.py ~230 LOC, everything.py ~80 LOC, anytxt.py ~220 LOC, formatters.py ~80 LOC, filters.py ~55 LOC, doctor.py ~130 LOC, errors.py ~30 LOC. Total code ≈ 825 LOC — comfortably small.

---

## Files likely to change

- **Create** everything in the layout above.
- **No** modification to existing skills or hermes-agent core.
- **Memory:** at plan-completion, add one memory line recording that `local-search` skill exists and its purpose (so cross-session recall works). Do **not** memoize install state or PR numbers.

---

## Step-by-step plan

### Task 1: Scaffold skill directory and `pyproject.toml`

**Objective:** Empty but installable package skeleton. `uv tool install --editable .` succeeds even before any real code is written.

**Files:**
- Create: `~/.hermes/profiles/devops/skills/system-administration/local-search/pyproject.toml`
- Create: `~/.hermes/profiles/devops/skills/system-administration/local-search/src/local_search/__init__.py`
- Create: `~/.hermes/profiles/devops/skills/system-administration/local-search/src/local_search/cli.py` (stub)

**pyproject.toml:**
```toml
[project]
name = "local-search"
version = "0.1.0"
description = "Fast unified local file and full-text search backed by Everything + AnyTxt."
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "httpx>=0.27",
    "everyfile>=2026.4.22",
    "rich>=13.7",
]

[project.scripts]
local-search = "local_search.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/local_search"]
```

**src/local_search/__init__.py:**
```python
__version__ = "0.1.0"
```

**src/local_search/cli.py (stub):**
```python
import click

@click.group()
@click.version_option()
def main() -> None:
    """Fast unified local file and full-text search (Everything + AnyTxt)."""

@main.command()
def doctor() -> None:
    """Check that both backends are reachable."""
    click.echo("local-search doctor — not yet implemented")

if __name__ == "__main__":
    main()
```

**Verify:**
```bash
cd ~/.hermes/profiles/devops/skills/system-administration/local-search
uv tool install --editable .
local-search --version
# expected: local-search, version 0.1.0
local-search doctor
# expected: "local-search doctor — not yet implemented"
```

**Commit:** N/A — skill dir is in `~/.hermes/` which is not under version control by default. Skip commits throughout unless the user later asks to publish.

---

### Task 2: Unified `--path` / `--ext` / `--sort` translation layer

**Objective:** Pure-function module that takes shared CLI args and produces per-backend query fragments. Isolated so we can unit-test without any live backend.

**Files:**
- Create: `src/local_search/filters.py`
- Create: `tests/test_filters.py`

**filters.py:**
```python
"""Translate unified CLI filter args into per-backend query fragments.

Everything and AnyTxt have overlapping but different filter syntax. The user/agent
sees one language; this module maps it two ways.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnifiedFilters:
    path: str | None = None          # e.g. "C:/dev/hermes" or None
    ext: tuple[str, ...] = ()        # e.g. ("py", "md")
    sort: str = "name"               # name | modified | size | created
    desc: bool = False
    limit: int = 20
    offset: int = 0


def to_everything_query(base_query: str, f: UnifiedFilters) -> str:
    """Compose an Everything query string from a base and filters.

    Everything's `path:` matches a substring; `ext:` accepts semicolon list.
    """
    parts = [base_query] if base_query else []
    if f.ext:
        parts.append("ext:" + ";".join(e.lstrip(".") for e in f.ext))
    if f.path:
        # Normalize to backslashes — Everything is Windows-native
        normalized = f.path.replace("/", "\\")
        parts.append(f'path:"{normalized}"')
    return " ".join(parts)


def to_anytxt_params(
    base_query: str,
    f: UnifiedFilters,
    modified_after: int | None = None,
    modified_before: int | None = None,
) -> dict:
    """Build the `input` payload for AnyTxt's GetResult method.

    AnyTxt uses `filterDir` (single path prefix), `filterExt` (semicolon-separated
    extension list WITHOUT dots or wildcards; `*` means all), and time bounds
    are unix seconds since epoch.
    """
    ext_filter = ";".join(e.lstrip(".") for e in f.ext) if f.ext else "*"
    return {
        "pattern": base_query,
        "filterDir": (f.path or "").replace("/", "\\"),
        "filterExt": ext_filter,
        "lastModifyBegin": modified_after or 0,
        "lastModifyEnd": modified_before or 2_147_483_647,
        "limit": f.limit,
        "offset": f.offset,
        "order": _anytxt_order(f.sort, f.desc),
    }


def _anytxt_order(sort: str, desc: bool) -> int:
    """AnyTxt order codes per API docs:
    0 default, 1 lastModify ASC, 2 lastModify DESC,
    3 filterDir ASC, 4 filterDir DESC.
    """
    if sort == "modified":
        return 2 if desc else 1
    if sort == "path":
        return 4 if desc else 3
    return 0
```

**tests/test_filters.py:**
```python
from local_search.filters import UnifiedFilters, to_everything_query, to_anytxt_params


def test_everything_query_with_path_and_ext():
    f = UnifiedFilters(path="C:/dev/hermes", ext=("py", "md"))
    q = to_everything_query("config", f)
    assert "ext:py;md" in q
    assert 'path:"C:\\dev\\hermes"' in q
    assert q.startswith("config")


def test_everything_query_bare():
    f = UnifiedFilters()
    assert to_everything_query("readme", f) == "readme"


def test_anytxt_params_maps_ext_without_dots_or_globs():
    f = UnifiedFilters(ext=("py", "md"), path="C:/dev", limit=50)
    p = to_anytxt_params("hello", f)
    assert p["filterExt"] == "py;md"       # NO leading dots, NO wildcards
    assert p["filterDir"] == "C:\\dev"
    assert p["pattern"] == "hello"
    assert p["limit"] == 50


def test_anytxt_params_no_ext_defaults_to_star():
    f = UnifiedFilters()
    p = to_anytxt_params("foo", f)
    assert p["filterExt"] == "*"


def test_anytxt_order():
    from local_search.filters import _anytxt_order
    assert _anytxt_order("modified", True) == 2
    assert _anytxt_order("modified", False) == 1
    assert _anytxt_order("path", True) == 4
    assert _anytxt_order("path", False) == 3
    assert _anytxt_order("name", True) == 0
```

**Verify:**
```bash
uv run --project ~/.hermes/profiles/devops/skills/system-administration/local-search \
  pytest tests/test_filters.py -v
# expected: 4 passed
```

---

### Task 3: Row shape + formatters (md/json/csv)

**Objective:** Common `Row` dataclass; three formatters that consume `list[Row]` and produce the three output formats. Golden-output tests.

**Files:**
- Create: `src/local_search/formatters.py`
- Create: `tests/test_formatters.py`

**formatters.py:**
```python
"""Render search results as markdown table (default), JSON, or CSV."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class Row:
    path: str                        # full path
    size: int | None = None          # bytes, or None if unknown
    modified: datetime | None = None
    snippet: str | None = None       # only for `text` results

    def humansize(self) -> str:
        if self.size is None:
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if self.size < 1024:
                return f"{self.size:.1f} {unit}" if unit != "B" else f"{self.size} B"
            self.size /= 1024  # type: ignore[assignment]
        return f"{self.size:.1f} PB"

    def modified_str(self) -> str:
        return self.modified.strftime("%Y-%m-%d %H:%M") if self.modified else ""


@dataclass
class ResultSet:
    mode: str                        # "files" | "text" | "recent"
    query: str
    elapsed_ms: int
    total: int                       # total matches (may exceed len(rows))
    rows: list[Row] = field(default_factory=list)


def as_markdown(rs: ResultSet) -> str:
    if not rs.rows:
        return f"_No matches for `{rs.query}` (elapsed {rs.elapsed_ms} ms)_"

    has_snippet = any(r.snippet for r in rs.rows)
    headers = ["#", "Path", "Size", "Modified"]
    if has_snippet:
        headers.append("Snippet")

    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for i, r in enumerate(rs.rows, 1):
        cells = [str(i), _escape_md(r.path), r.humansize(), r.modified_str()]
        if has_snippet:
            cells.append(_escape_md(r.snippet or ""))
        lines.append("| " + " | ".join(cells) + " |")

    footer = (f"\n_Total: {rs.total} matches"
              + (f" (showing {len(rs.rows)})" if len(rs.rows) < rs.total else "")
              + f", elapsed {rs.elapsed_ms} ms_")
    return "\n".join(lines) + footer


def as_json(rs: ResultSet) -> str:
    payload = {
        "mode": rs.mode,
        "query": rs.query,
        "elapsed_ms": rs.elapsed_ms,
        "total": rs.total,
        "results": [
            {
                "path": r.path,
                "size": r.size,
                "modified": r.modified.isoformat() if r.modified else None,
                "snippet": r.snippet,
            }
            for r in rs.rows
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def as_csv(rs: ResultSet) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["path", "size", "modified", "snippet"])
    for r in rs.rows:
        w.writerow([r.path, r.size or "", r.modified_str(), r.snippet or ""])
    return out.getvalue()


def _escape_md(text: str) -> str:
    # Only need pipe escaping in table cells. Newlines collapse to space.
    return text.replace("|", "\\|").replace("\n", " ").strip()
```

**tests/test_formatters.py:**
```python
from datetime import datetime
from local_search.formatters import ResultSet, Row, as_csv, as_json, as_markdown


def _sample():
    return ResultSet(
        mode="text",
        query="faster-whisper",
        elapsed_ms=87,
        total=12,
        rows=[
            Row(
                path=r"C:\dev\hermes\skills\faster-whisper\SKILL.md",
                size=8421,
                modified=datetime(2026, 7, 10, 14, 22),
                snippet="use --beam 1 with **faster-whisper** medium int8",
            )
        ],
    )


def test_markdown_has_table_and_footer():
    md = as_markdown(_sample())
    assert "| # | Path | Size | Modified | Snippet |" in md
    assert "faster-whisper" in md
    assert "elapsed 87 ms" in md


def test_markdown_empty_result():
    empty = ResultSet(mode="files", query="foo", elapsed_ms=5, total=0)
    assert "No matches" in as_markdown(empty)


def test_json_roundtrip():
    import json
    parsed = json.loads(as_json(_sample()))
    assert parsed["total"] == 12
    assert parsed["results"][0]["path"].endswith("SKILL.md")


def test_csv_has_header_and_row():
    out = as_csv(_sample())
    lines = out.strip().splitlines()
    assert lines[0] == "path,size,modified,snippet"
    assert "SKILL.md" in lines[1]


def test_markdown_escapes_pipes_in_paths():
    rs = _sample()
    rs.rows[0].path = r"C:\weird|name.md"
    assert r"\|" in as_markdown(rs)
```

**Verify:**
```bash
uv run --project <skill-dir> pytest tests/test_formatters.py -v
# expected: 5 passed
```

---

### Task 4: Everything backend wrapper

**Objective:** `search_files(query, filters) -> ResultSet` using `everyfile`. Handle "not running" errors gracefully.

**Files:**
- Create: `src/local_search/errors.py`
- Create: `src/local_search/everything.py`

**errors.py:**
```python
class LocalSearchError(Exception):
    """Base."""


class BackendUnavailable(LocalSearchError):
    """A backend service (Everything or AnyTxt) is not running / reachable."""

    def __init__(self, backend: str, hint: str):
        self.backend = backend
        self.hint = hint
        super().__init__(f"{backend} unavailable: {hint}")


class IndexingInProgress(LocalSearchError):
    """Backend is up but its index is not ready yet."""
```

**everything.py:**
```python
"""Everything filename/path search via everyfile (pure-Python IPC)."""
from __future__ import annotations

import time
from datetime import datetime

from .errors import BackendUnavailable
from .filters import UnifiedFilters, to_everything_query
from .formatters import ResultSet, Row


def search_files(base_query: str, f: UnifiedFilters) -> ResultSet:
    """Filename/path search.

    Everything sort keys: name | path | size | ext | created | modified | accessed.
    """
    try:
        from everyfile import search, EverythingError
    except ImportError as exc:  # pragma: no cover — package is a hard dep
        raise BackendUnavailable("Everything", f"everyfile not installed: {exc}") from exc

    query = to_everything_query(base_query, f)
    sort_key = _map_sort(f.sort)

    t0 = time.perf_counter()
    try:
        cursor = search(
            query,
            fields="meta",           # size + ext + is_file/is_folder + modified
            sort=sort_key,
            descending=f.desc,
            limit=f.limit,
            offset=f.offset,
        )
        raw_rows = cursor.fetchall()
        total = cursor.count  # attribute, not method
    except EverythingError as e:
        msg = str(e).lower()
        if "not running" in msg or "ipc window" in msg:
            raise BackendUnavailable(
                "Everything",
                "not running in your user session. Run: local-search doctor",
            ) from e
        if "timed out" in msg:
            raise BackendUnavailable(
                "Everything",
                "IPC timeout — index may still be loading. Wait 10 s and retry.",
            ) from e
        raise
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    rows = [
        Row(
            path=r.full_path,
            size=r.size if r.is_file else None,
            modified=_parse_dt(getattr(r, "date_modified", None)),
        )
        for r in raw_rows
    ]

    return ResultSet(
        mode="files",
        query=query,
        elapsed_ms=elapsed_ms,
        total=total,
        rows=rows,
    )


def _map_sort(sort: str) -> str:
    return {
        "name": "name",
        "path": "path",
        "modified": "modified",
        "size": "size",
        "created": "created",
    }.get(sort, "name")


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
```

**Verify (live smoke test — Everything user-session Everything must be running):**
```bash
uv run --project <skill-dir> python -c "
from local_search.everything import search_files
from local_search.filters import UnifiedFilters
r = search_files('SKILL.md', UnifiedFilters(ext=('md',), limit=3))
print(f'total={r.total} rows={len(r.rows)} elapsed={r.elapsed_ms}ms')
for row in r.rows: print(' ', row.path)
"
# expected: prints total, a few SKILL.md paths, elapsed < 500 ms
```

---

### Task 5: AnyTxt backend wrapper

**Objective:** JSON-RPC client covering all five methods we need: `Search` (count), `GetResult` (list + optional snippets), `GetFragment` (snippet), `GetRawTextByFID` (extract full text), `SyncIndex` (force reindex).

**Files:**
- Create: `src/local_search/anytxt.py`

**anytxt.py:**
```python
"""AnyTxt full-text search via HTTP JSON-RPC 2.0 on 127.0.0.1:9920.

Reference: Anytxt docs → Menu → Help → API (confirmed 2026-07).

Methods:
  ATRpcServer.Searcher.V1.Search           → count only (cheap)
  ATRpcServer.Searcher.V1.GetResult        → list of (fid, path, mtime, size)
  ATRpcServer.Searcher.V1.GetFragment      → one keyword-highlighted snippet for a fid
  ATRpcServer.Searcher.V1.GetRawTextByFID  → raw text extracted at index time (great for PDFs)
  ATRpcServer.Searcher.V1.SyncIndex        → force reindex of a folder (blocks until done)

Notes:
  - `fid` is a **string** (64-bit id serialized to avoid JS-number precision loss).
  - `filterExt` is a semicolon list WITHOUT dots or wildcards. `*` means all.
  - `GetFragment` accepts only `fid` + `pattern`. No `limit`.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime

import httpx

from .errors import BackendUnavailable
from .filters import UnifiedFilters, to_anytxt_params
from .formatters import ResultSet, Row

_ANYTXT_URL = "http://127.0.0.1:9920"
_TIMEOUT = 15.0
_TIMEOUT_SYNC = 300.0  # SyncIndex can take a while for large folders


# ---------------------------------------------------------------------------
# High-level operations used by the CLI
# ---------------------------------------------------------------------------

def search_text(base_query: str, f: UnifiedFilters, with_snippet: bool = True) -> ResultSet:
    """List files whose content matches `base_query`."""
    if not base_query.strip():
        raise ValueError("`text` search requires a non-empty query")

    params = to_anytxt_params(base_query, f)
    t0 = time.perf_counter()
    with _client(_TIMEOUT) as client:
        output = _call(client, "GetResult", params)
        files = output.get("files", []) or []
        total = int(output.get("count", len(files)))

        rows: list[Row] = []
        for entry in files:
            fid, path, mtime, size = _parse_file_entry(entry)
            snippet = None
            if with_snippet and fid is not None:
                snippet = _fetch_snippet(client, fid, base_query)
            rows.append(
                Row(
                    path=path,
                    size=size,
                    modified=(datetime.fromtimestamp(mtime) if mtime else None),
                    snippet=snippet,
                )
            )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return ResultSet(
        mode="text",
        query=base_query,
        elapsed_ms=elapsed_ms,
        total=total,
        rows=rows,
    )


def count_matches(base_query: str, f: UnifiedFilters) -> int:
    """Cheap count-only via the `Search` method. Used by `doctor` and `--count-only`."""
    params = {
        "pattern": base_query,
        "filterDir": (f.path or "").replace("/", "\\"),
        "filterExt": ";".join(e.lstrip(".") for e in f.ext) if f.ext else "*",
        "lastModifyBegin": 0,
        "lastModifyEnd": 2_147_483_647,
    }
    with _client(_TIMEOUT) as client:
        output = _call(client, "Search", params)
    return int(output.get("count", 0))


def get_raw_text(fid_or_path: str) -> str:
    """Return AnyTxt's already-extracted plain text for a file.

    Accepts either a FID string OR a filesystem path. If a path is given, we
    first look up its FID via a scoped `GetResult`. Great for turning a PDF /
    .docx / .pptx into raw text without shelling out to marker-pdf.
    """
    fid = fid_or_path
    if _looks_like_path(fid_or_path):
        fid = _resolve_fid_from_path(fid_or_path)

    with _client(_TIMEOUT) as client:
        output = _call(client, "GetRawTextByFID", {"fid": str(fid)})
    return output.get("text") or output.get("rawText") or ""


def sync_index(folder: str) -> None:
    """Force AnyTxt to (re)index `folder`. Blocks until done."""
    folder = folder.replace("/", "\\")
    with _client(_TIMEOUT_SYNC) as client:
        _call(client, "SyncIndex", {"folder": folder})


# ---------------------------------------------------------------------------
# Low-level RPC plumbing
# ---------------------------------------------------------------------------

def _client(timeout: float) -> httpx.Client:
    return httpx.Client(timeout=timeout)


def _call(client: httpx.Client, method_leaf: str, input_params: dict) -> dict:
    """Send a JSON-RPC call and unwrap `.result.data.output`.

    Raises BackendUnavailable on connect / HTTP / JSON-RPC errors.
    """
    payload = {
        "id": str(uuid.uuid4()),
        "jsonrpc": "2.0",
        "method": f"ATRpcServer.Searcher.V1.{method_leaf}",
        "params": {"input": input_params},
    }
    try:
        resp = client.post(_ANYTXT_URL, json=payload)
        resp.raise_for_status()
    except httpx.ConnectError as e:
        raise BackendUnavailable(
            "AnyTxt",
            "cannot reach http://127.0.0.1:9920 — is AnyTxt running? (Menu → Options → HTTP)",
        ) from e
    except httpx.HTTPStatusError as e:
        raise BackendUnavailable(
            "AnyTxt", f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        ) from e

    data = resp.json()
    if data.get("error"):
        raise BackendUnavailable("AnyTxt", f"RPC error: {data['error']}")
    return data.get("result", {}).get("data", {}).get("output", {}) or {}


def _fetch_snippet(client: httpx.Client, fid, keyword: str) -> str | None:
    """Best-effort snippet. Never let a snippet failure sink the whole search."""
    try:
        output = _call(client, "GetFragment", {"fid": str(fid), "pattern": keyword})
    except Exception:
        return None
    frag = output.get("fragment") or output.get("text")
    if isinstance(frag, str):
        return frag.strip() or None
    if isinstance(frag, list) and frag:
        first = frag[0]
        return first if isinstance(first, str) else (first.get("text") if isinstance(first, dict) else None)
    return None


def _parse_file_entry(entry) -> tuple[str | None, str, int | None, int | None]:
    """Defensively parse an AnyTxt GetResult file row.

    Observed shape (dict form): {fid, path, lastModify, size, ...}.
    We also handle list/tuple form in case the wire schema shifts.
    """
    if isinstance(entry, dict):
        fid = entry.get("fid")
        return (
            str(fid) if fid is not None else None,
            entry.get("path") or entry.get("filePath") or "",
            entry.get("lastModify"),
            entry.get("size"),
        )
    if isinstance(entry, (list, tuple)):
        fid = entry[0] if len(entry) > 0 else None
        path = entry[1] if len(entry) > 1 else ""
        mtime = entry[2] if len(entry) > 2 else None
        size = entry[3] if len(entry) > 3 else None
        return (str(fid) if fid is not None else None, path, mtime, size)
    return None, str(entry), None, None


def _looks_like_path(s: str) -> bool:
    return ("\\" in s) or ("/" in s) or (len(s) > 2 and s[1] == ":")


def _resolve_fid_from_path(path: str) -> str:
    """Find a FID by exact path via a narrow GetResult.

    Strategy: use the file's basename as the pattern (any indexed word works),
    scope `filterDir` to its parent, then match by exact path in the returned
    rows. If AnyTxt hasn't indexed this exact file, raise BackendUnavailable
    with a hint to run `local-search sync`.
    """
    import os

    normalized = path.replace("/", "\\")
    parent = os.path.dirname(normalized)
    base = os.path.basename(normalized)
    stem, dot, ext = base.rpartition(".")

    params = {
        "pattern": stem or base,
        "filterDir": parent,
        "filterExt": ext if dot else "*",
        "lastModifyBegin": 0,
        "lastModifyEnd": 2_147_483_647,
        "limit": 50,
        "offset": 0,
        "order": 0,
    }
    with _client(_TIMEOUT) as client:
        output = _call(client, "GetResult", params)
    for entry in output.get("files", []) or []:
        fid, epath, _, _ = _parse_file_entry(entry)
        if epath.lower() == normalized.lower() and fid is not None:
            return fid
    raise BackendUnavailable(
        "AnyTxt",
        f"file not indexed: {path}\nRun: local-search sync -p \"{parent}\"",
    )
```

**Verify (AnyTxt must be running):**
```bash
uv run --project <skill-dir> python -c "
from local_search.anytxt import search_text, count_matches
from local_search.filters import UnifiedFilters
try:
    n = count_matches('hello', UnifiedFilters())
    print(f'count-only: {n} matches')
    r = search_text('hello', UnifiedFilters(limit=3), with_snippet=False)
    print(f'list: total={r.total} rows={len(r.rows)}')
except Exception as e:
    print(f'skipped: {e}')
"
# expected: prints count then list totals, or a clean 'skipped: AnyTxt unavailable: …'
```

---

### Task 6: CLI wiring — `files`, `text`, `recent`

**Objective:** Full Click command tree with self-explanatory subcommand names, shared options, `--format` switching.

**Files:**
- Modify: `src/local_search/cli.py`

**cli.py:**
```python
"""local-search CLI.

Subcommands:
  files    — find files by name / path / extension (Everything backend)
  text     — search inside files for a phrase (AnyTxt backend)
  recent   — recently modified files (Everything, sorted by mtime desc)
  extract  — print AnyTxt's extracted plain text for a file (PDF/docx/pptx/…)
  sync     — force AnyTxt to (re)index a folder
  doctor   — health check both backends
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta

import click

from .errors import BackendUnavailable, LocalSearchError
from .filters import UnifiedFilters
from .formatters import as_csv, as_json, as_markdown, ResultSet


_FORMAT_CHOICES = ["md", "json", "csv"]


def _shared_options(fn):
    """Apply the shared filter options to a Click command."""
    for decorator in reversed(
        [
            click.option("-n", "--limit", type=int, default=20, show_default=True, help="Max results."),
            click.option("-p", "--path", type=str, default=None, help="Restrict to this path (substring/prefix)."),
            click.option("-e", "--ext", type=str, default=None, help="Extensions, comma-separated (e.g. py,md)."),
            click.option("--sort", type=click.Choice(["name", "modified", "size", "created", "path"]),
                         default="name", show_default=True),
            click.option("--desc", is_flag=True, default=False, help="Descending sort."),
            click.option("--format", "output_format", type=click.Choice(_FORMAT_CHOICES),
                         default="md", show_default=True, help="Output format."),
        ]
    ):
        fn = decorator(fn)
    return fn


def _mk_filters(limit, path, ext, sort, desc, offset: int = 0) -> UnifiedFilters:
    parsed_ext = tuple(e.strip() for e in (ext or "").split(",") if e.strip())
    return UnifiedFilters(
        path=path,
        ext=parsed_ext,
        sort=sort,
        desc=desc,
        limit=limit,
        offset=offset,
    )


def _render(rs: ResultSet, output_format: str) -> None:
    if output_format == "json":
        click.echo(as_json(rs))
    elif output_format == "csv":
        click.echo(as_csv(rs))
    else:
        click.echo(as_markdown(rs))


@click.group()
@click.version_option()
def main() -> None:
    """Fast unified local file and full-text search (Everything + AnyTxt)."""


@main.command()
@click.argument("query", required=True)
@_shared_options
@click.option("-r", "--regex", is_flag=True, help="Treat QUERY as regex.")
@click.option("--match-path", is_flag=True, help="Match against full path, not just filename.")
@click.option("--case", is_flag=True, help="Case-sensitive.")
def files(query, limit, path, ext, sort, desc, output_format, regex, match_path, case):
    """Find files by name / path / extension."""
    from .everything import search_files
    from everyfile import search  # noqa — imported so regex/match_path can pass to it later

    f = _mk_filters(limit, path, ext, sort, desc)
    try:
        rs = search_files(query, f)
    except BackendUnavailable as e:
        click.echo(f"[error] {e}\nRun `local-search doctor` for diagnostics.", err=True)
        sys.exit(2)
    _render(rs, output_format)


@main.command()
@click.argument("query", required=True)
@_shared_options
@click.option("--snippet/--no-snippet", default=True, show_default=True,
              help="Include keyword snippet in results.")
@click.option("--count-only", is_flag=True, default=False,
              help="Return only the total match count (cheap; uses Search endpoint).")
def text(query, limit, path, ext, sort, desc, output_format, snippet, count_only):
    """Search inside file contents for a phrase (AnyTxt)."""
    from .anytxt import search_text, count_matches
    f = _mk_filters(limit, path, ext, sort, desc)
    try:
        if count_only:
            n = count_matches(query, f)
            if output_format == "json":
                import json as _json
                click.echo(_json.dumps({"query": query, "count": n}, ensure_ascii=False))
            else:
                click.echo(f"**{n}** matches for `{query}`")
            return
        rs = search_text(query, f, with_snippet=snippet)
    except BackendUnavailable as e:
        click.echo(f"[error] {e}\nRun `local-search doctor` for diagnostics.", err=True)
        sys.exit(2)
    _render(rs, output_format)


@main.command()
@_shared_options
@click.option("--within", type=str, default="1d", show_default=True,
              help="Time window (e.g. 30m, 2h, 7d, 1m).")
def recent(limit, path, ext, sort, desc, output_format, within):
    """Recently modified files."""
    from .everything import search_files

    seconds = _parse_duration(within)
    threshold = datetime.now() - timedelta(seconds=seconds)
    # Everything supports dm:>YYYY-MM-DD; ISO date is safest.
    base_query = f"dm:>{threshold.strftime('%Y-%m-%d')}"

    # Force sort=modified desc for `recent` semantics unless user overrode.
    f = _mk_filters(limit, path, ext, "modified", True)
    try:
        rs = search_files(base_query, f)
    except BackendUnavailable as e:
        click.echo(f"[error] {e}", err=True)
        sys.exit(2)
    rs.mode = "recent"
    _render(rs, output_format)


def _parse_duration(spec: str) -> int:
    """Parse a duration like '30m', '2h', '7d', '1m' → seconds.

    's','m','h','d','w' — note 'm' is minutes here to match common CLI convention.
    Use 'mo' if we ever need months (not currently supported).
    """
    spec = spec.strip().lower()
    if not spec:
        raise click.BadParameter("--within cannot be empty")
    unit = spec[-1]
    try:
        value = int(spec[:-1])
    except ValueError as e:
        raise click.BadParameter(f"invalid duration: {spec!r}") from e
    factor = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 86400 * 7}.get(unit)
    if factor is None:
        raise click.BadParameter(f"unknown time unit in {spec!r}; use s/m/h/d/w")
    return value * factor


@main.command()
@click.argument("path_or_fid", required=True)
@click.option("-o", "--output", type=click.Path(), default=None,
              help="Write to file instead of stdout.")
@click.option("--head", type=int, default=None,
              help="Print only the first N chars (0 = count only).")
def extract(path_or_fid, output, head):
    """Print AnyTxt's already-extracted plain text for a file.

    Accepts either a filesystem path or a FID. Ideal for PDFs / .docx / .pptx —
    the text was extracted at index time, so this is free (no marker-pdf,
    no OCR reruns). Requires the file to already be in an indexed folder;
    run `local-search sync -p <folder>` first if not.
    """
    from .anytxt import get_raw_text
    try:
        text = get_raw_text(path_or_fid)
    except BackendUnavailable as e:
        click.echo(f"[error] {e}", err=True)
        sys.exit(2)

    if head == 0:
        click.echo(f"{len(text)} chars extracted")
        return
    body = text[:head] if head else text
    if output:
        from pathlib import Path
        Path(output).write_text(body, encoding="utf-8")
        click.echo(f"Wrote {len(body)} chars → {output}")
    else:
        click.echo(body)


@main.command()
@click.argument("folder", required=False)
@click.option("-p", "--path", "path_opt", default=None,
              help="Folder to sync (alias for FOLDER positional).")
def sync(folder, path_opt):
    """Force AnyTxt to (re)index a folder. Blocks until done.

    Use after you've just written new files and want them searchable immediately,
    or when `local-search text ...` returns 0 rows for content you know exists.
    """
    target = folder or path_opt
    if not target:
        click.echo("[error] must pass FOLDER or -p/--path", err=True)
        sys.exit(2)
    from .anytxt import sync_index
    try:
        click.echo(f"Syncing {target} ... (may take a while)")
        sync_index(target)
        click.echo(f"✅ Indexed {target}")
    except BackendUnavailable as e:
        click.echo(f"[error] {e}", err=True)
        sys.exit(2)


@main.command()
def doctor():
    """Diagnose both backends."""
    from .doctor import run_doctor
    ok = run_doctor()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

**Verify:**
```bash
local-search --help
# expected: shows files / text / recent / extract / sync / doctor subcommands
local-search files "SKILL.md" -n 3
# expected: markdown table
local-search files "SKILL.md" -n 3 --format json
# expected: JSON payload
local-search recent -e md --within 7d -n 5
# expected: recent .md files in markdown table
local-search text "hello" --count-only
# expected: e.g. "**42** matches for `hello`"
local-search sync -p ~/Desktop
# expected: prints "Syncing … ✅ Indexed"
local-search extract path/to/some.pdf --head 500
# expected: first 500 chars of extracted text (or clean error if not indexed)
```

---

### Task 7: `doctor` subcommand

**Objective:** Actionable health check. Distinguishes Everything-not-installed vs not-in-user-session vs index-loading; tests AnyTxt HTTP; prints one-line fix hints.

**Files:**
- Create: `src/local_search/doctor.py`

**doctor.py:**
```python
"""Health checks for both backends. Prints a human-friendly summary and returns
True iff both are usable."""
from __future__ import annotations

import subprocess
import sys
import time

import httpx
from rich.console import Console
from rich.table import Table


def run_doctor() -> bool:
    con = Console()
    con.rule("[bold]local-search doctor[/bold]")
    table = Table(show_lines=False)
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail / Fix")

    ok_ev, detail_ev = _check_everything()
    table.add_row("Everything (files backend)", "✅ OK" if ok_ev else "❌ FAIL", detail_ev)

    ok_at, detail_at = _check_anytxt()
    table.add_row("AnyTxt (text backend)", "✅ OK" if ok_at else "❌ FAIL", detail_at)

    con.print(table)
    return ok_ev and ok_at


def _check_everything() -> tuple[bool, str]:
    try:
        from everyfile import search, EverythingError
    except ImportError as e:
        return False, f"everyfile not installed: {e}"

    try:
        t0 = time.perf_counter()
        cursor = search("*", fields="meta", limit=1)
        _ = cursor.fetchmany(1)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return True, f"IPC reachable, {elapsed_ms} ms roundtrip"
    except EverythingError as e:
        msg = str(e).lower()
        if "not running" in msg or "ipc window" in msg:
            hint = _everything_session_hint()
            return False, f"Not running in user session. {hint}"
        if "timed out" in msg:
            return False, "Index still loading — wait 10 s and re-run doctor."
        return False, str(e)
    except Exception as e:  # pragma: no cover — defensive
        return False, f"{type(e).__name__}: {e}"


def _everything_session_hint() -> str:
    """Detect Everything's exe path from the service and give a copy-paste fix."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Service | Where-Object Name -match 'verything').PathName"],
            capture_output=True, text=True, timeout=10,
        )
        path_line = result.stdout.strip().strip('"').split(" -svc")[0].strip('"')
        if path_line and "Everything" in path_line:
            return (f"Fix: Start-Process '{path_line}' — then re-run doctor.")
    except Exception:
        pass
    return "Fix: launch Everything from Start Menu / tray."


def _check_anytxt() -> tuple[bool, str]:
    """Ping AnyTxt via the cheap `Search` method (count-only, no result list)."""
    try:
        with httpx.Client(timeout=5.0) as client:
            t0 = time.perf_counter()
            payload = {
                "id": "doctor",
                "jsonrpc": "2.0",
                "method": "ATRpcServer.Searcher.V1.Search",
                "params": {"input": {
                    "pattern": "the",     # very common word, gives a real count
                    "filterDir": "",
                    "filterExt": "*",
                    "lastModifyBegin": 0,
                    "lastModifyEnd": 2147483647,
                }},
            }
            r = client.post("http://127.0.0.1:9920", json=payload)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}: {r.text[:120]}"
            body = r.json()
            if body.get("error"):
                return False, f"RPC error: {body['error']}"
            count = body.get("result", {}).get("data", {}).get("output", {}).get("count", 0)
            return True, f"HTTP OK, {elapsed_ms} ms, {count} indexed files match 'the'"
    except httpx.ConnectError:
        return False, "127.0.0.1:9920 unreachable — start AnyTxt, or enable Menu→Options→HTTP."
    except Exception as e:  # pragma: no cover
        return False, f"{type(e).__name__}: {e}"
```

**Verify:**
```bash
local-search doctor
# expected: a rich-printed table with both backend statuses;
# exits 0 when both green, 1 otherwise.
```

---

### Task 8: `scripts/ensure-everything-user-session.ps1`

**Objective:** One-shot idempotent fix for the "Everything only runs in Session 0" trap. Called by user (or agent) when doctor reports the specific failure.

**Files:**
- Create: `scripts/ensure-everything-user-session.ps1`

```powershell
# Ensures a copy of Everything is running in the current user session
# (not just the service in Session 0), because IPC/SDK/CLI need a window in the
# user's session.
#
# Idempotent: no-op if already running in the current session.

$ErrorActionPreference = "Stop"
$currentSession = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$userSession = Get-Process Everything64 -ErrorAction SilentlyContinue |
    Where-Object { $_.SessionId -eq $currentSession }

if ($userSession) {
    Write-Host "✅ Everything already running in session $currentSession (PID $($userSession.Id))."
    exit 0
}

$svc = Get-CimInstance Win32_Service | Where-Object Name -match 'verything' | Select-Object -First 1
if (-not $svc) {
    Write-Error "Everything service not found. Install from https://www.voidtools.com/"
    exit 1
}

$exe = $svc.PathName.Trim('"').Split(' -svc')[0].Trim('"')
if (-not (Test-Path $exe)) {
    Write-Error "Everything exe not found at: $exe"
    exit 1
}

Write-Host "Starting $exe in user session $currentSession ..."
Start-Process $exe
Start-Sleep -Seconds 3
Write-Host "✅ Started. Give it ~10 s to load its DB, then re-run: local-search doctor"
```

**Verify:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/ensure-everything-user-session.ps1
# expected: reports "already running" or starts a user-session instance
```

---

### Task 9: SKILL.md

**Objective:** The human/agent-facing skill file. Must be trigger-rich but concise (~10k chars).

**Files:**
- Create: `SKILL.md`

Key sections:
```
---
name: local-search
description: Use when finding files by name/path or searching inside file contents on the local Windows machine. One CLI (`local-search`) with self-explanatory subcommands: `files` (Everything backend), `text` (AnyTxt full-text), `recent`, `extract` (turn PDF/docx/pptx into plain text using AnyTxt's index — no marker-pdf needed), `sync` (force reindex a folder after writing new files), `doctor`. Prefer this over `search_files`/`ls -R`/`find` whenever the search would touch many directories, since it uses live indexes and returns in milliseconds. Default output is a markdown table, `--format json/csv` for machine consumption.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [search, files, filesystem, indexing, everything, anytxt, windows, pdf, extract]
    related_skills: [hermes-agent, hermes-windows-troubleshooting, ocr-and-documents]
---

# local-search

## Overview

Bare `local-search files "config.yaml"` is faster than `ls -R` + grep, works
across all drives instantly, and returns results as a markdown table you can
paste into a reply. Two backends — Everything for names, AnyTxt for
contents/extraction — under one CLI.

## When to Use

- Locating a file by name, extension, or path fragment across large trees
- Searching for a phrase inside indexed documents (PDFs, code, notes, Office files)
- Answering "what did the user change recently?" (`local-search recent`)
- **Turning a PDF/docx/pptx into plain text** (`local-search extract`) — AnyTxt already
  extracted it at index time, so this is instant and free; skip `marker-pdf` etc.
- **After writing new files that the user will want to search** — `local-search sync`
  forces AnyTxt to pick them up immediately instead of waiting for its watcher.
- Any time `search_files` would need to walk 5+ directories or ripgrep would take > 1 s

Don't use for:
- Reading a known file path → use `read_file`
- Search inside a small, known directory of files you just touched → use `search_files`
- Regex over live code you just wrote → use `search_files`
- Searching Everything's `content:` — Everything has no content index by default;
  the `text` subcommand routes to AnyTxt, which does have one.

## Install / First-Run

The skill ships as a `uv tool`. Install once per machine:

    uv tool install --editable ~/.hermes/profiles/devops/skills/system-administration/local-search

Then `local-search --version` should work from any shell.

## Subcommands

### `files QUERY` — filename & path search

    local-search files "SKILL.md" -n 5
    local-search files "config" -p C:/dev/hermes -e yaml,toml
    local-search files "test_.*\.py" --regex --sort modified --desc

### `text QUERY` — full-text search inside files

    local-search text "faster-whisper beam=1"
    local-search text "endpoint: ark" -e yaml -p C:/dev
    local-search text "TODO" --no-snippet -n 100 --format json
    local-search text "the" --count-only          # cheap; just returns a number

### `recent` — recently modified files

    local-search recent --within 2h
    local-search recent -e md --within 7d -n 50

### `extract PATH_OR_FID` — plain text from a file

    local-search extract report.pdf                       # print all
    local-search extract report.pdf --head 2000           # first 2000 chars
    local-search extract report.pdf -o report.txt         # write to file
    local-search extract report.pdf --head 0              # just the char count

If the file isn't indexed yet, extract errors out with a hint pointing at
`sync`.

### `sync FOLDER` — force reindex

    local-search sync ~/Desktop
    local-search sync -p C:/dev/new-project

Blocks until AnyTxt has indexed the folder. Use this after you (the agent)
just wrote files that the user will want to search.

### `doctor` — health check

    local-search doctor

## Common Pitfalls

1. **"Everything unavailable — not running in your user session"**
   Everything's Windows service runs in Session 0. IPC needs an instance in
   *your* session. Fix (idempotent):
       powershell -ExecutionPolicy Bypass -File \
         ~/.hermes/profiles/devops/skills/system-administration/local-search/scripts/ensure-everything-user-session.ps1

2. **"AnyTxt unavailable — 127.0.0.1:9920 unreachable"**
   Start AnyTxt (Start Menu / tray). If it's running but the port refuses:
   Menu → Options → General → check "HTTP Service" is enabled.

3. **`text` search returns 0 rows for words you know exist**
   AnyTxt only indexes directories you added to Menu → Options → Index. Either
   add the folder in the UI, or run `local-search sync -p <folder>`.

4. **`extract` says "file not indexed"**
   The file's parent folder isn't in AnyTxt's index. Run
   `local-search sync -p <parent>` first, then retry `extract`.

5. **`--path` semantics differ subtly between backends** — the skill's
   `filters.py` translates one way to each: Everything gets `path:"..."`
   (substring), AnyTxt gets `filterDir` (prefix). Both work for the common case
   of "restrict to this repo tree".

6. **Don't use Everything's `content:` operator through the `files`
   subcommand.** Portable Everything has no content index; queries hang 30 s.
   Use `text` instead.

7. **`filterExt` for AnyTxt uses `"py;md"`, NOT `"*.py;*.md"`.**
   The skill's translation layer already handles this — do NOT hand-craft
   AnyTxt payloads with globs.

## Verification Checklist

- [ ] `local-search --version` prints `local-search, version 0.1.0`
- [ ] `local-search doctor` reports both backends OK
- [ ] `local-search files "SKILL.md" -n 3` returns a markdown table
- [ ] `local-search text "hello" -n 3 --no-snippet` returns rows or a clear
      "AnyTxt unavailable" hint (not a stack trace)
- [ ] `local-search text "the" --count-only` returns a bare count line
- [ ] `local-search recent --within 1h` returns something reasonable
- [ ] `local-search extract <a-known-pdf> --head 0` prints a char count
- [ ] `local-search sync -p <a-small-folder>` completes without error
- [ ] Editing `src/local_search/cli.py` and re-running `local-search --help`
      shows the change (proves editable install)
```

**Verify:**
- Description ≤ 1024 chars: use a Python one-liner to check.
- Total file ≤ 100k chars.
- Frontmatter starts at byte 0 with `---`.

---

### Task 10: One-shot install script

**Objective:** Install + smoke-check in a single command so the user (or a fresh Agent session) can go from cloned skill dir → working CLI in one line.

**Files:**
- Create: `scripts/install.sh`
- Create: `scripts/install.ps1`

**scripts/install.sh:**
```bash
#!/usr/bin/env bash
# One-shot install: uv tool install --editable + smoke check.
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Installing local-search from $SKILL_DIR ..."
uv tool install --editable "$SKILL_DIR" --force
echo
echo "Verifying:"
local-search --version
echo
echo "Running doctor:"
local-search doctor || {
    echo
    echo "→ Doctor reported issues. Common fixes:"
    echo "  Everything: powershell -File $SKILL_DIR/scripts/ensure-everything-user-session.ps1"
    echo "  AnyTxt:     start AnyTxt from Start Menu"
}
```

**scripts/install.ps1:** — PowerShell mirror; same three steps.

**Verify:**
```bash
bash ~/.hermes/profiles/devops/skills/system-administration/local-search/scripts/install.sh
# expected: install succeeds, --version prints, doctor runs
```

---

### Task 11: README + basic docs

**Objective:** Short human-facing README for anyone who cracks the skill directory open. Not the same as SKILL.md (which is agent-facing).

**Files:**
- Create: `README.md`

Should include:
- One-line pitch
- Install (one line)
- Prereqs (Everything ≥ 1.4 in user session; AnyTxt with HTTP enabled)
- Example commands
- Uninstall (`uv tool uninstall local-search`)
- Dev loop: `--editable` means edits to `src/local_search/` are live; no reinstall
- Where SKILL.md lives (pointer for humans curious about the agent guidance)

---

## Tests / Validation

- **Unit:** `pytest tests/` — filters, formatters (no live backend needed).
- **Smoke (live):** `local-search doctor && local-search files "SKILL.md" -n 3`.
- **Cross-shell:** run `local-search files "..."` from bash, pwsh, and cmd — all three should work post-install because `uv tool` puts the shim on PATH.
- **Editable proof:** modify a `click.echo` in `cli.py`, re-run without reinstall, see the change.

---

## Risks, tradeoffs, open questions

### Risks

1. **`everyfile` is alpha (2 GitHub stars).** If upstream breaks, we fork or fall back to `es.exe`. Mitigation: `errors.py`'s `BackendUnavailable` catches import errors and provides a clear message.
2. **AnyTxt response schema drift.** `_parse_file_entry` defensively handles both dict and list shapes.
3. **Windows-only.** Skill frontmatter declares `platforms: [windows]`. Everything and AnyTxt both have Linux/Mac builds, but the IPC/service model differs — future work if needed.
4. **`--path` semantic mismatch.** Everything's `path:` is substring; AnyTxt's `filterDir` is prefix. For most repo-scoped searches this is invisible, but if the user passes a bare folder name like `hermes`, Everything matches anywhere and AnyTxt likely returns 0. Document in the pitfalls section; if it becomes a real annoyance, add a `--path-mode substring|prefix` override.

### Tradeoffs

- **Chose `click` over `argparse`:** heavier dependency but nested subcommand groups + shared options are drastically cleaner.
- **Chose `rich` for `doctor` only:** doesn't bloat the main search path; can be swapped for plain text if we want zero third-party output deps.
- **`extract` re-uses AnyTxt's already-extracted text** (via `GetRawTextByFID`) instead of shelling out to `marker-pdf` / OCR. This is instant and free but limited to what AnyTxt already parsed — for un-indexed files, we surface a clear error pointing to `sync`, rather than silently falling back to a heavyweight extractor.
- **No OCR / GetFragmentAll subcommand in MVP.** Add later if the agent actually needs them; keeping surface area small.
- **No caching layer:** both backends already cache in-memory. Adding our own layer is premature optimization.

### Open questions (raise with user only if they surface during execution)

- Should `local-search text` retry once after a `ConnectError` to smooth over AnyTxt briefly being down? Probably not — Agent can just re-invoke. Ship without retry; add if flaky in practice.
- Do we want a `--json-lines` mode (NDJSON) for streaming very large result sets? Not for MVP; JSON array is fine at `--limit 20`.
- Should `recent` scan all drives or just the user's home tree? Currently all indexed drives. If noise is a problem, `-p ~` gives a sane default.

---

## Post-implementation memory update

After the skill is installed and doctored, add to persistent memory:

```
local-search skill installed under system-administration/. CLI: `local-search files|text|recent|extract|sync|doctor`. Everything (filenames) + AnyTxt (content + PDF/docx text extract + force-reindex). AnyTxt filterExt is "py;md" no dots no globs; fid is a string. Requires Everything in user session (Session != 0); ensure-everything-user-session.ps1 fixes.
```

Do NOT memorize file counts, install SHAs, or install-time details.

---

## Execution handoff

**Ready to execute.** Recommended: run tasks 1–11 in order (six subcommands live inside Task 6, so the task count stays at 11). Each task is self-contained. Commit boundaries are optional since the skill lives outside `git` unless the user later chooses to publish to a personal `dotfiles`/skills repo.

If executing via `subagent-driven-development`: dispatch one subagent per task with the full task text above as context. Two-stage review (spec compliance → code quality) after each.
