"""read_voice.py — Volcengine SAUC (streaming ASR) audio → text.

Usage:
    # single WAV
    python read_voice.py --input-wav in.wav --output-txt out.txt

    # folder produced by split_voice.py (or any dir of *.wav)
    python read_voice.py --input-folder ./chunks --output-txt out.txt

Config precedence (highest wins):
    CLI flag  >  env var  >  built-in default

Env vars honoured (first non-empty wins):
    --api-key    :  VOLCENGINE_API_KEY, ARK_API_KEY
    --endpoint   :  VOLCENGINE_ASR_ENDPOINT
                    (default: wss://openspeech.bytedance.com/api/v3/sauc/
                              bigmodel_nostream — the sauc streaming endpoint;
                              same auth as ARK API key)
    --resource   :  VOLCENGINE_ASR_RESOURCE
                    (default: volc.bigasr.sauc.duration — resource_id header)
    --language   :  VOLCENGINE_ASR_LANGUAGE (e.g. "zh-CN"; default: none)

Design (background):
- The Volcengine ARK chat/completions endpoint has an ``input_audio`` block for
  audio understanding, but that path requires a general-plan ARK key. This
  project has a coding-plan key, which does NOT include audio-model access.
- The sauc streaming ASR endpoint (``openspeech.bytedance.com/api/v3/sauc``)
  uses the SAME api-key and IS reachable with the coding-plan key. It's what
  ``volc_asr.py`` already targets, and what upstream volcengine-hermes-plugin
  proved works for chunks up to ~1 min.
- Long clips (>1 min) time out on that endpoint. Pair this with
  ``split_voice.py --max-seconds 30`` upstream and this script transcribes
  every chunk individually.

No third-party deps beyond ``websockets`` (already a project dep via volc_asr).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Import sibling vendored volc_asr — this skill is fully self-contained, no
# repo-root sys.path hack needed. Both files live under skill/scripts/.
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))
import volc_asr  # noqa: E402


DEFAULT_ENDPOINT = volc_asr.ASR_ENDPOINT
DEFAULT_RESOURCE = volc_asr.DEFAULT_RESOURCE_ID
API_KEY_ENVS = ("VOLCENGINE_API_KEY", "ARK_API_KEY")
ENDPOINT_ENVS = ("VOLCENGINE_ASR_ENDPOINT",)
RESOURCE_ENVS = ("VOLCENGINE_ASR_RESOURCE",)
LANGUAGE_ENVS = ("VOLCENGINE_ASR_LANGUAGE",)

MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 3.0


def _die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"read_voice: error: {msg}\n")
    sys.exit(code)


def _first_env(names: tuple[str, ...]) -> Optional[str]:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return None


def resolve_config(args: argparse.Namespace) -> dict:
    api_key = args.api_key or _first_env(API_KEY_ENVS)
    if not api_key:
        _die("no API key. Provide --api-key or set one of: "
             + ", ".join(API_KEY_ENVS))
    endpoint = args.endpoint or _first_env(ENDPOINT_ENVS) or DEFAULT_ENDPOINT
    resource = args.resource or _first_env(RESOURCE_ENVS) or DEFAULT_RESOURCE
    language = args.language or _first_env(LANGUAGE_ENVS) or None
    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "resource": resource,
        "language": language,
    }


def collect_input_wavs(args: argparse.Namespace) -> List[Path]:
    if args.input_wav:
        p = args.input_wav
        if not p.exists():
            _die(f"input WAV does not exist: {p}")
        if p.suffix.lower() != ".wav":
            _die(f"only .wav is supported; got {p.suffix!r}")
        return [p]
    folder: Path = args.input_folder
    if not folder.is_dir():
        _die(f"input folder does not exist or is not a directory: {folder}")
    wavs = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".wav" and p.is_file())
    if not wavs:
        _die(f"input folder contains no .wav files: {folder}")
    return wavs


async def transcribe_one(wav: Path, cfg: dict) -> str:
    """Send one WAV to sauc and return its transcript. Retries transient fails."""
    # WAV bytes go on the wire as-is: volc_asr._prepare_wav_bytes() only exists
    # to *produce* a mono/16k/s16 wav from mp3. Our inputs are already wav —
    # trust the caller; sauc handles wav rate/channel conversion server-side.
    audio_bytes = wav.read_bytes()
    # Fresh headers per attempt so X-Api-Request-Id is unique.
    last_err: Optional[str] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        # Temporarily inject the key so volc_asr._build_headers() picks it up.
        os.environ["VOLCENGINE_API_KEY"] = cfg["api_key"]
        headers = volc_asr._build_headers(resource_id=cfg["resource"])
        try:
            transcript = await volc_asr._run_asr_websocket(
                audio_bytes,
                headers=headers,
                endpoint=cfg["endpoint"],
                language=cfg["language"],
            )
            return transcript
        except Exception as exc:  # noqa: BLE001 — sauc raises a mix of types
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_ATTEMPTS:
                sleep_s = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                sys.stderr.write(
                    f"[read_voice] {wav.name}: attempt {attempt}/"
                    f"{MAX_ATTEMPTS} failed ({last_err}); sleeping "
                    f"{sleep_s:.1f}s\n"
                )
                await asyncio.sleep(sleep_s)
    raise RuntimeError(f"{wav.name}: exhausted retries; last error: {last_err}")


async def _run(args: argparse.Namespace) -> int:
    cfg = resolve_config(args)
    wavs = collect_input_wavs(args)

    # Log config with the key redacted.
    k = cfg["api_key"]
    redacted = f"{k[:6]}…{k[-4:]}" if len(k) > 12 else "***"
    print(f"[read_voice] endpoint={cfg['endpoint']}", flush=True)
    print(f"[read_voice] resource={cfg['resource']}", flush=True)
    print(f"[read_voice] language={cfg['language'] or '(server default)'}", flush=True)
    print(f"[read_voice] api_key={redacted}", flush=True)
    print(f"[read_voice] inputs: {len(wavs)} wav file(s)", flush=True)

    args.output_txt.parent.mkdir(parents=True, exist_ok=True)
    parts: List[str] = []
    for i, wav in enumerate(wavs, start=1):
        size_kb = wav.stat().st_size / 1024
        print(f"  [{i}/{len(wavs)}] {wav.name} ({size_kb:.1f} KiB) ...", end="", flush=True)
        t0 = time.time()
        text = await transcribe_one(wav, cfg)
        dt = time.time() - t0
        parts.append(text)
        preview = text.replace("\n", " ")[:50]
        print(f" -> {len(text)} chars in {dt:.1f}s   {preview!r}", flush=True)

    joined = "\n\n".join(parts).strip() + "\n"
    args.output_txt.write_text(joined, encoding="utf-8")
    total_chars = sum(len(p) for p in parts)
    print(f"[read_voice] wrote {total_chars} chars -> {args.output_txt}", flush=True)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="read_voice",
        description="Volcengine sauc ASR: audio → text. Accepts a single WAV "
                    "or a folder (e.g. split_voice.py output).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-wav", type=Path, help="Path to a single WAV file.")
    group.add_argument("--input-folder", type=Path,
                       help="Directory of WAV files; sorted lexicographically.")
    parser.add_argument("--output-txt", type=Path, required=True,
                        help="Where to write the concatenated transcript.")
    parser.add_argument("--api-key", default=None,
                        help=f"Override env {'/'.join(API_KEY_ENVS)}.")
    parser.add_argument("--endpoint", default=None,
                        help=f"Override env {'/'.join(ENDPOINT_ENVS)} "
                             f"(default: sauc bigmodel_nostream).")
    parser.add_argument("--resource", default=None,
                        help=f"Override env {'/'.join(RESOURCE_ENVS)} "
                             f"(default: {DEFAULT_RESOURCE}).")
    parser.add_argument("--language", default=None,
                        help=f"Override env {'/'.join(LANGUAGE_ENVS)} "
                             f"(BCP-47 tag, e.g. zh-CN; default: none).")
    args = parser.parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
