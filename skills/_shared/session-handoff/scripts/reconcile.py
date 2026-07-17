#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Session Handoff Protocol · reconcile helper.

Deterministic logic for the `hand-off` / `take-over` skills. Keeping YAML
parsing, git reality-check, cleanup classification, and atomic writes out
of the LLM's cognitive path (protocol §9 invariant "script-assisted
execution").

Commands
--------
init                             create <target-dir>/ from templates
validate                         frontmatter enum + timestamp sanity across docs
check-reality [--apply-soft-conflicts]
                                 verify docs vs git/fs; optionally log SOFT
                                 conflicts to open-questions.md
clean-up (--dry-run | --apply)   classify walkthrough / open-questions
                                 entries as CLEAR / STALE / KEEP / UNSURE;
                                 UNSURE items are surfaced only, never deleted
write-atomic --filepath P (--content S | --content-file P | stdin)
                                 write P atomically via <P>.tmp + rename

Invocation
----------
Skills are expected to call this via::

    uv run --isolated python <SKILL_DIR>/scripts/reconcile.py <command> ...

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
        "'uv run --isolated python .../reconcile.py ...' so uv installs the "
        "inline-script dependency automatically.\n"
    )
    sys.exit(2)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"

DEFAULT_DOCS = ["context.md", "task.md", "walkthrough.md", "open-questions.md"]
OPTIONAL_DOCS = ["plan.md", "review.md"]
ALL_DOCS = DEFAULT_DOCS + OPTIONAL_DOCS

VALID_KINDS = {"context", "task", "walkthrough", "open-questions", "plan", "review"}
VALID_STATUS = {"in-progress", "blocked", "phase-complete", "archived"}
VALID_WRITERS = {"hand-off", "take-over", "user", "migration"}

STALE_DAYS = 30           # walkthrough entry auto-stale threshold
VERIFY_STALE_DAYS = 7     # last_verified SOFT-conflict threshold

# ---------------------------------------------------------------------------
# Frontmatter (pyyaml-backed)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


def load_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter + body. Returns ({}, text) if none present.

    Raises ValueError on malformed frontmatter (agent should treat as HARD).
    """
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
    """Serialize back to frontmatter + body. Body is preserved verbatim.

    Fixes the double-newline bug from the earlier hand-rolled serializer:
    the ``---`` fence closes with exactly one ``\\n`` and the body is
    joined without a leading newline.
    """
    yaml_str = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
    body = body.lstrip("\n")
    return f"---\n{yaml_str}\n---\n\n{body}" if body else f"---\n{yaml_str}\n---\n"


def parse_iso_timestamp(v: object) -> tuple[bool, str | None]:
    """Return (ok, err). Naive datetimes are rejected."""
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
    """Return list of validation errors (empty = OK)."""
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
# Atomic write (POSIX rename + Windows os.replace)
# ---------------------------------------------------------------------------


def write_atomic(filepath: str | os.PathLike[str], content: str) -> None:
    fp = Path(filepath)
    fp.parent.mkdir(parents=True, exist_ok=True)
    tmp = fp.with_suffix(fp.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp, fp)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def git(*args: str) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "git not on PATH"


def git_status_paths() -> set[str]:
    rc, out, _ = git("status", "--short")
    if rc != 0:
        return set()
    paths: set[str] = set()
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            paths.add(parts[1].replace("\\", "/"))
    return paths


def git_recent_committed_files(n: int = 5) -> set[str]:
    rc, out, _ = git("log", f"-{n}", "--name-only", "--pretty=format:")
    if rc != 0:
        return set()
    return {ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()}


def git_deleted_files(since_days: int = 90) -> set[str]:
    rc, out, _ = git(
        "log",
        f"--since={since_days}.days",
        "--diff-filter=D",
        "--name-only",
        "--pretty=format:",
    )
    if rc != 0:
        return set()
    return {ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()}


# ---------------------------------------------------------------------------
# Cross-platform file-reference detection
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_PATH_TOKEN_RE = re.compile(
    r"""(?:[`"'\(\s]|^)                          # opening delimiter
        (                                        # capture path
          (?:[A-Za-z]:[\\/][^\s`"'\(\)\[\]]+)    # Windows: C:\foo or C:/foo
          |
          (?:/[A-Za-z]/[^\s`"'\(\)\[\]]+)        # MSYS:   /c/foo
          |
          (?:/[^\s`"'\(\)\[\]]+)                 # POSIX:  /foo/bar
        )
    """,
    re.VERBOSE,
)

# Deny-list for tokens that look like paths but are documentation examples.
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
    """Turn MSYS ``/c/foo`` into ``C:/foo`` on Windows; return Path."""
    if os.name == "nt":
        m = re.match(r"^/([A-Za-z])/(.*)$", p)
        if m:
            return Path(f"{m.group(1).upper()}:/{m.group(2)}")
    return Path(p)


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

_SECTION_RE = re.compile(r"^(##\s+.*)$", re.MULTILINE)
_DATE_IN_HEADER_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_KEEP_TAG_RE = re.compile(r"<!--\s*keep\s*-->", re.IGNORECASE)
_RESOLVED_TAG_RE = re.compile(r"<!--\s*resolved\s*-->", re.IGNORECASE)
_KEEP_WORD_RE = re.compile(r"\b(lesson|surprise|decision|invariant)\b", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"^\s*-?\s*(none\.?|tbd\.?|n/?a\.?)\s*$",
                              re.IGNORECASE | re.MULTILINE)


def strip_html_comments_preserving_tags(text: str) -> str:
    """Strip block-level HTML comment blocks while preserving inline markers.

    We keep single-line `<!-- keep -->` / `<!-- resolved -->` markers because
    the classifier looks for them explicitly. Multi-line/block comments that
    contain example markdown (e.g. template sample entries) are removed so
    their `## ...` headers don't confuse the section splitter.
    """
    def _replace(m: re.Match[str]) -> str:
        block = m.group(0)
        # Preserve short single-tag markers used by the classifier.
        stripped = block.strip()
        if stripped.lower() in {"<!--keep-->", "<!-- keep -->", "<!--resolved-->",
                                 "<!-- resolved -->"}:
            return block
        if "\n" not in stripped and len(stripped) <= 40:
            return block
        return ""
    return _HTML_COMMENT_RE.sub(_replace, text)


def _is_placeholder(content: str) -> bool:
    """A section body counts as a placeholder if empty or only 'None./TBD./N/A.'."""
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
    """Return (prefix_before_first_section, [(header_line, body_after), ...])."""
    # Strip block-level HTML comments so template example entries don't leak
    # into the section list. Inline `<!-- keep -->` / `<!-- resolved -->` tags
    # are preserved by strip_html_comments_preserving_tags.
    body = strip_html_comments_preserving_tags(body)
    parts = _SECTION_RE.split(body)
    prefix = parts[0]
    sections: list[tuple[str, str]] = []
    i = 1
    while i < len(parts):
        header = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((header, content))
        i += 2
    return prefix, sections


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    target_dir = Path(args.target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    agent = args.agent or "unknown-agent"
    session_id = args.session_id or "unknown-session"
    writer = args.writer or "migration"

    initialized: list[str] = []
    skipped: list[str] = []
    missing_templates: list[str] = []
    for doc in DEFAULT_DOCS:
        target = target_dir / doc
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
        "initialized": initialized,
        "skipped": skipped,
        "missing_templates": missing_templates,
    }
    print(json.dumps(result, indent=2))
    if missing_templates:
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(json.dumps({"status": "error", "message": f"{target_dir} does not exist"}))
        sys.exit(1)
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    for doc in ALL_DOCS:
        p = target_dir / doc
        if not p.exists():
            if doc in DEFAULT_DOCS:
                warnings.append(f"{doc}: missing (core doc)")
            continue
        try:
            meta, _ = load_frontmatter(p.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"{doc}: {e}")
            continue
        checked.append(doc)
        errors.extend(validate_meta(meta, doc))
    result = {
        "status": "success" if not errors else "invalid",
        "checked": checked,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        sys.exit(1)


def cmd_check_reality(args: argparse.Namespace) -> None:
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Handoff directory {target_dir} does not exist. Run init first.",
        }))
        sys.exit(1)

    hard_conflicts: list[dict] = []
    soft_conflicts: list[dict] = []
    uncommitted = git_status_paths()

    # 1. Frontmatter validity + stale verification
    for doc in ALL_DOCS:
        p = target_dir / doc
        if not p.exists():
            continue
        try:
            meta, _ = load_frontmatter(p.read_text(encoding="utf-8"))
        except ValueError as e:
            hard_conflicts.append({
                "type": "frontmatter_parse_error",
                "file": doc,
                "message": str(e),
            })
            continue
        for err in validate_meta(meta, doc):
            hard_conflicts.append({
                "type": "frontmatter_invalid",
                "file": doc,
                "message": err,
            })

        lv = meta.get("last_verified")
        if lv and lv != "SKIPPED":
            dt = as_aware_datetime(lv)
            if dt is None:
                soft_conflicts.append({
                    "type": "invalid_or_naive_timestamp",
                    "file": doc,
                    "message": f"last_verified={lv!r} is naive or unparseable",
                })
            else:
                delta_days = (datetime.now(timezone.utc) - dt).days
                if delta_days > VERIFY_STALE_DAYS:
                    soft_conflicts.append({
                        "type": "stale_verification",
                        "file": doc,
                        "message": (
                            f"last_verified is {delta_days} days old "
                            f"(> {VERIFY_STALE_DAYS})"
                        ),
                    })

    # 2. task.md → referenced files exist on filesystem?
    task_path = target_dir / "task.md"
    if task_path.exists():
        try:
            _, body = load_frontmatter(task_path.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        for ref in extract_referenced_paths(body):
            resolved = normalize_reference_path(ref)
            if not resolved.exists():
                hard_conflicts.append({
                    "type": "missing_file_in_task",
                    "message": (
                        f"task.md references {ref!r} but resolved path "
                        f"{resolved} does not exist"
                    ),
                })

    # 3. walkthrough.md → <session-tools-log> cross-checked against git
    wt_path = target_dir / "walkthrough.md"
    if wt_path.exists():
        try:
            _, body = load_frontmatter(wt_path.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        tools_log_match = re.search(
            r"<session-tools-log>(.*?)</session-tools-log>", body, re.DOTALL
        )
        if tools_log_match:
            raw = tools_log_match.group(1).strip()
            if raw and raw != "[]":
                try:
                    tools_log = json.loads(raw)
                except json.JSONDecodeError as e:
                    soft_conflicts.append({
                        "type": "invalid_tools_log",
                        "message": f"walkthrough <session-tools-log> not valid JSON: {e}",
                    })
                    tools_log = []
                recent_committed = git_recent_committed_files(5)
                cwd = Path.cwd()
                for call in tools_log:
                    if not isinstance(call, dict):
                        continue
                    tool = call.get("tool")
                    tgt = call.get("target")
                    if (tool in {"write_to_file", "write_file", "patch",
                                 "replace_file_content", "multi_replace_file_content"}
                            and tgt):
                        try:
                            rel = str(Path(tgt).resolve().relative_to(cwd)).replace("\\", "/")
                        except (ValueError, OSError):
                            rel = str(tgt).replace("\\", "/")
                        if rel not in uncommitted and rel not in recent_committed:
                            soft_conflicts.append({
                                "type": "tool_call_no_git_evidence",
                                "message": (
                                    f"walkthrough claims write to {rel!r} but no git "
                                    "evidence (not uncommitted, not in last 5 commits)"
                                ),
                            })

    result: dict = {
        "status": "success",
        "hard_conflicts": hard_conflicts,
        "soft_conflicts": soft_conflicts,
    }

    if getattr(args, "apply_soft_conflicts", False) and soft_conflicts:
        result["applied_soft_conflicts"] = apply_soft_conflicts(target_dir, soft_conflicts)

    print(json.dumps(result, indent=2))


def apply_soft_conflicts(target_dir: Path, conflicts: list[dict]) -> int:
    """Append SOFT conflicts to open-questions.md's ``## Soft Conflicts`` section."""
    oq = target_dir / "open-questions.md"
    if not oq.exists():
        return 0
    meta, body = load_frontmatter(oq.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    heading = "## Soft Conflicts (Reconciled)"
    lines = [
        f"- ⚠️ `{now}` · **{c.get('type', 'unknown')}** — {c.get('message', '')}"
        for c in conflicts
    ]
    block = "\n".join(lines) + "\n"

    if heading in body:
        idx = body.find(heading) + len(heading)
        # Insert on a new line immediately after the heading, preserving any
        # trailing "- None." placeholder line below it.
        body = body[:idx] + "\n\n" + block + body[idx:].lstrip("\n")
    else:
        body = body.rstrip() + f"\n\n{heading}\n\n{block}"

    meta["last_updated"] = now
    meta["last_writer"] = "take-over"
    write_atomic(oq, dump_frontmatter(meta, body))
    return len(conflicts)


def classify_cleanup(target_dir: Path) -> dict:
    """Return classification plan (does NOT mutate anything on disk)."""
    removed_clear: list[dict] = []
    removed_stale: list[dict] = []
    unsure_items: list[dict] = []
    kept: list[dict] = []
    deleted_files = git_deleted_files(90)

    # --- walkthrough.md ---
    wt = target_dir / "walkthrough.md"
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
                # Non-dated section (e.g. "## History of Active Entries") — leave.
                continue
            date_str = date_match.group(1)

            # Priority: KEEP > CLEAR > STALE > UNSURE
            if (_KEEP_TAG_RE.search(header) or _KEEP_TAG_RE.search(content)
                    or _KEEP_WORD_RE.search(header)):
                kept.append({"file": "walkthrough.md", "header": title,
                             "reason": "keep marker or keyword"})
                continue

            if _RESOLVED_TAG_RE.search(content) or _RESOLVED_TAG_RE.search(header):
                removed_clear.append({"file": "walkthrough.md", "header": title,
                                      "reason": "explicit <!-- resolved --> marker"})
                continue

            # CLEAR by git evidence: all referenced files present in deleted set
            path_refs = extract_referenced_paths(content)
            if path_refs and all(
                any(df.endswith(pr.replace("\\", "/").lstrip("/")) for df in deleted_files)
                for pr in path_refs
            ):
                removed_clear.append({
                    "file": "walkthrough.md",
                    "header": title,
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
                    p = target_dir / doc
                    if p.exists():
                        text = p.read_text(encoding="utf-8")
                        if date_str in text or title in text:
                            in_use = True
                            break
                if not in_use:
                    removed_stale.append({
                        "file": "walkthrough.md",
                        "header": title,
                        "age_days": delta_days,
                    })
                    continue

            unsure_items.append({
                "file": "walkthrough.md",
                "header": title,
                "snippet": content.strip().split("\n", 1)[0][:120],
            })

    # --- open-questions.md ---
    oq = target_dir / "open-questions.md"
    if oq.exists():
        try:
            _, body = load_frontmatter(oq.read_text(encoding="utf-8"))
        except ValueError:
            body = ""
        _, sections = split_sections(body)
        for header, content in sections:
            title = header.strip("# \r\n")
            if "Soft Conflicts" in title:
                continue
            if _KEEP_TAG_RE.search(header) or _KEEP_TAG_RE.search(content):
                kept.append({"file": "open-questions.md", "header": title,
                             "reason": "explicit <!-- keep --> marker"})
                continue
            if _RESOLVED_TAG_RE.search(content) or _RESOLVED_TAG_RE.search(header):
                removed_clear.append({"file": "open-questions.md", "header": title,
                                      "reason": "explicit <!-- resolved --> marker"})
                continue
            if _is_placeholder(content):
                kept.append({"file": "open-questions.md", "header": title,
                             "reason": "placeholder (empty or '- None.')"})
                continue
            unsure_items.append({
                "file": "open-questions.md",
                "header": title,
                "snippet": content.strip().split("\n", 1)[0][:120],
            })

    return {
        "clear": removed_clear,
        "stale": removed_stale,
        "kept": kept,
        "unsure": unsure_items,
    }


def apply_cleanup(target_dir: Path, plan: dict) -> dict:
    to_remove = {
        (item["file"], item["header"])
        for item in plan.get("clear", []) + plan.get("stale", [])
    }
    applied = {"walkthrough.md": 0, "open-questions.md": 0}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for doc in ("walkthrough.md", "open-questions.md"):
        p = target_dir / doc
        if not p.exists():
            continue
        meta, body = load_frontmatter(p.read_text(encoding="utf-8"))
        prefix, sections = split_sections(body)
        rebuilt = [prefix]
        for header, content in sections:
            title = header.strip("# \r\n")
            if (doc, title) in to_remove:
                applied[doc] += 1
                continue
            rebuilt.append(header)
            rebuilt.append(content)
        meta["last_updated"] = now
        meta["last_writer"] = "hand-off"
        write_atomic(p, dump_frontmatter(meta, "".join(rebuilt)))
    return applied


def cmd_clean_up(args: argparse.Namespace) -> None:
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(json.dumps({"status": "error", "message": f"{target_dir} not found"}))
        sys.exit(1)

    plan = classify_cleanup(target_dir)
    if args.dry_run:
        print(json.dumps({"status": "planned", **plan}, indent=2))
        return

    applied = apply_cleanup(target_dir, plan)
    print(json.dumps({"status": "applied", **plan, "applied": applied}, indent=2))


def cmd_write_atomic(args: argparse.Namespace) -> None:
    filepath = Path(args.filepath)
    if args.content is not None:
        content = args.content
    elif args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()
    write_atomic(filepath, content)
    print(json.dumps({
        "status": "success",
        "filepath": str(filepath),
        "bytes": len(content),
    }))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Session Handoff · reconcile helper"
    )
    parser.add_argument(
        "--target-dir",
        default=".hermes/handoff",
        help="Handoff directory (default: .hermes/handoff)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize handoff directory from templates")
    p_init.add_argument("--agent", help="Last agent name")
    p_init.add_argument("--session-id", help="Session ID")
    p_init.add_argument("--writer", default="migration",
                        choices=sorted(VALID_WRITERS))
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate",
                            help="Validate frontmatter across handoff docs")
    p_val.set_defaults(func=cmd_validate)

    p_check = sub.add_parser("check-reality",
                              help="Verify handoff docs against git/fs")
    p_check.add_argument(
        "--apply-soft-conflicts",
        action="store_true",
        help="Also append SOFT conflicts to open-questions.md",
    )
    p_check.set_defaults(func=cmd_check_reality)

    p_clean = sub.add_parser(
        "clean-up",
        help="Classify walkthrough / open-questions entries (two-phase)",
    )
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
    p_write.set_defaults(func=cmd_write_atomic)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
