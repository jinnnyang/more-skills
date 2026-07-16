---
name: speech2text
description: Local GPU faster-whisper speech-to-text pipeline, Chinese-first, offline. Use whenever the user wants to transcribe audio/video to text, extract subtitles, generate a transcript, run STT / ASR, convert 语音/录音/音频 to 文字, process a podcast or meeting recording, feed audio into an LLM as text, or handle a batch of hundreds of short videos without any API budget. Ships one CLI (`scripts/speech2text.py`) that takes mp4/wav (single file or directory), runs faster-whisper `medium int8` on CUDA (auto-falls back to CPU), applies a Chinese-simplified prompt + zhconv double safeguard, and writes UTF-8 `.txt` sidecar output. Idempotent — resumable by re-running. The old Volcengine sauc streaming pipeline is preserved under `legacy/` for the API-fallback case.
version: 2.0.0
author: Hermes Agent
license: MIT
---

# speech2text — local faster-whisper ASR (GPU-first)

## Overview

One-shot audio/video → transcript, running **offline** on your own GPU (or CPU as fallback). Any input format (`mp4`, `wav`, `mp3`, `m4a`, `aac`, `flac`, `ogg`, `opus`, `webm`) → clean UTF-8 text file.

The core problem this skill solves: batch transcription of many short clips (say, 200 抖音短视频) without paying for cloud ASR, and without cloud rate limits. `faster-whisper` loads the Whisper `medium` model once into GPU VRAM (~1.5 GB), then reuses it across the whole batch. On a modest 4 GB GTX 1650 you get roughly **4–6× real time** for Chinese content.

If you have no local GPU or you specifically need Volcengine's `sauc bigmodel_nostream` (e.g. corporate compliance requirement), the earlier cloud pipeline is preserved under `legacy/` — see `legacy/README.md`.

## When to Use

Load this skill whenever the user's request involves audio → text, even if they don't say "ASR" or "Whisper":

- "帮我把这段录音转成文字" / "字幕" / "transcribe this podcast"
- "extract subtitles from this video" (video → audio → transcript)
- "convert this meeting recording to text so I can summarize it"
- "run speech-to-text on X"
- "把这 200 个抖音视频转录出来" — batch of hundreds of short videos, offline, no API budget
- Any workflow whose next step is "feed a transcript to an LLM"
- Long-form content (>30 s) — no chunking needed, `faster-whisper` handles arbitrary length

Don't use for:
- Real-time / interactive dictation (this skill is batch)
- Text-to-speech (that's the reverse direction — different skill)
- When you have a strict cloud-only compliance requirement — reach for `legacy/` instead

## Prerequisites

```bash
# A) ffmpeg on PATH (needed for mp4/mp3 → wav transcode)
ffmpeg -version

# B) faster-whisper + zhconv (post-processing to Simplified Chinese)
pip install "faster-whisper>=1.2" "zhconv>=1.4"

# C) NVIDIA driver >= 527.41 for CUDA 12 GPU path (optional — CPU int8 path
#    works with no driver, just slower)
nvidia-smi   # look for "CUDA Version: 12.x"
```

Model download is automatic on first run: `medium` weights (~1.5 GB) go into your HuggingFace cache (`~/.cache/huggingface/hub/`). Subsequent runs load instantly from cache. Override cache path with `--model-dir DIR` if desired.

## Quick Start

```bash
# Single file → sidecar output (writes recording.txt next to recording.mp4)
python <skill>/scripts/speech2text.py --input recording.mp4

# Directory of *.wav → sidecar for each
python <skill>/scripts/speech2text.py --input videos/

# Directory → merged single txt (sorted by filename, appended with headers)
python <skill>/scripts/speech2text.py --input videos/ --output all.txt

# Dry-run: scan filesystem, estimate ETA, do NOT load the model
python <skill>/scripts/speech2text.py --input videos/ --dry-run

# Overwrite existing txt (default is skip-if-exists for cheap resume)
python <skill>/scripts/speech2text.py --input recording.mp4 --force

# CPU fallback (no GPU / driver too old)
python <skill>/scripts/speech2text.py --input videos/ --device cpu --compute-type int8

# Domain-tuned prompt (see "Writing an effective initial_prompt" below)
python <skill>/scripts/speech2text.py --input meeting.mp4 \
    --initial-prompt "以下是公司周会录音的简体中文转录，与会者：张三、李四、王五。术语：KV cache、量化。包含标点符号。"
```

## Performance Baseline

Measured 2026-07-15 on MediaCrawler douyin batch (mono 16 kHz 16-bit WAV, Chinese short-video 口播):

| Hardware / Path | Model / Compute | Model Load | 5 min Audio Wall Time | Speed | 200 videos ETA (avg 3 min each) |
|---|---|---|---|---|---|
| **GTX 1650 (4 GB, SM 7.5) — default** | `medium int8` beam=1 + prompt | 7–11 s (once) | **46–70 s** | **4–6× realtime** | **~1.5–2 h** |
| GTX 1650, beam=5 (old default) | `medium int8` beam=5 + prompt | ~10 s | 70.7 s | 4.2× realtime | ~2.5 h |
| CPU fallback (AMD 5900H) | `medium int8` beam=1 + prompt | 3.5 s | ~373 s | 0.8× realtime | ~12 h |

**ETA rule of thumb**: `wall_seconds ≈ audio_seconds / 5` on the default GPU path.

⚠️ **Do not kill the process mid-batch.** faster-whisper loads the model into GPU VRAM once and reuses it. Killing it can leak CUDA context — the *next* run may fail at model load with an OOM even though `nvidia-smi` shows the card free (fix: restart your shell to clear CUDA context). If you must stop, prefer `Ctrl-C` at a segment boundary; the skip-if-exists behavior then lets you resume by just re-running the same command.

## Output Behavior

`--output` is treated as a **file path** iff it ends in `.txt` (case-insensitive). Otherwise it is treated as a **directory** (created if missing).

| # | `--input` | `--output` | Behavior |
|---|---|---|---|
| 1 | file | (unset) | sidecar: write `<input_stem>.txt` next to the input |
| 2 | file | `path/x.txt` | write to that exact file |
| 3 | file | `path/dir/` | treat as directory: write `path/dir/<input_stem>.txt` |
| 4 | dir  | (unset) | for each `*.wav` under `--input`, write sidecar `<stem>.txt` next to it |
| 5 | dir  | `path/outdir/` | for each `*.wav`, write `path/outdir/<stem>.txt` |
| 6 | dir  | `path/all.txt` | **merge mode** — sort wavs by filename, **append** each transcript to `all.txt` prefixed by a `## <stem>\n` header line and a blank line separator |

Directory input globs `*.wav` **only** (matching the MediaCrawler post-`mp4-to-wav` convention). For an `mp4`/`mp3` batch, either loop over files yourself in shell or hand each file to the CLI individually. Merge mode's `append` is deliberate — safe for resumable batches (Ctrl-C, re-run picks up where you left off).

Every write is atomic: `<target>.txt.tmp` → `os.replace(...)`. You will never see a half-written `.txt` on interrupt.

## Config Resolution

Everything is CLI-flag driven — **no environment variables**, no config file. Design is intentional: one command line is enough context to reproduce any run, and there are no hidden knobs to worry about later. The full flag set:

| CLI flag | Default | What it does |
|---|---|---|
| `--input PATH` | (required) | File or directory |
| `--output PATH` | (unset) | See "Output Behavior" table above |
| `--model NAME` | `medium` | `tiny` / `base` / `small` / `medium` / `large-v3` |
| `--device` | `cuda` | `cuda` / `cpu` / `auto` |
| `--compute-type` | `int8` | `int8` (4 GB GPU friendly), `int8_float16`, `float16`, `int8_float32` |
| `--language` | `zh` | ISO code; `''` for auto-detect |
| `--beam-size N` | `1` | `1` = greedy (fastest, and quality matches beam=5 once `initial_prompt` is set) |
| `--vad-filter / --no-vad-filter` | `--vad-filter` | Skip silence chunks via voice-activity detection |
| `--initial-prompt STR` | (see fallback) | Decoder-priming string; see next section |
| `--simplified / --no-simplified` | `--simplified` | Post-process Traditional → Simplified via zhconv |
| `--model-dir DIR` | HF cache | Where the model weights live |
| `--force` | (off) | Overwrite existing `.txt` |
| `--dry-run` | (off) | Scan filesystem, print ETA, do NOT load the model |

Default `--initial-prompt` is a generic Chinese fallback: `"以下是简体中文的短视频语音识别文本，包含标点符号。"` — **override it per invocation** whenever you know the domain (see next section for how).

## Writing an Effective `initial_prompt`

`initial_prompt` is fed to Whisper's decoder as prior context. It **is not an instruction**; Whisper is not chat. What the prompt does:

1. **Biases token probabilities.** Proper nouns, jargon, brand names, and product acronyms that are present in the prompt become far more likely output tokens. Empirically this drops character-error-rate on domain terms by 5–15% on Chinese content.
2. **Steers language variant.** Including "简体中文，包含标点符号" biases the model toward Simplified Chinese with proper punctuation — this dropped zhconv fix-up rate from ~50% to ~26% in MediaCrawler smoke tests.
3. **Sets punctuation style.** Comma-heavy vs period-heavy, question marks, ellipses — Whisper mimics the density it sees in the prompt.

### The 224-token rule (critical)

Whisper's `initial_prompt` is capped at 224 tokens. If longer, it is truncated **from the head, silently**. Concrete budget:

- **Chinese**: ~1 token per 汉字 → **~200 汉字 usable**
- **English**: ~0.5 token per word → **~350 words usable**

Put the most-critical terms (speaker names, brand names, jargon) **at the end** of the prompt. The generic front matter (`"以下是..."` boilerplate) is what gets sacrificed if you overrun the budget.

### What to include (checklist)

1. **Genre/format cue** — `"以下是XX的语音识别文本"` sets the register
2. **Language + style bias** — `"简体中文，包含标点符号，短句"` or `"英语，会议记录风格"`
3. **Proper nouns unique to this recording** — 人名 / 品牌 / 产品名 / 缩写全称
4. **Domain jargon the base model likely doesn't know** — technical terms specific to the field
5. **A short representative example fragment** (optional but effective — one 10-字 sentence)

### What NOT to include

1. **Instructions to the model** ("请翻译成中文", "去除口头禅") — Whisper is not chat; these just eat budget and confuse the decoder
2. **Full transcripts of previous audio** — wastes budget with no measurable benefit
3. **Emojis or unusual Unicode** — unpredictable tokenization; you'll pay more tokens than you think

### Short templates

```
# Meeting recording
"以下是公司会议录音的中文转录，与会者：张三、李四、王五。涉及产品名：Aurora、Nebula。"

# Podcast interview
"以下是《XXX播客》第YY期节目转录，主持人陈老师，嘉宾李博士。话题：LLM 推理优化，术语：KV cache、量化。"

# Douyin short video
"以下是简体中文的抖音短视频口播，博主@某某，涉及品牌：小米、华为，包含标点符号。"

# Academic talk
"以下是学术会议演讲的中文转录，讲者：某教授，主题：因果推断。术语：DAG、confounder、propensity score。"
```

→ For longer worked examples, do/don't cases, and multilingual prompts, see [`references/prompt-cookbook.md`](references/prompt-cookbook.md).

## Verification (run before trusting output)

For any newly transcribed clip:

- [ ] `wc -m transcript.txt` — non-empty, roughly `spoken_seconds × 3–5` chars for Chinese, `× 12–15` for English
- [ ] Skim `head -c 500 transcript.txt` — first few sentences readable, punctuation present
- [ ] **Punctuation density sanity check**: count `，。？！,.?!` in output. Should be **≥ 5%** of char count on Chinese口播 content. If it's ~1% you likely regressed `condition_on_previous_text` — see pitfall below.
- [ ] No suspicious runs of the same short phrase 3+ times at the tail (rare `condition_on_previous_text=True` self-loop; see pitfall)

## Common Pitfalls

1. **"CUDA driver version is insufficient for CUDA runtime version"** on GPU load → upgrade NVIDIA driver to ≥ 527.41 for CUDA 12.x. See [`references/cuda-setup.md`](references/cuda-setup.md).

2. **Whisper outputs Traditional Chinese sometimes** — this is by design of the multilingual model. The double safeguard (`--initial-prompt` mentioning "简体中文" + `--simplified` running zhconv) fixes it. **Do not disable both.** See [`references/chinese-simplification.md`](references/chinese-simplification.md).

3. **`--model large-v3` on a 4 GB VRAM card OOMs** at model load. Stick to `medium int8`. `large-v3 int8_float32` won't fit either. If you truly need `large-v3`, use `--device cpu --compute-type int8` (slow but correct).

4. **Directory batch only picks up `*.wav`.** If you have `mp4`, either use single-file mode (`--input clip.mp4` — mp4 is ffmpeg-transcoded automatically) or run `ffmpeg` first to produce `.wav` alongside your source files.

5. **Process was killed mid-batch → next run fails at model load with OOM** even though `nvidia-smi` shows free VRAM. CUDA context leaked. Fix: restart your shell (or the whole terminal tab) to clear it. Do not kill the process; let it finish, or Ctrl-C and let it complete the current file cleanly.

6. **Do NOT set `condition_on_previous_text=False`** in `model.transcribe()`. Whisper decodes in 30 s windows; disabling cross-window conditioning drops Chinese punctuation density from ~9% to ~1% on long-form audio (measured on MediaCrawler 2026-07-15 — a 269 s wav went from 154 puncts / 1722 chars to 16 puncts / 1607 chars). Keep it at Whisper's default `True`. If a specific corpus DOES exhibit end-of-audio phrase repetition, mitigate with `no_repeat_ngram_size=3` or `--model large-v3` — never trade punctuation for anti-repetition.

7. **`--initial-prompt` >224 tokens is silently truncated from the head.** No warning, no error — the front of your carefully-crafted prompt just disappears. Put the most important tokens (proper nouns, jargon) at the **end**. See [`references/prompt-cookbook.md`](references/prompt-cookbook.md) for detailed guidance.

8. **Ctrl-C leaves partial `.txt` files?** — No: writes are atomic (`.tmp` → `os.replace`). But an in-flight transcribe that was killed will simply not produce a file for that input, and re-running picks it up thanks to skip-if-exists.

## Fallback: cloud ASR (Volcengine sauc)

If you have no GPU and CPU (~0.8× realtime) is too slow for your workload — or you have a corporate requirement to use Volcengine's `sauc bigmodel_nostream` — the earlier cloud pipeline is preserved intact under `legacy/`. It handles the same input/output shape but chunks on silence and streams each chunk over WebSocket to `openspeech.bytedance.com`. See [`legacy/README.md`](legacy/README.md) for its state, quirks, and how to invoke it.

## References

- [`references/faster-whisper-guide.md`](references/faster-whisper-guide.md) — model tradeoffs, compute-type matrix, VAD, silence heuristics
- [`references/cuda-setup.md`](references/cuda-setup.md) — driver / CUDA / cuDNN versions, how to verify, common install errors
- [`references/chinese-simplification.md`](references/chinese-simplification.md) — why Whisper drifts Traditional, how the prompt + zhconv fixes it
- [`references/gtx-1650-benchmark.md`](references/gtx-1650-benchmark.md) — full performance grid on the reference hardware
- [`references/prompt-cookbook.md`](references/prompt-cookbook.md) — worked `initial_prompt` examples for meeting, podcast, douyin, academic talk, mixed CN/EN, technical jargon
- `legacy/README.md` — how the v1 sauc pipeline works, and when to reach for it

## Next Step

After transcription completes, the natural follow-ons are:

- Feed `transcript.txt` to an LLM for summarization / Q&A / translation
- Diarize speakers (out of scope — Whisper doesn't return speaker IDs)
- Post-process for ASR homophone errors — a "transcript-fixer" pass typically catches ~10% of Chinese homophone errors that survive the prompt bias
