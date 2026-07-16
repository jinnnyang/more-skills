# GTX 1650 benchmark (reference hardware)

Raw smoke-test data used to size the `speech2text.py` defaults. All numbers
measured on a single reference machine.

## Environment

- CPU: AMD Ryzen 7 5900H (8 cores / 16 threads, 3.3 GHz base)
- RAM: 32 GB DDR4
- GPU: **NVIDIA GeForce GTX 1650 (Mobile)** — 4 GB GDDR5, Turing (TU117), SM 7.5, no Tensor Cores
- Driver: 551.86 (Windows 11 25H2)
- CUDA runtime: 12.4 (bundled via `ctranslate2 4.8.0`)
- Python: 3.11.11 (Hermes venv)
- Packages: `faster-whisper 1.2.1`, `zhconv 1.4.3`

## Audio corpora

- **Smoke A** — 269 s Chinese 口播 (MediaCrawler Douyin clip
  `7587777576036732212/video.wav`), mono 16 kHz s16le, cleaned via ffmpeg.
- **Smoke B** — 200 Douyin videos, avg ~180 s each, same normalized format.

## Beam / prompt sweep — Smoke A, `medium int8` on CUDA

| # | Beam | Prompt | Wall (s) | Speed (× realtime) | Notes |
|:-:|:----:|:------:|--------:|-------------------:|:------|
| 1 | 1    | ✅ default | **46.5** | **5.8×** | **Default. Best speed AND quality with prompt** |
| 2 | 1    | ✅ default | 44.1 | 6.1× | Re-run, `cond_on_prev=True` variant |
| 3 | 2    | ✅ default | 115.4 | 2.3× | Diminishing returns start here |
| 4 | 3    | ✅ default | 157.5 | 1.7× | |
| 5 | 5    | ✅ default | 134.3 | 2.0× | Old default from initial draft |
| 6 | 5    | ✅ domain-tuned | 114.9 | 2.3× | `A3` config in 2026-07-15 smoke |
| 7 | 5    | ❌ none | 70.7 | 3.8× | Baseline w/o prompt |
| 8 | 1    | ❌ none | ~39   | ~6.9× | `A0` config — but drops punctuation (see below) |

## `condition_on_previous_text` sweep — Smoke A, config #1

Same run except for the transcribe kwarg. Both include the default prompt
and `beam=1`.

| Setting                        | Chars | Punctuation count | **Density** | Verdict |
|--------------------------------|------:|------------------:|:-----------:|:--------|
| `condition_on_previous_text=False` | 1607 | 16 | **1.0%** | Broken — first segment has punctuation, everything after loses it |
| `condition_on_previous_text=True`  | 1722 | 154 | **8.9%** | **Correct — Whisper default, this skill's default** |

This ~9× density gap is why `speech2text.py` hardcodes `True` (see plan
Q16 and SKILL.md pitfall #6). Never disable this to prevent tail-repetition
— use `no_repeat_ngram_size=3` or a larger model instead.

## CPU fallback — Smoke A, no CUDA

| Compute type    | Wall (s) | Speed | Notes |
|-----------------|--------:|:-----:|:------|
| `int8`          | 373 | 0.8× | Baseline for the CPU path |
| `int8_float32`  | ~450 | 0.6× | Slightly better quality on ambiguous phonemes, slower |

## Full-batch projection — Smoke B (200 files, ~3 min avg)

Based on Smoke A speed and one full 200-file batch that completed:

| Config | Model-load overhead | Per-file wall (avg) | Total wall |
|:-------|--------------------:|--------------------:|-----------:|
| Default (cuda medium int8 beam=1) | 7–11 s (once) | ~50 s | **~2 h** |
| beam=5 (old default)              | ~10 s | ~120 s | ~4 h |
| CPU int8                          | 3.5 s | ~400 s | ~14 h |

## Recommendations

- **Stay on the default** (`--model medium --device cuda --compute-type int8 --beam-size 1 --initial-prompt "…" --simplified`) unless you have a specific reason not to.
- Do not raise beam above 1 on this hardware — accuracy gain is marginal
  and speed penalty is 2–3×.
- Do not switch to `int8_float16` — no Tensor Cores means no benefit.
- Do not run `large-v3` — will OOM at model load.

## References

- Full smoke-test methodology: `../2026-07-15_173418-speech2text-refactor.md`
  (Performance Baseline section)
- MediaCrawler source: `C:\Users\jinnn\Documents\MediaCrawler\data\douyin\wav-to-txt-fw.py`
- Reference-hardware CUDA setup: [`cuda-setup.md`](cuda-setup.md)
