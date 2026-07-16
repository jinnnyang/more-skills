"""split_voice.py — split a mono PCM WAV into ≤ max-seconds chunks on quiet points.

Usage:
    python split_voice.py --max-seconds 30 --input-wav in.wav --output-folder out/

Strategy (nearest-silence-first, greedy):

1. Load WAV via ``wave`` stdlib. Require mono / pcm_s16le. Anything else -> error.
2. Compute per-frame RMS energy on 10 ms windows.
3. Derive a silence threshold from the audio's own noise floor (20th percentile
   RMS × 2.5, floored by an absolute minimum so pure-silence clips don't crash).
4. Detect silence intervals: runs of ≥ 200 ms of below-threshold frames.
5. Greedy split from t=0:
     a. If remaining ≤ max_seconds → emit final chunk, done.
     b. Preferred split point: latest silence interval whose midpoint falls in
        [t + max*0.5, t + max]. Split at that midpoint.
     c. Second choice ("character gap"): in [t + max*0.7, t + max], pick the
        frame with the lowest RMS. Accept if its RMS is comfortably below the
        median (< median × 0.7) — probably an inter-syllable gap.
     d. Fallback: hard-cut at exactly t + max (may clip a syllable, but the
        script contract is "never exceed max-seconds", so precision loses to
        the length guarantee here).
6. Write each chunk as ``{start_ms:08d}-{end_ms:08d}.wav`` under output-folder.

No third-party deps (stdlib only): wave / array / argparse / pathlib / math.
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
MIN_SILENCE_FRAMES = 20           # 200 ms
ABSOLUTE_MIN_THRESHOLD = 60       # RMS on int16 samples — floor so silent clips don't yield 0


def _die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"split_voice: error: {msg}\n")
    sys.exit(code)


# ---------------------------------------------------------------------------
# WAV I/O
# ---------------------------------------------------------------------------

def load_wav_pcm16_mono(path: Path) -> Tuple[array.array, int]:
    """Return (samples int16 array, framerate). Reject anything but mono s16."""
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
    """Non-overlapping 10 ms RMS. Returns one value per frame in playback order."""
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
    """Linear-interpolated percentile (0..100)."""
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
    """Return list of (start_frame_inclusive, end_frame_exclusive) silence runs."""
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
# Segmentation
# ---------------------------------------------------------------------------

def choose_split_frame(
    cursor: int,
    max_frames: int,
    total_frames: int,
    rms: List[float],
    silences: List[Tuple[int, int]],
    silence_threshold: float,
) -> int:
    """Return the frame index at which to cut. Cursor <= return <= cursor+max_frames.

    Preference:
      1. Latest silence whose midpoint sits in [cursor+max/2, cursor+max].
      2. Frame with the lowest RMS in [cursor+max*0.7, cursor+max] if that RMS
         is < median(rms) * 0.7 (probably a syllable gap).
      3. Hard cut at cursor + max_frames.
    """
    end_max = cursor + max_frames
    if end_max >= total_frames:
        return total_frames

    prefer_start = cursor + max_frames // 2
    fallback_start = cursor + (max_frames * 7) // 10

    # (1) silence midpoint
    best_mid: int = -1
    for s_start, s_end in silences:
        if s_end <= cursor:
            continue
        if s_start >= end_max:
            break
        mid = (max(s_start, cursor) + min(s_end, end_max)) // 2
        if prefer_start <= mid <= end_max:
            if mid > best_mid:
                best_mid = mid
    if best_mid > 0:
        return best_mid

    # (2) local minimum RMS in fallback window — soft "between characters"
    lo = max(fallback_start, cursor + 1)
    hi = min(end_max, total_frames)
    if lo < hi:
        # median only on the current window slice for locality
        window = rms[lo:hi]
        window_median = percentile(window, 50)
        min_idx = lo + min(range(len(window)), key=lambda k: window[k])
        min_val = rms[min_idx]
        if min_val < window_median * 0.7 or min_val < silence_threshold * 1.5:
            return min_idx

    # (3) hard cut
    return end_max


def segment_audio(
    samples: array.array,
    framerate: int,
    max_seconds: float,
) -> List[Tuple[int, int]]:
    """Return list of (start_sample, end_sample) chunks obeying max_seconds."""
    samples_per_frame = max(1, framerate * FRAME_MS // 1000)
    rms = compute_frame_rms(samples, framerate)
    total_frames = len(rms)

    noise_floor = percentile(rms, 20)
    median_rms = percentile(rms, 50)
    silence_threshold = max(noise_floor * 2.5, ABSOLUTE_MIN_THRESHOLD)
    # If audio is very quiet overall, cap threshold at 60% of median so we
    # don't classify most of the clip as "silence".
    silence_threshold = min(silence_threshold, median_rms * 0.6 if median_rms > 0 else silence_threshold)

    silences = detect_silences(rms, silence_threshold)

    max_frames = int(max_seconds * FRAMES_PER_SECOND)
    if max_frames <= 0:
        _die(f"--max-seconds must be positive; got {max_seconds}")

    chunks: List[Tuple[int, int]] = []
    cursor = 0
    while cursor < total_frames:
        split_frame = choose_split_frame(
            cursor=cursor,
            max_frames=max_frames,
            total_frames=total_frames,
            rms=rms,
            silences=silences,
            silence_threshold=silence_threshold,
        )
        if split_frame <= cursor:
            # Guard against zero-length cut (shouldn't happen, but be safe).
            split_frame = min(cursor + max_frames, total_frames)
        start_sample = cursor * samples_per_frame
        end_sample = min(split_frame * samples_per_frame, len(samples))
        chunks.append((start_sample, end_sample))
        cursor = split_frame

    return chunks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="split_voice",
        description="Split a mono s16 WAV into ≤max-seconds chunks on quiet points.",
    )
    parser.add_argument("--max-seconds", type=float, required=True,
                        help="Hard upper bound on each chunk's length in seconds.")
    parser.add_argument("--input-wav", type=Path, required=True,
                        help="Path to source WAV (mono / pcm_s16le).")
    parser.add_argument("--output-folder", type=Path, required=True,
                        help="Directory to write chunks into (created if missing).")
    args = parser.parse_args(argv)

    if args.max_seconds <= 0:
        _die(f"--max-seconds must be > 0; got {args.max_seconds}")

    samples, framerate = load_wav_pcm16_mono(args.input_wav)
    total_seconds = len(samples) / framerate
    print(f"[split_voice] input: {args.input_wav.name}  "
          f"{total_seconds:.2f}s  {framerate} Hz  {len(samples)} samples",
          flush=True)

    chunks = segment_audio(samples, framerate, args.max_seconds)

    args.output_folder.mkdir(parents=True, exist_ok=True)
    for start_sample, end_sample in chunks:
        start_ms = int(start_sample * 1000 / framerate)
        end_ms = int(end_sample * 1000 / framerate)
        chunk = samples[start_sample:end_sample]
        name = f"{start_ms:08d}-{end_ms:08d}.wav"
        write_wav_pcm16_mono(args.output_folder / name, chunk, framerate)
        dur = (end_sample - start_sample) / framerate
        print(f"  wrote {name}  ({dur:.2f}s)", flush=True)

    print(f"[split_voice] done: {len(chunks)} chunks -> {args.output_folder}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
