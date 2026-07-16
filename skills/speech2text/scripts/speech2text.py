"""speech2text — local faster-whisper batch ASR (Chinese-first, GPU-default).

Replaces the Volcengine sauc streaming pipeline (preserved under legacy/).
Reference implementation: MediaCrawler's wav-to-txt-fw.py (2026-07-15 final).

Input:   single audio/video file OR a directory of *.wav
Output:  UTF-8 .txt, sidecar by default; --output file/dir/all.txt (see Output
         Behavior table in SKILL.md)
Design:  see the plan at ../2026-07-15_173418-speech2text-refactor.md — 17 decisions.

Notable defaults (do NOT casually change):
  --model medium --device cuda --compute-type int8 --language zh
  --beam-size 1 --vad-filter --simplified
  condition_on_previous_text=True  (hardcoded — see plan Q16)
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import wave
from pathlib import Path
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Output-path resolution (SKILL.md "Output Behavior" — 6 rows)
# ---------------------------------------------------------------------------
def is_txt_path(p: Path) -> bool:
    return p.suffix.lower() == ".txt"


def resolve_targets(
    input_path: Path, output: Optional[Path]
) -> tuple[list[Path], dict[Path, Path], Optional[Path]]:
    """
    Returns (input_wavs, per_wav_output_map, merge_target_or_None).

    * merge_target is set only for row 6 (dir + file .txt output).
    * per_wav_output_map is populated for rows 1-5.
    * Directory input globs *.wav non-recursively (top level) AND recursively
      via rglob — we keep the same behavior as MediaCrawler's wav-to-txt-fw.py.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"--input path not found: {input_path}")

    # --- Directory input ---
    if input_path.is_dir():
        wavs = sorted(input_path.rglob("*.wav"))
        if not wavs:
            return [], {}, None

        if output is None:
            # Row 4: sidecar for each
            return wavs, {w: w.with_suffix(".txt") for w in wavs}, None

        if is_txt_path(output):
            # Row 6: merge mode
            output.parent.mkdir(parents=True, exist_ok=True)
            return wavs, {}, output

        # Row 5: dir output → outdir/<stem>.txt
        output.mkdir(parents=True, exist_ok=True)
        return wavs, {w: output / f"{w.stem}.txt" for w in wavs}, None

    # --- Single-file input ---
    if output is None:
        # Row 1: sidecar
        return [input_path], {input_path: input_path.with_suffix(".txt")}, None
    if is_txt_path(output):
        # Row 2: exact file
        output.parent.mkdir(parents=True, exist_ok=True)
        return [input_path], {input_path: output}, None
    # Row 3: dir target
    output.mkdir(parents=True, exist_ok=True)
    return [input_path], {input_path: output / f"{input_path.stem}.txt"}, None


# ---------------------------------------------------------------------------
# Idempotence filter
# ---------------------------------------------------------------------------
def filter_idempotent(
    wavs: list[Path],
    per_wav_out: dict[Path, Path],
    merge_target: Optional[Path],
    force: bool,
) -> tuple[list[Path], int]:
    """Return (todo, skipped_count).

    In merge mode there's no per-file idempotence; --force truncates the merge
    target upfront, otherwise we append."""
    if merge_target is not None:
        if force and merge_target.exists():
            merge_target.unlink()
        return list(wavs), 0

    todo: list[Path] = []
    skipped = 0
    for w in wavs:
        tgt = per_wav_out[w]
        if tgt.exists() and not force:
            skipped += 1
        else:
            todo.append(w)
    return todo, skipped


# ---------------------------------------------------------------------------
# Audio-duration probing (dry-run ETA)
# ---------------------------------------------------------------------------
def probe_seconds(wav: Path) -> Optional[float]:
    """Read PCM WAV header via stdlib. Returns None if the file isn't a valid
    PCM WAV (e.g. mp4/mp3/opus in single-file mode)."""
    try:
        with wave.open(str(wav), "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return frames / rate if rate else None
    except (wave.Error, EOFError, FileNotFoundError):
        return None


def estimate_seconds_fallback(wav: Path) -> float:
    """Rough heuristic: file size / 32000 assumes mono 16 kHz s16le. Off by up
    to 4x on stereo/44k. Used only when the wav header can't be parsed."""
    try:
        return os.path.getsize(wav) / 32000.0
    except OSError:
        return 180.0  # 3 min default


def estimate_batch_seconds(wavs: list[Path]) -> float:
    total = 0.0
    for w in wavs:
        d = probe_seconds(w)
        if d is None:
            d = estimate_seconds_fallback(w)
        total += d
    return total


# ---------------------------------------------------------------------------
# Model loading with CUDA→CPU auto-fallback
# ---------------------------------------------------------------------------
def load_model(model_name: str, device: str, compute_type: str, model_dir: Optional[str]):
    from faster_whisper import WhisperModel

    kwargs = {"device": device, "compute_type": compute_type}
    if model_dir:
        kwargs["download_root"] = model_dir

    try:
        return WhisperModel(model_name, **kwargs), device
    except Exception as e:
        if device == "cuda":
            err = f"{type(e).__name__}: {e}"
            print(
                f"[speech2text] CUDA init failed ({err[:120]}); falling back to CPU int8",
                flush=True,
            )
            kwargs["device"] = "cpu"
            kwargs["compute_type"] = "int8"
            return WhisperModel(model_name, **kwargs), "cpu"
        raise


# ---------------------------------------------------------------------------
# Transcription (single file)
# ---------------------------------------------------------------------------
def transcribe_one(
    model,
    wav: Path,
    args: argparse.Namespace,
    zh_convert: Optional[Callable[[str], str]],
) -> tuple[str, float]:
    segments, info = model.transcribe(
        str(wav),
        language=args.language or None,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
        # Whisper's own default. See SKILL.md pitfall #6 and plan Q16 —
        # setting this to False drops Chinese punctuation density from ~9% to
        # ~1% on long-form audio. Do not "optimize" this to False.
        condition_on_previous_text=True,
        initial_prompt=args.initial_prompt or None,
    )
    parts = [s.text for s in segments]  # generator — actual inference here
    text = "".join(parts).strip()
    if zh_convert is not None:
        text = zh_convert(text)
    if not text:
        raise RuntimeError("empty transcript")
    return text, info.duration or 0.0


# ---------------------------------------------------------------------------
# Atomic write / merge append
# ---------------------------------------------------------------------------
def atomic_write(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(target)


def append_merge(target: Path, stem: str, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    header = f"## {stem}\n\n"
    footer = "\n\n"
    with target.open("a", encoding="utf-8") as f:
        f.write(header + text + footer)


# ---------------------------------------------------------------------------
# ETA / banner / summary
# ---------------------------------------------------------------------------
def format_hms(seconds: float) -> str:
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def print_banner(
    args: argparse.Namespace,
    total: int,
    skipped: int,
    todo: int,
    total_audio_s: float,
) -> None:
    speed = 5.0 if args.device == "cuda" else 0.8
    eta_s = total_audio_s / speed
    print(
        f"[speech2text] input={args.input}  total={total} skip={skipped} todo={todo}",
        flush=True,
    )
    print(
        f"[speech2text] model={args.model} device={args.device} "
        f"compute={args.compute_type} beam={args.beam_size} lang={args.language or 'auto'}",
        flush=True,
    )
    print(
        f"[speech2text] audio_total={format_hms(total_audio_s)}  "
        f"ETA≈{format_hms(eta_s)}  (assuming ~{speed:.1f}x realtime)",
        flush=True,
    )
    print(
        "[speech2text] WARN: do not kill this process mid-batch — CUDA context "
        "can leak (SKILL.md pitfall #5)",
        flush=True,
    )


def print_summary(
    ok: int, fail: int, skipped: int, total_audio: float, wall: float, failed_log: Path
) -> None:
    speed = total_audio / wall if wall else 0.0
    print(
        f"\n[speech2text] done. ok={ok} skipped={skipped} failed={fail}  "
        f"wall={format_hms(wall)}  audio={format_hms(total_audio)}  "
        f"speed={speed:.1f}x realtime",
        flush=True,
    )
    if fail:
        print(f"[speech2text] failed list: {failed_log}", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="speech2text",
        description="Local faster-whisper batch ASR (Chinese-first, GPU-default).",
    )
    ap.add_argument("--input", type=Path, required=True,
                    help="Audio/video file OR directory of *.wav")
    ap.add_argument("--output", type=Path, default=None,
                    help="See SKILL.md 'Output Behavior' table. Ends in .txt "
                         "→ file (or merge target for dir input). Else → dir.")
    ap.add_argument("--model", default="medium",
                    help="Whisper model: tiny/base/small/medium/large-v3 (default: medium)")
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"],
                    help="Inference device (default: cuda; auto-falls back to cpu)")
    ap.add_argument("--compute-type", default="int8",
                    help="ct2 compute type: int8 / int8_float16 / float16 / int8_float32 "
                         "(default: int8 — 4 GB GPU friendly)")
    ap.add_argument("--language", default="zh",
                    help="Language code (default: zh). Pass '' for auto-detect.")
    ap.add_argument("--beam-size", type=int, default=1,
                    help="Beam search size (default: 1 — greedy is fastest AND "
                         "quality matches beam=5 when initial_prompt is set)")
    ap.add_argument("--vad-filter", action=argparse.BooleanOptionalAction, default=True,
                    help="Use voice-activity detection to skip silence (default: on)")
    ap.add_argument(
        "--initial-prompt",
        default="以下是简体中文的短视频语音识别文本，包含标点符号。",
        help="Decoder-priming string (max ~224 tokens ≈ 200 汉字 / 350 英文单词, "
             "truncated FROM THE HEAD if longer — put critical terms at the end). "
             "Pass '' to disable. See SKILL.md 'Writing an effective initial_prompt'.",
    )
    ap.add_argument("--simplified", action=argparse.BooleanOptionalAction, default=True,
                    help="Post-convert output to Simplified Chinese via zhconv (default: on)")
    ap.add_argument("--model-dir", default=None,
                    help="Optional model cache dir (default: HuggingFace cache)")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing .txt (or truncate merge target)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Scan filesystem, print ETA, do NOT load the model")
    return ap


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    args = build_argparser().parse_args(argv)

    # Normalize empty-string flags to None where meaningful
    if args.language == "":
        args.language = None
    if args.initial_prompt == "":
        args.initial_prompt = None

    try:
        wavs, per_wav_out, merge_target = resolve_targets(args.input, args.output)
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    if not wavs:
        print(f"[speech2text] no *.wav found under {args.input}", flush=True)
        return 0

    todo, skipped = filter_idempotent(wavs, per_wav_out, merge_target, args.force)
    total_audio_s = estimate_batch_seconds(wavs) if args.dry_run else 0.0
    if not args.dry_run:
        total_audio_s = estimate_batch_seconds(todo)  # ETA reflects only work-to-do

    print_banner(args, total=len(wavs), skipped=skipped, todo=len(todo),
                 total_audio_s=total_audio_s)

    if args.dry_run:
        for w in todo:
            tgt = merge_target if merge_target else per_wav_out[w]
            dur = probe_seconds(w)
            dur_str = f"{dur:.0f}s" if dur is not None else "(unprobed)"
            print(f"  DRY  {w}  →  {tgt}  audio={dur_str}", flush=True)
        return 0

    if not todo:
        print("[speech2text] nothing to do.", flush=True)
        return 0

    # Lazy imports — avoids loading heavy libs for --help / --dry-run
    zh_convert: Optional[Callable[[str], str]] = None
    if args.simplified:
        try:
            from zhconv import convert as _zh_convert
            zh_convert = lambda s: _zh_convert(s, "zh-cn")
        except ImportError:
            print(
                "[speech2text] WARN: zhconv not installed, --simplified is a no-op. "
                "Install: pip install zhconv",
                flush=True,
            )

    t_load = time.time()
    print(f"[speech2text] loading model {args.model} ...", flush=True)
    model, device_used = load_model(
        args.model, args.device, args.compute_type, args.model_dir
    )
    print(
        f"[speech2text] model loaded on {device_used} in {time.time() - t_load:.1f}s",
        flush=True,
    )

    # Determine failed-log location
    failed_log = (
        (args.input.parent if args.input.is_file() else args.input) / "speech2text.failed.log"
    )
    if failed_log.exists():
        failed_log.unlink()

    t0 = time.time()
    ok = fail = 0
    total_audio_done = 0.0

    for i, wav in enumerate(todo, 1):
        t = time.time()
        try:
            text, audio_s = transcribe_one(model, wav, args, zh_convert)
            if merge_target is not None:
                append_merge(merge_target, wav.stem, text)
                tgt_display = f"{merge_target}::{wav.stem}"
            else:
                target = per_wav_out[wav]
                atomic_write(target, text)
                tgt_display = str(target)

            dt = time.time() - t
            rtf = dt / audio_s if audio_s else 0.0
            total_audio_done += audio_s

            # ETA remaining
            done_frac = i / len(todo)
            elapsed = time.time() - t0
            eta_left = elapsed * (1 - done_frac) / done_frac if done_frac > 0 else 0.0

            print(
                f"[{i:3d}/{len(todo)}] OK    {wav.name}  "
                f"audio={audio_s:.0f}s wall={dt:.1f}s RTF={rtf:.2f} "
                f"chars={len(text)}  ETA_left={format_hms(eta_left)}  → {tgt_display}",
                flush=True,
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            fail += 1
            dt = time.time() - t
            err = f"{type(exc).__name__}: {exc}"
            print(
                f"[{i:3d}/{len(todo)}] FAIL  {wav.name}  after {dt:.1f}s: {err}",
                flush=True,
            )
            with failed_log.open("a", encoding="utf-8") as f:
                f.write(f"{wav}\t{err}\n")

    print_summary(ok, fail, skipped, total_audio_done, time.time() - t0, failed_log)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
