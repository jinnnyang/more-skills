"""pytest suite for the concurrency-lock lifecycle in ``scripts/reconcile.py``.

Regression net for the take-over stale-lock bug found on 2026-07-20
(see walkthrough.md § 2026-07-20 and DECISIONS.md ADR "check-reality is
read-only by default"). Before that fix, calling ``check-reality`` with
``--session-id`` would silently ``acquire_lock`` as a side effect, leak
``.handoff.lock`` past take-over's exit, and later ambush hand-off with
a HARD ``concurrency_lock_conflict``.

Load via SourceFileLoader because reconcile.py carries a PEP-723 header.

Run from ``skills/take-over/``:

    uv run --with pytest --with pyyaml pytest scripts/tests/ -v
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    """Enough for _check_reality_scope to run: the four core docs each
    with valid frontmatter and empty body. No git repo needed — reality
    check just falls back to non-git branches for the doc reads."""
    for kind, name in (
        ("context", "context.md"),
        ("task", "task.md"),
        ("walkthrough", "walkthrough.md"),
        ("questions", "questions.md"),
    ):
        (tmp_path / name).write_text(_frontmatter(kind) + f"# {kind}\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Core semantics
# ---------------------------------------------------------------------------


def test_check_reality_default_does_not_write_lock(tmp_path: Path):
    """Regression: default (acquire=False) must never create .handoff.lock,
    even with --session-id / --agent supplied. This is the exact failure
    mode from the 2026-07-20 walkthrough."""
    scope = _make_minimal_scope(tmp_path)

    result = reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_TAKEOVER", agent="A_TAKEOVER",
    )

    assert (scope / ".handoff.lock").exists() is False, (
        "default check-reality must be read-only; found leaked lock"
    )
    assert result.get("status") != "error"
    assert not result.get("hard_conflicts"), \
        f"clean scope should have no hard conflicts, got {result.get('hard_conflicts')}"


def test_check_reality_opt_in_writes_lock(tmp_path: Path):
    """acquire=True (mirrors --acquire-lock CLI flag) preserves the old
    behaviour so hand-off's prepare can still take the lock deliberately."""
    scope = _make_minimal_scope(tmp_path)

    reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_HANDOFF", agent="A_HANDOFF", acquire=True,
    )

    lock = scope / ".handoff.lock"
    assert lock.exists(), "acquire=True must write .handoff.lock"
    data = json.loads(lock.read_text(encoding="utf-8"))
    assert data["session_id"] == "S_HANDOFF"
    assert data["agent"] == "A_HANDOFF"


def test_read_only_check_still_reports_existing_lock_conflict(tmp_path: Path):
    """A leaked lock from an earlier acquire must still surface as a HARD
    conflict on a later read-only check — the fix must not weaken detection,
    only stop the accidental *acquire*."""
    scope = _make_minimal_scope(tmp_path)
    # Simulate: an earlier op (hand-off's prepare, or an old buggy take-over)
    # took the lock.
    reconcile.acquire_lock(scope, "S_OWNER", "A_OWNER")
    assert (scope / ".handoff.lock").exists()

    # Now a *different* session runs plain check-reality.
    result = reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_STRANGER", agent="A_STRANGER",
    )

    hard = result.get("hard_conflicts", [])
    assert any(c.get("type") == "concurrency_lock_conflict" for c in hard), \
        f"expected concurrency_lock_conflict in hard_conflicts, got {hard}"

    # And the existing lock must not have been clobbered.
    data = json.loads((scope / ".handoff.lock").read_text(encoding="utf-8"))
    assert data["session_id"] == "S_OWNER", "read-only check must not overwrite the lock"


def test_same_session_reacquire_is_noop(tmp_path: Path):
    """Sanity: acquire=True with the same session-id that already owns the
    lock is not a conflict (matches check_lock_conflict's early return)."""
    scope = _make_minimal_scope(tmp_path)
    reconcile.acquire_lock(scope, "S_SELF", "A_SELF")

    result = reconcile._check_reality_scope(
        scope, apply_soft=False,
        session_id="S_SELF", agent="A_SELF", acquire=True,
    )
    hard = result.get("hard_conflicts", [])
    assert not any(c.get("type") == "concurrency_lock_conflict" for c in hard), \
        f"same-session re-acquire must not be a conflict, got {hard}"


# ---------------------------------------------------------------------------
# CLI-level plumbing: parser must expose --acquire-lock, cmd_check_reality
# must forward it into _check_reality_scope.
# ---------------------------------------------------------------------------


def test_cli_parser_exposes_acquire_lock_flag():
    parser = reconcile.build_parser() if hasattr(reconcile, "build_parser") else None
    # reconcile.py does not export build_parser; parse via main-style route
    # by re-invoking the argparse setup inline instead. Fall back to argv
    # smoke test.
    import subprocess, sys
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check-reality", "--help"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--acquire-lock" in proc.stdout, \
        "check-reality --help must document --acquire-lock"


def test_cli_default_does_not_write_lock(tmp_path: Path):
    """End-to-end CLI parity of test_check_reality_default_does_not_write_lock."""
    scope = _make_minimal_scope(tmp_path)
    import subprocess, sys
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check-reality",
         "--scope", str(scope),
         "--session-id", "S_CLI", "--agent", "A_CLI"],
        capture_output=True, text=True,
    )
    # returncode may be 0 or non-zero depending on incidental warnings;
    # what matters is the side effect on disk.
    assert (scope / ".handoff.lock").exists() is False, (
        f"CLI default must not write .handoff.lock. stdout={proc.stdout} stderr={proc.stderr}"
    )


def test_cli_acquire_flag_writes_lock(tmp_path: Path):
    scope = _make_minimal_scope(tmp_path)
    import subprocess, sys
    here = Path(__file__).resolve().parent
    script = here.parent / "reconcile.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check-reality",
         "--acquire-lock",
         "--scope", str(scope),
         "--session-id", "S_CLI", "--agent", "A_CLI"],
        capture_output=True, text=True,
    )
    assert (scope / ".handoff.lock").exists(), (
        f"CLI --acquire-lock must write .handoff.lock. stdout={proc.stdout} stderr={proc.stderr}"
    )
