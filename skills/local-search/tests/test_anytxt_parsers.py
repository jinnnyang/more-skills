"""Tests for the AnyTxt response parser.

The parser is the highest-risk component in anytxt.py because it depends on
server response shape. These tests lock down the wire-check-confirmed shape
and prove we're future-proof against column reordering.
"""
from local_search.anytxt import _parse_file_entry, _parse_result_output


# ─── Wire-check confirmed shape ──────────────────────────────────────────

def test_parse_file_entry_from_list_matches_wire_check():
    """Real AnyTxt row shape (2026-07 wire-check)."""
    field_order = ["fid", "lastModify", "size", "file"]
    entry = [
        "2879675253150734652",
        "1761804532",
        "15674533",
        "C:\\Users\\jinnn\\Downloads\\PostgreSQL 18.0 Documentation(A4).pdf",
    ]
    fid, path, mtime, size = _parse_file_entry(entry, field_order)
    assert fid == "2879675253150734652"
    assert path.endswith("Documentation(A4).pdf")
    assert mtime == 1761804532
    assert size == 15674533


# ─── Future-proof: server reorders columns ───────────────────────────────

def test_parse_file_entry_handles_reordered_field_array():
    """Parser follows response's field array, not hardcoded column indexes."""
    field_order = ["size", "file", "lastModify", "fid"]
    entry = ["100", "C:\\a.txt", "1234567890", "99"]
    fid, path, mtime, size = _parse_file_entry(entry, field_order)
    assert fid == "99"
    assert path == "C:\\a.txt"
    assert mtime == 1234567890
    assert size == 100


# ─── Defensive fallbacks ─────────────────────────────────────────────────

def test_parse_file_entry_dict_form_still_works():
    """If server ever returns dicts, we handle it."""
    entry = {"fid": "123", "file": "C:\\b.md", "lastModify": "1700000000", "size": "5"}
    fid, path, mtime, size = _parse_file_entry(
        entry, ["fid", "lastModify", "size", "file"],
    )
    assert (fid, path, mtime, size) == ("123", "C:\\b.md", 1700000000, 5)


def test_parse_file_entry_dict_with_path_field_alias():
    """dict fallback tolerates alternate field names."""
    entry = {"fid": "1", "filePath": "C:\\x", "lastModify": "0", "fileSize": "10"}
    fid, path, mtime, size = _parse_file_entry(entry, ["fid", "lastModify", "size", "file"])
    assert path == "C:\\x"
    assert size == 10


def test_parse_file_entry_missing_fields_return_none():
    entry = ["", "", "", ""]
    fid, path, mtime, size = _parse_file_entry(
        entry, ["fid", "lastModify", "size", "file"],
    )
    assert fid == ""       # empty string is not None, but stringified
    assert path == ""
    assert mtime is None    # int('') raises → caught → None
    assert size is None


def test_parse_file_entry_scalar_entry_degrades_gracefully():
    """Unexpected shape should not crash."""
    fid, path, mtime, size = _parse_file_entry(
        42, ["fid", "lastModify", "size", "file"],
    )
    assert fid is None
    assert path == "42"
    assert mtime is None
    assert size is None


# ─── _parse_result_output composition ────────────────────────────────────

def test_parse_result_output_uses_field_from_response():
    output = {
        "count": 1,
        "field": ["fid", "lastModify", "size", "file"],
        "files": [["1", "1700000000", "42", "C:\\x.py"]],
    }
    rows = _parse_result_output(output)
    assert rows == [("1", "C:\\x.py", 1700000000, 42)]


def test_parse_result_output_empty_files():
    output = {
        "count": 0,
        "field": ["fid", "lastModify", "size", "file"],
        "files": [],
    }
    assert _parse_result_output(output) == []


def test_parse_result_output_missing_field_falls_back_to_default_order():
    """If `field` is absent, use the wire-check default column order."""
    output = {"count": 1, "files": [["1", "1700000000", "42", "C:\\x.py"]]}
    rows = _parse_result_output(output)
    assert rows == [("1", "C:\\x.py", 1700000000, 42)]


def test_parse_result_output_multiple_rows():
    output = {
        "count": 3,
        "field": ["fid", "lastModify", "size", "file"],
        "files": [
            ["1", "1700000000", "100", "C:\\a.py"],
            ["2", "1700000001", "200", "C:\\b.py"],
            ["3", "1700000002", "300", "C:\\c.py"],
        ],
    }
    rows = _parse_result_output(output)
    assert len(rows) == 3
    assert rows[1] == ("2", "C:\\b.py", 1700000001, 200)
