"""pytest regression suite for hand-off's concurrency-lock lifecycle in
``scripts/reconcile.py``.

Mirrors ``skills/take-over/scripts/tests/test_lock_lifecycle.py``. Different
call sites, same invariant: reads don't take write-locks. hand-off's twist
is that ``_prepare_scope`` is the *deliberate* writer — it must pass
``acquire=True`` so hand-off itself remains atomic-ish.

See ``skills/take-over/DECISIONS.md`` ADR R35 / R36 for context.

Run from ``skills/hand-off/``:

    uv run --with pytest --with pyyaml pytest scripts/tests/test_lock_lifecycle.py -v
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_reconcile():
    here = Path(__file__).resolve().parent
    src = here.parent / "reconcile.py"
    loader = importlib.machinery.SourceFileLoader("reconcile", str(src))
    spec = importlib.util.spec_from_loader("reconcile", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


reconcile = _load_reconcile()


def _frontmatter(kind: str, session_id: str = "test-session") -> str:
    ts = "2026-07-20T12:00:00+00:00"
    return (
        "---\n"
        f"kind: {kind}\n"
        "version: 1\n"
        f"last_updated: {ts}\n"
        f"last_verified: {ts}\n"
        "last_agent: test-agent\n"
        "last_writer: hand-off\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n\n"
    )


def _make_minimal_scope(tmp_path: Path) -> Path:
    for kind, name in (
        ("context", "context.md"),
        ("task", "task.md"),
        ("walkthrough", "walkthrough.md"),
        ("questions", "questions.md"),
    ):
        (tmp_path / name).write_text(_frontmatter(kind) + f"# {kind}\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# _check_reality_scope semantics
# ---------------------------------------------------------------------------


def test_check_reality_default_does_not_write_lock(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    result = reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_ADHOC", agent="A_ADHOC",
    )
    assert (scope / ".handoff.lock").exists() is False, \
        "default check-reality must be read-only"
    assert result.get("status") != "error"


def test_check_reality_opt_in_writes_lock(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_WRITER", agent="A_WRITER", acquire=True,
    )
    lock = scope / ".handoff.lock"
    assert lock.exists()
    data = json.loads(lock.read_text(encoding="utf-8"))
    assert data["session_id"] == "S_WRITER"


def test_read_only_check_still_reports_existing_lock_conflict(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    reconcile.acquire_lock(scope, "S_OWNER", "A_OWNER")

    result = reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_STRANGER", agent="A_STRANGER",
    )
    hard = result.get("hard_conflicts", [])
    assert any(c.get("type") == "concurrency_lock_conflict" for c in hard), \
        f"expected concurrency_lock_conflict, got {hard}"

    data = json.loads((scope / ".handoff.lock").read_text(encoding="utf-8"))
    assert data["session_id"] == "S_OWNER"


# ---------------------------------------------------------------------------
# _prepare_scope: this is hand-off's write-intending caller. Must acquire.
# ---------------------------------------------------------------------------


def test_prepare_scope_acquires_lock_by_default(tmp_path: Path):
    """hand-off's `prepare` is the intended writer. It must still take the
    lock even after the fix — otherwise concurrent hand-offs on the same
    scope could stomp each other."""
    scope = _make_minimal_scope(tmp_path)

    result = reconcile._prepare_scope(
        scope, apply_soft=False,
        session_id="S_HANDOFF", agent="A_HANDOFF",
    )

    lock = scope / ".handoff.lock"
    assert lock.exists(), (
        "_prepare_scope must acquire .handoff.lock (it's the write-intending caller). "
        f"prepare result: {result}"
    )
    data = json.loads(lock.read_text(encoding="utf-8"))
    assert data["session_id"] == "S_HANDOFF"


def test_two_concurrent_prepares_conflict(tmp_path: Path):
    """First prepare acquires; a second prepare with a different session-id
    while the first hasn't cleaned up must HARD-conflict — this is the actual
    concurrency-protection story that lock exists for."""
    scope = _make_minimal_scope(tmp_path)

    r1 = reconcile._prepare_scope(
        scope, apply_soft=False,
        session_id="S_FIRST", agent="A_FIRST",
    )
    assert (scope / ".handoff.lock").exists()

    r2 = reconcile._prepare_scope(
        scope, apply_soft=False,
        session_id="S_SECOND", agent="A_SECOND",
    )
    # _prepare_scope surfaces _check_reality_scope's hard_conflicts either
    # in reality.hard_conflicts or as a halt_on_hard_conflicts status —
    # accept either representation.
    hard = r2.get("hard_conflicts") or r2.get("reality", {}).get("hard_conflicts") or []
    status = r2.get("status", "")
    has_conflict = (
        any(c.get("type") == "concurrency_lock_conflict" for c in hard)
        or "halt" in status
        or "conflict" in status
    )
    assert has_conflict, (
        f"second prepare must detect the first's lock. status={status} hard={hard}"
    )


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------


def test_cli_parser_exposes_acquire_lock_flag():
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check-reality", "--help"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--acquire-lock" in proc.stdout


def test_cli_default_does_not_write_lock(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    subprocess.run(
        [sys.executable, str(script), "check-reality",
         "--scope", str(scope),
         "--session-id", "S_CLI", "--agent", "A_CLI"],
        capture_output=True, text=True,
    )
    assert (scope / ".handoff.lock").exists() is False


def test_cli_acquire_flag_writes_lock(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    subprocess.run(
        [sys.executable, str(script), "check-reality",
         "--acquire-lock",
         "--scope", str(scope),
         "--session-id", "S_CLI", "--agent", "A_CLI"],
        capture_output=True, text=True,
    )
    assert (scope / ".handoff.lock").exists()


def test_cli_prepare_writes_lock(tmp_path: Path):
    """CLI-level echo of test_prepare_scope_acquires_lock_by_default."""
    scope = _make_minimal_scope(tmp_path)
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    subprocess.run(
        [sys.executable, str(script), "prepare",
         "--scope", str(scope),
         "--session-id", "S_PREP", "--agent", "A_PREP"],
        capture_output=True, text=True,
    )
    assert (scope / ".handoff.lock").exists(), \
        "prepare CLI must acquire the lock"
