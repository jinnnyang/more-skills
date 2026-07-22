"""pytest suite for ``write-atomic``'s hardening flags in ``scripts/reconcile.py``.

Covers the ``--scope`` boundary check (DECISIONS R32) and the
``--stamp-frontmatter`` frontmatter-stamping path (DECISIONS R33).
Originally driven by the 9-case smoke matrix in ``BUG-REPORT-20260722.md``;
this file promotes that matrix to a real regression suite so the two flags
can't silently regress.

Uses subprocess against the CLI so exit codes, JSON payload shape, and
argparse ``choices=`` validation are all exercised end-to-end.

Run from ``skills/hand-off/``::

    uv run --with pytest --with pyyaml pytest scripts/tests/test_write_atomic.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "reconcile.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    """Invoke ``reconcile.py`` with ``args`` and return the completed process."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )


def _valid_frontmatter(kind: str = "context") -> str:
    """Minimal valid handoff-doc frontmatter (pre-stamping)."""
    return (
        "---\n"
        f"kind: {kind}\n"
        "version: 1\n"
        "last_updated: 2020-01-01T00:00:00+00:00\n"
        "last_verified: 2020-01-01T00:00:00+00:00\n"
        "last_agent: old-agent\n"
        "last_writer: migration\n"
        "session_id: old-session\n"
        "status: in-progress\n"
        "---\n"
        "\nBody paragraph.\n"
    )


# ===========================================================================
# --scope boundary (DECISIONS R32)
# ===========================================================================


class TestScopeBoundary:
    def test_no_scope_flag_writes_anywhere(self, tmp_path):
        """Default behavior — no --scope, any path accepted (backward compat)."""
        target = tmp_path / "any.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", "hi",
        )
        assert proc.returncode == 0, proc.stderr
        assert target.read_text(encoding="utf-8") == "hi"
        payload = json.loads(proc.stdout)
        assert payload["status"] == "success"

    def test_filepath_inside_scope_succeeds(self, tmp_path):
        scope = tmp_path / "scope"
        scope.mkdir()
        target = scope / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--scope", str(scope),
            "--content", "ok",
        )
        assert proc.returncode == 0, proc.stderr
        assert target.read_text(encoding="utf-8") == "ok"

    def test_filepath_outside_scope_refused_exit_4(self, tmp_path):
        scope = tmp_path / "scope"
        scope.mkdir()
        # Sibling directory outside the scope
        (tmp_path / "outside").mkdir()
        target = tmp_path / "outside" / "leaked.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--scope", str(scope),
            "--content", "should not land",
        )
        assert proc.returncode == 4, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["status"] == "error"
        assert payload["reason"] == "path_outside_scope"
        assert "hint" in payload
        # The write must NOT have created the file
        assert not target.exists()

    def test_filepath_traversal_via_dotdot_refused(self, tmp_path):
        """`..` sneaking out of scope is refused because we .resolve() first."""
        scope = tmp_path / "scope"
        scope.mkdir()
        (tmp_path / "sibling").mkdir()
        # Path syntactically starts with $scope but resolves out
        target = scope / ".." / "sibling" / "escaped.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--scope", str(scope),
            "--content", "no",
        )
        assert proc.returncode == 4, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["reason"] == "path_outside_scope"

    def test_bash_escape_trap_would_be_caught(self, tmp_path):
        """Repro of BUG-REPORT Issue 1 — an unescaped ${f} concatenation.

        Simulates what bash produces when ``"$SCOPE\\${f}.md"`` collapses
        to ``<scope>${f}.md`` (no separator, literal placeholder). With
        ``--scope`` the write is refused; without it, it would silently
        land outside the scope. This test exists so future refactors of
        write-atomic can't lose the safety net.
        """
        scope = tmp_path / "MediaCrawler"
        scope.mkdir()
        # This is what bash would hand to the tool after the escape trap:
        malformed = tmp_path / "MediaCrawler${f}.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(malformed),
            "--scope", str(scope),
            "--content", "hi",
        )
        assert proc.returncode == 4, proc.stderr
        assert not malformed.exists(), (
            "write-atomic must refuse before creating the malformed sibling"
        )


# ===========================================================================
# --stamp-frontmatter (DECISIONS R33)
# ===========================================================================


class TestStampFrontmatter:
    def test_no_flag_writes_content_verbatim(self, tmp_path):
        """Default: content passes through untouched, no stamping."""
        target = tmp_path / "context.md"
        original = _valid_frontmatter()
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", original,
        )
        assert proc.returncode == 0, proc.stderr
        assert target.read_text(encoding="utf-8") == original

    def test_missing_frontmatter_hard_error_exit_5(self, tmp_path):
        target = tmp_path / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", "just plain text, no frontmatter fence\n",
            "--stamp-frontmatter",
        )
        assert proc.returncode == 5, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["reason"] == "frontmatter_missing"
        # The file must NOT have been written
        assert not target.exists()

    def test_stamp_updates_timestamps_and_preserves_other_keys(self, tmp_path):
        import yaml  # available under uv run's inline pyyaml dep

        target = tmp_path / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", _valid_frontmatter(),
            "--stamp-frontmatter",
        )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["stamped_frontmatter"] is True

        written = target.read_text(encoding="utf-8")
        # Split frontmatter for round-trip check
        assert written.startswith("---\n")
        _, fm_block, body = written.split("---", 2)
        meta = yaml.safe_load(fm_block)
        # Timestamps refreshed (not the 2020 placeholder)
        assert meta["last_updated"].startswith("202"), meta
        assert meta["last_updated"] != "2020-01-01T00:00:00+00:00"
        assert meta["last_verified"] == meta["last_updated"]
        # Other keys untouched
        assert meta["kind"] == "context"
        assert meta["version"] == 1
        assert meta["status"] == "in-progress"
        # Metadata args not passed → unchanged
        assert meta["last_writer"] == "migration"
        assert meta["last_agent"] == "old-agent"
        assert meta["session_id"] == "old-session"
        # Body preserved
        assert "Body paragraph." in body

    def test_stamp_with_writer_agent_session_updates_all(self, tmp_path):
        import yaml

        target = tmp_path / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", _valid_frontmatter(),
            "--stamp-frontmatter",
            "--writer", "hand-off",
            "--agent", "new-agent",
            "--session-id", "new-session",
        )
        assert proc.returncode == 0, proc.stderr
        written = target.read_text(encoding="utf-8")
        _, fm_block, _ = written.split("---", 2)
        meta = yaml.safe_load(fm_block)
        assert meta["last_writer"] == "hand-off"
        assert meta["last_agent"] == "new-agent"
        assert meta["session_id"] == "new-session"

    def test_invalid_writer_rejected_by_argparse(self, tmp_path):
        """`choices=` catches this before write-atomic runs. Exit code is 2."""
        target = tmp_path / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--content", _valid_frontmatter(),
            "--stamp-frontmatter",
            "--writer", "not-a-real-writer",
        )
        assert proc.returncode == 2, proc.stderr
        assert "invalid choice" in proc.stderr

    def test_stamp_plus_scope_combines_cleanly(self, tmp_path):
        """The two flags are orthogonal — both should apply in one call."""
        scope = tmp_path / "scope"
        scope.mkdir()
        target = scope / "context.md"
        proc = _run(
            "write-atomic",
            "--filepath", str(target),
            "--scope", str(scope),
            "--content", _valid_frontmatter(),
            "--stamp-frontmatter",
            "--writer", "hand-off",
        )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["stamped_frontmatter"] is True
        assert payload["status"] == "success"
        assert target.exists()
