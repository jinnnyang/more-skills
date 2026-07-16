"""Render search results as markdown table (default), JSON, or CSV.

Row / ResultSet are the shared data shapes both backends produce.
"""
from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime


# AnyTxt highlight markers around matched keywords: *<<*keyword*>>*
_HIGHLIGHT_RE = re.compile(r"\*<<\*(.+?)\*>>\*")


@dataclass
class Row:
    """One search result row."""

    path: str
    size: int | None = None
    modified: datetime | None = None
    snippet: str | None = None       # may contain AnyTxt *<<*keyword*>>* markers

    def humansize(self) -> str:
        """Format size as human-readable string.

        v2 fix: uses a local variable so `self.size` is not mutated
        (v1 had a subtle bug where repeated calls returned wrong values).
        """
        if self.size is None:
            return ""
        size = float(self.size)
        if size < 1024:
            return f"{int(size)} B"
        for unit in ("KB", "MB", "GB", "TB"):
            size /= 1024
            if size < 1024:
                return f"{size:.1f} {unit}"
        return f"{size / 1024:.1f} PB"

    def modified_str(self) -> str:
        return self.modified.strftime("%Y-%m-%d %H:%M") if self.modified else ""

    def snippet_md(self) -> str:
        """Snippet with AnyTxt highlight markers converted to markdown **bold**."""
        if not self.snippet:
            return ""
        return _HIGHLIGHT_RE.sub(r"**\1**", self.snippet)

    def snippet_plain(self) -> str:
        """Snippet with AnyTxt highlight markers stripped (keyword kept)."""
        if not self.snippet:
            return ""
        return _HIGHLIGHT_RE.sub(r"\1", self.snippet)


@dataclass
class ResultSet:
    """A page of search results plus context."""

    mode: str                        # "files" | "text" | "recent"
    query: str
    elapsed_ms: int
    total: int                       # total matches known to backend (may exceed len(rows))
    rows: list[Row] = field(default_factory=list)

    @property
    def truncated(self) -> bool:
        """True when there are more matches than the current page returned."""
        return len(self.rows) < self.total


def as_markdown(rs: ResultSet) -> str:
    """Render a ResultSet as a markdown table (default output)."""
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

    footer_bits = [f"Total: {rs.total} matches"]
    if rs.truncated:
        footer_bits.append(f"showing {len(rs.rows)}, truncated")
    footer_bits.append(f"elapsed {rs.elapsed_ms} ms")
    footer = "\n_" + ", ".join(footer_bits) + "_"

    return "\n".join(lines) + footer


def as_json(rs: ResultSet) -> str:
    """Render a ResultSet as pretty-printed JSON.

    Includes a `truncated: bool` field so agents can detect paging without
    computing `len(results) < total` themselves.
    """
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
    """Render a ResultSet as CSV (path, size, modified, snippet)."""
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["path", "size", "modified", "snippet"])
    for r in rs.rows:
        w.writerow([
            r.path,
            r.size if r.size is not None else "",
            r.modified_str(),
            r.snippet_plain() if r.snippet else "",
        ])
    return out.getvalue()


def _escape_md(text: str) -> str:
    """Escape pipes and collapse newlines for markdown table cells."""
    return text.replace("|", "\\|").replace("\n", " ").strip()
