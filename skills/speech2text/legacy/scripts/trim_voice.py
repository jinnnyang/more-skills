"""trim_voice.py — clamp long silences in a WAV to reduce STT token cost.

Usage:
    python trim_voice.py --max-silence 0.5 --input-wav in.wav --output-wav out.wav

Behaviour:
- Load a mono / pcm_s16le WAV (anything else → error).
- Detect silence runs via 10 ms RMS windows using the audio's own noise floor.
- For every silence run longer than --max-silence seconds, keep the first
  ``max_silence`` seconds intact and drop the remainder. Voice / non-silent
  audio is preserved sample-for-sample; short natural pauses stay untouched.
- Write result to --output-wav (parent dir created if missing).

No third-party deps; uses only ``wave`` / ``array`` / ``argparse`` / ``math``.
"""

from __future__ import annotations

import argparse
import array
import math
import sys
import wave
from pathlib import Path
from typing import List, Tuple


FRAME_MS = 10                     # analysis frame length
FRAMES_PER_SECOND = 1000 // FRAME_MS
MIN_SILENCE_FRAMES = 20           # only *count* runs of ≥ 200 ms as silence
ABSOLUTE_MIN_THRESHOLD = 60       # int16-space RMS floor for pathological clips


def _die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"trim_voice: error: {msg}\n")
    sys.exit(code)


# ---------------------------------------------------------------------------
# WAV I/O (identical contract to split_voice.py)
# ---------------------------------------------------------------------------

def load_wav_pcm16_mono(path: Path) -> Tuple[array.array, int]:
    if not path.exists():
        _die(f"input WAV does not exist: {path}")
    if path.suffix.lower() != ".wav":
        _die(f"only .wav is supported; got {path.suffix!r}")
    try:
        wf = wave.open(str(path), "rb")
    except (wave.Error, EOFError) as exc:
        _die(f"could not open WAV: {exc}")
    with wf:
        nch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        if nch != 1:
            _die(f"WAV must be mono; got nchannels={nch}")
        if sampwidth != 2:
            _die(f"WAV must be 16-bit PCM (sampwidth=2); got sampwidth={sampwidth}")
        raw = wf.readframes(nframes)
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder == "big":
        samples.byteswap()
    if not samples:
        _die("input WAV is empty (0 samples)")
    return samples, framerate


def write_wav_pcm16_mono(path: Path, samples: array.array, framerate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        buf = samples
        if sys.byteorder == "big":
            buf = array.array("h", samples)
            buf.byteswap()
        wf.writeframes(buf.tobytes())


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def compute_frame_rms(samples: array.array, framerate: int) -> List[float]:
    samples_per_frame = max(1, framerate * FRAME_MS // 1000)
    rms: List[float] = []
    total = len(samples)
    for start in range(0, total, samples_per_frame):
        end = start + samples_per_frame
        if end > total:
            end = total
        s = 0
        for i in range(start, end):
            v = samples[i]
            s += v * v
        n = end - start
        rms.append(math.sqrt(s / n) if n else 0.0)
    return rms


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    idx = (len(ordered) - 1) * (p / 100.0)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def detect_silences(rms: List[float], threshold: float) -> List[Tuple[int, int]]:
    """Return (start_frame_incl, end_frame_excl) runs of ≥ MIN_SILENCE_FRAMES."""
    silences: List[Tuple[int, int]] = []
    run_start: int = -1
    for i, v in enumerate(rms):
        if v < threshold:
            if run_start < 0:
                run_start = i
        else:
            if run_start >= 0 and i - run_start >= MIN_SILENCE_FRAMES:
                silences.append((run_start, i))
            run_start = -1
    if run_start >= 0 and len(rms) - run_start >= MIN_SILENCE_FRAMES:
        silences.append((run_start, len(rms)))
    return silences


# ---------------------------------------------------------------------------
# Trim
# ---------------------------------------------------------------------------

def trim_silences(
    samples: array.array,
    framerate: int,
    max_silence_seconds: float,
) -> Tuple[array.array, int, float]:
    """Return (new_samples, kept_silence_count, dropped_seconds)."""
    rms = compute_frame_rms(samples, framerate)
    if not rms:
        return samples, 0, 0.0

    noise_floor = percentile(rms, 20)
    median_rms = percentile(rms, 50)
    silence_threshold = max(noise_floor * 2.5, ABSOLUTE_MIN_THRESHOLD)
    silence_threshold = min(
        silence_threshold,
        median_rms * 0.6 if median_rms > 0 else silence_threshold,
    )

    silences = detect_silences(rms, silence_threshold)
    max_silence_frames = max(1, int(max_silence_seconds * FRAMES_PER_SECOND))
    samples_per_frame = max(1, framerate * FRAME_MS // 1000)

    # Build a list of (start_sample, end_sample) segments to KEEP.
    keep_ranges: List[Tuple[int, int]] = []
    cursor_sample = 0
    dropped_frames = 0
    trimmed = 0
    for s_start, s_end in silences:
        run_len = s_end - s_start
        if run_len <= max_silence_frames:
            continue  # short pause — leave it alone
        # Long silence: keep first max_silence_frames, drop the rest.
        trim_boundary_frame = s_start + max_silence_frames
        keep_end_sample = trim_boundary_frame * samples_per_frame
        if keep_end_sample > cursor_sample:
            keep_ranges.append((cursor_sample, keep_end_sample))
        cursor_sample = s_end * samples_per_frame
        dropped_frames += run_len - max_silence_frames
        trimmed += 1
    # Tail: whatever remains after the last long silence.
    if cursor_sample < len(samples):
        keep_ranges.append((cursor_sample, len(samples)))

    # Concatenate.
    if not keep_ranges:
        return samples, 0, 0.0
    out = array.array("h")
    for a, b in keep_ranges:
        out.extend(samples[a:b])
    dropped_seconds = dropped_frames * FRAME_MS / 1000.0
    return out, trimmed, dropped_seconds


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trim_voice",
        description="Clamp long silences in a mono s16 WAV to shrink STT input.",
    )
    parser.add_argument("--max-silence", type=float, required=True,
                        help="Maximum silence duration to keep (seconds). "
                             "Anything longer is trimmed to this length.")
    parser.add_argument("--input-wav", type=Path, required=True,
                        help="Path to source WAV (mono / pcm_s16le).")
    parser.add_argument("--output-wav", type=Path, required=True,
                        help="Path to output WAV (parent dir auto-created).")
    args = parser.parse_args(argv)

    if args.max_silence <= 0:
        _die(f"--max-silence must be > 0; got {args.max_silence}")

    samples, framerate = load_wav_pcm16_mono(args.input_wav)
    total_seconds = len(samples) / framerate
    print(f"[trim_voice] input: {args.input_wav.name}  "
          f"{total_seconds:.2f}s  {framerate} Hz  {len(samples)} samples",
          flush=True)

    trimmed, kept_count, dropped_seconds = trim_silences(
        samples, framerate, args.max_silence,
    )
    write_wav_pcm16_mono(args.output_wav, trimmed, framerate)

    out_seconds = len(trimmed) / framerate
    reduction_pct = (dropped_seconds / total_seconds * 100.0) if total_seconds else 0.0
    print(
        f"[trim_voice] trimmed {kept_count} long silences, dropped "
        f"{dropped_seconds:.2f}s ({reduction_pct:.1f}%). "
        f"output: {out_seconds:.2f}s -> {args.output_wav}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
