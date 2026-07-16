"""local-search CLI.

Subcommands:
  files    — find files by name / path / extension (Everything backend)
  text     — search inside files for a phrase (AnyTxt backend)
  recent   — recently modified files (Everything, sorted by mtime desc)
  extract  — print AnyTxt's extracted plain text (PDF/docx/pptx/…)
  sync     — force AnyTxt to (re)index a folder
  doctor   — health check both backends
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click

from . import __version__
from .errors import BackendUnavailable, InvalidQuery
from .filters import UnifiedFilters, VALID_SORT, normalize_ext
from .formatters import as_csv, as_json, as_markdown, ResultSet


_FORMAT_CHOICES = ["md", "json", "csv"]

# MSYS-style path prefix: /c/Users/... -> C:\Users\...
# Hermes' `terminal` runs bash on Windows and users/agents habitually paste
# git-bash paths. Detect and convert to native Windows form BEFORE calling
# Path.resolve() (which would otherwise prepend the CWD drive letter and
# produce garbage like C:\c\Users\...).
_MSYS_PATH_RE = re.compile(r"^/([a-zA-Z])/(.*)$")


def _normalize_path_arg(p: str | None) -> str | None:
    """Resolve -p / --path to an absolute Windows path.

    Handles three input styles:
      1. Native Windows: `C:\\Users\\me\\Desktop`   → passthrough (after resolve)
      2. Relative + tilde:  `.`, `~/Desktop`, `../foo`  → expand + resolve
      3. MSYS/git-bash:  `/c/Users/me/Desktop`     → `C:\\Users\\me\\Desktop`

    Empty strings and whitespace-only inputs return None (no restriction).
    """
    if not p or not p.strip():
        return None

    # MSYS-style → Windows-style (before Path.resolve, which would mangle it)
    m = _MSYS_PATH_RE.match(p)
    if m:
        drive, rest = m.group(1).upper(), m.group(2)
        p = f"{drive}:\\{rest.replace('/', chr(92))}"

    expanded = Path(p).expanduser()
    try:
        return str(expanded.resolve(strict=False))
    except (OSError, RuntimeError):
        return str(expanded)


def _shared_options(fn):
    """Apply the shared filter options to a Click command.

    Order matters: options apply bottom-up when decorators stack; we reverse
    so they appear top-down in --help.
    """
    for decorator in reversed([
        click.option("-n", "--limit", type=int, default=20, show_default=True,
                     help="Max results."),
        click.option("--offset", type=int, default=0, show_default=True,
                     help="Skip N results (pagination)."),
        click.option("-p", "--path", type=str, default=None,
                     help="Restrict to this directory (PREFIX match on both backends)."),
        click.option("-e", "--ext", type=str, default=None,
                     help="Extensions, comma-separated (e.g. py,md). Dots/globs/case normalized."),
        click.option("--sort", type=click.Choice(sorted(VALID_SORT)),
                     default="name", show_default=True),
        click.option("--desc", is_flag=True, default=False, help="Descending sort."),
        click.option("--format", "output_format", type=click.Choice(_FORMAT_CHOICES),
                     default="md", show_default=True, help="Output format."),
    ]):
        fn = decorator(fn)
    return fn


def _mk_filters(limit, offset, path, ext, sort, desc) -> UnifiedFilters:
    parsed_ext = normalize_ext(
        tuple(e.strip() for e in (ext or "").split(",") if e.strip())
    )
    return UnifiedFilters(
        path=_normalize_path_arg(path),
        ext=parsed_ext, sort=sort, desc=desc, limit=limit, offset=offset,
    )


def _render(rs: ResultSet, output_format: str) -> None:
    if output_format == "json":
        click.echo(as_json(rs))
    elif output_format == "csv":
        click.echo(as_csv(rs))
    else:
        click.echo(as_markdown(rs))


def _die(exc: BackendUnavailable | InvalidQuery) -> None:
    if isinstance(exc, InvalidQuery):
        click.echo(f"[error] {exc}", err=True)
        sys.exit(2)
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
@click.option("-r", "--regex", is_flag=True, help="Treat QUERY as a regular expression.")
@click.option("--match-path", is_flag=True,
              help="Match against the full path, not just filename.")
@click.option("--case", "match_case", is_flag=True, help="Case-sensitive matching.")
@click.option("--whole-word", "match_whole_word", is_flag=True, help="Whole-word matching.")
def files(query, limit, offset, path, ext, sort, desc, output_format,
          regex, match_path, match_case, match_whole_word):
    """Find files by name / path / extension (Everything backend)."""
    from .everything import search_files

    # Safety rail: an empty QUERY with no scope (-p, -e) matches the entire
    # 4M-file index and returns whatever `--sort name` orders alphabetically.
    # That's almost never what the caller wanted — usually a typo / bash
    # variable expanded to empty. Refuse and force explicit intent.
    if not query.strip() and not path and not ext:
        click.echo(
            "[error] Empty QUERY with no --path/--ext scope would match the "
            "entire index (millions of files).\n"
            "  If you want that, pass an explicit filter, e.g.:\n"
            "    local-search files \"\" -p C:\\Users\\me\\Desktop\n"
            "    local-search files \"\" -e py",
            err=True,
        )
        sys.exit(2)

    f = _mk_filters(limit, offset, path, ext, sort, desc)
    try:
        rs = search_files(
            query, f,
            regex=regex,
            match_path=match_path,
            match_case=match_case,
            match_whole_word=match_whole_word,
        )
    except (BackendUnavailable, InvalidQuery) as e:
        _die(e)
    _render(rs, output_format)


# ─── text ─────────────────────────────────────────────────────────────────

@main.command()
@click.argument("query", required=True)
@_shared_options
@click.option("--snippet/--no-snippet", default=True, show_default=True,
              help="Include per-file keyword snippet (adds 1 RPC per row).")
@click.option("--count-only", is_flag=True, default=False,
              help="Return only the total match count (cheap; uses Search endpoint).")
def text(query, limit, offset, path, ext, sort, desc, output_format,
         snippet, count_only):
    """Search inside file contents for a phrase (AnyTxt backend)."""
    from .anytxt import count_matches, search_text

    f = _mk_filters(limit, offset, path, ext, sort, desc)
    try:
        if count_only:
            if not query.strip():
                raise InvalidQuery(
                    "`text --count-only` requires a non-empty query."
                )
            n = count_matches(query, f)
            if output_format == "json":
                import json as _json
                click.echo(_json.dumps({"query": query, "count": n}, ensure_ascii=False))
            else:
                click.echo(f"**{n}** matches for `{query}`")
            return
        rs = search_text(query, f, with_snippet=snippet)
    except (BackendUnavailable, InvalidQuery) as e:
        _die(e)
    _render(rs, output_format)


# ─── recent ───────────────────────────────────────────────────────────────

def _parse_within(spec: str) -> str:
    """Translate --within value to an Everything `dm:` query fragment.

    Supported spellings:
      - Everything-native: any string starting with `dm:` is passed through
      - Named windows:  1h/hour, 1d/day/today, 1w/week, 1mo/month
      - Numeric + unit: 30min, 2h, 7d, 4w  (note: 'm' alone is NOT accepted
        due to conflict with 'month' in common tools)

    Raises click.BadParameter on unrecognized input.
    """
    spec = spec.strip().lower()

    # Everything-native: passthrough
    if spec.startswith("dm:"):
        return spec

    # Named
    named = {
        "hour": "dm:lasthour", "1h": "dm:lasthour",
        "today": "dm:today", "day": "dm:today", "1d": "dm:today",
        "week": "dm:lastweek", "1w": "dm:lastweek",
        "month": "dm:lastmonth", "1mo": "dm:lastmonth",
    }
    if spec in named:
        return named[spec]

    # <N>min (minutes) — explicit spelling to avoid m/month ambiguity
    if spec.endswith("min") and spec[:-3].isdigit():
        n = int(spec[:-3])
        threshold = datetime.now() - timedelta(minutes=n)
        return f"dm:>{threshold.strftime('%Y-%m-%dT%H:%M:%S')}"

    # <N><s|h|d|w>
    if len(spec) >= 2 and spec[-1] in "shdw" and spec[:-1].isdigit():
        n = int(spec[:-1])
        unit = spec[-1]
        # Named shortcuts for 1-of-a-unit
        if n == 1 and unit == "h":
            return "dm:lasthour"
        if n == 1 and unit == "d":
            return "dm:today"
        if n == 1 and unit == "w":
            return "dm:lastweek"
        factor = {"s": 1, "h": 3600, "d": 86400, "w": 86400 * 7}[unit]
        threshold = datetime.now() - timedelta(seconds=n * factor)
        return f"dm:>{threshold.strftime('%Y-%m-%dT%H:%M:%S')}"

    raise click.BadParameter(
        f"--within value {spec!r} not recognized. "
        "Try: 1h / today / 1w / month / 30min / 7d / 2w, or Everything-native dm:..."
    )


@main.command()
@click.option("--within", type=str, default="today", show_default=True,
              help="Time window: 1h/today/1w/month/30min/7d or dm:...")
@click.option("-n", "--limit", type=int, default=20, show_default=True,
              help="Max results.")
@click.option("--offset", type=int, default=0, show_default=True,
              help="Skip N results.")
@click.option("-p", "--path", type=str, default=None,
              help="Restrict to this directory (prefix).")
@click.option("-e", "--ext", type=str, default=None,
              help="Extensions, comma-separated.")
@click.option("--format", "output_format", type=click.Choice(_FORMAT_CHOICES),
              default="md", show_default=True)
def recent(within, limit, offset, path, ext, output_format):
    """Recently modified files (Everything, sorted by mtime desc).

    Sort is fixed to `modified desc` — that's the whole point of this command.
    """
    from .everything import search_files

    base_query = _parse_within(within)
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
@click.option("--count-only", is_flag=True, default=False,
              help="Just print the character count.")
@click.option("--strip-page-marks", is_flag=True, default=False,
              help="Strip AnyTxt PDF page markers (📄 P N ).")
def extract(path_or_fid, output, head, count_only, strip_page_marks):
    """Print AnyTxt's already-extracted plain text for a file.

    Accepts a filesystem path or a FID. Ideal for PDF/docx/pptx — text was
    extracted at index time, so this is instant (no marker-pdf, no OCR).
    The file must be in an AnyTxt-indexed folder; run `local-search sync`
    first if not.
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

    AnyTxt's SyncIndex returns no confirmation payload, so we follow up with
    a Search under `folder` and report the file count actually indexed. If
    the count is 0, the folder is likely not in AnyTxt's index configuration
    (Menu → Options → Index).
    """
    from .anytxt import sync_index

    click.echo(f"Syncing {folder} ... (may take a while for large folders)")
    try:
        elapsed, count = sync_index(folder)
    except BackendUnavailable as e:
        _die(e)

    if count == 0:
        click.echo(
            f"⚠️  Sync completed in {elapsed}s but 0 files are indexed under {folder}.\n"
            "    Verify AnyTxt Menu → Options → Index includes this folder.",
            err=True,
        )
        sys.exit(1)
    click.echo(f"✅ {count} files indexed under {folder} ({elapsed}s)")


# ─── doctor ───────────────────────────────────────────────────────────────

@main.command()
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", show_default=True,
              help="Output format (json for scripting).")
def doctor(output_format):
    """Diagnose both backends and print an actionable status report."""
    from .doctor import run_doctor
    ok = run_doctor(output_format=output_format)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
