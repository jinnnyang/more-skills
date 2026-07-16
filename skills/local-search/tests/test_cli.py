"""CLI smoke tests locking down v0.1.1 reviewer-era behaviors.

These tests DO NOT hit real backends — they only cover the CLI pre-validation
layer (empty-query safety rail, regex pre-check, path normalization). The
backend layer has its own tests.

Regressions we're locking in:
  1. `files ""` without --path/--ext must fail (safety rail against index-wide dump).
  2. `files ""` WITH --path or --ext must pass CLI validation.
  3. `files <bad-regex> --regex` must fail BEFORE touching Everything.
  4. `text ""` must raise InvalidQuery (not ValueError → traceback).
  5. `text "" --count-only` must raise InvalidQuery.
  6. `_normalize_path_arg` handles: None / "" / "  " / "." / "~/…" / "/c/Users/…" / native.
"""
import pytest
from click.testing import CliRunner

from local_search import cli as cli_mod
from local_search.cli import _normalize_path_arg, main


runner = CliRunner()


# ─── Empty QUERY safety rail ─────────────────────────────────────────────────

def test_files_empty_query_no_scope_rejected():
    """No -p AND no -e → refuse; would otherwise dump the entire index."""
    result = runner.invoke(main, ["files", ""])
    assert result.exit_code == 2
    assert "Empty QUERY" in result.output or "Empty QUERY" in (result.stderr_bytes or b"").decode(errors="replace")


def test_files_empty_query_with_ext_scope_passes_validation(monkeypatch):
    """Empty QUERY with -e must pass the safety rail and reach the backend."""
    called = {}

    def fake_search_files(q, f, **kw):
        called["q"] = q
        called["ext"] = f.ext
        from local_search.formatters import ResultSet
        return ResultSet(mode="files", query=q, elapsed_ms=0, total=0, rows=[])

    monkeypatch.setattr("local_search.everything.search_files", fake_search_files)
    result = runner.invoke(main, ["files", "", "-e", "py"])
    assert result.exit_code == 0, result.output
    assert called["ext"] == ("py",)


def test_files_empty_query_with_path_scope_passes_validation(monkeypatch):
    """Empty QUERY with -p must pass the safety rail."""
    def fake_search_files(q, f, **kw):
        from local_search.formatters import ResultSet
        return ResultSet(mode="files", query=q, elapsed_ms=0, total=0, rows=[])
    monkeypatch.setattr("local_search.everything.search_files", fake_search_files)
    result = runner.invoke(main, ["files", "", "-p", "C:\\Users"])
    assert result.exit_code == 0, result.output


# ─── Regex pre-validation ────────────────────────────────────────────────────

def test_files_bad_regex_rejected_before_backend():
    """Malformed regex must be caught by the CLI/backend pre-check.

    The regex validation lives inside `everything.search_files` and fires
    BEFORE the everyfile import + IPC call — so we can run the real code
    path (no monkeypatch) and observe that a bad regex short-circuits with
    exit 2, without needing Everything to be running.
    """
    result = runner.invoke(main, ["files", "test[", "--regex"])
    assert result.exit_code == 2, f"expected 2, got {result.exit_code}. output: {result.output}"
    combined = result.output + (result.stderr_bytes or b"").decode(errors="replace")
    assert "Invalid regex" in combined
    assert "test[" in combined  # error should quote the offending pattern


def test_files_good_regex_reaches_backend(monkeypatch):
    """A valid regex must NOT be rejected by the pre-check."""
    called = {}
    def fake_search_files(q, f, **kw):
        called["regex"] = kw.get("regex")
        from local_search.formatters import ResultSet
        return ResultSet(mode="files", query=q, elapsed_ms=0, total=0, rows=[])
    monkeypatch.setattr("local_search.everything.search_files", fake_search_files)
    result = runner.invoke(main, ["files", "test_.*\\.py", "--regex", "-p", "C:\\"])
    assert result.exit_code == 0, result.output
    assert called["regex"] is True


# ─── text empty-query safety rail ───────────────────────────────────────────

def test_text_empty_query_raises_invalid_query():
    """`text ""` must return exit 2 with a friendly error (not a Python traceback)."""
    result = runner.invoke(main, ["text", ""])
    assert result.exit_code == 2
    combined = result.output + (result.stderr_bytes or b"").decode(errors="replace")
    # Must NOT show a Python traceback / raw ValueError:
    assert "Traceback" not in combined
    assert "ValueError" not in combined
    # Must be a friendly [error] line:
    assert "[error]" in combined
    assert "non-empty query" in combined


def test_text_count_only_empty_query_raises_invalid_query():
    """`text "" --count-only` must ALSO be gated (would hit AnyTxt otherwise)."""
    result = runner.invoke(main, ["text", "", "--count-only"])
    assert result.exit_code == 2
    combined = result.output + (result.stderr_bytes or b"").decode(errors="replace")
    assert "Traceback" not in combined
    assert "[error]" in combined


# ─── _normalize_path_arg ────────────────────────────────────────────────────

def test_normalize_path_none_and_empty():
    """None, "", "   " all mean "no restriction" → return None."""
    assert _normalize_path_arg(None) is None
    assert _normalize_path_arg("") is None
    assert _normalize_path_arg("   ") is None


def test_normalize_path_tilde_expands():
    """~/Desktop must expand to an absolute path under HOME."""
    out = _normalize_path_arg("~/Desktop")
    assert out is not None
    # On Windows the resolved path is C:\Users\<user>\Desktop
    assert ":" in out and "Desktop" in out
    assert "~" not in out


def test_normalize_path_dot_becomes_absolute():
    """`.` must become an absolute path (the CWD)."""
    out = _normalize_path_arg(".")
    assert out is not None
    assert ":" in out  # has a drive letter → absolute
    assert out != "."


def test_normalize_path_msys_style_converted():
    """MSYS `/c/Users/jinnn/Desktop` must convert to `C:\\Users\\jinnn\\Desktop`.

    This is the git-bash / Hermes-terminal case: agents habitually pass
    /c/Users/... but Path.resolve would prepend the CWD drive → C:\\c\\Users\\...
    """
    out = _normalize_path_arg("/c/Users/jinnn/Desktop")
    assert out is not None
    # Must NOT be under C:\c\... (the pre-fix wrong output)
    assert "\\c\\Users" not in out and "/c/Users" not in out
    # Must be under a real drive at path start
    assert out[:3].upper() == "C:\\"
    assert out.upper().endswith("USERS\\JINNN\\DESKTOP")


def test_normalize_path_msys_style_uppercases_drive():
    """`/d/data` must produce `D:\\data`, not `d:\\data`."""
    out = _normalize_path_arg("/d/data")
    assert out is not None
    assert out[:3] == "D:\\"


def test_normalize_path_native_windows_passthrough():
    """A native Windows path must survive (resolved but not mangled)."""
    out = _normalize_path_arg("C:\\Users\\jinnn")
    assert out is not None
    assert out.upper().startswith("C:\\USERS\\JINNN")
    # No MSYS-style artifacts:
    assert "/c/" not in out
    assert not out.startswith("C:\\c\\")
