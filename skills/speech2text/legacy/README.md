# legacy/ — Volcengine sauc streaming ASR (v1.x fallback)

This directory holds the previous implementation of `speech2text`: a
Volcengine `sauc bigmodel_nostream` streaming pipeline. It is **no longer the
default path** — the new `../scripts/speech2text.py` runs `faster-whisper`
locally on GPU/CPU and covers 99% of the use cases the sauc path used to
serve, at zero API cost and with no rate limits.

The files here are preserved intact for the rare cases where you actually
need cloud ASR. Their pre-refactor git history is retained (they were moved
with `git mv`, not copied), so `git log --follow legacy/scripts/voice_pipeline.py`
still shows their full evolution.

## When to reach for legacy

Use this pipeline only when **all** of these apply:

- You have **no local GPU**, or your GPU is unusable for other reasons.
- CPU int8 fallback in the new pipeline (~0.8× realtime) is too slow for your
  batch — e.g. hundreds of hours of audio on a machine without CUDA.
- You have a **Volcengine sauc-capable API key** and are willing to pay per
  audio-second.
- Your audio is Chinese/multilingual short-form speech (sauc handles this
  particularly well; it struggles with long-form + music + heavy dialect).

If any of the above is false, prefer the default `../scripts/speech2text.py`.

## How to use

The files here are byte-for-byte identical to the pre-2.0 implementation.
The full v1 SKILL.md is preserved as `SKILL.md.old` in this directory —
read that for the complete usage manual (CLI flags, config resolution, error
codes, keepalive-timeout mitigations, etc.).

Quick command:

```bash
export VOLCENGINE_API_KEY=<your-sauc-capable-key>

# one-shot audio → transcript
python legacy/scripts/voice_pipeline.py \
    --input recording.mp3 \
    --output transcript.txt
```

The pipeline: `ffmpeg` transcode → trim long silences → split into ≤30 s
chunks on silence boundaries → sauc ASR each chunk with retries →
concatenate → write UTF-8 txt.

## Retained files

| File | Purpose |
|---|---|
| `SKILL.md.old`                          | Full v1.0.0 SKILL.md (backup) |
| `scripts/voice_pipeline.py`             | one-shot ffmpeg + trim + split + sauc |
| `scripts/read_voice.py`                 | sauc ASR wrapper (single wav or folder) |
| `scripts/volc_asr.py`                   | low-level sauc websocket client |
| `scripts/trim_voice.py`                 | clamp long silences (pure stdlib) |
| `scripts/split_voice.py`                | chunk on silence (pure stdlib) |
| `references/volcengine-asr-protocol.md` | sauc wire format cheat sheet |
| `references/troubleshooting.md`         | error codes / keepalive / endpoint permutations |

## Migration note

If you were previously invoking `python <skill>/scripts/voice_pipeline.py`
in a script or cron job, that path still works — just prefix it with
`legacy/`:

```
# before
python <skill>/scripts/voice_pipeline.py ...
# after
python <skill>/legacy/scripts/voice_pipeline.py ...
```

No flags changed. No behavior changed. Only the path.
