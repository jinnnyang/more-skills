"""voice_pipeline.py — one-shot audio → transcript.

Usage:
    python voice_pipeline.py --input in.mp3 --output out.txt

Pipeline (all four steps in one process):
    1. ffmpeg transcode        →  mono / 16 kHz / pcm_s16le wav
    2. trim_voice.py           →  clamp long silences to --max-silence
    3. split_voice.py          →  chunk to ≤ --max-seconds on silence points
    4. read_voice.py           →  Volcengine sauc ASR, concat to --output

Intermediate artefacts land in a temp dir (auto-cleaned unless --keep-workdir
is given, in which case the path is printed for inspection).

Config precedence for each stage matches the underlying single-purpose script
(CLI flag > env > default). Only the flags most people tune are lifted here;
for anything else, run the underlying script directly.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional

_MODULE_DIR = Path(__file__).resolve().parent

TRIM = _MODULE_DIR / "trim_voice.py"
SPLIT = _MODULE_DIR / "split_voice.py"
READ = _MODULE_DIR / "read_voice.py"

SUPPORTED_INPUT_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".webm"}


def _die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"voice_pipeline: error: {msg}\n")
    sys.exit(code)


SECRET_FLAGS = {"--api-key"}


def _redact(cmd: List[str]) -> List[str]:
    """Return a copy of cmd with values of SECRET_FLAGS replaced by ***."""
    out: List[str] = []
    i = 0
    while i < len(cmd):
        tok = str(cmd[i])
        out.append(tok)
        if tok in SECRET_FLAGS and i + 1 < len(cmd):
            out.append("***")
            i += 2
            continue
        i += 1
    return out


def _step(label: str, cmd: List[str], *, cwd: Optional[Path] = None) -> None:
    printable = " ".join(_redact(cmd))
    print(f"\n=== [{label}] {printable}", flush=True)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    dt = time.time() - t0
    if res.returncode != 0:
        _die(f"[{label}] exited {res.returncode} after {dt:.1f}s", code=res.returncode)
    print(f"=== [{label}] done in {dt:.1f}s", flush=True)


def _ffmpeg_transcode(src: Path, dst: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        _die("ffmpeg not found on PATH")
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(dst),
    ]
    _step("transcode", cmd)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="voice_pipeline",
        description="One-shot: audio file → Volc ASR transcript.",
    )
    parser.add_argument("--input", type=Path, required=True,
                        help=f"Input audio file. Supported: {sorted(SUPPORTED_INPUT_EXTS)}")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output transcript .txt path.")
    parser.add_argument("--max-silence", type=float, default=0.5,
                        help="trim_voice: silences longer than this get clamped (default: 0.5s).")
    parser.add_argument("--max-seconds", type=float, default=30.0,
                        help="split_voice: hard upper bound per chunk (default: 30s).")
    parser.add_argument("--skip-trim", action="store_true",
                        help="Skip the trim_voice stage (feed raw wav directly to split).")
    parser.add_argument("--workdir", type=Path, default=None,
                        help="Directory for intermediate artefacts. Default: auto-clean temp dir.")
    parser.add_argument("--keep-workdir", action="store_true",
                        help="Do not delete the workdir on exit (default: auto-clean if we made it).")
    # read_voice pass-through flags — same semantics as read_voice.py.
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--resource", default=None)
    parser.add_argument("--language", default=None)
    args = parser.parse_args(argv)

    src: Path = args.input
    if not src.exists():
        _die(f"input does not exist: {src}")
    if src.suffix.lower() not in SUPPORTED_INPUT_EXTS:
        _die(f"unsupported input extension {src.suffix!r}. "
             f"Supported: {sorted(SUPPORTED_INPUT_EXTS)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Workdir setup.
    made_own_workdir = False
    if args.workdir is not None:
        workdir = args.workdir
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="voice-pipeline-"))
        made_own_workdir = True

    t_start = time.time()
    print(f"[voice_pipeline] input:  {src}", flush=True)
    print(f"[voice_pipeline] output: {args.output}", flush=True)
    print(f"[voice_pipeline] workdir: {workdir}", flush=True)

    try:
        # 1. transcode → raw.wav
        raw = workdir / "01-raw.wav"
        _ffmpeg_transcode(src, raw)

        # 2. trim → trimmed.wav (optional)
        if args.skip_trim:
            trimmed = raw
            print("=== [trim]     SKIPPED (--skip-trim)", flush=True)
        else:
            trimmed = workdir / "02-trimmed.wav"
            _step("trim", [sys.executable, str(TRIM),
                           "--max-silence", str(args.max_silence),
                           "--input-wav", str(raw),
                           "--output-wav", str(trimmed)])

        # 3. split → chunks/
        chunks_dir = workdir / "03-chunks"
        chunks_dir.mkdir(exist_ok=True)
        _step("split", [sys.executable, str(SPLIT),
                        "--max-seconds", str(args.max_seconds),
                        "--input-wav", str(trimmed),
                        "--output-folder", str(chunks_dir)])
        chunk_files = sorted(chunks_dir.glob("*.wav"))
        if not chunk_files:
            _die("split_voice produced no chunks — refuse to continue")
        print(f"[voice_pipeline] {len(chunk_files)} chunk(s) ready for ASR", flush=True)

        # 4. read → output txt
        read_cmd = [sys.executable, str(READ),
                    "--input-folder", str(chunks_dir),
                    "--output-txt", str(args.output)]
        # forward optional read_voice params only if user set them
        for flag, val in [("--api-key", args.api_key),
                          ("--endpoint", args.endpoint),
                          ("--resource", args.resource),
                          ("--language", args.language)]:
            if val:
                read_cmd += [flag, val]
        _step("read", read_cmd)

        total = time.time() - t_start
        try:
            n_chars = len(args.output.read_text(encoding="utf-8"))
        except Exception:
            n_chars = -1
        print(f"\n[voice_pipeline] done. {n_chars} chars -> {args.output}   "
              f"total elapsed: {total:.1f}s", flush=True)
        return 0
    finally:
        if made_own_workdir and not args.keep_workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"[voice_pipeline] workdir kept: {workdir}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
