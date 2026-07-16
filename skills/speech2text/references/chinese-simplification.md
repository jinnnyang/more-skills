# Chinese Simplification — why Whisper drifts Traditional, and how to fix it

Whisper's multilingual weights were trained on a mix of Simplified and
Traditional Chinese web/subtitle data. As a result, on any given clip you
can get:

- Predominantly Simplified with occasional Traditional characters mixed in
- Whole segments in Traditional, especially early in the audio before the
  decoder settles into a variant
- Traditional-Simplified hybrids of the same word within one sentence
  (e.g. `台灣` and `台湾` in adjacent clauses)

`speech2text.py` applies **two independent safeguards** — both on by
default, and both worth keeping.

## Safeguard 1 — `--initial-prompt` (inference-time bias)

The default prompt is:

```
以下是简体中文的短视频语音识别文本，包含标点符号。
```

Whisper's decoder is conditioned on the last 224 tokens of the prompt as
if they were spoken in a prior segment. Because these tokens are Simplified
Chinese, the decoder's early-decoding distribution is biased toward
Simplified Chinese tokens. Effect on the reference MediaCrawler smoke test
(2026-07-15, one 269 s Douyin clip):

- **Without prompt (or with a neutral English prompt):** ~50% of output
  characters were Traditional variants that zhconv then converted.
- **With the Simplified-biased prompt:** ~26% of output characters still
  needed zhconv conversion. Prompt cuts the drift roughly in half but
  doesn't eliminate it.

That's why we also apply the second safeguard.

## Safeguard 2 — `zhconv` post-processing

After Whisper emits the full transcript, we run:

```python
from zhconv import convert
text = convert(text, "zh-cn")
```

This is a deterministic character-by-character Traditional → Simplified
map from the `zhconv` package. It catches everything the prompt bias missed.
Fast — negligible cost on the total pipeline.

## Why not just zhconv, skip the prompt?

Two reasons.

1. **Some Traditional → Simplified mappings are lossy in one direction.**
   For example, the Traditional character `發` can map to either `发`
   (to send / to develop) or `髮` → `发` (hair). `zhconv` picks the more
   common mapping, which is right most of the time but wrong for hair-related
   content. Better: keep Whisper on the Simplified side of the fence from
   the start.
2. **The prompt biases *token* selection during decoding**, not just the
   final glyphs. This tends to nudge Whisper toward Simplified vocabulary
   choices (`软件` vs `軟體`), not just Traditional-form characters, which
   `zhconv` cannot infer from the output alone.

## Empirical numbers (MediaCrawler 2026-07-15 smoke test)

Source: one Douyin video, 269 s of Chinese口播, GTX 1650 `medium int8 beam=1`.

| Variant | Chars | Traditional found | zhconv conversions applied |
|---|---:|---:|---:|
| No prompt, no zhconv | 1668 | ~830 (50%) | — |
| Simplified prompt, no zhconv | 1722 | ~450 (26%) | — |
| Simplified prompt + zhconv (**default**) | 1722 | 0 | 434 |
| No prompt + zhconv | 1668 | 0 | ~830 |

The default configuration is the last-but-one row. It has the same output
as `no prompt + zhconv` in terms of Simplified compliance, but the prompt
also improves token choices (see rationale above), so it's the recommended
combination.

## Turning safeguards off (rare)

- `--initial-prompt ""` — empty string disables prompt. Do this only if
  you specifically want the model to pick the variant itself (e.g. transcribing
  Taiwanese content in Traditional).
- `--no-simplified` — skip zhconv post-processing. Do this only if you
  want the raw Whisper output for downstream analysis (e.g. measuring the
  Traditional-drift rate for a research question).

## When both safeguards aren't enough

If you're still seeing Traditional characters after the default config:

1. Confirm zhconv is actually installed:
   `python -c "import zhconv; print(zhconv.__version__)"` — should be `>= 1.4`.
2. Confirm the prompt landed:
   `python scripts/speech2text.py --input clip.wav --dry-run` shows the
   config; visually verify `--initial-prompt` starts with 简体中文…
3. If both check out, the input audio may actually be Taiwanese/Cantonese
   speech — Whisper will output in the variant it hears. In that case
   zhconv converts the glyphs, but the vocabulary and grammar remain
   TW-flavored (`軟體` → `软体`, but not automatically to `软件`). That's a
   downstream text-normalization problem, not an ASR problem.

## References

- zhconv package: https://github.com/gumblex/zhconv
- Whisper multilingual training paper: https://arxiv.org/abs/2212.04356
- OpenCC (alternative, more configurable): https://github.com/BYVoid/OpenCC
