# local-search Skill Implementation Plan — v2 (REVISED)

> **Version:** 2.0 (2026-07-16, 基于 REVIEW.md + AnyTxt/everyfile wire-check 实测重写)
> **Supersedes:** `2026-07-16_145318-local-search-skill.md` (v1)
> **Skill root:** `C:\Users\jinnn\Documents\more-skills\skills\local-search\`
>
> **Registration**: 用户手动 `mklink /J` 挂到需要的 agent profile 下。本计划**不依赖** hermes agent 的自动发现。
> **CLI 全局可用**: `uv tool install --editable .` — 已在 Task 1 完成。

**Goal:** Ship a `local-search` skill giving Hermes Agent (and the user) a fast, uniform CLI for local file & content search on Windows, backed by Voidtools **Everything** (filename/path via `everyfile`) and **AnyTxt** (full-text via HTTP JSON-RPC).

**Architecture:**
- Thin CLI wrapper (`click`) → dispatches to two backends:
  - `everything.py` — wraps `everyfile.search()` (pure-Python IPC, no DLL).
  - `anytxt.py` — HTTP JSON-RPC 2.0 client to AnyTxt on `127.0.0.1:9920`. **Uses field-order-driven parsing based on wire-check findings** (响应里 `field` 数组决定 `files` 每行 tuple 的列顺序).
- Unified `--path` / `--ext` semantics **统一为 prefix 语义** (v2 修正: v1 存在双语义混乱).
- Output layer: **markdown table (default)**, **json**, **csv**.
- Distributed as a `uv tool` (isolated venv, `--editable`).

**Command surface:** `files`, `text`, `recent`, `extract`, `sync`, `doctor` — 六个自解释子命令.

**Tech Stack:** Python 3.11, `click` (CLI), `httpx` (HTTP), `everyfile>=2026.4.22` (Everything IPC), `rich` (optional, doctor only), stdlib for csv/json/md.

---

## v1 → v2 变更总览

**基于 REVIEW.md 的 P0/P1 全部应用. wire-check 与 everyfile 探测把 8 处假设从"可能对"变成"实测正确"。**

### 🔴 P0 修正 (v1 完全错的)

| # | v1 假设 | v2 事实 (实测) |
|---|---|---|
| 1 | AnyTxt `GetResult.files` = list of dicts | list of tuples, 列顺序由 `output.field` 数组声明: `["fid","lastModify","size","file"]` |
| 2 | AnyTxt 路径字段叫 `path` 或 `filePath` | 叫 **`file`** |
| 3 | AnyTxt 数字字段 = int | fid/lastModify/size 全是 **str** — 需要客户端 int 转换 |
| 4 | AnyTxt `GetFragment` = `{fragment}` 或 `{text}` | 只有 `{text}`, 高亮用 `*<<*keyword*>>*` |
| 5 | AnyTxt `filterDir=""` = 全盘 | 服务端改写为 `C:`, **只搜 C 盘** |
| 6 | AnyTxt `filterExt` 必须 `"py;md"` 无点无 glob | 服务端容错 `.md` / `*.md` / `MD` |
| 7 | AnyTxt `SyncIndex` 返回文件数 | 返回空 dict `{}`, 需要 client 自己 verify |
| 8 | everyfile `total = cursor.count` | `cursor.count` = 本页行数; `cursor.total` = 总匹配数 |
| 9 | everyfile `EverythingError` 类名 | ✅ 确认: `EverythingError(Exception)` |
| 10 | everyfile `regex=`, `match_path=`, `case_sensitive=` | ✅ `regex`, `match_path`, **`match_case`** (不是 `case_sensitive`) |
| 11 | everyfile sort `"date_modified"` | 无效, 就叫 **`"modified"`**; `"extension"` 无效, 叫 **`"ext"`** |
| 12 | `Row.humansize()` 就地修改 `self.size` | 已修 (改用局部变量) |
| 13 | `recent` 命令吞掉 `--sort/--desc` | 已修 (v2 从 recent 移除这两个 flag) |
| 14 | `files` 命令 `--regex/--match-path/--case` 声明但不实现 | 已实装 (映射到 `regex`/`match_path`/`match_case`) |
| 15 | Everything `path:"..."` 加引号 | v2 只在含空格时加, 且引号包住整个 token |
| 16 | `recent` 用 `dm:>YYYY-MM-DD` (精度只到天) | v2 用 Everything 相对时间 `dm:lasthour`/`dm:today`/`dm:lastweek` |

### 🟡 P1 修正 (v1 有语义问题)

| # | v1 行为 | v2 行为 |
|---|---|---|
| 17 | `--path` Everything=substring, AnyTxt=prefix (双语义) | **统一 prefix** (Everything 用 `path:C:\dev\` 加尾反斜杠强制前缀) |
| 18 | `--ext` 只 lstrip(".") | v2 加 `.lower()` |
| 19 | `sync` 同时接受 positional 和 `-p/--path` | v2 只保留 positional `FOLDER` |
| 20 | `--within` 里 `m=分钟` (与 sleep/find 冲突) | v2 支持 `s/h/d/w` + `min`/`mo`, 不支持裸 `m` |
| 21 | `extract --head 0` = 只输出字符数 | v2 改成 `--count-only` |
| 22 | `doctor` 只有 rich table 输出 | v2 加 `--format {text,json}` |
| 23 | `rich` 在主 deps 里 | v2 移到 `[project.optional-dependencies].doctor` |

### 🟠 P2 增强

- everyfile ImportError 时降级到 `es.exe` CLI (若在 PATH);
- SyncIndex 完立刻 `Search(pattern="*", filterDir=folder)` 验证并显示 index 后文件数;
- CLI 加 `--offset`, JSON 输出加 `"truncated": bool` 字段;
- `_resolve_fid_from_path` 用 `filterExt=ext + pattern=stem + limit=1 + 精确路径比对` 优化;
- SKILL.md `related_skills` 顺序调整, `ocr-and-documents` 放第一位.

---

## 目录布局 (v2, 已含 Task 1 落地)

```
C:\Users\jinnn\Documents\more-skills\skills\local-search\
├── SKILL.md                       # ~10k chars, agent-facing trigger + usage
├── README.md                      # human-facing install/dev notes
├── REVIEW.md                      # (已存在) 评审报告 + wire-check findings
├── pyproject.toml                 # ✅ Task 1 done
├── .gitignore                     # ✅ Task 1 done
├── src/
│   └── local_search/
│       ├── __init__.py            # ✅ Task 1 done
│       ├── cli.py                 # ✅ Task 1 stub done; expand in Task 6
│       ├── everything.py          # Task 4
│       ├── anytxt.py              # Task 5 (field-order-driven parsing)
│       ├── formatters.py          # Task 3
│       ├── filters.py             # Task 2
│       ├── doctor.py              # Task 7
│       └── errors.py              # Task 4
├── scripts/
│   ├── ensure-everything-user-session.ps1   # Task 8
│   ├── install.sh                 # Task 10
│   └── install.ps1                # Task 10
└── tests/
    ├── test_filters.py            # Task 2
    ├── test_formatters.py         # Task 3
    ├── test_anytxt_parsers.py     # Task 5 (新增, 覆盖 field-order 逻辑)
    └── test_cli_smoke.py          # Task 6
```

预计 LOC (含 v2 新增逻辑): cli.py ~260, everything.py ~120, anytxt.py ~260, formatters.py ~90, filters.py ~65, doctor.py ~140, errors.py ~30. **总 ~965 LOC**, 仍算小巧.

---

## Task 1: ✅ 骨架 & 首装 (已完成)

**Done in this session:**
- `pyproject.toml` (dependencies + `[project.optional-dependencies].doctor` + `[project.scripts]`)
- `src/local_search/__init__.py` (`__version__ = "0.1.0"`)
- `src/local_search/cli.py` (Click group + doctor stub)
- `.gitignore`
- `uv tool install --editable . --force` 成功
- `local-search --version` / `--help` / `doctor` stub 都跑通

**Verify (已跑过):**
```bash
local-search --version    # → local-search, version 0.1.0
local-search --help       # → shows doctor stub
local-search doctor       # → "not yet implemented"
```

---

## Task 2: filters.py — 统一 --path/--ext/--sort 翻译

**Objective:** 纯函数模块, 把共享 CLI 参数翻译为每个后端的查询片段. 隔离到可脱机测试.

**Files:**
- Create: `src/local_search/filters.py`
- Create: `tests/test_filters.py`

**filters.py 关键差异 (vs v1):**
- `UnifiedFilters.sort` 默认 `"name"`, 但**valid choices** 收敛为实测确认的 everyfile 支持列表: `name/path/size/ext/modified/created/accessed`
- `to_everything_query()`:
  - `--path` **prefix 语义**: 生成 `path:C:\dev\` (强制加尾反斜杠) 而不是 `path:"C:\dev"`;
  - 含空格时用 `"path:C:\Program Files\"` (整个 token 引号包住);
- `to_anytxt_params()`:
  - `ext` 归一化: `e.lstrip(".").lower()`;
  - `filterDir=""` 时**警告**——AnyTxt 会 rewrite 为 `C:` 只搜 C 盘;
  - `filterExt` 空 tuple → `"*"`, 否则 `";".join(exts)`.
- `_anytxt_order()` 保留 v1 逻辑 (0/1/2/3/4).

```python
"""Translate unified CLI filter args into per-backend query fragments."""
from __future__ import annotations

from dataclasses import dataclass


VALID_SORT = frozenset({"name", "path", "size", "ext", "modified", "created", "accessed"})


@dataclass(frozen=True)
class UnifiedFilters:
    path: str | None = None          # e.g. "C:\\dev\\hermes" or None
    ext: tuple[str, ...] = ()        # e.g. ("py", "md") — lowercased, no dots
    sort: str = "name"
    desc: bool = False
    limit: int = 20
    offset: int = 0


def normalize_ext(exts: tuple[str, ...]) -> tuple[str, ...]:
    """Strip leading dots, lowercase. `.PY` and `*.py` both → `py`."""
    out = []
    for e in exts:
        e = e.strip().lstrip("*").lstrip(".").lower()
        if e:
            out.append(e)
    return tuple(out)


def to_everything_query(base_query: str, f: UnifiedFilters) -> str:
    """Compose an Everything query string.

    v2 semantics: --path is PREFIX. We generate `path:<dir>\\` so Everything
    matches only files whose full path starts with that directory.

    Quoting rule (实测): `path:C:\\dev\\hermes\\` (no quotes) works;
    含空格时用 `"path:C:\\Program Files\\"` (整个 token 引号包).
    """
    parts = [base_query] if base_query else []
    if f.ext:
        parts.append("ext:" + ";".join(f.ext))
    if f.path:
        normalized = f.path.replace("/", "\\").rstrip("\\") + "\\"
        if " " in normalized:
            parts.append(f'"path:{normalized}"')
        else:
            parts.append(f"path:{normalized}")
    return " ".join(parts)


def to_anytxt_params(
    base_query: str,
    f: UnifiedFilters,
    modified_after: int | None = None,
    modified_before: int | None = None,
) -> dict:
    """Build the `input` payload for AnyTxt's GetResult method.

    Wire-check findings (2026-07):
      - filterDir '' is rewritten to 'C:' by server → only searches C drive
      - filterExt is case-insensitive, tolerates dots and globs — but we
        still normalize to bare lowercase like 'py;md' for determinism
      - filterExt='*' means all
    """
    ext_filter = ";".join(f.ext) if f.ext else "*"
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
    """AnyTxt order codes: 0 default, 1 lastModify ASC, 2 DESC, 3 filterDir ASC, 4 DESC."""
    if sort == "modified":
        return 2 if desc else 1
    if sort == "path":
        return 4 if desc else 3
    return 0
```

**tests/test_filters.py — 新增 v2 用例:**
```python
from local_search.filters import (
    UnifiedFilters, normalize_ext, to_everything_query, to_anytxt_params, _anytxt_order,
)


def test_normalize_ext_strips_dots_and_globs_and_lowercases():
    assert normalize_ext(("py", ".md", "*.txt", ".PDF", "*.")) == ("py", "md", "txt", "pdf")


def test_everything_query_prefix_semantics():
    """v2: --path is a prefix (has trailing backslash)."""
    f = UnifiedFilters(path="C:/dev/hermes", ext=("py", "md"))
    q = to_everything_query("config", f)
    assert "ext:py;md" in q
    assert "path:C:\\dev\\hermes\\" in q  # trailing backslash for prefix
    assert '"' not in q  # no quotes when no spaces
    assert q.startswith("config")


def test_everything_query_path_with_spaces_gets_quoted():
    f = UnifiedFilters(path="C:/Program Files")
    q = to_everything_query("cfg", f)
    assert '"path:C:\\Program Files\\"' in q  # whole token quoted


def test_everything_query_bare():
    assert to_everything_query("readme", UnifiedFilters()) == "readme"


def test_anytxt_params_maps_ext_without_dots_or_globs():
    f = UnifiedFilters(ext=("py", "md"), path="C:/dev", limit=50)
    p = to_anytxt_params("hello", f)
    assert p["filterExt"] == "py;md"
    assert p["filterDir"] == "C:\\dev"
    assert p["pattern"] == "hello"
    assert p["limit"] == 50


def test_anytxt_params_no_ext_defaults_to_star():
    assert to_anytxt_params("foo", UnifiedFilters())["filterExt"] == "*"


def test_anytxt_order_codes():
    assert _anytxt_order("modified", True) == 2
    assert _anytxt_order("modified", False) == 1
    assert _anytxt_order("path", True) == 4
    assert _anytxt_order("path", False) == 3
    assert _anytxt_order("name", True) == 0
```

**Verify:**
```bash
cd C:/Users/jinnn/Documents/more-skills/skills/local-search
uv run pytest tests/test_filters.py -v  # expected: 7 passed
```

---

## Task 3: formatters.py — Row + md/json/csv 渲染器

**Objective:** 通用 Row/ResultSet 数据类 + 三种输出格式.

**v2 关键差异 vs v1:**
- `Row.humansize()` 用**局部变量** (v1 会破坏 `self.size`);
- `Row.snippet` 支持 AnyTxt 高亮标记 `*<<*keyword*>>*` → markdown `**keyword**` 转换 (可选, `render_highlight=True` 时启用);
- `as_json()` 输出加 `"truncated": bool` 字段, 明确告诉 agent 结果被截断.

```python
"""Render search results as markdown table (default), JSON, or CSV."""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime


# AnyTxt highlight markers around matched keywords
_HIGHLIGHT_RE = re.compile(r"\*<<\*(.+?)\*>>\*")


@dataclass
class Row:
    path: str
    size: int | None = None
    modified: datetime | None = None
    snippet: str | None = None       # may contain *<<*keyword*>>* markers

    def humansize(self) -> str:
        """v2 fix: use local variable so field isn't mutated."""
        if self.size is None:
            return ""
        size = float(self.size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def modified_str(self) -> str:
        return self.modified.strftime("%Y-%m-%d %H:%M") if self.modified else ""

    def snippet_md(self) -> str:
        """Convert AnyTxt highlight markers to markdown **bold**."""
        if not self.snippet:
            return ""
        return _HIGHLIGHT_RE.sub(r"**\1**", self.snippet)

    def snippet_plain(self) -> str:
        """Strip AnyTxt highlight markers, keep just the keyword."""
        if not self.snippet:
            return ""
        return _HIGHLIGHT_RE.sub(r"\1", self.snippet)


@dataclass
class ResultSet:
    mode: str                        # "files" | "text" | "recent"
    query: str
    elapsed_ms: int
    total: int                       # total matches (may exceed len(rows))
    rows: list[Row] = field(default_factory=list)

    @property
    def truncated(self) -> bool:
        return len(self.rows) < self.total


def as_markdown(rs: ResultSet) -> str:
    if not rs.rows:
        return f"_No matches for `{rs.query}` (elapsed {rs.elapsed_ms} ms)_"

    has_snippet = any(r.snippet for r in rs.rows)
    headers = ["#", "Path", "Size", "Modified"]
    if has_snippet:
        headers.append("Snippet")
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for i, r in enumerate(rs.rows, 1):
        cells = [str(i), _escape_md(r.path), r.humansize(), r.modified_str()]
        if has_snippet:
            cells.append(_escape_md(r.snippet_md()))
        lines.append("| " + " | ".join(cells) + " |")
    footer = (
        f"\n_Total: {rs.total} matches"
        + (f" (showing {len(rs.rows)}, truncated)" if rs.truncated else "")
        + f", elapsed {rs.elapsed_ms} ms_"
    )
    return "\n".join(lines) + footer


def as_json(rs: ResultSet) -> str:
    payload = {
        "mode": rs.mode,
        "query": rs.query,
        "elapsed_ms": rs.elapsed_ms,
        "total": rs.total,
        "truncated": rs.truncated,
        "results": [
            {
                "path": r.path,
                "size": r.size,
                "modified": r.modified.isoformat() if r.modified else None,
                "snippet": r.snippet_plain() if r.snippet else None,
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
        w.writerow([r.path, r.size or "", r.modified_str(), r.snippet_plain() if r.snippet else ""])
    return out.getvalue()


def _escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()
```

**tests/test_formatters.py — v2 新增用例:**
```python
from datetime import datetime
from local_search.formatters import ResultSet, Row, as_csv, as_json, as_markdown


def test_humansize_does_not_mutate_size():
    """v2 regression: v1 stored the divided value back into self.size."""
    r = Row(path="x", size=1024 * 1024 * 5)
    assert r.humansize() == "5.0 MB"
    assert r.size == 1024 * 1024 * 5  # unchanged
    assert r.humansize() == "5.0 MB"  # second call also correct


def test_snippet_highlight_markers_render_as_bold():
    r = Row(path="x", snippet="use *<<*faster-whisper*>>* medium int8")
    md = as_markdown(ResultSet(mode="text", query="fw", elapsed_ms=1, total=1, rows=[r]))
    assert "**faster-whisper**" in md


def test_json_has_truncated_field():
    rs = ResultSet(mode="files", query="q", elapsed_ms=5, total=100, rows=[Row(path="x")])
    import json as _j
    p = _j.loads(as_json(rs))
    assert p["truncated"] is True

    rs2 = ResultSet(mode="files", query="q", elapsed_ms=5, total=1, rows=[Row(path="x")])
    p2 = _j.loads(as_json(rs2))
    assert p2["truncated"] is False


def test_json_strips_highlight_markers():
    import json as _j
    rs = ResultSet(mode="text", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path="x", snippet="a *<<*b*>>* c")])
    p = _j.loads(as_json(rs))
    assert p["results"][0]["snippet"] == "a b c"


def test_markdown_empty_result():
    empty = ResultSet(mode="files", query="foo", elapsed_ms=5, total=0)
    assert "No matches" in as_markdown(empty)


def test_csv_has_header_and_row():
    rs = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path=r"C:\a.md", size=100, modified=datetime(2026, 7, 10, 14, 22))])
    out = as_csv(rs)
    lines = out.strip().splitlines()
    assert lines[0] == "path,size,modified,snippet"
    assert "a.md" in lines[1]


def test_markdown_escapes_pipes():
    rs = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path=r"C:\weird|name.md")])
    assert r"\|" in as_markdown(rs)
```

**Verify:**
```bash
uv run pytest tests/test_formatters.py -v  # expected: 7 passed
```

---

## Task 4: everything.py — everyfile 后端

**Objective:** `search_files()` + `es.exe` fallback + 精确异常映射.

**v2 关键差异 vs v1:**
- **`total = cursor.total`** (v1 用了 `cursor.count` 会显示本页行数, 严重误导);
- **异常类 `EverythingError(Exception)`** 已确认;
- `sort` valid values: `name/path/size/ext/modified/created/accessed` (v1 里写 `date_modified` 会 ValueError);
- **`regex` / `match_path` / `match_case` / `match_whole_word` 四个 kwargs** 直接透传;
- 加 `es.exe` 降级 (若 `everyfile` ImportError 或 IPC 失败).

```python
"""Everything filename/path search via everyfile (pure-Python IPC).

Wire-check confirmed (2026-07):
  - Signature: search(query, *, fields='meta', sort='name', descending=False,
                      limit=None, offset=0, match_case=False, match_path=False,
                      match_whole_word=False, regex=False, instance=None) -> Cursor
  - Cursor.count = rows in current page
  - Cursor.total = total matches server has
  - Row.date_modified is ISO string like '2026-07-16T07:09:46Z'
  - Valid sort keys: name/path/size/ext/modified/created/accessed/attributes/date-run/recently-chan
"""
from __future__ import annotations

import time
from datetime import datetime

from .errors import BackendUnavailable
from .filters import UnifiedFilters, to_everything_query
from .formatters import ResultSet, Row


def search_files(
    base_query: str,
    f: UnifiedFilters,
    *,
    regex: bool = False,
    match_path: bool = False,
    match_case: bool = False,
    match_whole_word: bool = False,
) -> ResultSet:
    """Filename/path search via everyfile."""
    try:
        from everyfile import search, EverythingError
    except ImportError as exc:
        raise BackendUnavailable(
            "Everything",
            f"everyfile not installed: {exc}",
        ) from exc

    query = to_everything_query(base_query, f)
    sort_key = _map_sort(f.sort)

    t0 = time.perf_counter()
    try:
        cursor = search(
            query,
            fields="meta",
            sort=sort_key,
            descending=f.desc,
            limit=f.limit,
            offset=f.offset,
            regex=regex,
            match_path=match_path,
            match_case=match_case,
            match_whole_word=match_whole_word,
        )
        raw_rows = cursor.fetchall()
        total = cursor.total  # v2 fix: was cursor.count in v1
    except EverythingError as e:
        msg = str(e).lower()
        if "not running" in msg or "ipc window" in msg or "not started" in msg:
            raise BackendUnavailable(
                "Everything",
                "not running in your user session. "
                "Run: local-search doctor  (or invoke ensure-everything-user-session.ps1)",
            ) from e
        if "timed out" in msg or "timeout" in msg:
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
            modified=_parse_iso_dt(getattr(r, "date_modified", None)),
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


_SORT_MAP = {
    "name": "name",
    "path": "path",
    "modified": "modified",     # NOT "date_modified" per wire-check
    "size": "size",
    "created": "created",
    "accessed": "accessed",
    "ext": "ext",
}


def _map_sort(sort: str) -> str:
    return _SORT_MAP.get(sort, "name")


def _parse_iso_dt(value) -> datetime | None:
    """Parse everyfile's ISO datetime string, e.g. '2026-07-16T07:09:46Z'."""
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

**errors.py — 同 v1:**
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

**Verify (live):**
```bash
uv run python -c "
from local_search.everything import search_files
from local_search.filters import UnifiedFilters
r = search_files('SKILL.md', UnifiedFilters(ext=('md',), limit=3))
print(f'total={r.total} rows={len(r.rows)} elapsed={r.elapsed_ms}ms')
for row in r.rows: print(' ', row.path, row.size, row.modified)
"
# expected: total>3000, 3 rows, elapsed <500ms, each row has size and datetime
```

---

## Task 5: anytxt.py — AnyTxt 后端 (**v2 重写**)

**Objective:** 基于 wire-check 实测的 **field-order-driven** 解析.

**v2 关键差异 vs v1:**
- **`_parse_result_output()`** 新增: 消费 `output.field` 数组来动态映射 `files` 里 tuple 的列;
- **`_parse_file_entry()`** 改为接受 `field_order: list[str]` 参数, 而不是硬编码列顺序;
- **`_fetch_snippet()`** 只查 `output.text` (wire-check 确认唯一字段);
- **`get_raw_text()`** 只查 `output.text` (且 wire-check 显示 PDF 会有 `📄 P N ` 页码标记, 加 `strip_page_marks` 参数);
- **`sync_index()`** 完成后立刻 `Search(pattern="*", filterDir=folder)` 验证, 返回 index 后文件数;
- **顶层 JSON-RPC error** 检查: 既查 `resp.get("error")` 也查 `resp["result"]["data"].get("errno")`.

```python
"""AnyTxt full-text search via HTTP JSON-RPC 2.0 on 127.0.0.1:9920.

Wire-check confirmed (2026-07):
  Search response:     {count: int}
  GetResult response:  {count: int, field: ["fid","lastModify","size","file"],
                        files: [[str,str,str,str], ...]}   ← files is list of tuples
  GetFragment response: {text: "... *<<*keyword*>>* ..."}
  GetRawTextByFID resp: {text: "..."}   ← PDFs contain '📄 P N ' page markers
  SyncIndex response:   {}              ← no confirmation, verify with Search
  Numeric fields (fid, lastModify, size) are all STRINGS, need client-side int()
"""
from __future__ import annotations

import os
import re
import time
import uuid
from datetime import datetime

import httpx

from .errors import BackendUnavailable
from .filters import UnifiedFilters, to_anytxt_params
from .formatters import ResultSet, Row

_ANYTXT_URL = "http://127.0.0.1:9920"
_TIMEOUT = 15.0
_TIMEOUT_SYNC = 300.0


# ---------------------------------------------------------------------------
# High-level operations
# ---------------------------------------------------------------------------

def search_text(base_query: str, f: UnifiedFilters, with_snippet: bool = True) -> ResultSet:
    """List files whose content matches `base_query`."""
    if not base_query.strip():
        raise ValueError("`text` search requires a non-empty query")

    params = to_anytxt_params(base_query, f)
    t0 = time.perf_counter()
    with _client(_TIMEOUT) as client:
        output = _call(client, "GetResult", params)
        rows_data = _parse_result_output(output)
        total = int(output.get("count", len(rows_data)))

        rows: list[Row] = []
        for fid, path, mtime, size in rows_data:
            snippet = None
            if with_snippet and fid is not None:
                snippet = _fetch_snippet(client, fid, base_query)
            rows.append(Row(
                path=path,
                size=size,
                modified=(datetime.fromtimestamp(mtime) if mtime else None),
                snippet=snippet,
            ))
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return ResultSet(mode="text", query=base_query, elapsed_ms=elapsed_ms,
                     total=total, rows=rows)


def count_matches(base_query: str, f: UnifiedFilters) -> int:
    """Cheap count-only via `Search` method."""
    params = {
        "pattern": base_query,
        "filterDir": (f.path or "").replace("/", "\\"),
        "filterExt": ";".join(f.ext) if f.ext else "*",
        "lastModifyBegin": 0,
        "lastModifyEnd": 2_147_483_647,
    }
    with _client(_TIMEOUT) as client:
        output = _call(client, "Search", params)
    return int(output.get("count", 0))


_PAGE_MARK_RE = re.compile(r"📄\s*P\s*\d+\s*")


def get_raw_text(fid_or_path: str, strip_page_marks: bool = False) -> str:
    """Return AnyTxt's extracted plain text.

    Accepts either a FID string or a filesystem path. PDFs contain
    '📄 P N ' page markers — pass strip_page_marks=True to remove them.
    """
    fid = fid_or_path
    if _looks_like_path(fid_or_path):
        fid = _resolve_fid_from_path(fid_or_path)

    with _client(_TIMEOUT) as client:
        output = _call(client, "GetRawTextByFID", {"fid": str(fid)})
    text = output.get("text") or ""
    if strip_page_marks:
        text = _PAGE_MARK_RE.sub("", text)
    return text


def sync_index(folder: str) -> tuple[int, int]:
    """Force AnyTxt to (re)index `folder`. Blocks until done.

    Returns (elapsed_seconds, files_indexed_after) — files count comes from a
    Search(pattern='*', filterDir=folder) POST-sync since SyncIndex response is
    empty.
    """
    folder = folder.replace("/", "\\")
    t0 = time.perf_counter()
    with _client(_TIMEOUT_SYNC) as client:
        _call(client, "SyncIndex", {"folder": folder})
        # Verify: SyncIndex returns empty dict, so query file count under folder
        verify_output = _call(client, "Search", {
            "pattern": "*",
            "filterDir": folder,
            "filterExt": "*",
            "lastModifyBegin": 0,
            "lastModifyEnd": 2_147_483_647,
        })
    elapsed = int(time.perf_counter() - t0)
    count = int(verify_output.get("count", 0))
    return elapsed, count


# ---------------------------------------------------------------------------
# Low-level RPC + parsing
# ---------------------------------------------------------------------------

def _client(timeout: float) -> httpx.Client:
    return httpx.Client(timeout=timeout)


def _call(client: httpx.Client, method_leaf: str, input_params: dict) -> dict:
    """Send a JSON-RPC call and unwrap `.result.data.output`.

    Raises BackendUnavailable on any error.
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
            "cannot reach http://127.0.0.1:9920 — is AnyTxt running? "
            "(Menu → Options → General → HTTP Service)",
        ) from e
    except httpx.HTTPStatusError as e:
        raise BackendUnavailable(
            "AnyTxt", f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        ) from e

    data = resp.json()
    if data.get("error"):
        raise BackendUnavailable("AnyTxt", f"JSON-RPC error: {data['error']}")
    result_data = data.get("result", {}).get("data", {}) or {}
    errno = result_data.get("errno")
    if isinstance(errno, int) and errno not in (0, 1):
        # errno==1 观察到伴随成功响应 (Search 大结果集), 只有明确非 0/1 才当错
        raise BackendUnavailable("AnyTxt", f"server errno={errno}")
    return result_data.get("output", {}) or {}


def _parse_result_output(output: dict) -> list[tuple[str | None, str, int | None, int | None]]:
    """Parse GetResult output into (fid, path, mtime, size) tuples.

    Uses the response's `field` array to map columns — future-proof against
    schema changes (server may add/reorder fields).
    """
    field_order = output.get("field") or ["fid", "lastModify", "size", "file"]
    files = output.get("files") or []
    result = []
    for entry in files:
        result.append(_parse_file_entry(entry, field_order))
    return result


def _parse_file_entry(
    entry, field_order: list[str],
) -> tuple[str | None, str, int | None, int | None]:
    """Map one row (list-of-values) to (fid, path, mtime, size).

    Field names per wire-check: 'fid', 'lastModify', 'size', 'file'.
    All values arrive as strings; numeric fields need int().
    """
    if isinstance(entry, dict):
        # Defensive fallback if server ever returns dicts
        row = entry
    elif isinstance(entry, (list, tuple)):
        row = dict(zip(field_order, entry))
    else:
        return None, str(entry), None, None

    fid = row.get("fid")
    path = row.get("file") or row.get("path") or row.get("filePath") or ""

    mtime_raw = row.get("lastModify") or row.get("modifiedTime")
    try:
        mtime = int(mtime_raw) if mtime_raw is not None else None
    except (ValueError, TypeError):
        mtime = None

    size_raw = row.get("size") or row.get("fileSize")
    try:
        size = int(size_raw) if size_raw is not None else None
    except (ValueError, TypeError):
        size = None

    return (str(fid) if fid is not None else None, str(path), mtime, size)


def _fetch_snippet(client: httpx.Client, fid, keyword: str) -> str | None:
    """Best-effort snippet with *<<*keyword*>>* highlight markers."""
    try:
        output = _call(client, "GetFragment", {"fid": str(fid), "pattern": keyword})
    except Exception:
        return None
    text = output.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def _looks_like_path(s: str) -> bool:
    return ("\\" in s) or ("/" in s) or (len(s) > 2 and s[1] == ":")


def _resolve_fid_from_path(path: str) -> str:
    """Look up a FID by exact path.

    v2 optimization: use filterExt=<ext> + pattern=<stem> + limit=1 for a fast
    single-row lookup, then verify path matches (case-insensitive on Windows).
    """
    normalized = path.replace("/", "\\")
    parent = os.path.dirname(normalized)
    base = os.path.basename(normalized)
    stem, dot, ext = base.rpartition(".")

    params = {
        "pattern": stem or base,
        "filterDir": parent,
        "filterExt": ext.lower() if dot else "*",
        "lastModifyBegin": 0,
        "lastModifyEnd": 2_147_483_647,
        "limit": 5,          # small: usually 1-2 hits
        "offset": 0,
        "order": 0,
    }
    with _client(_TIMEOUT) as client:
        output = _call(client, "GetResult", params)

    for fid, epath, _, _ in _parse_result_output(output):
        if epath.lower() == normalized.lower() and fid is not None:
            return fid

    raise BackendUnavailable(
        "AnyTxt",
        f"file not indexed: {path}\n"
        f'Fix: local-search sync "{parent}"',
    )
```

**tests/test_anytxt_parsers.py — 新增, 覆盖 field-order-driven 解析:**
```python
from local_search.anytxt import _parse_file_entry, _parse_result_output


def test_parse_file_entry_from_list_of_strings():
    """v2 wire-check: files rows are lists of strings, columns per `field`."""
    field_order = ["fid", "lastModify", "size", "file"]
    entry = ["2879675253150734652", "1761804532", "15674533",
             "C:\\Users\\jinnn\\Downloads\\PostgreSQL 18.0 Documentation.pdf"]
    fid, path, mtime, size = _parse_file_entry(entry, field_order)
    assert fid == "2879675253150734652"
    assert path.endswith("Documentation.pdf")
    assert mtime == 1761804532
    assert size == 15674533


def test_parse_file_entry_handles_reordered_fields():
    """If server ever swaps column order, our parser follows the field array."""
    field_order = ["size", "file", "lastModify", "fid"]
    entry = ["100", "C:\\a.txt", "1234567890", "99"]
    fid, path, mtime, size = _parse_file_entry(entry, field_order)
    assert fid == "99"
    assert path == "C:\\a.txt"
    assert mtime == 1234567890
    assert size == 100


def test_parse_file_entry_dict_fallback():
    """Server switching to dict form doesn't break us."""
    entry = {"fid": "123", "file": "C:\\b.md", "lastModify": "100", "size": "5"}
    fid, path, mtime, size = _parse_file_entry(entry, ["fid", "lastModify", "size", "file"])
    assert (fid, path, mtime, size) == ("123", "C:\\b.md", 100, 5)


def test_parse_result_output_uses_field_from_response():
    output = {
        "count": 1,
        "field": ["fid", "lastModify", "size", "file"],
        "files": [["1", "1700000000", "42", "C:\\x.py"]],
    }
    rows = _parse_result_output(output)
    assert rows == [("1", "C:\\x.py", 1700000000, 42)]


def test_parse_result_output_empty_files():
    output = {"count": 0, "field": ["fid", "lastModify", "size", "file"], "files": []}
    assert _parse_result_output(output) == []


def test_parse_result_output_missing_field_fallback():
    """If `field` is missing, fall back to default column order."""
    output = {"count": 1, "files": [["1", "1700000000", "42", "C:\\x.py"]]}
    rows = _parse_result_output(output)
    assert rows == [("1", "C:\\x.py", 1700000000, 42)]
```

**Verify (live, AnyTxt required):**
```bash
uv run python -c "
from local_search.anytxt import search_text, count_matches
from local_search.filters import UnifiedFilters
n = count_matches('the', UnifiedFilters())
print(f'count: {n}')
r = search_text('hermes', UnifiedFilters(ext=('md',), limit=3), with_snippet=True)
print(f'total={r.total} rows={len(r.rows)} elapsed={r.elapsed_ms}ms')
for row in r.rows:
    print(' ', row.path)
    if row.snippet: print('   snippet:', row.snippet[:80])
"
# expected: real count, 3 md rows with snippets containing *<<*hermes*>>*
```

---

## Task 6: cli.py — 全部子命令

**Objective:** Click 完整命令树, 六个子命令全部实装.

**v2 关键差异 vs v1:**
- `files` 子命令**真正传递** `regex/match_path/match_case`;
- `recent` 子命令**去掉** `--sort/--desc` (它们对 recent 无意义);
- `recent` **不再手工 dm:>YYYY-MM-DD**, 改用 Everything 相对时间语法 `dm:lasthour` 等;
- `sync` 去掉 `-p/--path` 别名, 只接受 positional `FOLDER`; sync 完打印 "Now indexed: N files";
- `extract --head 0` → `extract --count-only`;
- `extract` 加 `--strip-page-marks` 选项;
- `--within` 支持 `s/h/d/w/min/mo`, 不再支持裸 `m`;
- `_shared_options` 增加 `--offset`;
- 每个 CLI 命令 exception → `[error] ...` + `sys.exit(2)`.

```python
"""local-search CLI.

Subcommands:
  files    — find files by name / path / extension (Everything)
  text     — search inside files for a phrase (AnyTxt)
  recent   — recently modified files (Everything)
  extract  — print AnyTxt's extracted plain text (PDF/docx/pptx/...)
  sync     — force AnyTxt to (re)index a folder
  doctor   — health check both backends
"""
from __future__ import annotations

import sys

import click

from . import __version__
from .errors import BackendUnavailable
from .filters import UnifiedFilters, VALID_SORT, normalize_ext
from .formatters import as_csv, as_json, as_markdown, ResultSet


_FORMAT_CHOICES = ["md", "json", "csv"]


def _shared_options(fn):
    """Apply the shared filter options to a Click command."""
    for decorator in reversed([
        click.option("-n", "--limit", type=int, default=20, show_default=True, help="Max results."),
        click.option("--offset", type=int, default=0, show_default=True, help="Skip N results (pagination)."),
        click.option("-p", "--path", type=str, default=None,
                     help="Restrict to this path (PREFIX match on both backends)."),
        click.option("-e", "--ext", type=str, default=None,
                     help="Extensions, comma-separated (e.g. py,md). Dots/globs/case are normalized."),
        click.option("--sort", type=click.Choice(sorted(VALID_SORT)),
                     default="name", show_default=True),
        click.option("--desc", is_flag=True, default=False, help="Descending sort."),
        click.option("--format", "output_format", type=click.Choice(_FORMAT_CHOICES),
                     default="md", show_default=True, help="Output format."),
    ]):
        fn = decorator(fn)
    return fn


def _mk_filters(limit, offset, path, ext, sort, desc) -> UnifiedFilters:
    parsed_ext = normalize_ext(tuple(e.strip() for e in (ext or "").split(",") if e.strip()))
    return UnifiedFilters(
        path=path, ext=parsed_ext, sort=sort, desc=desc, limit=limit, offset=offset,
    )


def _render(rs: ResultSet, output_format: str) -> None:
    if output_format == "json":
        click.echo(as_json(rs))
    elif output_format == "csv":
        click.echo(as_csv(rs))
    else:
        click.echo(as_markdown(rs))


def _die(exc: BackendUnavailable) -> None:
    click.echo(f"[error] {exc}\nRun `local-search doctor` for diagnostics.", err=True)
    sys.exit(2)


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Fast unified local file and full-text search (Everything + AnyTxt)."""


# ─── files ────────────────────────────────────────────────────────────────

@main.command()
@click.argument("query", required=True)
@_shared_options
@click.option("-r", "--regex", is_flag=True, help="Treat QUERY as regex.")
@click.option("--match-path", is_flag=True, help="Match against full path, not just filename.")
@click.option("--case", "match_case", is_flag=True, help="Case-sensitive.")
@click.option("--whole-word", "match_whole_word", is_flag=True, help="Whole-word match.")
def files(query, limit, offset, path, ext, sort, desc, output_format,
          regex, match_path, match_case, match_whole_word):
    """Find files by name / path / extension (Everything backend)."""
    from .everything import search_files
    f = _mk_filters(limit, offset, path, ext, sort, desc)
    try:
        rs = search_files(query, f, regex=regex, match_path=match_path,
                          match_case=match_case, match_whole_word=match_whole_word)
    except BackendUnavailable as e:
        _die(e)
    _render(rs, output_format)


# ─── text ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("query", required=True)
@_shared_options
@click.option("--snippet/--no-snippet", default=True, show_default=True,
              help="Include keyword snippet in results.")
@click.option("--count-only", is_flag=True, default=False,
              help="Return only the total match count (cheap; uses Search endpoint).")
def text(query, limit, offset, path, ext, sort, desc, output_format, snippet, count_only):
    """Search inside file contents for a phrase (AnyTxt backend)."""
    from .anytxt import search_text, count_matches
    f = _mk_filters(limit, offset, path, ext, sort, desc)
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
        _die(e)
    _render(rs, output_format)


# ─── recent ───────────────────────────────────────────────────────────────

_RELATIVE_TIME_MAP = {
    # Everything supports these relative-time modifiers natively
    "1h": "dm:lasthour",
    "hour": "dm:lasthour",
    "1d": "dm:today",
    "day": "dm:today",
    "today": "dm:today",
    "1w": "dm:lastweek",
    "week": "dm:lastweek",
    "1mo": "dm:lastmonth",
    "month": "dm:lastmonth",
}


def _parse_within(spec: str) -> str:
    """Translate --within value to an Everything `dm:` query fragment.

    Supported: `1h`/`hour`, `1d`/`today`, `1w`/`week`, `1mo`/`month`, or
    Everything-native `dm:...` passed through untouched.
    """
    spec = spec.strip().lower()
    if spec.startswith("dm:"):
        return spec  # pass through Everything-native syntax
    if spec in _RELATIVE_TIME_MAP:
        return _RELATIVE_TIME_MAP[spec]
    # Numeric with unit
    if len(spec) >= 2 and spec[-1] in "shdw" and spec[:-1].isdigit():
        # Convert to nearest Everything native — best effort
        n = int(spec[:-1])
        unit = spec[-1]
        if unit == "h" and n <= 1:
            return "dm:lasthour"
        if unit == "d" and n <= 1:
            return "dm:today"
        if unit == "w" and n <= 1:
            return "dm:lastweek"
        # For larger windows, fall back to date range
        from datetime import datetime, timedelta
        seconds = {"s": 1, "h": 3600, "d": 86400, "w": 86400 * 7}[unit]
        threshold = datetime.now() - timedelta(seconds=n * seconds)
        return f"dm:>{threshold.strftime('%Y-%m-%dT%H:%M:%S')}"
    if spec.endswith("min") and spec[:-3].isdigit():
        from datetime import datetime, timedelta
        n = int(spec[:-3])
        threshold = datetime.now() - timedelta(minutes=n)
        return f"dm:>{threshold.strftime('%Y-%m-%dT%H:%M:%S')}"
    raise click.BadParameter(
        f"--within value {spec!r} not recognized. "
        "Use e.g. 1h / today / 1w / 30min / 7d / month, or Everything-native dm:..."
    )


@main.command()
@click.option("--within", type=str, default="today", show_default=True,
              help="Time window: 1h/today/1w/month/30min/7d or dm:...")
@click.option("-n", "--limit", type=int, default=20, show_default=True)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("-p", "--path", type=str, default=None,
              help="Restrict to this path (prefix).")
@click.option("-e", "--ext", type=str, default=None)
@click.option("--format", "output_format", type=click.Choice(_FORMAT_CHOICES),
              default="md", show_default=True)
def recent(within, limit, offset, path, ext, output_format):
    """Recently modified files (Everything, sorted by mtime desc)."""
    from .everything import search_files

    base_query = _parse_within(within)
    # recent always sorts by modified desc — no user override
    f = _mk_filters(limit, offset, path, ext, "modified", True)
    try:
        rs = search_files(base_query, f)
    except BackendUnavailable as e:
        _die(e)
    rs.mode = "recent"
    _render(rs, output_format)


# ─── extract ──────────────────────────────────────────────────────────────

@main.command()
@click.argument("path_or_fid", required=True)
@click.option("-o", "--output", type=click.Path(), default=None,
              help="Write to file instead of stdout.")
@click.option("--head", type=int, default=None,
              help="Print only the first N chars.")
@click.option("--count-only", is_flag=True, help="Just print the char count.")
@click.option("--strip-page-marks", is_flag=True,
              help="Strip AnyTxt PDF page markers (📄 P N ).")
def extract(path_or_fid, output, head, count_only, strip_page_marks):
    """Print AnyTxt's already-extracted plain text.

    Accepts a filesystem path or a FID. Great for PDFs/.docx/.pptx —
    text was extracted at index time, so this is instant and free.
    """
    from .anytxt import get_raw_text
    try:
        text = get_raw_text(path_or_fid, strip_page_marks=strip_page_marks)
    except BackendUnavailable as e:
        _die(e)

    if count_only:
        click.echo(f"{len(text)} chars extracted")
        return

    body = text[:head] if head else text
    if output:
        from pathlib import Path
        Path(output).write_text(body, encoding="utf-8")
        click.echo(f"Wrote {len(body)} chars → {output}")
    else:
        click.echo(body)


# ─── sync ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("folder", required=True)
def sync(folder):
    """Force AnyTxt to (re)index a folder. Blocks until done.

    Since AnyTxt's SyncIndex returns no confirmation, we run a follow-up
    Search under `folder` and report the file count actually indexed.
    """
    from .anytxt import sync_index
    click.echo(f"Syncing {folder} ... (may take a while)")
    try:
        elapsed, count = sync_index(folder)
    except BackendUnavailable as e:
        _die(e)
    if count == 0:
        click.echo(f"⚠️  Sync completed in {elapsed}s but 0 files indexed under {folder}.")
        click.echo("    Verify AnyTxt Menu → Options → Index includes this folder.")
    else:
        click.echo(f"✅ Indexed {count} files in {folder} ({elapsed}s)")


# ─── doctor ───────────────────────────────────────────────────────────────

@main.command()
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", show_default=True)
def doctor(output_format):
    """Diagnose both backends."""
    from .doctor import run_doctor
    ok = run_doctor(output_format=output_format)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

**Verify:**
```bash
local-search --help
local-search files "SKILL.md" -n 3
local-search files "SKILL.md" -n 3 --format json    # → has "truncated": bool
local-search files "test_.*\.py" --regex --sort modified --desc -n 5
local-search files "hermes" --match-path -n 5
local-search recent --within 1h -e md
local-search recent --within today
local-search recent --within 30min
local-search text "hello" --count-only
local-search text "hermes" -e md -n 3    # → snippets with **bold** highlight
local-search sync C:\Users\jinnn\Desktop
local-search extract "C:\Users\jinnn\Downloads\PostgreSQL 18.0 Documentation(A4).pdf" --head 500 --strip-page-marks
local-search doctor --format json
```

---

## Task 7: doctor.py — 双后端体检 (v2)

**Objective:** 可执行的健康检查, 支持 `--format text|json`, 失败时打印 `ensure-everything-user-session.ps1` 完整路径.

**v2 关键差异:**
- 加 `output_format="text"|"json"` 参数;
- lazy import `rich` (若缺则用纯 text 输出), 从主 deps 移除;
- Everything 失败提示引用 `ensure-everything-user-session.ps1` 的**绝对路径**;
- AnyTxt 使用 wire-check 过的 `Search(pattern="the")` 计数.

```python
"""Health checks for both backends."""
from __future__ import annotations

import json as _json
import subprocess
import time
from pathlib import Path

import httpx


def run_doctor(output_format: str = "text") -> bool:
    """Run all health checks; print results; return True iff all backends OK."""
    ok_ev, elapsed_ev, detail_ev = _check_everything()
    ok_at, elapsed_at, detail_at = _check_anytxt()

    if output_format == "json":
        _print_json(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at)
    else:
        _print_text(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at)

    return ok_ev and ok_at


def _print_json(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at):
    payload = {
        "everything": {"ok": ok_ev, "elapsed_ms": elapsed_ev, "detail": detail_ev},
        "anytxt": {"ok": ok_at, "elapsed_ms": elapsed_at, "detail": detail_at},
        "ok": ok_ev and ok_at,
    }
    print(_json.dumps(payload, ensure_ascii=False, indent=2))


def _print_text(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at):
    try:
        from rich.console import Console
        from rich.table import Table
        con = Console()
        con.rule("[bold]local-search doctor[/bold]")
        t = Table(show_lines=False)
        t.add_column("Check", style="cyan")
        t.add_column("Status")
        t.add_column("Detail / Fix")
        t.add_row("Everything (files)", "✅ OK" if ok_ev else "❌ FAIL", detail_ev)
        t.add_row("AnyTxt (text)", "✅ OK" if ok_at else "❌ FAIL", detail_at)
        con.print(t)
    except ImportError:
        # Plain fallback when rich not installed
        print("=== local-search doctor ===")
        print(f"Everything (files):  {'OK' if ok_ev else 'FAIL'}  [{elapsed_ev} ms]  {detail_ev}")
        print(f"AnyTxt (text):       {'OK' if ok_at else 'FAIL'}  [{elapsed_at} ms]  {detail_at}")


def _check_everything() -> tuple[bool, int, str]:
    try:
        from everyfile import search, EverythingError
    except ImportError as e:
        return False, 0, f"everyfile not installed: {e}"

    t0 = time.perf_counter()
    try:
        cursor = search("*", fields="meta", limit=1)
        _ = cursor.fetchmany(1)
        total = cursor.total
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return True, elapsed_ms, f"IPC OK, {total} files indexed"
    except EverythingError as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        msg = str(e).lower()
        if "not running" in msg or "ipc window" in msg:
            fix = _everything_session_hint()
            return False, elapsed_ms, f"not running in user session. {fix}"
        if "timed out" in msg or "timeout" in msg:
            return False, elapsed_ms, "Index still loading — wait 10 s and re-run."
        return False, elapsed_ms, str(e)
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def _everything_session_hint() -> str:
    """Point at the idempotent PowerShell fixer script we ship."""
    script = Path(__file__).resolve().parent.parent.parent / "scripts" / "ensure-everything-user-session.ps1"
    if script.exists():
        return f'Fix: powershell -ExecutionPolicy Bypass -File "{script}"'

    # Fallback: try to find Everything exe from service
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Service | Where-Object Name -match 'verything').PathName"],
            capture_output=True, text=True, timeout=10,
        )
        exe = r.stdout.strip().strip('"').split(" -svc")[0].strip('"')
        if exe and "Everything" in exe:
            return f'Fix: Start-Process "{exe}"'
    except Exception:
        pass
    return "Fix: launch Everything from Start Menu / tray."


def _check_anytxt() -> tuple[bool, int, str]:
    """Ping AnyTxt via the cheap `Search` method."""
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "id": "doctor",
                "jsonrpc": "2.0",
                "method": "ATRpcServer.Searcher.V1.Search",
                "params": {"input": {
                    "pattern": "the",
                    "filterDir": "",
                    "filterExt": "*",
                    "lastModifyBegin": 0,
                    "lastModifyEnd": 2147483647,
                }},
            }
            r = client.post("http://127.0.0.1:9920", json=payload)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            if r.status_code != 200:
                return False, elapsed_ms, f"HTTP {r.status_code}: {r.text[:120]}"
            body = r.json()
            if body.get("error"):
                return False, elapsed_ms, f"RPC error: {body['error']}"
            count = body.get("result", {}).get("data", {}).get("output", {}).get("count", 0)
            return True, elapsed_ms, f"HTTP OK, {count} files match 'the'"
    except httpx.ConnectError:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return False, elapsed_ms, "127.0.0.1:9920 unreachable — start AnyTxt (Menu→Options→General→HTTP Service)"
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"
```

**Verify:**
```bash
local-search doctor
local-search doctor --format json    # → structured payload
```

---

## Task 8: ensure-everything-user-session.ps1 — 同 v1

保持 v1 内容不变, 作用点没变.

**Verify:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/ensure-everything-user-session.ps1
```

---

## Task 9: SKILL.md — agent-facing 触发文档 (v2)

**Objective:** trigger-rich 但简洁的技能主文档.

**v2 关键差异 vs v1:**
- `description` 挤更多关键词 (~950 字符, 从 v1 的 630 提升);
- `related_skills` 顺序: `ocr-and-documents` 放**第一位** + 明确二者互补关系;
- Common Pitfalls 里加"`filterDir='' → 只搜 C 盘"这条 (wire-check 发现);
- pitfall 里 `ensure-everything-user-session.ps1` 使用**新的绝对路径** (`C:\Users\jinnn\Documents\more-skills\skills\local-search\scripts\...`).

**关键 frontmatter:**
```yaml
---
name: local-search
description: Use when finding files by name/path or searching inside file contents on the local Windows machine. Faster than `search_files` / `ls -R` / `find` / ripgrep when the search would touch many directories, because it uses live indexes (Voidtools Everything for filenames, AnyTxt for full-text). One CLI (`local-search`) with self-explanatory subcommands: `files` (filename/path/ext, sub-second), `text` (full-text incl. PDF/docx/pptx/code), `recent` (recently modified), `extract` (turn PDF/docx/pptx into plain text using AnyTxt's index — instant, no marker-pdf/OCR needed), `sync` (force reindex a folder after writing new files so agent can search them immediately), `doctor` (health-check both backends). Default output is a markdown table; `--format json/csv` for machine consumption. Windows only.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [search, files, filesystem, indexing, everything, anytxt, windows, pdf, docx, pptx, extract, grep, fulltext, ripgrep-alternative, local-search]
    related_skills: [ocr-and-documents, hermes-agent, hermes-windows-troubleshooting]
---
```

**Body key sections** (完整正文见实施时具体撰写):
- Overview
- When to Use (含反例)
- **Relationship to `ocr-and-documents`**: `local-search extract` = 免费 (AnyTxt 已索引的文件); `ocr-and-documents` = 未索引的、需要 OCR 的、需要精确布局的
- Install (`uv tool install --editable ...`)
- 6 个子命令的详细示例
- Common Pitfalls (7 条, 含 wire-check 发现的 C 盘限制)
- Verification Checklist

**Verify:**
- Description 字符数 ≤ 1024
- 总文件 ≤ 100k 字符
- Frontmatter 起始 `---`

---

## Task 10: 安装脚本 (`install.sh` / `install.ps1`) — 同 v1

保持 v1 结构, 但**路径改为新工作目录**:
```bash
# scripts/install.sh
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # 依然对应到 more-skills/skills/local-search
uv tool install --editable "$SKILL_DIR" --force
local-search --version
local-search doctor
```

---

## Task 11: README.md — 人类阅读的说明 (同 v1 结构)

内容与 v1 一致, 但**明确说明**:
- 技能开发路径: `C:\Users\jinnn\Documents\more-skills\skills\local-search\`
- 用户需 `mklink /J` 到 hermes agent 的 skills 目录才能被自动发现
- `uv tool install --editable` 已经让 CLI 全局可用, agent 可直接调用 CLI, 不必依赖 SKILL.md 的自动加载

---

## 完整测试策略 (v2)

**Unit tests (pytest, no live backend):**
- `test_filters.py` — 7 tests (v2 加了 prefix 语义 + normalize_ext + 引号规则)
- `test_formatters.py` — 7 tests (v2 加了 humansize regression + truncated 字段 + highlight marker)
- `test_anytxt_parsers.py` — 6 tests (**v2 新增**, field-order-driven 解析)

**Smoke (live, 需 Everything + AnyTxt):**
```bash
local-search doctor
local-search files "SKILL.md" -n 3
local-search files "*.py" -p C:/Users/jinnn/Documents --regex -n 5
local-search text "hermes" -e md -n 3
local-search text "the" --count-only
local-search recent --within 1h
local-search sync C:/Users/jinnn/Desktop
local-search extract "<some.pdf>" --count-only
```

**Editable proof:**
- 修改 `src/local_search/cli.py` 里任意 `click.echo`, 重新运行, 见到变更即证明 editable.

---

## 风险 & 权衡 (v2)

### 保留自 v1
- `everyfile` 是 alpha; **v2 增加 mitigation**: doctor 的 EverythingError 消息里明确指向 `ensure-everything-user-session.ps1` 路径;
- Windows-only;
- markdown-first 输出兼容 agent 场景.

### v2 新的风险
- **AnyTxt `filterDir=""` 只搜 C 盘的限制**: 在 SKILL.md pitfalls 里明确写出, 用户若有多盘可传显式 `-p D:\` 分别搜; 若日后需要, 可加 `--all-drives` 开关内部循环所有 fixed drives (**MVP 不做**);
- **AnyTxt errno 语义不清**: 观察到 `errno=1` 伴随成功响应 (Search 大结果集), `errno=0` 也是成功 (Sync/GetFragment). v2 的 `_call()` 只在明确非 0/1 才抛 — **可能漏掉一些真错误**. 保守做法, 未来跟进.

### 权衡决策 (v2 新增)
- **`--path` 统一为 prefix**: 放弃 Everything 的 substring 灵活性以换来跨后端语义一致. 用户若需要 substring, 直接把关键词写进 QUERY 而非 `--path`.
- **`recent` 移除 `--sort/--desc`**: 语义就是"按 mtime 倒序", 显式移除比"接受输入然后忽略"更诚实.
- **`--within` 语法**: 拥抱 Everything 原生 `dm:...` 语法而不是自己重发明; `1h/today/1w/30min` 是常用别名, 其他直接透传 `dm:`.

---

## 实施顺序 (v2 建议)

**优先级排序:** 从"仅需 mock 的可测部分"到"依赖活体后端的部分", 每一步都能独立跑 pytest 或 smoke.

1. ✅ Task 1 — 骨架 & 首装 (已完成)
2. **Task 2 — filters.py + tests** (纯函数, 无外部依赖)
3. **Task 3 — formatters.py + tests** (纯函数, 无外部依赖)
4. **Task 4 — everything.py** (live smoke — Everything 用户会话)
5. **Task 5 — anytxt.py + parsers tests** (mocked unit tests + live smoke)
6. **Task 6 — cli.py 全命令** (`--help` 各命令跑通)
7. **Task 7 — doctor.py** (`local-search doctor` 输出正常)
8. **Task 8 — ensure-everything-user-session.ps1**
9. **Task 9 — SKILL.md** (最后写, 因为要根据实际实现描述 pitfalls)
10. **Task 10 — install.sh/ps1**
11. **Task 11 — README.md**

**每 Task 结束后:** 跑 `pytest` (相关 test 文件) + `local-search doctor` + 该 Task 声明的 verify 命令. 全绿再进入下一 Task.

**手动 mklink 注册时机**: 全部 Task 完成、smoke test 通过后, 由用户手动执行:
```powershell
mklink /J `
  "C:\Users\jinnn\.hermes\profiles\devops\skills\system-administration\local-search" `
  "C:\Users\jinnn\Documents\more-skills\skills\local-search"
```
(以及需要挂到的其他 agent profile 下.)

---

## Post-implementation memory update

安装并 doctor 通过后, 添加到持久内存:

```
local-search 已安装为 uv tool @ C:\Users\jinnn\Documents\more-skills\skills\local-search. CLI: local-search files|text|recent|extract|sync|doctor. Everything (filenames) + AnyTxt (fulltext + PDF/docx text extract + reindex). --path 是 prefix 语义. AnyTxt filterDir='' 只搜 C 盘. Everything 需 user session (Session != 0), ensure-everything-user-session.ps1 修.
```

不要记 install SHA / 文件数 / commit ID.

---

## Execution handoff

**Ready to execute.** v2 计划已 wire-check + everyfile probe 双重验证, 所有 P0/P1 已应用. 每 Task 2–5 分钟聚焦工作.

**若用 subagent-driven-development**: 每 Task 派一个 subagent, 上下文塞完整 Task 文本. 每 Task 完成两阶段 review (spec compliance → code quality).

---

## v2 相对 v1 的净收益

| 维度 | v1 (原计划) | v2 (本文档) |
|---|---|---|
| 代码级 Bug | 6 个未修 | 全部修复 |
| AnyTxt API 假设 | 4 处错误 | wire-check 确认, 100% 匹配实测 |
| everyfile API 假设 | 参数名/异常类未验证 | probe 确认, `EverythingError` / `regex` / `match_path` / `match_case` |
| `cursor.total` vs `.count` | 用错字段导致 total 严重错误 | 使用正确字段 |
| `--path` 语义 | 双语义混乱 | 统一 prefix |
| Test 覆盖 | filters+formatters | filters+formatters+**anytxt_parsers** (6 new tests) |
| Rich 依赖 | 主 deps | optional deps |
| JSON 输出 | 无截断信号 | `truncated: bool` |
| 高亮标记 | 未处理 | `*<<*key*>>*` → `**key**` 转换 |
| SyncIndex verify | 空响应无法确认 | 后置 Search 计数 |
| 相关 skill | ocr-and-documents 顺序靠后 | 放第一 + 明确互补 |

预计**总返工减少 60%+**, 因为字段名 / 参数名 / 异常类都已提前钉死.
