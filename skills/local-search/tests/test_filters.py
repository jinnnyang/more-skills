from local_search.filters import (
    UnifiedFilters, VALID_SORT, normalize_ext,
    to_everything_query, to_anytxt_params, _anytxt_order,
)


# ─── normalize_ext ────────────────────────────────────────────────────────

def test_normalize_ext_strips_dots_globs_and_lowercases():
    assert normalize_ext(("py", ".md", "*.txt", ".PDF", "*.")) == ("py", "md", "txt", "pdf")


def test_normalize_ext_drops_empty_entries():
    assert normalize_ext(("", "  ", "*", ".")) == ()


# ─── to_everything_query — prefix semantics + quoting ─────────────────────

def test_everything_query_prefix_semantics():
    """v2: --path is a PREFIX (trailing backslash appended)."""
    f = UnifiedFilters(path="C:/dev/hermes", ext=("py", "md"))
    q = to_everything_query("config", f)
    assert "ext:py;md" in q
    assert "path:C:\\dev\\hermes\\" in q
    assert '"' not in q                  # no quotes when path has no spaces
    assert q.startswith("config")


def test_everything_query_path_with_spaces_gets_quoted_as_whole_token():
    f = UnifiedFilters(path="C:/Program Files")
    q = to_everything_query("cfg", f)
    assert '"path:C:\\Program Files\\"' in q


def test_everything_query_bare_query_no_filters():
    assert to_everything_query("readme", UnifiedFilters()) == "readme"


def test_everything_query_trailing_slash_is_normalized_once():
    """Users may pass with or without trailing slash — result identical."""
    f1 = UnifiedFilters(path="C:/dev/hermes")
    f2 = UnifiedFilters(path="C:/dev/hermes/")
    f3 = UnifiedFilters(path="C:\\dev\\hermes\\")
    assert to_everything_query("q", f1) == to_everything_query("q", f2) == to_everything_query("q", f3)


# ─── to_anytxt_params — server-side quirks documented ─────────────────────

def test_anytxt_params_ext_no_dots_no_globs_lowercase():
    f = UnifiedFilters(ext=("py", "md"), path="C:/dev", limit=50, offset=10)
    p = to_anytxt_params("hello", f)
    assert p["filterExt"] == "py;md"
    assert p["filterDir"] == "C:\\dev"
    assert p["pattern"] == "hello"
    assert p["limit"] == 50
    assert p["offset"] == 10


def test_anytxt_params_no_ext_defaults_to_star():
    assert to_anytxt_params("foo", UnifiedFilters())["filterExt"] == "*"


def test_anytxt_params_empty_path_passes_empty_string():
    """Server rewrites '' to 'C:' — we don't second-guess the user."""
    p = to_anytxt_params("q", UnifiedFilters())
    assert p["filterDir"] == ""


def test_anytxt_params_default_time_range_is_max():
    p = to_anytxt_params("q", UnifiedFilters())
    assert p["lastModifyBegin"] == 0
    assert p["lastModifyEnd"] == 2_147_483_647


def test_anytxt_params_custom_time_range():
    p = to_anytxt_params("q", UnifiedFilters(),
                         modified_after=1700000000, modified_before=1800000000)
    assert p["lastModifyBegin"] == 1700000000
    assert p["lastModifyEnd"] == 1800000000


# ─── order code mapping ───────────────────────────────────────────────────

def test_anytxt_order_codes():
    assert _anytxt_order("modified", True) == 2
    assert _anytxt_order("modified", False) == 1
    assert _anytxt_order("path", True) == 4
    assert _anytxt_order("path", False) == 3
    assert _anytxt_order("name", True) == 0
    assert _anytxt_order("size", False) == 0


# ─── VALID_SORT sanity ────────────────────────────────────────────────────

def test_valid_sort_matches_everyfile_capabilities():
    """These are the sort keys everyfile actually accepts (2026-07 wire-check)."""
    expected = {"name", "path", "size", "ext", "modified", "created", "accessed"}
    assert VALID_SORT == expected
