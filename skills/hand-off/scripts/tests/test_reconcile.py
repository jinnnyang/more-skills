"""pytest suite for the pure-logic parts of ``scripts/reconcile.py``.

Rationale (see ``REVIEW-2026-07-20.md`` §P1 · reconcile.py test coverage):
these three functions encode the most consequential product decisions
(five-bucket cleanup classifier, questions.md archive semantics, multi-hop
trust health). They are pure logic (no live network / no user prompts) so
they can be safety-netted with pytest before anyone touches the internals.

The module is loaded via ``SourceFileLoader`` because ``scripts/reconcile.py``
carries a PEP-723 ``# /// script`` header that trips normal ``import``.

Run from ``skills/hand-off/``:

    uv run --with pytest --with pyyaml pytest scripts/tests/ -v
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------


def _load_reconcile():
    here = Path(__file__).resolve().parent
    # tests/ lives inside scripts/; go one up to grab reconcile.py.
    src = here.parent / "reconcile.py"
    loader = importlib.machinery.SourceFileLoader("reconcile", str(src))
    spec = importlib.util.spec_from_loader("reconcile", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


reconcile = _load_reconcile()


# ---------------------------------------------------------------------------
# Helpers for building fake scope directories
# ---------------------------------------------------------------------------


def _frontmatter(kind: str, session_id: str = "test-session") -> str:
    """Minimal valid frontmatter block for a handoff doc."""
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


def _make_scope(
    tmp_path: Path,
    *,
    walkthrough_body: str | None = None,
    questions_body: str | None = None,
    context_body: str | None = None,
    task_body: str | None = None,
) -> Path:
    """Create a scope directory with any subset of the four core docs."""
    if walkthrough_body is not None:
        (tmp_path / "walkthrough.md").write_text(
            _frontmatter("walkthrough") + walkthrough_body, encoding="utf-8"
        )
    if questions_body is not None:
        (tmp_path / "questions.md").write_text(
            _frontmatter("questions") + questions_body, encoding="utf-8"
        )
    if context_body is not None:
        (tmp_path / "context.md").write_text(
            _frontmatter("context") + context_body, encoding="utf-8"
        )
    if task_body is not None:
        (tmp_path / "task.md").write_text(
            _frontmatter("task") + task_body, encoding="utf-8"
        )
    return tmp_path


@pytest.fixture(autouse=True)
def _isolate_git(monkeypatch):
    """Neutralise git calls by default; individual tests can override."""
    monkeypatch.setattr(reconcile, "git_deleted_files", lambda *_a, **_kw: set())
    monkeypatch.setattr(reconcile, "git_repo_root", lambda *_a, **_kw: None)
    monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (0, []))
    monkeypatch.setattr(
        reconcile, "git", lambda *_a, **_kw: (1, "", "not a repo")
    )


# ===========================================================================
# classify_cleanup — five buckets: clear / stale / kept / unsure / archived
# ===========================================================================


class TestClassifyCleanup:
    def test_empty_scope_returns_empty_buckets(self, tmp_path):
        scope = _make_scope(tmp_path)
        plan = reconcile.classify_cleanup(scope)
        assert plan == {
            "clear": [],
            "stale": [],
            "kept": [],
            "unsure": [],
            "archived": [],
        }

    def test_walkthrough_resolved_marker_goes_to_clear(self, tmp_path):
        body = (
            "## 2026-06-01 — old fix <!-- resolved -->\n"
            "- Body content\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["clear"]) == 1
        assert plan["clear"][0]["file"] == "walkthrough.md"
        assert "resolved" in plan["clear"][0]["reason"]

    def test_walkthrough_keep_marker_goes_to_kept(self, tmp_path):
        body = (
            "## 2026-06-01 — permanent decision <!-- keep -->\n"
            "- Reasoning\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["kept"]) == 1
        assert plan["kept"][0]["file"] == "walkthrough.md"

    def test_walkthrough_keep_keyword_in_header_goes_to_kept(self, tmp_path):
        """Header containing lesson/surprise/decision/invariant → KEEP."""
        body = (
            "## 2026-06-01 — a critical decision\n"
            "- Note.\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert any(k["file"] == "walkthrough.md" for k in plan["kept"])

    def test_walkthrough_old_entry_goes_to_stale(self, tmp_path):
        """Entry older than STALE_DAYS and not referenced elsewhere → STALE."""
        old_date = (
            datetime.now(timezone.utc) - timedelta(days=reconcile.STALE_DAYS + 5)
        ).strftime("%Y-%m-%d")
        body = (
            f"## {old_date} — antique note\n"
            "- Body.\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["stale"]) == 1
        assert plan["stale"][0]["age_days"] > reconcile.STALE_DAYS

    def test_walkthrough_old_but_referenced_by_task_goes_to_unsure(self, tmp_path):
        """Old entry still referenced from task.md must NOT be stale."""
        old_date = (
            datetime.now(timezone.utc) - timedelta(days=reconcile.STALE_DAYS + 5)
        ).strftime("%Y-%m-%d")
        body = (
            f"## {old_date} — still relevant note\n"
            "- Body.\n\n"
        )
        # task.md mentions the same date string, so `in_use = True`.
        scope = _make_scope(
            tmp_path,
            walkthrough_body=body,
            task_body=f"- `[ ]` continue work from {old_date}\n",
        )
        plan = reconcile.classify_cleanup(scope)
        assert plan["stale"] == []
        assert len(plan["unsure"]) == 1

    def test_walkthrough_recent_unmarked_goes_to_unsure(self, tmp_path):
        recent = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body = (
            f"## {recent} — ambiguous entry\n"
            "- Body without markers.\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["unsure"]) == 1
        assert plan["unsure"][0]["header"].endswith("ambiguous entry")

    def test_walkthrough_deleted_file_ref_goes_to_clear(self, tmp_path, monkeypatch):
        """Entry referencing files deleted in git history → CLEAR."""
        monkeypatch.setattr(
            reconcile,
            "git_deleted_files",
            lambda *_a, **_kw: {"src/foo.py"},
        )
        body = (
            "## 2026-06-01 — removed foo module\n"
            "- Deleted `src/foo.py` in this session.\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["clear"]) == 1
        assert "deleted in git" in plan["clear"][0]["reason"]

    def test_walkthrough_entry_without_date_is_ignored(self, tmp_path):
        """Cleanup classifier requires ## YYYY-MM-DD — <slug> format."""
        body = (
            "## Random header without a date\n"
            "- Content.\n\n"
        )
        scope = _make_scope(tmp_path, walkthrough_body=body)
        plan = reconcile.classify_cleanup(scope)
        # No bucket receives it — classifier skips undated headers.
        assert plan == {
            "clear": [],
            "stale": [],
            "kept": [],
            "unsure": [],
            "archived": [],
        }

    def test_questions_resolved_goes_to_archived(self, tmp_path):
        body = (
            "## Open\n\n"
            "### Q1 · Should we use Postgres or MySQL? <!-- resolved -->\n"
            "Chose Postgres.\n\n"
            "## Closed\n\n"
        )
        scope = _make_scope(tmp_path, questions_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert len(plan["archived"]) == 1
        assert plan["archived"][0]["file"] == "questions.md"
        assert "resolved" in plan["archived"][0]["reason"]

    def test_questions_already_closed_stays_kept(self, tmp_path):
        body = (
            "## Open\n\n"
            "- None.\n\n"
            "## Closed\n\n"
            "### Q0 · Historical decision\n"
            "Answer.\n\n"
        )
        scope = _make_scope(tmp_path, questions_body=body)
        plan = reconcile.classify_cleanup(scope)
        # ## Closed entries must NOT be re-archived (they're already there).
        assert plan["archived"] == []
        # The archived entry is reported as kept for audit.
        assert any(
            k["file"] == "questions.md" and "archived" in k["reason"].lower()
            for k in plan["kept"]
        )

    def test_questions_active_open_stays_kept(self, tmp_path):
        body = (
            "## Open\n\n"
            "### Q1 · Real active question\n"
            "Body text.\n\n"
            "## Closed\n\n"
        )
        scope = _make_scope(tmp_path, questions_body=body)
        plan = reconcile.classify_cleanup(scope)
        assert plan["archived"] == []
        assert any(
            k["file"] == "questions.md" and "active" in k["reason"]
            for k in plan["kept"]
        )


# ===========================================================================
# _rebuild_questions_body — moves archived entries Open → Closed
# ===========================================================================


class TestRebuildQuestionsBody:
    def test_archive_migrates_open_entry_to_closed(self):
        body = (
            "## Open\n\n"
            "### Q1 · Should we ship? <!-- resolved -->\n"
            "Yes, ship it.\n\n"
            "## Closed\n\n"
        )
        archived = [
            {
                "file": "questions.md",
                "header": "Q1 · Should we ship? <!-- resolved -->",
                "reason": "explicit <!-- resolved -->",
                "content": "Yes, ship it.\n\n",
            }
        ]
        result = reconcile._rebuild_questions_body(body, archived, set())
        assert "## Open" in result
        assert "## Closed" in result
        # The Open section should now be empty (rebuilder inserts "- None.")
        open_split, closed_split = result.split("## Closed", 1)
        assert "Q1 · Should we ship?" not in open_split
        assert "Q1 · Should we ship?" in closed_split
        assert "Yes, ship it." in closed_split

    def test_empty_open_gets_none_placeholder(self):
        body = "## Open\n\n## Closed\n\n"
        result = reconcile._rebuild_questions_body(body, [], set())
        assert "- None." in result.split("## Closed", 1)[0]

    def test_active_open_survives(self):
        body = (
            "## Open\n\n"
            "### Q1 · Active thing\n"
            "Body.\n\n"
            "## Closed\n\n"
        )
        result = reconcile._rebuild_questions_body(body, [], set())
        open_part = result.split("## Closed", 1)[0]
        assert "Q1 · Active thing" in open_part
        assert "Body." in open_part

    def test_existing_closed_entries_preserved(self):
        body = (
            "## Open\n\n"
            "- None.\n\n"
            "## Closed\n\n"
            "### Q0 · Historical decision\n"
            "Answer.\n\n"
        )
        result = reconcile._rebuild_questions_body(body, [], set())
        assert "Q0 · Historical decision" in result.split("## Closed", 1)[1]

    def test_explicit_delete_removes_entry(self):
        body = (
            "## Open\n\n"
            "### Q_delete · Discard this\n"
            "Body.\n\n"
            "## Closed\n\n"
        )
        result = reconcile._rebuild_questions_body(
            body,
            archived=[],
            to_remove={("questions.md", "Q_delete · Discard this")},
        )
        assert "Q_delete" not in result


# ===========================================================================
# _analyze_multihop_health — verdict thresholds
# ===========================================================================


def _ctx_lines(*, git: int = 0, user: int = 0, test: int = 0,
               inferred: int = 0, unknown: int = 0, untagged: int = 0) -> str:
    """Build a synthetic context.md invariants body with the exact tag mix."""
    lines: list[str] = ["## Invariants\n"]
    for _ in range(git):
        lines.append("- [git:a1b2c3d] Some git-attested fact.\n")
    for _ in range(user):
        lines.append("- [user:2026-07-20] Some user-confirmed fact.\n")
    for _ in range(test):
        lines.append("- [test:test_x] Some test-enforced fact.\n")
    for _ in range(inferred):
        lines.append("- [inferred:sess-x] Some inferred fact.\n")
    for _ in range(unknown):
        lines.append("- [unknown] Some untraceable fact.\n")
    for _ in range(untagged):
        lines.append("- Some unattributed fact with no tag.\n")
    return "".join(lines) + "\n"


class TestAnalyzeMultihopHealth:
    def test_fresh_when_no_hops(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (0, []))
        scope = _make_scope(tmp_path, context_body=_ctx_lines(inferred=10))
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["health"] == "fresh"
        assert result["hop_count"] == 0
        assert result["issues"] == []

    def test_healthy_low_hops_low_inferred(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (1, ["alice"]))
        scope = _make_scope(tmp_path, context_body=_ctx_lines(git=8, inferred=2))
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["health"] == "healthy"
        assert result["issues"] == []

    def test_hop3_low_inferred_stays_healthy(self, tmp_path, monkeypatch):
        """hop_count ≥ 3 alone is not an issue — needs inferred_pct too."""
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (3, []))
        # 10% inferred < 40% threshold
        scope = _make_scope(tmp_path, context_body=_ctx_lines(git=9, inferred=1))
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["health"] == "healthy"
        assert result["hop_count"] == 3

    def test_hop3_high_inferred_triggers_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (3, []))
        # 50% inferred >= 40%, single issue → warning
        scope = _make_scope(tmp_path, context_body=_ctx_lines(git=5, inferred=5))
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["health"] == "warning"
        assert len(result["issues"]) == 1
        assert "hallucination-cascade" in result["issues"][0]

    def test_hop3_high_inferred_and_untagged_triggers_unhealthy(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (3, []))
        # Need BOTH inferred_pct ≥ 40 AND untagged_pct ≥ 50 → 2 issues → unhealthy.
        # 1 git + 5 inferred + 6 untagged = 12 total.
        # inferred_pct = 100 * 5 / 12 = 41 (≥ 40) ✓
        # untagged_pct = 100 * 6 / 12 = 50 (≥ 50) ✓
        scope = _make_scope(
            tmp_path,
            context_body=_ctx_lines(git=1, inferred=5, untagged=6),
        )
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["health"] == "unhealthy"
        assert len(result["issues"]) >= 2

    def test_soft_conflicts_count_toward_health(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (2, []))
        scope = _make_scope(tmp_path, context_body=_ctx_lines(git=5))
        result = reconcile._analyze_multihop_health(
            scope,
            {"soft_conflicts": [{"id": 1}, {"id": 2}, {"id": 3}]},
        )
        # 1 issue → warning (hop 2 alone with all-git tags is otherwise clean)
        assert result["health"] == "warning"
        assert any("SOFT conflicts" in i for i in result["issues"])

    def test_inferred_samples_capped_at_5(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (1, []))
        scope = _make_scope(tmp_path, context_body=_ctx_lines(inferred=10))
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert len(result["inferred_samples"]) <= 5

    def test_provenance_distribution_totals_match_input(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (1, []))
        scope = _make_scope(
            tmp_path,
            context_body=_ctx_lines(git=2, user=1, test=1, inferred=3, unknown=1, untagged=2),
        )
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        dist = result["provenance_distribution"]
        assert dist["git"] == 2
        assert dist["user"] == 1
        assert dist["test"] == 1
        assert dist["inferred"] == 3
        assert dist["unknown"] == 1
        assert dist["untagged"] == 2

    def test_missing_context_md_treated_as_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(reconcile, "_count_hops", lambda *_a, **_kw: (2, []))
        scope = _make_scope(tmp_path)  # no context.md
        result = reconcile._analyze_multihop_health(scope, {"soft_conflicts": []})
        assert result["hop_count"] == 2
        assert result["inferred_pct"] == 0
        assert result["untagged_pct"] == 0
        assert result["health"] == "healthy"
