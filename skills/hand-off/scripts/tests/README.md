# reconcile.py tests

Pytest suite for the pure-logic core of `scripts/reconcile.py`.

Covers the three highest-risk functions:

| Function | Buckets / signals verified |
| --- | --- |
| `classify_cleanup(scope)` | five buckets — clear / stale / kept / unsure / archived |
| `_rebuild_questions_body(body, archived, to_remove)` | Open → Closed archive migration |
| `_analyze_multihop_health(scope, reality)` | verdict thresholds — fresh / healthy / warning / unhealthy |

## Running

From `skills/hand-off/`:

```bash
uv run --with pytest --with pyyaml python -m pytest scripts/tests/ -v
```

`uv run` transparently installs pytest + pyyaml into an isolated env each call,
so no persistent dev-dependency setup is required.

## Design notes

- **Module loading via `SourceFileLoader`.** `scripts/reconcile.py` carries a
  PEP-723 `# /// script` header (inline metadata for `uv run …`) that trips
  normal `import`. Tests bypass this by loading the file as a module directly.
- **Git is stubbed by default** via an autouse `_isolate_git` fixture; individual
  tests override the stub when they need a specific `git_deleted_files` /
  `_count_hops` behaviour.
- **No temp git repos.** All tests operate on tmp_path directories without
  `git init`; git-dependent code paths are exercised via monkeypatch. This
  keeps the suite fast (< 0.5 s) and Windows-compatible without needing shell.

## Deliberately not covered

The following are exercised end-to-end in real hand-off runs and would need a
fixture harness disproportionate to their risk:

- `_prepare_scope` / `cmd_prepare` composite output (would need real git repo)
- `write_atomic` filesystem semantics (tested implicitly via classify tests)
- MSYS path resolution on non-Windows hosts

Add coverage only if a regression escapes here.
