"""Everything filename/path search via everyfile (pure-Python IPC).

Wire-check confirmed (2026-07):
  Signature:
    everyfile.search(query, *, fields='meta', sort='name', descending=False,
                     limit=None, offset=0, match_case=False, match_path=False,
                     match_whole_word=False, regex=False, instance=None) -> Cursor
  Cursor:
    .count = rows in current page (NOT total!)
    .total = total matches server has  ← we use this
  Row attributes: full_path, path, name, ext, size, is_file, is_folder,
                  date_modified (ISO str like '2026-07-16T07:09:46Z'),
                  date_created, date_accessed, attributes, hl_*
  Valid sort keys: name, path, size, ext, modified, created, accessed,
                   attributes, date-run, recently-chan
"""
from __future__ import annotations

import re
import time
from datetime import datetime

from .errors import BackendUnavailable, InvalidQuery
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
    """Search files by name / path / extension via everyfile.

    Args:
        base_query: The main query string (may be a regex when regex=True).
        f: Filters (path, ext, sort, desc, limit, offset).
        regex: Interpret base_query as a regular expression.
        match_path: Match against full path instead of just filename.
        match_case: Case-sensitive matching.
        match_whole_word: Whole-word matching.

    Returns:
        ResultSet with mode="files".

    Raises:
        BackendUnavailable: Everything IPC unreachable or timing out.
        InvalidQuery: base_query is not a valid regex when regex=True.
    """
    # Pre-validate the regex BEFORE hitting the backend. Everything's IPC
    # silently returns 0 rows for a malformed pattern, which is indistinguishable
    # from "no matches" — the worst kind of failure for an agent. Python's
    # re.compile is a good-enough proxy for Everything's regex flavor (both
    # are POSIX-ish, no lookahead/lookbehind); rejects the common syntax
    # mistakes (unclosed brackets, dangling quantifiers).
    if regex:
        try:
            re.compile(base_query)
        except re.error as e:
            raise InvalidQuery(
                f"Invalid regex {base_query!r}: {e}. "
                "Everything regex is POSIX-flavored: use . * + ? [] | () — "
                "no lookahead/lookbehind."
            ) from e

    try:
        from everyfile import search, EverythingError
    except ImportError as exc:
        raise BackendUnavailable(
            "Everything",
            f"everyfile package not installed: {exc}",
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
        total = cursor.total          # v2 fix: v1 used cursor.count (page size)
    except EverythingError as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)  # noqa: F841
        msg = str(e).lower()
        if "not running" in msg or "ipc" in msg or "not started" in msg:
            raise BackendUnavailable(
                "Everything",
                "not running in your user session (Session ID must be > 0). "
                "Run: local-search doctor",
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


# UnifiedFilters.sort  →  everyfile sort key (they're all direct passthroughs
# in v2, but keep the map for future divergence).
_SORT_MAP = {
    "name": "name",
    "path": "path",
    "size": "size",
    "ext": "ext",
    "modified": "modified",
    "created": "created",
    "accessed": "accessed",
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
