#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Session Handoff Protocol · reconcile helper (flat-file layout).

Deterministic logic for the `hand-off` / `take-over` skills. Keeps YAML
parsing, git reality-check, cleanup classification, and atomic writes out
of the LLM's cognitive path (protocol §9 invariant "script-assisted
execution").

Layout (flat-file, no prefix)
-----------------------------
Every handoff scope lives DIRECTLY inside a directory. The four core files
use their natural short names — the enclosing directory identifies what
they belong to:

    <scope>/context.md
    <scope>/task.md
    <scope>/walkthrough.md
    <scope>/questions.md
    <scope>/plan.md         (optional)
    <scope>/review.md       (optional)

A "scope" is any directory containing at least one file whose YAML
frontmatter carries a recognised handoff ``kind`` value. This avoids
false positives from unrelated ``context.md`` / ``task.md`` files in
generic projects.

Scope resolution
----------------
1. If ``--scope <path>`` is passed, use it verbatim.
2. Else if pwd contains at least one file with recognised handoff ``kind``
   frontmatter, use pwd (silent).
3. Else emit ``WARNING`` on stderr with an explicit prompt structure so the
   caller (agent) can decide via ``clarify`` whether to init at pwd or
   pick another location. Exit code 3 for this "ambiguous scope" state.

Commands
--------
init      [--scope P]              write core docs at scope from templates
validate  [--scope P | --all-scopes]  frontmatter enum + timestamp sanity
check-reality [--scope P | --all-scopes] [--apply-soft-conflicts]
                                   verify docs vs git/fs; log SOFT conflicts
clean-up  [--scope P | --all-scopes] (--dry-run | --apply)
                                   classify walkthrough / questions entries;
                                   ``<!-- resolved -->`` questions migrate
                                   to the ``## Closed`` archive section.
write-atomic --filepath P (--content S | --content-file P | stdin)
                                   write P atomically via <P>.tmp + rename
list-scopes  [--root R]            find every scope under R (default: cwd)

Invocation
----------
Skills call this via::

    uv run <SKILL_DIR>/scripts/reconcile.py <command> [--scope ...] ...

which uses the inline script metadata above to install pyyaml on demand.
Running via bare `python` requires pyyaml on the ambient interpreter.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - environment error path
    sys.stderr.write(
        "reconcile.py: missing pyyaml. Run via "
        "'uv run <path>/reconcile.py ...' so uv installs the "
        "inline-script dependency automatically.\n"
    )
    sys.exit(2)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"

DEFAULT_DOCS = ["context.md", "task.md", "walkthrough.md", "questions.md"]
OPTIONAL_DOCS = ["plan.md", "review.md"]
ALL_DOCS = DEFAULT_DOCS + OPTIONAL_DOCS

VALID_KINDS = {"context", "task", "walkthrough", "questions", "plan", "review"}
VALID_STATUS = {"in-progress", "blocked", "phase-complete", "archived"}
VALID_WRITERS = {"hand-off", "take-over", "user", "migration"}

STALE_DAYS = 30           # walkthrough entry auto-stale threshold
VERIFY_STALE_DAYS = 7     # last_verified SOFT-conflict threshold

# Directories skipped when scanning for scopes (list-scopes / --all-scopes).
SCOPE_SCAN_SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".tox", "dist", "build", "target", ".idea", ".vscode",
    ".ruff_cache",
}
SCOPE_SCAN_MAX_DEPTH = 6

# Candidate filenames whose frontmatter is inspected during scope detection.
_SCOPE_CANDIDATE_NAMES = set(ALL_DOCS)

# ---------------------------------------------------------------------------
# Frontmatter (pyyaml-backed)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


def load_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    yaml_str, body = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"invalid YAML frontmatter: {e}") from e
    if not isinstance(meta, dict):
        raise ValueError(
            f"frontmatter root must be a mapping, got {type(meta).__name__}"
        )
    return meta, body


def dump_frontmatter(meta: dict, body: str) -> str:
    yaml_str = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
    body = body.lstrip("\n")
    return f"---\n{yaml_str}\n---\n\n{body}" if body else f"---\n{yaml_str}\n---\n"


def parse_iso_timestamp(v: object) -> tuple[bool, str | None]:
    if isinstance(v, datetime):
        return (True, None) if v.tzinfo else (False, "naive datetime (missing timezone)")
    if not isinstance(v, str):
        return False, f"expected ISO-8601 string, got {type(v).__name__}"
    try:
        dt = datetime.fromisoformat(v)
    except ValueError as e:
        return False, f"unparseable ISO-8601: {e}"
    return (True, None) if dt.tzinfo else (False, "missing timezone offset")


def as_aware_datetime(v: object) -> datetime | None:
    if isinstance(v, datetime):
        return v if v.tzinfo else None
    if not isinstance(v, str):
        return None
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    return dt if dt.tzinfo else None


def validate_meta(meta: dict, filename: str) -> list[str]:
    errors: list[str] = []
    kind = meta.get("kind")
    if kind not in VALID_KINDS:
        errors.append(
            f"{filename}: invalid kind={kind!r} (must be one of {sorted(VALID_KINDS)})"
        )
    for ts_field in ("last_updated", "last_verified"):
        v = meta.get(ts_field)
        if v is None:
            errors.append(f"{filename}: missing {ts_field}")
            continue
        if v == "SKIPPED":
            continue
        ok, err = parse_iso_timestamp(v)
        if not ok:
            errors.append(f"{filename}: {ts_field}={v!r} — {err}")
    status = meta.get("status")
    if status is not None and status not in VALID_STATUS:
        errors.append(
            f"{filename}: invalid status={status!r} (must be one of {sorted(VALID_STATUS)})"
        )
    writer = meta.get("last_writer")
    if writer is not None and writer not in VALID_WRITERS:
        errors.append(
            f"{filename}: invalid last_writer={writer!r} "
            f"(must be one of {sorted(VALID_WRITERS)})"
        )
    return errors


# ---------------------------------------------------------------------------
# Path helpers (MSYS-aware)
# ---------------------------------------------------------------------------


def resolve_msys_path(p: str | os.PathLike[str]) -> Path:
    """Translate MSYS-style paths (/c/foo, /tmp/foo) to native Windows paths.

    On non-Windows hosts this is a no-op wrapper around ``Path``.
    """
    s = os.fspath(p)
    if os.name != "nt":
        return Path(s)
    # /c/foo → C:/foo, /d/foo → D:/foo, etc.
    m = re.match(r"^/([A-Za-z])/(.*)$", s)
    if m:
        return Path(f"{m.group(1).upper()}:/{m.group(2)}")
    # /tmp/... → $TMPDIR or $TEMP or C:\Users\<u>\AppData\Local\Temp
    if s.startswith("/tmp/") or s == "/tmp":
        tmp_root = os.environ.get("TMPDIR") or os.environ.get("TEMP") or os.environ.get("TMP")
        if tmp_root:
            tail = s[len("/tmp"):].lstrip("/")
            return Path(tmp_root) / tail if tail else Path(tmp_root)
    return Path(s)


# ---------------------------------------------------------------------------
# Atomic write (POSIX rename + Windows os.replace)
# ---------------------------------------------------------------------------


def write_atomic(filepath: str | os.PathLike[str], content: str) -> None:
    fp = resolve_msys_path(filepath)
    fp.parent.mkdir(parents=True, exist_ok=True)
    tmp = fp.with_suffix(fp.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8", newline="\n")
        os.replace(tmp, fp)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Concurrency Lock Helpers
# ---------------------------------------------------------------------------


def check_lock_conflict(scope: Path, session_id: str | None) -> str | None:
    lock_file = scope / ".handoff.lock"
    if not lock_file.exists():
        return None
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        locked_session = data.get("session_id")
        if session_id and locked_session == session_id:
            return None  # Same session, no conflict
        
        # Check TTL
        acquired_at_str = data.get("acquired_at")
        if acquired_at_str:
            try:
                acquired_at = datetime.fromisoformat(acquired_at_str)
                if not acquired_at.tzinfo:
                    acquired_at = acquired_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if (now - acquired_at).total_seconds() > 7200:
                    return None  # Expired lock is not considered a conflict (will be overridden on write)
            except Exception:
                pass
        
        locked_agent = data.get("agent", "unknown")
        locked_at = data.get("acquired_at", "unknown")
        return f"Locked by agent {locked_agent!r} (session: {locked_session!r}) since {locked_at}"
    except Exception as e:
        return f"Locked by invalid lock file (error reading: {e})"


def acquire_lock(scope: Path, session_id: str | None, agent: str | None) -> str | None:
    if not session_id:
        return None
    conflict = check_lock_conflict(scope, session_id)
    if conflict:
        return conflict
    lock_file = scope / ".handoff.lock"
    lock_data = {
        "session_id": session_id,
        "agent": agent or "unknown",
        "acquired_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
    }
    try:
        # Atomic lock file creation (O_CREAT | O_EXCL)
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(lock_data, indent=2))
        return None
    except FileExistsError:
        # Check again in case it was written concurrently or has expired
        return check_lock_conflict(scope, session_id)


def release_lock(scope: Path, session_id: str) -> None:
    lock_file = scope / ".handoff.lock"
    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text(encoding="utf-8"))
            if data.get("session_id") == session_id:
                lock_file.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def git(*args: str, cwd: Path | str | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False,
            cwd=cwd
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "git not on PATH"


def git_repo_root(cwd: Path | str | None = None) -> Path | None:
    rc, out, _ = git("rev-parse", "--show-toplevel", cwd=cwd)
    if rc != 0:
        return None
    return Path(out.strip()).resolve()


def git_status_paths(cwd: Path | str | None = None) -> set[str]:
    rc, out, _ = git("status", "--porcelain", cwd=cwd)
    if rc != 0:
        return set()
    paths: set[str] = set()
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_part = line[3:].strip()
        if " -> " in path_part:
            parts = path_part.split(" -> ")
            target_path = parts[-1].strip('"').replace("\\", "/")
        else:
            target_path = path_part.strip('"').replace("\\", "/")
        paths.add(target_path)
    return paths


def git_recent_committed_files(n: int = 5, cwd: Path | str | None = None) -> set[str]:
    rc, out, _ = git("log", f"-{n}", "--name-only", "--pretty=format:", cwd=cwd)
    if rc != 0:
        return set()
    return {ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()}


def git_deleted_files(since_days: int = 90, cwd: Path | str | None = None) -> set[str]:
    rc, out, _ = git(
        "log",
        f"--since={since_days}.days",
        "--diff-filter=D",
        "--name-only",
        "--pretty=format:",
        cwd=cwd
    )
    if rc != 0:
        return set()
    return {ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()}


# ---------------------------------------------------------------------------
# Cross-platform file-reference detection
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_PATH_TOKEN_RE = re.compile(
    r"""(?:[`"'\(\s]|^)
        (
          (?:[A-Za-z]:[\\/][^\s`"'\(\)\[\]]+)  # Windows absolute
          |
          (?:/[A-Za-z]/[^\s`"'\(\)\[\]]+)      # MSYS absolute
          |
          (?:/[^\s`"'\(\)\[\]]+)                # Unix absolute
          |
          (?:\.\.?/[^\s`"'\(\)\[\]]+)            # Relative with ./ or ../
          |
          (?:\.\.?\\+[^\s`"'\(\)\[\]]+)          # Relative with Windows backslash
          |
          (?:[^\s`"'\(\)\[\]]+(?:[\\/][^\s`"'\(\)\[\]]+)+) # Relative with slashes
        )
    """,
    re.VERBOSE,
)

_PATH_DENY_PREFIXES = (
    "/http", "/dev/", "/tmp/", "/usr/bin/", "/etc/", "/proc/", "/sys/",
    "/var/", "//",
)


def strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


def _looks_like_file_reference(candidate: str) -> bool:
    if any(candidate.startswith(pfx) for pfx in _PATH_DENY_PREFIXES):
        return False
    if "://" in candidate:
        return False
    name = candidate.replace("\\", "/").rsplit("/", 1)[-1]
    return "." in name


def normalize_reference_path(p: str) -> Path:
    """Alias retained for backward compatibility; MSYS-aware."""
    return resolve_msys_path(p)


def extract_referenced_paths(body: str) -> list[str]:
    stripped = strip_code_fences(body)
    seen: list[str] = []
    for m in _PATH_TOKEN_RE.finditer(stripped):
        candidate = m.group(1).strip("`\"'()[]")
        candidate = candidate.split("#", 1)[0]
        if _looks_like_file_reference(candidate) and candidate not in seen:
            seen.append(candidate)
    return seen


# ---------------------------------------------------------------------------
# Section splitting (markdown ##)
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^(#{2,3}\s+.*)$", re.MULTILINE)
_DATE_IN_HEADER_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_KEEP_TAG_RE = re.compile(r"<!--\s*keep\s*-->", re.IGNORECASE)
_RESOLVED_TAG_RE = re.compile(r"<!--\s*resolved\s*-->", re.IGNORECASE)
_KEEP_WORD_RE = re.compile(r"\b(lesson|surprise|decision|invariant)\b", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"^\s*-?\s*(none\.?|tbd\.?|n/?a\.?)\s*$",
                              re.IGNORECASE | re.MULTILINE)


def strip_html_comments_preserving_tags(text: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        block = m.group(0)
        stripped = block.strip()
        if stripped.lower() in {"<!--keep-->", "<!-- keep -->", "<!--resolved-->",
                                 "<!-- resolved -->"}:
            return block
        if "\n" not in stripped and len(stripped) <= 40:
            return block
        return ""
    return _HTML_COMMENT_RE.sub(_replace, text)


def _is_placeholder(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    for line in stripped.splitlines():
        if not line.strip():
            continue
        if not _PLACEHOLDER_RE.match(line):
            return False
    return True


def split_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    prefix_lines = []
    sections: list[tuple[str, str]] = []
    
    in_code_block = False
    current_header = None
    current_content_lines = []
    
    lines = body.splitlines(keepends=True)
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            
        if not in_code_block and (line.startswith("## ") or line.startswith("### ")):
            if current_header is None:
                prefix = "".join(prefix_lines)
            else:
                sections.append((current_header, "".join(current_content_lines)))
                current_content_lines = []
            current_header = line
        else:
            if current_header is None:
                prefix_lines.append(line)
            else:
                current_content_lines.append(line)
                
    if current_header is not None:
        sections.append((current_header, "".join(current_content_lines)))
        
    prefix = "".join(prefix_lines) if current_header is not None else body
    return prefix, sections


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------


def _peek_kind(p: Path) -> str | None:
    """Read only enough of file `p` to extract the frontmatter ``kind`` field.

    Returns the kind string when present + recognised, else None. Cheap enough
    to run against every ``*.md`` candidate during scope discovery.
    """
    try:
        lines = []
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
            if not first.startswith("---"):
                return None
            lines.append(first)
            for _ in range(100):
                line = fh.readline()
                if not line:
                    break
                lines.append(line)
                if line.startswith("---"):
                    break
            else:
                return None
        text = "".join(lines)
        meta, _ = load_frontmatter(text)
        kind = meta.get("kind")
        return kind if isinstance(kind, str) and kind in VALID_KINDS else None
    except Exception:
        return None
    kind = meta.get("kind")
    return kind if isinstance(kind, str) and kind in VALID_KINDS else None


def scope_has_docs(scope: Path) -> bool:
    """A directory qualifies as a scope if any candidate file has handoff kind."""
    if not scope.is_dir():
        return False
    for name in _SCOPE_CANDIDATE_NAMES:
        candidate = scope / name
        if candidate.is_file() and _peek_kind(candidate) is not None:
            return True
    return False


def scope_docs_present(scope: Path) -> list[str]:
    """Return the ordered list of recognised handoff docs actually present."""
    present: list[str] = []
    for name in ALL_DOCS:
        candidate = scope / name
        if candidate.is_file() and _peek_kind(candidate) is not None:
            present.append(name)
    return present


def resolve_scope(explicit: str | None, *, allow_missing: bool = False) -> Path:
    """Resolve the target scope directory.

    Rules:
      1. explicit `--scope <path>`: use verbatim (after MSYS resolution).
      2. pwd contains recognised handoff docs: use pwd silently.
      3. Otherwise emit WARNING on stderr describing the ambiguity and
         exit with code 3 unless ``allow_missing=True`` (used by ``init``).
    """
    if explicit:
        p = resolve_msys_path(explicit).resolve()
        return p

    cwd = Path.cwd()
    if scope_has_docs(cwd):
        return cwd

    if allow_missing:
        return cwd

    sys.stderr.write(
        "WARNING: no handoff docs found in current directory "
        f"{cwd}.\n"
        "  Options:\n"
        "    (a) init a new scope here by running:\n"
        f"          reconcile.py init --scope {cwd}\n"
        "    (b) specify an existing scope:\n"
        "          reconcile.py <cmd> --scope /path/to/scope\n"
        "    (c) discover existing scopes:\n"
        "          reconcile.py list-scopes\n"
    )
    sys.stderr.flush()
    print(json.dumps({
        "status": "ambiguous_scope",
        "message": (
            "No handoff docs (recognised kind frontmatter) in cwd and no "
            "--scope given. Agent must clarify with the user before proceeding."
        ),
        "cwd": str(cwd),
    }, indent=2))
    sys.exit(3)


def find_scopes(root: Path, max_depth: int = SCOPE_SCAN_MAX_DEPTH) -> list[Path]:
    """Return all scope directories at or below ``root`` (deduped, sorted)."""
    root = root.resolve()
    results: set[Path] = set()

    def _walk(cur: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = list(cur.iterdir())
        except OSError:
            return
        if scope_has_docs(cur):
            results.add(cur.resolve())
        for p in entries:
            if p.is_dir() and p.name not in SCOPE_SCAN_SKIP_DIRS and not p.is_symlink():
                _walk(p, depth + 1)

    _walk(root, 0)
    return sorted(results)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    scope = resolve_scope(args.scope, allow_missing=True)
    scope.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    agent = args.agent or "unknown-agent"
    session_id = args.session_id or "unknown-session"
    writer = args.writer or "migration"

    lock_err = acquire_lock(scope, session_id, agent)
    if lock_err:
        print(json.dumps({
            "status": "error",
            "message": f"Cannot initialize: {lock_err}"
        }, indent=2))
        sys.exit(1)

    initialized: list[str] = []
    skipped: list[str] = []
    missing_templates: list[str] = []
    for doc in DEFAULT_DOCS:
        target = scope / doc
        if target.exists():
            skipped.append(doc)
            continue
        template = TEMPLATES_DIR / doc
        if not template.exists():
            missing_templates.append(doc)
            continue
        content = template.read_text(encoding="utf-8")
        for token, value in (
            ("{{TIMESTAMP}}", now),
            ("{{AGENT}}", agent),
            ("{{WRITER}}", writer),
            ("{{SESSION_ID}}", session_id),
        ):
            content = content.replace(token, value)
        write_atomic(target, content)
        initialized.append(doc)

    result = {
        "status": "success" if not missing_templates else "partial",
        "scope": str(scope),
        "initialized": initialized,
        "skipped": skipped,
        "missing_templates": missing_templates,
    }
    print(json.dumps(result, indent=2))
    if missing_templates:
        sys.exit(1)


def _validate_scope(scope: Path) -> dict:
    if not scope.exists():
        return {"scope": str(scope), "status": "error",
                "message": f"{scope} does not exist"}
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    for doc in ALL_DOCS:
        p = scope / doc
        if not p.exists():
            if doc in DEFAULT_DOCS:
                warnings.append(f"{doc}: missing (core doc)")
            continue
        try:
            body_raw = p.read_text(encoding="utf-8")
            meta, body = load_frontmatter(body_raw)
        except ValueError as e:
            errors.append(f"{doc}: {e}")
            continue
        checked.append(doc)
        errors.extend(validate_meta(meta, doc))
        
        # Validate date format in walkthrough.md headers to prevent parsing bugs
        if doc == "walkthrough.md" and not errors:
            prefix, sections = split_sections(body)
            for header, _ in sections:
                title = header.strip("# \r\n")
                date_match = _DATE_IN_HEADER_RE.search(header)
                if not date_match:
                    warnings.append(
                        f"walkthrough.md: header {title!r} does not contain "
                        "valid YYYY-MM-DD date. Will be ignored by clean-up."
                    )
    return {
        "scope": str(scope),
        "status": "success" if not errors else "invalid",
        "checked": checked,
        "warnings": warnings,
        "errors": errors,
    }


def cmd_validate(args: argparse.Namespace) -> None:
    scopes = _collect_scopes(args)
    results = [_validate_scope(s) for s in scopes]
    payload = _wrap_batch(results)
    print(json.dumps(payload, indent=2))
    if any(r.get("status") in {"error", "invalid"} for r in results):
        sys.exit(1)


def _check_reality_scope(scope: Path, apply_soft: bool, session_id: str | None = None,
                         agent: str | None = None, acquire: bool = False) -> dict:
    if not scope.exists():
        return {"scope": str(scope), "status": "error",
                "message": f"{scope} does not exist"}

    hard_conflicts: list[dict] = []
    soft_conflicts: list[dict] = []

    # Concurrency Lock Check
    #
    # Historical bug (2026-07-20): passing --session-id was silently promoting
    # this read-only preflight into a write op (acquire_lock). See take-over's
    # DECISIONS.md ADR R35 / R36 for the full history.
    #
    # Semantics now: acquire only when the caller opts in (acquire=True /
    # --acquire-lock). hand-off's _prepare_scope passes acquire=True because
    # it *is* the intending-to-write caller; ad-hoc CLI users of
    # `check-reality` get read-only behaviour by default.
    if acquire and session_id:
        lock_err = acquire_lock(scope, session_id, agent)
    else:
        lock_err = check_lock_conflict(scope, session_id)
        
    if lock_err:
        hard_conflicts.append({
            "type": "concurrency_lock_conflict",
            "message": lock_err,
        })

    repo_root = git_repo_root(cwd=scope)
    is_git = repo_root is not None
    uncommitted = git_status_paths(cwd=scope)

    for doc in ALL_DOCS:
        p = scope / doc
        if not p.exists():
            continue
        try:
            meta, _ = load_frontmatter(p.read_text(encoding="utf-8"))
        except ValueError as e:
            hard_conflicts.append({
                "type": "frontmatter_parse_error", "file": doc, "message": str(e),
            })
            continue
        for err in validate_meta(meta, doc):
            hard_conflicts.append({
                "type": "frontmatter_invalid", "file": doc, "message": err,
            })
        lv = meta.get("last_verified")
        if lv and lv != "SKIPPED":
            dt = as_aware_datetime(lv)
            if dt is None:
                soft_conflicts.append({
                    "type": "invalid_or_naive_timestamp", "file": doc,
                    "message": f"last_verified={lv!r} is naive or unparseable",
                })
            else:
                delta_days = (datetime.now(timezone.utc) - dt).days
                if delta_days > VERIFY_STALE_DAYS:
                    soft_conflicts.append({
                        "type": "stale_verification", "file": doc,
                        "message": (
                            f"last_verified is {delta_days} days old "
                            f"(> {VERIFY_STALE_DAYS})"
                        ),
                    })

    task_path = scope / "task.md"
    if task_path.exists():
        try:
            _, body = load_frontmatter(task_path.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        for ref in extract_referenced_paths(body):
            if Path(ref).is_absolute():
                resolved = normalize_reference_path(ref)
            else:
                resolved = (scope / ref).resolve()
                if not resolved.exists() and is_git and repo_root:
                    git_resolved = (repo_root / ref).resolve()
                    if git_resolved.exists():
                        resolved = git_resolved
            if not resolved.exists():
                hard_conflicts.append({
                    "type": "missing_file_in_task",
                    "message": (
                        f"task.md references {ref!r} but resolved path "
                        f"{resolved} does not exist"
                    ),
                })

    wt_path = scope / "walkthrough.md"
    recent_walkthroughs = []
    if wt_path.exists():
        try:
            _, body = load_frontmatter(wt_path.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        # Get walkthrough headers for L1 preview
        _, sections = split_sections(body)
        for header, _ in sections:
            title = header.strip("# \r\n")
            if title:
                recent_walkthroughs.append(title)
                if len(recent_walkthroughs) >= 3:
                    break

    result: dict = {
        "scope": str(scope),
        "status": "success",
        "hard_conflicts": hard_conflicts,
        "soft_conflicts": soft_conflicts,
        "recent_walkthroughs": recent_walkthroughs,
    }
    if apply_soft and soft_conflicts:
        result["applied_soft_conflicts"] = apply_soft_conflicts(scope, soft_conflicts)
    return result


def cmd_check_reality(args: argparse.Namespace) -> None:
    scopes = _collect_scopes(args)
    session_id = getattr(args, "session_id", None)
    agent = getattr(args, "agent", None)
    acquire = bool(getattr(args, "acquire_lock", False))
    results = [_check_reality_scope(s, args.apply_soft_conflicts, session_id, agent, acquire=acquire) for s in scopes]
    payload = _wrap_batch(results)
    print(json.dumps(payload, indent=2))
    if any(r.get("hard_conflicts") or r.get("status") == "error" for r in results):
        sys.exit(1)


def apply_soft_conflicts(scope: Path, conflicts: list[dict]) -> int:
    """Append SOFT conflicts as ### subsections under ## Open in questions.md.

    Each conflict becomes its own `### Soft conflict · <type> · <timestamp>`
    entry so it can be individually resolved by adding `<!-- resolved -->`
    (which the next hand-off will archive to ## Closed).
    """
    q = scope / "questions.md"
    if not q.exists() or not conflicts:
        return 0
    meta, body = load_frontmatter(q.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries: list[str] = []
    for c in conflicts:
        ctype = c.get("type", "unknown")
        msg = c.get("message", "")
        entries.append(f"### Soft conflict · {ctype} · {now}\n\n- ⚠️ {msg}\n\n")
    block = "".join(entries)

    match = re.search(r"^## Open\s*$", body, re.MULTILINE)
    if match:
        # Insert immediately after the '## Open' header + trailing blank line
        idx = match.end()
        # Skip to end of the ## Open header line and following blank lines
        rest = body[idx:]
        # Preserve one newline after header, insert block, then rest
        # Find first double-newline or end-of-first-line
        newline_pos = rest.find("\n")
        after_header = rest[newline_pos + 1 :] if newline_pos >= 0 else rest
        body = body[:idx] + "\n\n" + block + after_header.lstrip("\n")
    else:
        # Legacy body without ## Open — inject the whole structure
        body = body.rstrip() + f"\n\n## Open\n\n{block}## Closed\n\n- None.\n"
    meta["last_updated"] = now
    meta["last_writer"] = "take-over"
    write_atomic(q, dump_frontmatter(meta, body))
    return len(conflicts)


def classify_cleanup(scope: Path) -> dict:
    removed_clear: list[dict] = []
    removed_stale: list[dict] = []
    unsure_items: list[dict] = []
    kept: list[dict] = []
    archived: list[dict] = []  # questions to move from ## Open to ## Closed
    deleted_files = git_deleted_files(90)

    wt = scope / "walkthrough.md"
    if wt.exists():
        try:
            _, body = load_frontmatter(wt.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        _, sections = split_sections(body)
        for header, content in sections:
            title = header.strip("# \r\n")
            date_match = _DATE_IN_HEADER_RE.search(header)
            if not date_match:
                continue
            date_str = date_match.group(1)
            if (_KEEP_TAG_RE.search(header) or _KEEP_TAG_RE.search(content)
                    or _KEEP_WORD_RE.search(header)):
                kept.append({"file": "walkthrough.md", "header": title,
                             "reason": "keep marker or keyword"})
                continue
            if _RESOLVED_TAG_RE.search(content) or _RESOLVED_TAG_RE.search(header):
                removed_clear.append({"file": "walkthrough.md", "header": title,
                                      "reason": "explicit <!-- resolved --> marker"})
                continue
            path_refs = extract_referenced_paths(content)
            if path_refs and all(
                any(df.endswith(pr.replace("\\", "/").lstrip("/")) for df in deleted_files)
                for pr in path_refs
            ):
                removed_clear.append({
                    "file": "walkthrough.md", "header": title,
                    "reason": (
                        "all referenced files deleted in git history "
                        "(--diff-filter=D within 90 days)"
                    ),
                })
                continue
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                delta_days = (datetime.now(timezone.utc).date() - entry_date).days
            except ValueError:
                delta_days = 0
            if delta_days > STALE_DAYS:
                in_use = False
                for doc in ("task.md", "context.md"):
                    p = scope / doc
                    if p.exists():
                        text = p.read_text(encoding="utf-8")
                        if date_str in text or title in text:
                            in_use = True
                            break
                if not in_use:
                    removed_stale.append({
                        "file": "walkthrough.md", "header": title,
                        "age_days": delta_days,
                    })
                    continue
            unsure_items.append({
                "file": "walkthrough.md", "header": title,
                "snippet": content.strip().split("\n", 1)[0][:120],
            })

    oq = scope / "questions.md"
    if oq.exists():
        try:
            _, body = load_frontmatter(oq.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        prefix, sections = split_sections(body)
        # Determine which top-level section a subsection lives under. We only
        # classify entries under `## Open`; entries already under `## Closed`
        # stay put (they're the archive).
        current_top = None
        for header, content in sections:
            title = header.strip("# \r\n")
            # Detect top-level Open / Closed section headers (## level 2)
            # from the raw header text.
            stripped_hash = header.lstrip("#").strip()
            hash_count = len(header) - len(header.lstrip("#"))
            if hash_count == 2 and stripped_hash.lower() in ("open", "closed"):
                current_top = stripped_hash.lower()
                if _KEEP_TAG_RE.search(header) or _KEEP_TAG_RE.search(content):
                    kept.append({"file": "questions.md", "header": title,
                                 "reason": "structural section, always kept"})
                continue
            # Entries already under ## Closed are archived; leave untouched.
            if current_top == "closed":
                kept.append({"file": "questions.md", "header": title,
                             "reason": "already archived under ## Closed"})
                continue
            # Entries under ## Open (or top-level, legacy) — classify.
            if _KEEP_TAG_RE.search(header) or _KEEP_TAG_RE.search(content):
                kept.append({"file": "questions.md", "header": title,
                             "reason": "explicit <!-- keep --> marker"})
                continue
            if _RESOLVED_TAG_RE.search(content) or _RESOLVED_TAG_RE.search(header):
                # NEW SEMANTICS: resolved questions ARCHIVE (move to Closed),
                # not delete. They stay forever for historical review.
                archived.append({"file": "questions.md", "header": title,
                                 "reason": "explicit <!-- resolved --> marker",
                                 "content": content})
                continue
            if _is_placeholder(content):
                kept.append({"file": "questions.md", "header": title,
                             "reason": "placeholder (empty or '- None.')"})
                continue
            # Keep unresolved open questions by default
            kept.append({"file": "questions.md", "header": title,
                         "reason": "active open question"})

    return {"clear": removed_clear, "stale": removed_stale,
            "kept": kept, "unsure": unsure_items, "archived": archived}


def _rebuild_questions_body(body: str, archived: list[dict], to_remove: set[tuple[str, str]]) -> str:
    """Rebuild questions.md body: move archived entries from ## Open to ## Closed.

    Preserves:
      - prefix (frontmatter body prelude before first section)
      - ## Open header + its non-archived subsections
      - ## Closed header + its existing entries + newly archived entries appended
    """
    prefix, sections = split_sections(body)
    archived_titles = {a["header"] for a in archived if a["file"] == "questions.md"}
    archived_content_by_title = {a["header"]: a["content"] for a in archived
                                 if a["file"] == "questions.md"}

    open_entries: list[tuple[str, str]] = []      # (header, content) under ## Open
    closed_entries: list[tuple[str, str]] = []    # existing content under ## Closed
    current_top: str | None = None
    has_open_header = False
    has_closed_header = False
    open_intro = ""
    closed_intro = ""

    for header, content in sections:
        stripped = header.lstrip("#").strip()
        hash_count = len(header) - len(header.lstrip("#"))
        # Detect ## Open / ## Closed top-level headers
        if hash_count == 2 and stripped.lower() in ("open", "closed"):
            current_top = stripped.lower()
            if current_top == "open":
                has_open_header = True
                open_intro = content
            else:
                has_closed_header = True
                closed_intro = content
            continue
        # Under ## Closed — preserve
        if current_top == "closed":
            closed_entries.append((header, content))
            continue
        # Under ## Open (or legacy top-level)
        title = header.strip("# \r\n")
        if title in archived_titles:
            continue  # will be moved to Closed
        if ("questions.md", title) in to_remove:
            continue  # explicit delete (rare; only if user pushes STALE)
        open_entries.append((header, content))

    # Assemble new body
    parts: list[str] = [prefix]
    parts.append("## Open\n\n" if not has_open_header else "## Open\n\n")
    if open_intro.strip():
        parts.append(open_intro.lstrip("\n"))
    for header, content in open_entries:
        parts.append(header)
        parts.append(content)
    if not open_entries:
        parts.append("- None.\n\n")
    parts.append("## Closed\n\n")
    if closed_intro.strip():
        parts.append(closed_intro.lstrip("\n"))
    for header, content in closed_entries:
        parts.append(header)
        parts.append(content)
    for a in archived:
        if a["file"] != "questions.md":
            continue
        # Re-emit as a subsection (### level) so nesting under ## Closed is clean
        title = a["header"]
        content = archived_content_by_title.get(title, "")
        parts.append(f"### {title}\n")
        parts.append(content if content.endswith("\n") else content + "\n")

    return "".join(parts)


def apply_cleanup(scope: Path, plan: dict) -> dict:
    to_remove = {
        (item["file"], item["header"])
        for item in plan.get("clear", []) + plan.get("stale", [])
    }
    archived = plan.get("archived", [])
    applied = {"walkthrough.md": 0, "questions.md": 0, "archived_to_closed": 0}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # walkthrough.md — straight deletion (unchanged from prior behaviour)
    wt = scope / "walkthrough.md"
    if wt.exists():
        meta, body = load_frontmatter(wt.read_text(encoding="utf-8"))
        prefix, sections = split_sections(body)
        rebuilt = [prefix]
        for header, content in sections:
            title = header.strip("# \r\n")
            if ("walkthrough.md", title) in to_remove:
                applied["walkthrough.md"] += 1
                continue
            rebuilt.append(header)
            rebuilt.append(content)
        meta["last_updated"] = now
        meta["last_writer"] = "hand-off"
        write_atomic(wt, dump_frontmatter(meta, "".join(rebuilt)))

    # questions.md — archive resolved entries to ## Closed
    q = scope / "questions.md"
    if q.exists():
        meta, body = load_frontmatter(q.read_text(encoding="utf-8"))
        new_body = _rebuild_questions_body(body, archived, to_remove)
        # Count how many were moved (from archived list, filtered to this file)
        moved_count = sum(1 for a in archived if a["file"] == "questions.md")
        applied["archived_to_closed"] += moved_count
        # Also count any hard-delete of questions (STALE / CLEAR)
        deleted_count = sum(1 for h in to_remove if h[0] == "questions.md")
        applied["questions.md"] += deleted_count
        meta["last_updated"] = now
        meta["last_writer"] = "hand-off"
        write_atomic(q, dump_frontmatter(meta, new_body))

    return applied


def _clean_up_scope(scope: Path, dry_run: bool) -> dict:
    if not scope.exists():
        return {"scope": str(scope), "status": "error",
                "message": f"scope {scope} does not exist"}
    plan = classify_cleanup(scope)
    if dry_run:
        return {"scope": str(scope), "status": "planned", **plan}
    applied = apply_cleanup(scope, plan)
    return {"scope": str(scope), "status": "applied", **plan, "applied": applied}


def cmd_clean_up(args: argparse.Namespace) -> None:
    scopes = _collect_scopes(args)
    session_id = getattr(args, "session_id", None)
    results = []
    for s in scopes:
        lock_err = check_lock_conflict(s, session_id)
        if lock_err:
            results.append({
                "scope": str(s),
                "status": "error",
                "message": f"Lock conflict during clean-up: {lock_err}"
            })
            continue
        res = _clean_up_scope(s, args.dry_run)
        if not args.dry_run and res.get("status") == "applied" and session_id:
            release_lock(s, session_id)
        results.append(res)
    payload = _wrap_batch(results)
    print(json.dumps(payload, indent=2))
    if any(r.get("status") == "error" for r in results):
        sys.exit(1)


# ---------------------------------------------------------------------------
# Multi-hop trust health analysis
# ---------------------------------------------------------------------------
# When a scope is being handed off for the 4th / 5th / Nth time, the risk of
# hallucination cascade rises: each agent tends to trust the previous agent's
# assertions verbatim, so a hallucinated "invariant" propagates freely until
# a human notices. These helpers make multi-hop-ness visible to the agent so
# it can adjust caution accordingly, without imposing costs on 1st-hop flows.

# Provenance tag written by hand-off Step 2 authors on invariants / decisions:
#   [git:<short-sha>]         backed by a git commit
#   [user:<YYYY-MM-DD>]       user confirmed in-session
#   [test:<test-name>]        automated test enforces this
#   [inferred:<session-id>]   agent's own inference — treat as low-confidence
#   [unknown]                 explicit "we don't know where this came from"
_PROVENANCE_RE = re.compile(
    r"\[(git|user|test|inferred|unknown)(?::([^\]]+))?\]",
    re.IGNORECASE,
)
_HOP_COMMIT_RE = re.compile(r"docs\(hand[-]?off\)", re.IGNORECASE)


def _count_hops(cwd: Path) -> tuple[int, list[str]]:
    """Count hand-off commits in git history for this scope.

    Returns (hop_count, recent_writers_or_authors). hop_count of 0 means either
    the scope is not in a git repo, or no `docs(hand-off):` commits exist yet.
    """
    rc, out, _ = git(
        "log",
        "--pretty=format:%H|%an|%s",
        "--",
        ".",
        cwd=cwd,
    )
    if rc != 0 or not out.strip():
        return 0, []
    hop_lines = [ln for ln in out.splitlines() if _HOP_COMMIT_RE.search(ln)]
    authors: list[str] = []
    seen = set()
    for ln in hop_lines[:10]:
        parts = ln.split("|", 2)
        if len(parts) >= 2 and parts[1] not in seen:
            authors.append(parts[1])
            seen.add(parts[1])
    return len(hop_lines), authors


def _extract_provenance_lines(body: str) -> list[dict]:
    """Scan a markdown body for lines containing a [provenance:...] tag.

    Returns [{line_no, line_text, tag_type, tag_value}] sorted by line number.
    Lines without a recognised tag are omitted; the caller can compute the
    'untagged invariant' count from total-line-count minus this list's length.
    """
    hits: list[dict] = []
    for i, line in enumerate(body.splitlines(), start=1):
        m = _PROVENANCE_RE.search(line)
        if not m:
            continue
        hits.append({
            "line_no": i,
            "line_text": line.strip()[:200],
            "tag_type": m.group(1).lower(),
            "tag_value": (m.group(2) or "").strip(),
        })
    return hits


def _count_invariant_lines(body: str) -> int:
    """Rough count of substantive lines in context.md — bullets and paragraphs.

    Excludes blank lines, headers (## / ###), HTML comments, and code fences.
    Used as the denominator for provenance-coverage %.
    """
    n = 0
    in_fence = False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not s or s.startswith("#") or s.startswith("<!--"):
            continue
        n += 1
    return n


def _analyze_multihop_health(scope: Path, reality: dict) -> dict:
    """Compute multi-hop health signals for a scope.

    Never mutates disk. Reads context.md + walkthrough.md + git log to derive:
      - hop_count             : number of docs(hand-off) commits touching this scope
      - unique_writers        : distinct git authors + last_writer fields seen
      - provenance_distribution : {git, user, test, inferred, unknown, untagged}
      - stale_invariants      : context.md lines older than 30 days by git blame
                                (best-effort; skipped if not a git repo)
      - health                : fresh | healthy | warning | unhealthy
      - issues                : list of human-readable strings
    """
    ctx_path = scope / "context.md"
    wt_path = scope / "walkthrough.md"
    q_path = scope / "questions.md"

    # 1. Hop count from git log
    hop_count, git_authors = _count_hops(scope)

    # 2. Unique writers (union of git authors + last_writer frontmatter fields)
    writers: set[str] = set(git_authors)
    for p in (ctx_path, wt_path, q_path):
        if not p.exists():
            continue
        try:
            meta, _ = load_frontmatter(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        w = meta.get("last_writer")
        if w:
            writers.add(str(w))
        a = meta.get("last_agent")
        if a:
            writers.add(str(a))

    # 3. Provenance distribution across context.md
    provenance_dist = {
        "git": 0, "user": 0, "test": 0, "inferred": 0, "unknown": 0, "untagged": 0
    }
    inferred_lines: list[dict] = []
    if ctx_path.exists():
        try:
            _, ctx_body = load_frontmatter(ctx_path.read_text(encoding="utf-8"))
        except ValueError:
            ctx_body = ""
        tagged = _extract_provenance_lines(ctx_body)
        total_lines = _count_invariant_lines(ctx_body)
        for entry in tagged:
            provenance_dist[entry["tag_type"]] += 1
            if entry["tag_type"] == "inferred":
                inferred_lines.append(entry)
        provenance_dist["untagged"] = max(0, total_lines - len(tagged))

    # 4. Stale invariants — git blame per line, filter age > 30d
    stale_invariants: list[dict] = []
    if ctx_path.exists() and git_repo_root(cwd=scope):
        rc, blame_out, _ = git(
            "blame",
            "--line-porcelain",
            "context.md",
            cwd=scope,
        )
        if rc == 0:
            now = datetime.now(timezone.utc)
            # Parse porcelain blame: each block starts with a SHA line, then
            # metadata, then a `\tline content` line.
            blocks = blame_out.split("\n\t")
            for block in blocks[:-1]:  # last "block" is trailing content
                # Extract author-time
                m_time = re.search(r"^author-time (\d+)", block, re.MULTILINE)
                if not m_time:
                    continue
                m_line = re.search(r"^author-line-number (\d+)", block, re.MULTILINE)
                # author-line-number isn't in porcelain by default; fall back
                # to counting.
                try:
                    ts = int(m_time.group(1))
                    age_days = (now - datetime.fromtimestamp(ts, timezone.utc)).days
                except (ValueError, OSError):
                    continue
                if age_days > 30:
                    # We only need the count + a couple of samples for the summary
                    if len(stale_invariants) < 5:
                        stale_invariants.append({
                            "age_days": age_days,
                        })

    # 5. Health verdict
    inferred_pct = 0
    ctx_line_total = sum(provenance_dist.values())
    if ctx_line_total > 0:
        inferred_pct = int(100 * provenance_dist["inferred"] / ctx_line_total)
    untagged_pct = 0
    if ctx_line_total > 0:
        untagged_pct = int(100 * provenance_dist["untagged"] / ctx_line_total)

    issues: list[str] = []
    if hop_count == 0:
        health = "fresh"
    else:
        health = "healthy"
        if hop_count >= 3 and inferred_pct >= 40:
            issues.append(
                f"{inferred_pct}% of context.md invariants are [inferred:*] "
                f"(hop #{hop_count}) — high hallucination-cascade risk"
            )
        if hop_count >= 3 and untagged_pct >= 50:
            issues.append(
                f"{untagged_pct}% of context.md invariants have no provenance "
                f"tag — cannot audit source across {hop_count} hops"
            )
        if len(stale_invariants) >= 5:
            issues.append(
                f"{len(stale_invariants)}+ context.md lines are older than 30 "
                "days by git blame — review for currency"
            )
        # Reality-check soft conflicts also count as health signals
        if len(reality.get("soft_conflicts", [])) >= 3:
            issues.append(
                f"{len(reality['soft_conflicts'])} SOFT conflicts pending in "
                "questions.md — resolve before next hand-off"
            )
        if len(issues) >= 2:
            health = "unhealthy"
        elif len(issues) == 1:
            health = "warning"

    return {
        "hop_count": hop_count,
        "unique_writers": sorted(writers),
        "provenance_distribution": provenance_dist,
        "inferred_pct": inferred_pct,
        "untagged_pct": untagged_pct,
        "stale_invariants_count": len(stale_invariants),
        "stale_invariants_sample": stale_invariants,
        "inferred_samples": inferred_lines[:5],
        "health": health,
        "issues": issues,
    }


def _prepare_scope(scope: Path, apply_soft: bool, session_id: str | None,
                   agent: str | None) -> dict:
    """One-shot composite: reality-check + cleanup dry-run + multi-hop health.

    Combines the read-only preflight phases of the hand-off flow into a single
    JSON payload so the agent can make its next branching decision without
    spawning multiple `uv run` subprocesses.

    The output includes a `next_action` field the agent should read first:
      - `halt_on_hard_conflicts`  : reality-check found HARD conflicts;
                                    resolve via `clarify` before touching anything.
      - `challenge_required`      : multi-hop trust health check flagged this
                                    scope as unhealthy — force user
                                    re-confirmation of key invariants before
                                    proceeding.
      - `clarify_unsure`          : cleanup produced UNSURE items; batch them
                                    into one `clarify` prompt, then call
                                    `clean-up --apply`.
      - `safe_to_apply`           : no HARD conflicts, no UNSURE items; the
                                    agent may proceed directly to
                                    `clean-up --apply`.
    """
    if not scope.exists():
        return {
            "scope": str(scope),
            "status": "error",
            "message": f"scope {scope} does not exist",
        }

    reality = _check_reality_scope(scope, apply_soft, session_id, agent, acquire=True)
    hard_conflicts = reality.get("hard_conflicts", [])
    health = _analyze_multihop_health(scope, reality)

    # If reality-check hard-failed on this scope, don't attempt cleanup —
    # the docs are in an inconsistent state and any classification would
    # be advising on stale ground.
    if hard_conflicts:
        return {
            "scope": str(scope),
            "status": "halted",
            "reality": reality,
            "cleanup_plan": None,
            "health": health,
            "next_action": "halt_on_hard_conflicts",
            "guidance": (
                f"[AGENT GUIDANCE] {len(hard_conflicts)} HARD conflict(s) — "
                "surface each via clarify before any mutation. Do NOT proceed "
                "to clean-up or write-atomic until resolved."
            ),
        }

    plan = classify_cleanup(scope)
    unsure = plan.get("unsure", [])

    # Multi-hop challenge takes precedence over clarify_unsure — if the docs
    # are unhealthy, forcing UNSURE cleanup is putting deck chairs on the
    # Titanic. Address the trust problem first, then cleanup on next pass.
    if health["health"] == "unhealthy":
        next_action = "challenge_required"
        challenge_items = health["inferred_samples"][:3] or \
                          health.get("stale_invariants_sample", [])[:3]
        guidance = (
            f"[AGENT GUIDANCE] Hop #{health['hop_count']} — health: unhealthy. "
            f"Issues: {'; '.join(health['issues'])}. "
            "Before Step 2 write, present the top low-confidence context.md "
            "entries to the user via ONE batched clarify prompt "
            "(still valid / stale / rewrite). Then re-run `prepare` before "
            "proceeding. Sample items to challenge: "
            f"{[i.get('line_text', i) for i in challenge_items]}"
        )
    elif unsure:
        next_action = "clarify_unsure"
        health_note = (
            f" (health: {health['health']}, hop #{health['hop_count']})"
            if health["hop_count"] >= 2 else ""
        )
        guidance = (
            f"[AGENT GUIDANCE] {len(unsure)} UNSURE cleanup item(s){health_note} — "
            "batch them into ONE clarify prompt (keep vs drop per item), "
            "then call `clean-up --apply` regardless of the answers "
            "(apply preserves UNSURE by default)."
        )
    else:
        next_action = "safe_to_apply"
        health_note = (
            f" (health: {health['health']}, hop #{health['hop_count']})"
            if health["hop_count"] >= 2 else ""
        )
        guidance = (
            f"[AGENT GUIDANCE] No HARD conflicts, no UNSURE items{health_note} — "
            "call `clean-up --apply` directly. Report the audit trail "
            "(clear / stale / archived counts) in the final summary."
        )

    return {
        "scope": str(scope),
        "status": "ok",
        "reality": reality,
        "cleanup_plan": plan,
        "health": health,
        "next_action": next_action,
        "guidance": guidance,
    }


def cmd_prepare(args: argparse.Namespace) -> None:
    """Composite hand-off preflight: reality-check + cleanup dry-run in one call."""
    scopes = _collect_scopes(args)
    session_id = getattr(args, "session_id", None)
    agent = getattr(args, "agent", None)
    apply_soft = getattr(args, "apply_soft_conflicts", False)
    results = [_prepare_scope(s, apply_soft, session_id, agent) for s in scopes]
    payload = _wrap_batch(results)
    print(json.dumps(payload, indent=2))
    if any(r.get("status") == "error"
           or r.get("next_action") == "halt_on_hard_conflicts"
           for r in results):
        sys.exit(1)


def cmd_unlock(args: argparse.Namespace) -> None:
    scope = resolve_scope(args.scope)
    lock_file = scope / ".handoff.lock"
    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text(encoding="utf-8"))
            sess = data.get("session_id", "unknown")
            lock_file.unlink(missing_ok=True)
            print(json.dumps({"status": "success", "message": f"Released lock for session {sess}"}, indent=2))
        except Exception as e:
            lock_file.unlink(missing_ok=True)
            print(json.dumps({"status": "success", "message": f"Forcibly deleted invalid lock file: {e}"}, indent=2))
    else:
        print(json.dumps({"status": "success", "message": "No lock file existed"}, indent=2))


def cmd_write_atomic(args: argparse.Namespace) -> None:
    filepath = resolve_msys_path(args.filepath).resolve()
    if args.content is not None:
        content = args.content
    elif args.content_file:
        cf = resolve_msys_path(args.content_file)
        content = cf.read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()

    # ----- Scope boundary check (DECISIONS R32) -----
    # If --scope is given, --filepath MUST resolve inside it. This closes
    # the class of bug where an unescaped shell variable (e.g. bash
    # collapsing "$SCOPE\\${f}.md" to a path with no separator and a
    # literal ${f}) lets write-atomic clobber files outside the scope.
    if args.scope:
        scope_root = resolve_msys_path(args.scope).resolve()
        try:
            inside = filepath.is_relative_to(scope_root)
        except AttributeError:  # pragma: no cover  (Python <3.9)
            inside = str(filepath).startswith(str(scope_root))
        if not inside:
            print(json.dumps({
                "status": "error",
                "reason": "path_outside_scope",
                "filepath": str(filepath),
                "scope": str(scope_root),
                "hint": (
                    "Check for unescaped shell variables or missing "
                    "separators. On Windows/git-bash prefer forward slashes "
                    "in paths that also expand variables — see "
                    "references/atomic-writes.md#windows-path-pitfalls."
                ),
            }))
            sys.exit(4)

    # ----- Frontmatter stamping (DECISIONS R33) -----
    # Optional --stamp-frontmatter re-writes last_updated / last_verified
    # (and optionally last_writer / last_agent / session_id) in-place so
    # callers don't hand-maintain ISO timestamps and metadata on every
    # hand-off write. Requires the payload to already carry a YAML
    # frontmatter block — a hand-off doc without one is a caller bug.
    if args.stamp_frontmatter:
        try:
            meta, body = load_frontmatter(content)
        except ValueError as e:
            print(json.dumps({
                "status": "error",
                "reason": "invalid_frontmatter",
                "message": str(e),
            }))
            sys.exit(5)
        if not meta:
            print(json.dumps({
                "status": "error",
                "reason": "frontmatter_missing",
                "hint": (
                    "--stamp-frontmatter requires the payload to begin with "
                    "a YAML frontmatter block (--- … ---). This is a hand-off "
                    "doc — it must have frontmatter."
                ),
            }))
            sys.exit(5)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        meta["last_updated"] = now
        meta["last_verified"] = now
        # --writer values are validated at argparse layer (choices=VALID_WRITERS);
        # last_agent / session_id are free-form strings.
        if args.writer:
            meta["last_writer"] = args.writer
        if args.agent:
            meta["last_agent"] = args.agent
        if args.session_id:
            meta["session_id"] = args.session_id
        content = dump_frontmatter(meta, body)

    write_atomic(filepath, content)
    payload = {
        "status": "success",
        "filepath": str(filepath),
        "bytes": len(content),
    }
    if args.stamp_frontmatter:
        payload["stamped_frontmatter"] = True
    print(json.dumps(payload))


def cmd_list_scopes(args: argparse.Namespace) -> None:
    root = resolve_msys_path(args.root).resolve() if args.root else Path.cwd()
    scopes = find_scopes(root)
    payload = []
    for s in scopes:
        docs_present = [
            doc for doc in ALL_DOCS if (s / doc).exists()
        ]
        latest_updated = None
        for doc in docs_present:
            try:
                meta, _ = load_frontmatter((s / doc).read_text(encoding="utf-8"))
                lv = meta.get("last_updated")
                if lv and (latest_updated is None or str(lv) > latest_updated):
                    latest_updated = str(lv)
            except (ValueError, OSError):
                continue
        payload.append({
            "scope": str(s),
            "relative": str(s.relative_to(root)) if s != root else ".",
            "docs": docs_present,
            "last_updated": latest_updated,
        })
    print(json.dumps({
        "root": str(root),
        "scope_count": len(payload),
        "scopes": payload,
    }, indent=2))


# ---------------------------------------------------------------------------
# Batch helpers (--all-scopes)
# ---------------------------------------------------------------------------


def _collect_scopes(args: argparse.Namespace) -> list[Path]:
    """Resolve one or many scopes based on args."""
    if getattr(args, "all_scopes", False):
        root = Path.cwd()
        scopes = find_scopes(root)
        if not scopes:
            sys.stderr.write(
                f"WARNING: --all-scopes found no handoff docs under {root}\n"
            )
        return scopes or [root]
    return [resolve_scope(args.scope)]


def _wrap_batch(results: list[dict]) -> dict:
    if len(results) == 1:
        return results[0]
    aggregate_status = "success"
    for r in results:
        st = r.get("status")
        if st in {"error", "invalid"}:
            aggregate_status = st
            break
    return {
        "status": aggregate_status,
        "scope_count": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _add_scope_args(p: argparse.ArgumentParser, *, allow_all: bool = True) -> None:
    grp = p.add_mutually_exclusive_group()
    grp.add_argument(
        "--scope",
        help="Handoff scope directory (defaults to cwd if it contains handoff docs)",
    )
    if allow_all:
        grp.add_argument(
            "--all-scopes",
            action="store_true",
            help="Apply to every scope discovered under cwd",
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Session Handoff · reconcile helper"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize handoff docs at scope from templates")
    _add_scope_args(p_init, allow_all=False)
    p_init.add_argument("--agent", help="Last agent name")
    p_init.add_argument("--session-id", help="Session ID")
    p_init.add_argument("--writer", default="migration",
                        choices=sorted(VALID_WRITERS))
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate",
                            help="Validate frontmatter across handoff docs")
    _add_scope_args(p_val)
    p_val.add_argument("--agent", help="Active agent name")
    p_val.add_argument("--session-id", help="Session ID")
    p_val.set_defaults(func=cmd_validate)

    p_check = sub.add_parser("check-reality",
                              help="Verify handoff docs against git/fs")
    _add_scope_args(p_check)
    p_check.add_argument(
        "--apply-soft-conflicts",
        action="store_true",
        help="Also append SOFT conflicts to questions.md",
    )
    p_check.add_argument("--agent", help="Active agent name")
    p_check.add_argument("--session-id", help="Session ID")
    p_check.add_argument(
        "--acquire-lock",
        action="store_true",
        help=(
            "Opt in to acquiring .handoff.lock during this check. Without this "
            "flag check-reality is strictly read-only regardless of --session-id. "
            "hand-off's `prepare` sets acquire=True internally; ad-hoc callers "
            "should generally NOT pass the flag."
        ),
    )
    p_check.set_defaults(func=cmd_check_reality)

    p_clean = sub.add_parser(
        "clean-up",
        help="Classify walkthrough / questions entries (two-phase)",
    )
    _add_scope_args(p_clean)
    p_clean.add_argument("--agent", help="Active agent name")
    p_clean.add_argument("--session-id", help="Session ID")
    grp = p_clean.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true",
                      help="Print classification plan JSON, don't mutate")
    grp.add_argument("--apply", action="store_true",
                      help="Apply the classified plan (removes CLEAR + STALE)")
    p_clean.set_defaults(func=cmd_clean_up)

    p_write = sub.add_parser("write-atomic", help="Write file atomically")
    p_write.add_argument("--filepath", required=True)
    p_write.add_argument("--content",
                          help="Inline content (avoid for large content)")
    p_write.add_argument("--content-file",
                          help="Read payload from this file (recommended)")
    p_write.add_argument("--scope",
                          help=(
                              "Optional scope root. When set, --filepath must "
                              "resolve inside this directory or the write is "
                              "refused (protects against unescaped shell vars "
                              "silently writing outside the scope)."
                          ))
    p_write.add_argument("--stamp-frontmatter", action="store_true",
                          help=(
                              "Re-write last_updated / last_verified (to now) "
                              "and optionally last_writer / last_agent / "
                              "session_id in the payload's YAML frontmatter "
                              "before atomic write."
                          ))
    p_write.add_argument("--writer",
                          choices=sorted(VALID_WRITERS),
                          help="With --stamp-frontmatter: set last_writer.")
    p_write.add_argument("--agent",
                          help="With --stamp-frontmatter: set last_agent.")
    p_write.add_argument("--session-id",
                          help="With --stamp-frontmatter: set session_id.")
    p_write.set_defaults(func=cmd_write_atomic)

    p_list = sub.add_parser("list-scopes",
                             help="Discover all handoff scopes under root")
    p_list.add_argument("--root",
                         help="Root directory to scan (default: cwd)")
    p_list.set_defaults(func=cmd_list_scopes)

    p_unlock = sub.add_parser("unlock", help="Forcibly release the concurrency lock at scope")
    _add_scope_args(p_unlock, allow_all=False)
    p_unlock.set_defaults(func=cmd_unlock)

    p_prepare = sub.add_parser(
        "prepare",
        help="One-shot preflight: reality-check + cleanup dry-run (composite of check-reality + clean-up --dry-run)",
    )
    _add_scope_args(p_prepare)
    p_prepare.add_argument(
        "--apply-soft-conflicts",
        action="store_true",
        help="Also append SOFT conflicts to questions.md (same semantics as check-reality)",
    )
    p_prepare.add_argument("--agent", help="Active agent name")
    p_prepare.add_argument("--session-id", help="Session ID")
    p_prepare.set_defaults(func=cmd_prepare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
