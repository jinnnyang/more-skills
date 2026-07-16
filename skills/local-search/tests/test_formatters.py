import json
from datetime import datetime

from local_search.formatters import ResultSet, Row, as_csv, as_json, as_markdown


# ─── Row.humansize regression (v1 mutated self.size) ─────────────────────

def test_humansize_does_not_mutate_size():
    r = Row(path="x", size=1024 * 1024 * 5)  # 5 MB
    assert r.humansize() == "5.0 MB"
    assert r.size == 1024 * 1024 * 5         # unchanged
    assert r.humansize() == "5.0 MB"          # second call still correct


def test_humansize_edge_cases():
    assert Row(path="x", size=None).humansize() == ""
    assert Row(path="x", size=0).humansize() == "0 B"
    assert Row(path="x", size=512).humansize() == "512 B"
    assert Row(path="x", size=1024).humansize() == "1.0 KB"
    assert Row(path="x", size=1024 * 1024).humansize() == "1.0 MB"
    assert Row(path="x", size=1024**4).humansize() == "1.0 TB"


# ─── AnyTxt highlight marker handling ────────────────────────────────────

def test_snippet_highlight_markers_become_markdown_bold():
    r = Row(path="x", snippet="use *<<*faster-whisper*>>* medium int8")
    rs = ResultSet(mode="text", query="fw", elapsed_ms=1, total=1, rows=[r])
    md = as_markdown(rs)
    assert "**faster-whisper**" in md
    assert "*<<*" not in md


def test_snippet_plain_strips_markers_keeps_keyword():
    r = Row(path="x", snippet="a *<<*keyword*>>* b *<<*keyword*>>* c")
    assert r.snippet_plain() == "a keyword b keyword c"


# ─── JSON output ─────────────────────────────────────────────────────────

def test_json_has_truncated_true_when_more_than_page():
    rs = ResultSet(mode="files", query="q", elapsed_ms=5, total=100,
                   rows=[Row(path="a")])
    p = json.loads(as_json(rs))
    assert p["truncated"] is True


def test_json_has_truncated_false_when_all_returned():
    rs = ResultSet(mode="files", query="q", elapsed_ms=5, total=1,
                   rows=[Row(path="a")])
    p = json.loads(as_json(rs))
    assert p["truncated"] is False


def test_json_strips_highlight_markers_from_snippet_field():
    rs = ResultSet(mode="text", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path="x", snippet="a *<<*b*>>* c")])
    p = json.loads(as_json(rs))
    assert p["results"][0]["snippet"] == "a b c"


def test_json_roundtrip_all_fields():
    rs = ResultSet(mode="text", query="q", elapsed_ms=42, total=7,
                   rows=[Row(path="C:/a.md", size=100,
                             modified=datetime(2026, 7, 10, 14, 22),
                             snippet="x")])
    p = json.loads(as_json(rs))
    assert p["mode"] == "text"
    assert p["query"] == "q"
    assert p["elapsed_ms"] == 42
    assert p["total"] == 7
    assert p["results"][0]["path"] == "C:/a.md"
    assert p["results"][0]["size"] == 100
    assert p["results"][0]["modified"].startswith("2026-07-10T14:22")


# ─── Markdown output ─────────────────────────────────────────────────────

def test_markdown_empty_result():
    empty = ResultSet(mode="files", query="foo", elapsed_ms=5, total=0)
    assert "No matches" in as_markdown(empty)


def test_markdown_has_header_and_footer():
    rs = ResultSet(mode="files", query="q", elapsed_ms=87, total=1,
                   rows=[Row(path="C:/a.md", size=1024,
                             modified=datetime(2026, 1, 1, 12, 0))])
    md = as_markdown(rs)
    assert "| # | Path | Size | Modified |" in md
    assert "1.0 KB" in md
    assert "2026-01-01 12:00" in md
    assert "elapsed 87 ms" in md
    assert "Total: 1 matches" in md


def test_markdown_footer_shows_truncated():
    rs = ResultSet(mode="files", query="q", elapsed_ms=5, total=999,
                   rows=[Row(path="a"), Row(path="b")])
    md = as_markdown(rs)
    assert "showing 2, truncated" in md


def test_markdown_escapes_pipes_in_paths():
    rs = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path=r"C:\weird|name.md")])
    assert r"\|" in as_markdown(rs)


def test_markdown_snippet_column_appears_only_when_snippets_exist():
    rs_no = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                      rows=[Row(path="a")])
    rs_yes = ResultSet(mode="text", query="q", elapsed_ms=1, total=1,
                       rows=[Row(path="a", snippet="hi")])
    assert "Snippet" not in as_markdown(rs_no)
    assert "Snippet" in as_markdown(rs_yes)


# ─── CSV output ──────────────────────────────────────────────────────────

def test_csv_has_header_and_row():
    rs = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path=r"C:\a.md", size=100,
                             modified=datetime(2026, 7, 10, 14, 22))])
    out = as_csv(rs)
    lines = out.strip().splitlines()
    assert lines[0] == "path,size,modified,snippet"
    assert "a.md" in lines[1]
    assert "100" in lines[1]


def test_csv_empty_size_and_snippet_render_as_empty_cells():
    rs = ResultSet(mode="files", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path="a")])
    out = as_csv(rs)
    assert out.strip().splitlines()[1] == "a,,,"


def test_csv_strips_highlight_markers_from_snippet():
    rs = ResultSet(mode="text", query="q", elapsed_ms=1, total=1,
                   rows=[Row(path="a", snippet="x *<<*key*>>* y")])
    out = as_csv(rs)
    assert "x key y" in out
    assert "*<<*" not in out
