---
name: speech2text
description: Volcengine (豆包 / doubao / seed-asr) sauc streaming speech-to-text pipeline. Use whenever the user wants to transcribe audio/video to text, extract subtitles from a recording, generate a transcript, run STT / ASR, convert 语音/录音/音频 to 文字, process a podcast or meeting recording, feed audio into an LLM as text, or handle Chinese/multilingual voice content. Handles arbitrarily long files by auto-splitting on silence to stay under Volcengine's per-session limits. Ships four composable CLI tools plus a one-shot pipeline; the pipeline is the default entry point.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# speech2text — Volcengine sauc ASR pipeline

## Overview

One-shot audio → transcript, using Volcengine's `sauc bigmodel_nostream`
streaming ASR (a.k.a. 豆包 / doubao seed-asr). Any input format (mp3, wav,
m4a, aac, flac, ogg, opus, webm) → clean UTF-8 text file.

The core problem this skill solves: sauc is a **streaming** endpoint that
becomes unreliable past ~25 seconds of audio (server-side per-packet
timeout, plus client-side WebSocket-keepalive races). The pipeline
side-steps this by chopping the input on silence boundaries so every
request stays inside the safe window, then concatenating the transcripts.

## When to Use

Load this skill whenever the user's request involves audio → text, even if
they don't say "ASR" or "Volcengine":

- "帮我把这段录音转成文字" / "字幕" / "transcribe this podcast"
- "extract subtitles from this video" (video → audio → transcript)
- "convert this meeting recording to text so I can summarize it"
- "run speech-to-text on X"
- Any workflow whose next step is "feed a transcript to an LLM"
- Long-form content (>30 s) that must be chunked

Don't use for:
- Real-time / interactive dictation (this skill is batch)
- English-only content where a local Whisper is preferred and offline
- Text-to-speech (that's the reverse direction — different skill)

## Prerequisites

1. `ffmpeg` on PATH (transcode + probe). Verify: `ffmpeg -version`.
2. Python 3.10+ with `websockets` installed: `pip install websockets`.
3. Volcengine API key with sauc streaming ASR access.
   - Key looks like `ark-<hex>-<suffix>` for coding-plan keys, works with
     endpoint `wss://.../plan/sauc/bigmodel_nostream` (the pipeline default).
   - Straight openspeech.bytedance.com keys (`X-Api-App-Key` +
     `X-Api-Access-Key`) work too but need the non-`plan/` endpoint —
     override with `VOLCENGINE_ASR_ENDPOINT`.
   - Export: `export VOLCENGINE_API_KEY=<key>` (or `ARK_API_KEY`).

## Quick Start (one command)

```bash
python <skill>/scripts/voice_pipeline.py \
    --input recording.mp3 \
    --output transcript.txt
```

That's it. Under the hood: ffmpeg transcode → trim long silences → split
into ≤30s chunks on silence points → sauc ASR each chunk with retries →
concatenate → write UTF-8 txt.

## The Four Tools

Reach for the one-shot pipeline first. Drop to individual tools only when
you need to tweak an intermediate stage.

| Tool | Purpose | CLI shape |
|------|---------|-----------|
| **voice_pipeline.py** | end-to-end audio → transcript | `--input FILE --output TXT [--max-silence 0.5] [--max-seconds 30] [--skip-trim] [--workdir DIR] [--keep-workdir]` |
| trim_voice.py         | clamp long silences         | `--max-silence SEC --input-wav IN.wav --output-wav OUT.wav` |
| split_voice.py        | chunk on silence            | `--max-seconds SEC --input-wav IN.wav --output-folder DIR/` |
| read_voice.py         | sauc ASR only               | `--input-wav IN.wav \| --input-folder DIR/ --output-txt OUT.txt` |

split_voice / trim_voice are pure-stdlib (`wave` + `struct` + `array`), no
third-party deps. read_voice needs `websockets`. voice_pipeline needs both
plus `ffmpeg`.

## Config Resolution (all read_voice-facing knobs)

Every parameter follows the **CLI flag > env var > default** chain:

| CLI flag     | Env fallback                | Default |
|--------------|-----------------------------|---------|
| `--api-key`  | `VOLCENGINE_API_KEY`, `ARK_API_KEY` | (required — fail fast if unset) |
| `--endpoint` | `VOLCENGINE_ASR_ENDPOINT`   | `wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream` |
| `--resource` | `VOLCENGINE_ASR_RESOURCE`   | `volc.seedasr.sauc.duration` |
| `--language` | `VOLCENGINE_ASR_LANGUAGE`   | (server auto-detect) |

Log lines always redact the key: `api_key=ark-73…22d4`. The pipeline also
redacts on the `=== [read] ...` subprocess-invocation trace.

## Tuning knobs (rare)

- `--max-silence 0.5`: silences ≥ 0.5s get clamped to 0.5s. Lower saves
  ASR tokens (fewer paid audio-seconds) but risks trimming actual pauses;
  0.5s is a good default for spoken content.
- `--max-seconds 30`: hard upper bound per chunk. Do NOT raise above ~30 —
  server timeouts start biting hard past that.
- `--skip-trim`: preserve original pacing (skip stage 2). Use for music,
  interviews with meaningful long pauses.
- `--workdir DIR`: keep intermediate files (raw wav, trimmed wav, chunks)
  for debugging. Combine with `--keep-workdir` to inspect after run.

## Verification (run before trusting output)

For any newly transcribed clip:

- [ ] `wc -m transcript.txt` — non-empty, roughly `spoken-seconds × 3-5`
  chars for Chinese, `× 12-15` for English.
- [ ] `head -c 200 transcript.txt` — first sentence readable.
- [ ] No `\n\n` runs longer than the clip's actual pauses (a run of 3+ `\n\n`
  usually means a chunk hard-failed silently — check stderr).
- [ ] Stderr has zero `attempt N/3 failed` lines for a clean run, or the
  failures are isolated (chunk-level retries are normal on sauc).

## Common Pitfalls

1. **API key with wrong permission.** The Coding-Plan key
   (`ark-…-…22d4`-style) works only against endpoints prefixed with
   `/api/v3/plan/…`. It authenticates against `/api/v3/auc/…` (recording-file
   API) but returns 403 "resource not granted." The pipeline defaults to
   the correct `plan/sauc/` endpoint — don't override unless you have a
   different key type.

2. **`1011 keepalive-ping-timeout` on longer clips.** Symptom: chunk fails
   after ~20s. Fix: `volc_asr.py` sets `ping_interval=None` on
   `websockets.connect()`. If you re-implement, DO the same — sauc doesn't
   reply to ws-level pings while it's ingesting a send burst, so client-side
   ping expires. See `references/troubleshooting.md`.

3. **`45000081` waiting-next-packet-timeout.** Server-side: didn't receive
   next audio frame within 5s. `DEFAULT_CHUNK_SIZE=3200` bytes = 100 ms of
   16 kHz mono s16le audio; you're well inside the window. If you're rewriting,
   keep `await asyncio.sleep(0)` after each `send()` so keepalive tasks yield.

4. **"audio input is not supported by this model" (chat/completions).**
   That means someone tried to route through
   `/api/v3/chat/completions` with `input_audio` — that's a different Volc
   API and needs a different model + key. This skill uses sauc streaming;
   don't switch endpoints unless you know why.

5. **Mono/16kHz constraint.** split_voice and trim_voice reject anything
   that isn't mono 16-bit 16 kHz WAV (stderr contains `mono`). The pipeline
   handles this by running ffmpeg first; if you invoke split/trim directly,
   pre-convert with:
   ```bash
   ffmpeg -y -i src.mp3 -ac 1 -ar 16000 -c:a pcm_s16le raw.wav
   ```

6. **Empty transcript.** Silent chunk or BGM-only chunk. read_voice raises
   `RuntimeError` on total emptiness. If it's a single-chunk file and the
   audio is real speech, check the key permission (pitfall 1).

7. **API key leaked in logs.** voice_pipeline redacts `--api-key` in the
   step-invocation printout. read_voice redacts in its config log. If you
   fork/edit these, keep `_redact()` / the `k[:6]…k[-4:]` truncation.

## Performance Notes

- 225 s of Chinese speech → 8 chunks (avg 28 s each) → ~8 min total ASR
  wall time (server queue is the bottleneck, not the wire).
- ASR-per-chunk cost varies wildly: 8 s to 130 s. First attempt sometimes
  fails; retry #2 usually succeeds (server-side scheduling). Keep default
  `MAX_ATTEMPTS = 3` in `read_voice.py`.
- Serial across chunks by design — parallelizing hits server rate limits
  and doesn't improve wall time (the queue is what's slow, not concurrency).

## References

- `references/volcengine-asr-protocol.md` — sauc wire format cheat sheet
  (headers, frame layout, sequence semantics). Read this if the protocol
  needs to change.
- `references/troubleshooting.md` — error codes, keepalive fix reasoning,
  endpoint permutations, alt endpoints considered.

## Next Step

After transcription completes, the natural follow-ons are:

- Feed `transcript.txt` to an LLM for summarization / Q&A / translation
- Diarize speakers (out of scope — sauc doesn't return speaker IDs)
- Post-process (fix ASR-recognition errors) — a "transcript-fixer" style
  pass typically catches ~10% of Chinese homophone errors
