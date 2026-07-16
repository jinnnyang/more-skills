"""Health checks for both backends.

Prints a human-friendly (or JSON) status report and returns True iff both
backends are usable. Called by `local-search doctor`.
"""
from __future__ import annotations

import json as _json
import subprocess
import time
from pathlib import Path

import httpx


def run_doctor(output_format: str = "text") -> bool:
    """Run all health checks and print results.

    Args:
        output_format: "text" (rich table w/ plain-print fallback) or "json".

    Returns:
        True iff both backends are OK.
    """
    ok_ev, elapsed_ev, detail_ev = _check_everything()
    ok_at, elapsed_at, detail_at = _check_anytxt()

    if output_format == "json":
        _print_json(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at)
    else:
        _print_text(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at)

    return ok_ev and ok_at


def _print_json(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at):
    payload = {
        "everything": {"ok": ok_ev, "elapsed_ms": elapsed_ev, "detail": detail_ev},
        "anytxt": {"ok": ok_at, "elapsed_ms": elapsed_at, "detail": detail_at},
        "ok": ok_ev and ok_at,
    }
    print(_json.dumps(payload, ensure_ascii=False, indent=2))


def _print_text(ok_ev, elapsed_ev, detail_ev, ok_at, elapsed_at, detail_at):
    """Prefer rich table; fall back to plain print if rich is not installed."""
    try:
        from rich.console import Console
        from rich.table import Table
        con = Console()
        con.rule("[bold]local-search doctor[/bold]")
        t = Table(show_lines=False)
        t.add_column("Check", style="cyan", no_wrap=True)
        t.add_column("Status")
        t.add_column("Detail / Fix", overflow="fold")
        t.add_row("Everything (files)",
                  "[green]✅ OK[/green]" if ok_ev else "[red]❌ FAIL[/red]",
                  f"{elapsed_ev} ms — {detail_ev}")
        t.add_row("AnyTxt (text)",
                  "[green]✅ OK[/green]" if ok_at else "[red]❌ FAIL[/red]",
                  f"{elapsed_at} ms — {detail_at}")
        con.print(t)
    except ImportError:
        # Plain fallback when rich is not installed
        print("=== local-search doctor ===")
        s = "OK  " if ok_ev else "FAIL"
        print(f"Everything (files):  {s}  [{elapsed_ev} ms]  {detail_ev}")
        s = "OK  " if ok_at else "FAIL"
        print(f"AnyTxt (text):       {s}  [{elapsed_at} ms]  {detail_at}")


def _check_everything() -> tuple[bool, int, str]:
    """Ping Everything via a trivial fetch."""
    try:
        from everyfile import EverythingError, search
    except ImportError as e:
        return False, 0, f"everyfile package not installed: {e}"

    t0 = time.perf_counter()
    try:
        cursor = search("*", fields="meta", limit=1)
        _ = cursor.fetchmany(1)
        total = cursor.total
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return True, elapsed_ms, f"IPC OK, {total:,} files indexed"
    except EverythingError as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        msg = str(e).lower()
        if "not running" in msg or "ipc" in msg or "not started" in msg:
            fix = _everything_session_hint()
            return False, elapsed_ms, f"not running in user session — {fix}"
        if "timed out" in msg or "timeout" in msg:
            return False, elapsed_ms, "index still loading, wait 10 s and re-run"
        return False, elapsed_ms, str(e)
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def _everything_session_hint() -> str:
    """Point at the idempotent PowerShell fixer script we ship, if present."""
    script = (
        Path(__file__).resolve().parent.parent.parent
        / "scripts" / "ensure-everything-user-session.ps1"
    )
    if script.exists():
        return f'Fix: powershell -ExecutionPolicy Bypass -File "{script}"'

    # Fallback: introspect the Everything service PathName
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Service | Where-Object Name -match 'verything').PathName"],
            capture_output=True, text=True, timeout=10,
        )
        exe = r.stdout.strip().strip('"').split(" -svc")[0].strip('"')
        if exe and "Everything" in exe:
            return f'Fix: Start-Process "{exe}"'
    except Exception:
        pass
    return "Fix: launch Everything from Start Menu / tray"


def _check_anytxt() -> tuple[bool, int, str]:
    """Ping AnyTxt via the cheap `Search` method."""
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "id": "doctor",
                "jsonrpc": "2.0",
                "method": "ATRpcServer.Searcher.V1.Search",
                "params": {"input": {
                    "pattern": "the",
                    "filterDir": "",
                    "filterExt": "*",
                    "lastModifyBegin": 0,
                    "lastModifyEnd": 2_147_483_647,
                }},
            }
            r = client.post("http://127.0.0.1:9920", json=payload)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            if r.status_code != 200:
                return False, elapsed_ms, f"HTTP {r.status_code}: {r.text[:120]}"
            body = r.json()
            if body.get("error"):
                return False, elapsed_ms, f"RPC error: {body['error']}"
            count = (
                body.get("result", {}).get("data", {})
                .get("output", {}).get("count", 0)
            )
            return True, elapsed_ms, f"HTTP OK, {count:,} files match 'the'"
    except httpx.ConnectError:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return (False, elapsed_ms,
                "127.0.0.1:9920 unreachable — start AnyTxt "
                "(Menu → Options → General → enable HTTP Service)")
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"
