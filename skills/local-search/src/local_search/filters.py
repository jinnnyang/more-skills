"""Translate unified CLI filter args into per-backend query fragments.

Everything (via everyfile) and AnyTxt have overlapping but different filter
syntax. The user/agent sees ONE language; this module maps it two ways.

v2 semantics:
  --path  → PREFIX match on both backends (was substring on Everything in v1)
  --ext   → case-insensitive, dots and globs stripped (`*.PY` and `.py` both → `py`)
  --sort  → constrained to values valid on Everything (see VALID_SORT)
"""
from __future__ import annotations

from dataclasses import dataclass


VALID_SORT = frozenset({
    "name", "path", "size", "ext",
    "modified", "created", "accessed",
})


@dataclass(frozen=True)
class UnifiedFilters:
    """Shared filter state that both backends translate from."""

    path: str | None = None          # e.g. "C:\\dev\\hermes" or None (no restriction)
    ext: tuple[str, ...] = ()        # e.g. ("py", "md") — normalized lowercase, no dots
    sort: str = "name"               # must be in VALID_SORT
    desc: bool = False
    limit: int = 20
    offset: int = 0


def normalize_ext(exts: tuple[str, ...]) -> tuple[str, ...]:
    """Strip leading dots, leading globs, and lowercase.

    Examples:
        (".PY", "*.md", "txt") -> ("py", "md", "txt")
        ("*.", "  ", "") -> ()
    """
    out = []
    for e in exts:
        e = e.strip().lstrip("*").lstrip(".").lower()
        if e:
            out.append(e)
    return tuple(out)


def to_everything_query(base_query: str, f: UnifiedFilters) -> str:
    """Compose an Everything query string from a base query and filters.

    Prefix semantics (v2):
        --path C:\\dev\\hermes  →  path:C:\\dev\\hermes\\
        (Trailing backslash forces Everything to match only paths starting
        with that directory, matching AnyTxt's filterDir prefix behaviour.)

    Quoting:
        `path:C:\\dev\\hermes\\` (no quotes)          for paths without spaces
        `"path:C:\\Program Files\\"` (whole token)    for paths with spaces
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
      - filterDir="" is server-rewritten to "C:" (only searches C drive).
        We pass "" as-is; the CLI documents this quirk.
      - filterExt is case-insensitive and tolerates dots/globs, but we
        still normalize for determinism ("py;md", not ".PY;*.md").
      - filterExt="*" means all extensions.
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
    """AnyTxt order codes (per official API):
        0 default, 1 lastModify ASC, 2 lastModify DESC,
        3 filterDir ASC, 4 filterDir DESC.
    """
    if sort == "modified":
        return 2 if desc else 1
    if sort == "path":
        return 4 if desc else 3
    return 0
