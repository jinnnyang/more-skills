"""AnyTxt full-text search via HTTP JSON-RPC 2.0 on 127.0.0.1:9920.

Wire-check confirmed (2026-07):

  Method: ATRpcServer.Searcher.V1.<leaf>

  Search response:
    {count: int}

  GetResult response:
    {count: int,
     field: ["fid","lastModify","size","file"],    ← column names
     files: [[str,str,str,str], ...]}              ← rows as tuples

  GetFragment response:
    {text: "... *<<*keyword*>>* ..."}              ← highlight markers

  GetRawTextByFID response:
    {text: "..."}                                  ← PDFs contain '📄 P N ' markers

  SyncIndex response:
    {}                                             ← no confirmation, verify with Search

Quirks:
  - fid, lastModify, size are all STRINGS (int() them on the client)
  - filterDir="" is server-rewritten to "C:" (only searches C drive)
  - filterExt is case-insensitive and tolerates dots/globs (normalized upstream)
  - errno=0 is success; errno=1 has been observed on success too
"""
from __future__ import annotations

import os
import re
import time
import uuid
from datetime import datetime

import httpx

from .errors import BackendUnavailable, InvalidQuery
from .filters import UnifiedFilters, to_anytxt_params
from .formatters import ResultSet, Row


_ANYTXT_URL = "http://127.0.0.1:9920"
_TIMEOUT = 15.0
_TIMEOUT_SYNC = 300.0

_PAGE_MARK_RE = re.compile(r"📄\s*P\s*\d+\s*")


# ---------------------------------------------------------------------------
# High-level operations
# ---------------------------------------------------------------------------

def search_text(base_query: str, f: UnifiedFilters, with_snippet: bool = True) -> ResultSet:
    """List files whose content matches `base_query`.

    Args:
        base_query: Content search phrase (non-empty).
        f: Filters (path, ext, sort, desc, limit, offset).
        with_snippet: Fetch a per-file snippet via GetFragment (adds ~1 RPC/row).

    Returns:
        ResultSet with mode="text".
    """
    if not base_query.strip():
        raise InvalidQuery(
            "`text` search requires a non-empty query — searching all indexed "
            "content is not supported (would take minutes and return millions of hits)."
        )

    params = to_anytxt_params(base_query, f)
    t0 = time.perf_counter()
    with _client(_TIMEOUT) as client:
        # GetResult returns the current page; its `count` is len(files), not
        # the total matches. Grab the real total via the cheap Search method.
        output = _call(client, "GetResult", params)
        rows_data = _parse_result_output(output)

        total_output = _call(client, "Search", {
            "pattern": params["pattern"],
            "filterDir": params["filterDir"],
            "filterExt": params["filterExt"],
            "lastModifyBegin": params["lastModifyBegin"],
            "lastModifyEnd": params["lastModifyEnd"],
        })
        total = int(total_output.get("count", len(rows_data)))

        rows: list[Row] = []
        for fid, path, mtime, size in rows_data:
            snippet = _fetch_snippet(client, fid, base_query) if with_snippet and fid else None
            rows.append(Row(
                path=path,
                size=size,
                modified=(datetime.fromtimestamp(mtime) if mtime else None),
                snippet=snippet,
            ))
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return ResultSet(
        mode="text",
        query=base_query,
        elapsed_ms=elapsed_ms,
        total=total,
        rows=rows,
    )


def count_matches(base_query: str, f: UnifiedFilters) -> int:
    """Cheap count-only via the `Search` method (no result list)."""
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


def get_raw_text(fid_or_path: str, strip_page_marks: bool = False) -> str:
    """Return AnyTxt's already-extracted plain text for a file.

    Accepts a FID string or filesystem path. Great for PDF/docx/pptx —
    text was extracted at index time, so this is instant. PDFs contain
    '📄 P N ' page markers; pass strip_page_marks=True to remove them.
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

    Returns:
        (elapsed_seconds, files_indexed_under_folder)

    SyncIndex responds with an empty dict, so we run a follow-up Search
    to count files under the folder as a verification signal.
    """
    folder = folder.replace("/", "\\")
    t0 = time.perf_counter()
    with _client(_TIMEOUT_SYNC) as client:
        _call(client, "SyncIndex", {"folder": folder})
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

    Raises BackendUnavailable on connect / HTTP / JSON-RPC error.
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
            "AnyTxt", f"HTTP {e.response.status_code}: {e.response.text[:200]}",
        ) from e

    data = resp.json()
    if data.get("error"):
        raise BackendUnavailable("AnyTxt", f"JSON-RPC error: {data['error']}")

    result_data = data.get("result", {}).get("data", {}) or {}
    errno = result_data.get("errno")
    # errno=0 is success; errno=1 has been observed on successful Search
    # responses with large result sets. Only bail on explicitly non-{0,1}.
    if isinstance(errno, int) and errno not in (0, 1):
        raise BackendUnavailable("AnyTxt", f"server errno={errno}")

    return result_data.get("output", {}) or {}


def _parse_result_output(output: dict) -> list[tuple[str | None, str, int | None, int | None]]:
    """Parse GetResult output into (fid, path, mtime, size) tuples.

    Uses the response's `field` array to map tuple columns — future-proof
    against schema changes.
    """
    field_order = output.get("field") or ["fid", "lastModify", "size", "file"]
    files = output.get("files") or []
    return [_parse_file_entry(entry, field_order) for entry in files]


def _parse_file_entry(
    entry, field_order: list[str],
) -> tuple[str | None, str, int | None, int | None]:
    """Map one AnyTxt result row to (fid, path, mtime, size).

    Handles both list-of-strings (wire-check confirmed shape) and dict
    (defensive fallback if the server ever changes shape).
    """
    if isinstance(entry, dict):
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

    return (
        str(fid) if fid is not None else None,
        str(path),
        mtime,
        size,
    )


def _fetch_snippet(client: httpx.Client, fid, keyword: str) -> str | None:
    """Best-effort snippet with *<<*keyword*>>* highlight markers.

    Never let a snippet failure sink the whole search.
    """
    try:
        output = _call(client, "GetFragment", {"fid": str(fid), "pattern": keyword})
    except Exception:
        return None
    text = output.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def _looks_like_path(s: str) -> bool:
    """Cheap heuristic: contains a slash or has a drive letter."""
    return ("\\" in s) or ("/" in s) or (len(s) > 2 and s[1] == ":")


def _resolve_fid_from_path(path: str) -> str:
    """Look up a FID by exact path.

    v2 optimization: filterExt=<ext> + pattern=<stem> + limit=5 for a fast
    scoped lookup, then verify by case-insensitive path equality.
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
        "limit": 5,
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
        f'file not indexed: {path}\n'
        f'Fix: local-search sync "{parent}"',
    )
