# speech2text Refactor Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> **Status:** APPROVED — do not execute in this session. Reserved for a future implementation session.

**Goal:** Convert the `speech2text` skill from a Volcengine sauc streaming-ASR pipeline into a local faster-whisper GPU-first pipeline. Retain the sauc code as a documented `legacy/` fallback rather than deleting it.

**Architecture:** A single new CLI entry point `scripts/speech2text.py` accepts any audio/video (mp4/mp3/wav/…), auto-detects file vs directory input, runs faster-whisper (`WhisperModel medium int8` on CUDA with automatic CPU fallback) with a Chinese-simplified prompt + zhconv post-processing double safeguard, and writes UTF-8 `.txt` output. The old sauc-based pipeline (`voice_pipeline.py`, `read_voice.py`, `volc_asr.py`, `trim_voice.py`, `split_voice.py`) is moved intact to `legacy/scripts/` with a `legacy/README.md` explaining when to reach for it. Cloud-ASR usage is fully off the default path.

**Tech Stack:**
- Python 3.10+
- `faster-whisper >= 1.2` (CTranslate2 backend, ships bundled cuDNN 9)
- `ctranslate2 >= 4.6`
- `zhconv >= 1.4` (Traditional → Simplified post-processing)
- `ffmpeg` on PATH (faster-whisper shells out to it for non-WAV inputs)
- NVIDIA driver ≥ 527.41 for CUDA 12 GPU path (CPU int8 path works with no driver)

**Performance Baseline (from MediaCrawler smoke tests 2026-07-15):**

| Hardware / Path | Model / Compute | Model Load | 5min Audio Wall Time | Speed | 200 videos ETA (avg 3 min each) |
|---|---|---|---|---|---|
| **GTX 1650 (4 GB, SM 7.5) — default** | medium int8 beam=1 + prompt | 7–11 s (once) | **46–70 s** | **4–6x realtime** | **~1.5–2 h** |
| GTX 1650, beam=5 (old default) | medium int8 beam=5 + prompt | ~10 s | 70.7 s | 4.2x realtime | ~2.5 h |
| CPU fallback (AMD 5900H) | medium int8 beam=1 + prompt | 3.5 s | ~373 s | 0.8x realtime | ~12 h |

Model is loaded exactly once per process; skill MUST NOT spawn a new python for each file (would add ~10 s per file → wastes ~33 min for 200 files). Never kill the process mid-run — CUDA context can leak, forcing a python restart.

---

## Current Context / Assumptions

- Skill directory: `C:\Users\jinnn\Documents\more-skills\skills\speech2text\`
- Git repo: `more-skills`, branch `more`, currently `?? skills/speech2text/` (untracked — first-time commit is fine).
- Existing files (all preserved, only relocated):
  - `SKILL.md` (185 lines, sauc-focused) → will be rewritten
  - `scripts/voice_pipeline.py`
  - `scripts/read_voice.py`
  - `scripts/volc_asr.py`
  - `scripts/trim_voice.py`
  - `scripts/split_voice.py`
  - `scripts/__pycache__/*.pyc` (delete, do not move)
  - `references/volcengine-asr-protocol.md`
  - `references/troubleshooting.md`
- Hermes venv on this host has `faster_whisper 1.2.1`, `ctranslate2 4.8.0`, `zhconv 1.4.3`, and CUDA 12.4 driver (551.86) — implementation session on this machine will not need any pip install.
- MediaCrawler's `data/douyin/wav-to-txt-fw.py` is the working reference implementation (already validated end-to-end); the new `speech2text.py` will absorb its architecture and expand it (file OR directory input, 5 output modes, dry-run, ETA banner).

---

## Design Decisions (locked)

| # | Question | Decision |
|---|---|---|
| Direction | Refactor style | A — sauc becomes documented `legacy/`, fw is the new default, skill name unchanged, SKILL.md rewritten from scratch |
| Q1 | Input format | mp4/mp3/wav/m4a/aac/flac/ogg/opus/webm — fw shells out to ffmpeg internally, no upfront transcode step |
| Q2 | Batch vs single | Both — `--input` accepts either a file path or a directory path; behavior branches on `Path.is_dir()` |
| Q3 | Backend fallback ladder | `cuda` first → on CUDA runtime error auto-fall back to `cpu int8`. sauc is NOT a runtime fallback; it lives only in `legacy/` |
| Q4 | Fate of sauc code | Move entire sauc pipeline to `legacy/scripts/` and `legacy/references/`; not deleted, not dead-code — accessible via a documented "when to use legacy" note |
| Q5 | Output path rules | 6 combinations (file/dir input × unset/file/dir output) — see table below |
| Q5.1 | Merge-mode write | Append by default (helps resumable batches); no explicit overwrite flag for merge mode in v1 |
| Q6 | Dependency install | SKILL.md documents `pip install faster-whisper zhconv` + CUDA prerequisites; code carries no auto-install logic |
| Q7 | Legacy stdlib tools | All 5 scripts (including pure-stdlib trim/split) move to `legacy/scripts/` — new fw path does not need them |
| Q8 | New entry name | `scripts/speech2text.py` — this becomes the skill's "core" (kernel) function |
| Q9 | Defaults | `--model medium --device cuda --compute-type int8 --language zh --beam-size 1 --initial-prompt "以下是简体中文的短视频语音识别文本，包含标点符号。" --simplified` (double safeguard: prompt + zhconv). The default prompt is a **generic fallback** — SKILL.md instructs the caller (agent or human) to override `--initial-prompt` per invocation with domain-specific terms whenever possible (speaker names, brand names, jargon, formatting bias). See Task 1 "Writing an effective initial_prompt" section and `references/prompt-cookbook.md`. **Also: pass `condition_on_previous_text=True` to `model.transcribe()`** — see Q16. |
| Q16 | `condition_on_previous_text` | **`True`** (Whisper's own default). Each 30 s window uses the prior window's output as decoder context — this is what keeps punctuation style, spelling patterns, and Simplified/Traditional bias consistent across a long audio. **Do NOT set it to `False`** in an over-cautious effort to prevent hallucinated repetitions at long-audio tails: this has been observed to drop Chinese punctuation density from ~9% to ~1% on 4-minute videos (measured 2026-07-15 on MediaCrawler `7587777576036732212/video.wav`, 269 s, `medium int8`, GTX 1650: `False` → 16 puncts / 1607 chars = 1.0%; `True` → 154 puncts / 1722 chars = 8.9%). If a specific corpus DOES exhibit end-of-audio repetition with `True`, prefer to (a) enable `no_repeat_ngram_size=3` or (b) switch to `large-v3` — do not disable this flag. |
| Q15 | Prompt customization | **A — single `--initial-prompt STRING` flag**. No preset library, no file input, no extra layer. Simplicity wins on CLI surface; guidance for writing good prompts lives in SKILL.md + `references/prompt-cookbook.md`. |
| Q10 | Parallelism | Serial. Single WhisperModel instance for the whole batch. No `--workers`. GTX 1650 is already GPU-saturated by one instance |
| Q11 | Idempotence | Skip when target `.txt` exists; `--force` re-runs |
| Q12 | Code layout | One file `scripts/speech2text.py` — no sub-modules |
| Q13 | Dry-run | `--dry-run` scans, prints file list + ETA, exits without loading the model |
| Q14 | Task granularity | 4 top-level tasks: SKILL.md rewrite → speech2text.py → legacy/ relocation → references/ additions |

### Output Path Resolution Rules (Q5 + Q5.1)

`--output` is considered a **file path** iff it ends in `.txt` (case-insensitive). Otherwise it is a **directory path** (created if missing).

| # | --input | --output | Behavior |
|---|---|---|---|
| 1 | file | (unset) | sidecar: write `<input_stem>.txt` next to the input |
| 2 | file | `path/x.txt` | write to that exact file |
| 3 | file | `path/dir/` (no `.txt`) | treat as directory: write `path/dir/<input_stem>.txt` |
| 4 | dir | (unset) | for each `*.wav` under input dir, sidecar `<stem>.txt` next to it |
| 5 | dir | `path/outdir/` | for each wav, write `path/outdir/<stem>.txt` |
| 6 | dir | `path/all.txt` | merge mode — sort wavs by filename, transcribe each, **append** each transcript to `path/all.txt` with a `## <stem>\n` header line and a blank line separator |

Directory input glob is `*.wav` **only** in v1 (matching MediaCrawler's convention); mp4/mp3 batch is deferred to a v2 (or user supplies explicit file paths one at a time).

---

## Files Likely to Change

**Created** (relative to `skills/speech2text/`):
- `scripts/speech2text.py` (new, ~250 lines)
- `legacy/README.md` (new, ~40 lines)
- `references/faster-whisper-guide.md` (new)
- `references/cuda-setup.md` (new)
- `references/chinese-simplification.md` (new)
- `references/gtx-1650-benchmark.md` (new, with the raw smoke-test data)
- `references/prompt-cookbook.md` (new — Whisper `initial_prompt` guidance for agents)

**Rewritten:**
- `SKILL.md` (rewrite from scratch, keep the old one at `legacy/SKILL.md.old`)

**Moved (via `git mv`):**
- `scripts/voice_pipeline.py` → `legacy/scripts/voice_pipeline.py`
- `scripts/read_voice.py` → `legacy/scripts/read_voice.py`
- `scripts/volc_asr.py` → `legacy/scripts/volc_asr.py`
- `scripts/trim_voice.py` → `legacy/scripts/trim_voice.py`
- `scripts/split_voice.py` → `legacy/scripts/split_voice.py`
- `references/volcengine-asr-protocol.md` → `legacy/references/volcengine-asr-protocol.md`
- `references/troubleshooting.md` → `legacy/references/troubleshooting.md`

**Deleted:**
- `scripts/__pycache__/` (bytecode)

---

## Task 1 — Rewrite `SKILL.md`

**Objective:** Replace the sauc-focused SKILL.md with a fw-first, GPU-default document. Provide a Performance Baseline section that includes the "don't kill the process" warning.

**Files:**
- Create: `legacy/SKILL.md.old` (backup, exact byte copy of current SKILL.md)
- Rewrite: `SKILL.md`

**Structure of the new SKILL.md** (~200 lines):
1. Frontmatter (bump `version` to `2.0.0`, update `description` to mention "local GPU faster-whisper, Chinese-first, mp4/wav → txt, offline")
2. `# speech2text — local faster-whisper ASR (GPU-first)`
3. Overview — one paragraph: replaces sauc streaming; runs offline on GPU or CPU; ships mp4→txt one-shot.
4. **When to Use** — same intent triggers as v1 (中文 audio → text, transcribe, subtitle, meeting recording, etc.) but adds "offline / batch of hundreds of short videos / no API budget".
5. **Prerequisites** — bullet list with exact commands:
   ```bash
   # A) ffmpeg on PATH
   ffmpeg -version
   # B) faster-whisper + zhconv
   pip install "faster-whisper>=1.2" "zhconv>=1.4"
   # C) (Optional but recommended) NVIDIA driver >= 527.41 for CUDA 12 GPU path
   nvidia-smi   # look for "CUDA Version: 12.x"
   ```
6. **Quick Start** — 4 canonical invocations covering the 6 output modes:
   ```bash
   # single file, sidecar output
   python <skill>/scripts/speech2text.py --input recording.mp4
   # directory, sidecar
   python <skill>/scripts/speech2text.py --input videos/
   # directory → merged single txt (appended, sorted by filename)
   python <skill>/scripts/speech2text.py --input videos/ --output all.txt
   # dry-run: scan + ETA, no model load
   python <skill>/scripts/speech2text.py --input videos/ --dry-run
   ```
7. **Performance Baseline** — the table above verbatim, plus:
   - ⚠️ **Do not kill the process mid-batch.** Faster-whisper loads a ~1.5 GB model into GPU VRAM once and reuses it for every file. Killing it can leak CUDA context (the next run may fail at model load with an OOM even though `nvidia-smi` shows the card free — restart python to clear). Prefer `Ctrl-C` at a segment boundary if you must stop; the skip-if-exists behavior lets you resume by just re-running.
   - ETA rule of thumb: `wall_seconds ≈ audio_seconds / 5` on GTX 1650 medium int8 beam=1.
8. **Output Behavior** — the 6-row table verbatim, plus a note that merge-mode is append (safe for resumable batches).
9. **Config Resolution** — CLI flag > default (no env vars in v1; keep the design symmetric to old skill; add env vars only if user asks later).
10. **Common Pitfalls** —
    - "CUDA driver version is insufficient" → upgrade NVIDIA driver ≥ 527.41 (link to `references/cuda-setup.md`)
    - Whisper outputs Traditional Chinese sometimes — this is by design of the model; the double safeguard (`--initial-prompt` + `--simplified`) fixes it; do not disable both
    - `--model large-v3` on 4 GB VRAM: OOMs; stick to `medium int8`
    - Directory batch only picks up `*.wav`; if you have mp4 use single-file mode (mp4 is ffmpeg-transcoded automatically)
    - Process was killed → next run may fail to load model; run `python -c "import ctranslate2; ctranslate2.Whisper('medium', device='cuda')"` and if it still fails, restart the shell to clear CUDA context
    - **Do NOT set `condition_on_previous_text=False`** in `model.transcribe()`. Whisper decodes in 30 s windows; disabling cross-window conditioning drops punctuation density from ~9% to ~1% on Chinese long-form audio (measured on MediaCrawler 2026-07-15). Keep it at Whisper's default `True`. See plan Q16 for the rationale and the correct mitigations for tail-repetition (they are NOT this flag).
    - `--initial-prompt` >224 tokens is silently truncated **from the head**; keep the most important tokens (proper nouns, jargon) near the end of the string. See `references/prompt-cookbook.md`.
11. **Writing an effective `initial_prompt`** — new section (~30 lines). Content:
    - **Why it matters**: `initial_prompt` steers decoder token probabilities. Empirically it lowers character-error-rate on proper nouns and technical terms by 5–15% on Chinese content, and biases the output toward Simplified Chinese (helped drop the zhconv fix-up rate from ~50% to 26% in MediaCrawler smoke tests).
    - **The 224-token rule**: Prompt is truncated **from the head** if longer. Put the most-critical terms (speaker names, brand names, jargon) at the **end**. For Chinese, budget ~200 汉字; for English, ~350 words.
    - **What to include** (checklist):
      1. Genre/format cue ("以下是XX的语音识别文本")
      2. Language + style bias ("简体中文，包含标点符号，短句" / "英语，会议记录风格")
      3. Proper nouns unique to this recording (人名 / 品牌 / 产品名 / 缩写全称)
      4. Domain jargon that the base model likely doesn't know
      5. A short representative example fragment (optional but effective)
    - **What NOT to include**:
      1. Instructions to the model ("请翻译成中文" — Whisper is NOT chat)
      2. Full transcripts of previous audio (waste of budget, no benefit)
      3. Emojis or unusual Unicode (unpredictable tokenization)
    - **Short templates** (four inline, ~40 chars each):
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
    - **Link**: "→ For longer worked examples, do/don't cases, and multilingual prompts, see `references/prompt-cookbook.md`."
12. **Fallback: cloud ASR** — one paragraph: "If you have no GPU and CPU is too slow, or your batch spans many hours of audio and you have a Volcengine sauc key, the old streaming pipeline lives in `legacy/` — see `legacy/README.md`."
13. **References** — links to all new `references/*.md` files (including `prompt-cookbook.md`).
14. **Next Step** — same as v1 (feed to LLM, diarize, post-process).

**Verification for Task 1:**
- `read_file skills/speech2text/SKILL.md` — visually confirm structure
- Skill validator: `python -m hermes_agent.skills.validator skills/speech2text/SKILL.md` (or equivalent — see `hermes-agent-skill-authoring` skill)
- `git diff --stat` shows only SKILL.md changed + new legacy/SKILL.md.old

**Estimated wall time:** 15–20 min of drafting.

---

## Task 2 — Write `scripts/speech2text.py`

**Objective:** Create the new CLI. Absorb architecture from MediaCrawler's `wav-to-txt-fw.py`; add file-vs-dir input dispatch, 6-output-mode resolution, dry-run, ETA banner, and CUDA→CPU auto-fallback.

**File:** `scripts/speech2text.py` (~250 lines)

**Skeleton (subagent must fill in with copy-pasteable code):**

```python
"""speech2text — local faster-whisper batch ASR (Chinese-first, GPU-default).

Replaces the sauc streaming pipeline. Reference implementation:
    C:/Users/jinnn/Documents/MediaCrawler/data/douyin/wav-to-txt-fw.py
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
from typing import Iterable, Optional

# -----------------------------------------------------------------------------
# Output resolution
# -----------------------------------------------------------------------------
def is_txt_path(p: Path) -> bool:
    return p.suffix.lower() == ".txt"

def resolve_targets(input_path: Path, output: Optional[Path]) -> tuple[list[Path], dict[Path, Path], Optional[Path]]:
    """Returns (input_wavs, per_wav_output_map, merge_target_or_None)."""
    # ... implement the 6-row table

# -----------------------------------------------------------------------------
# Backend
# -----------------------------------------------------------------------------
def load_model(model: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel
    try:
        return WhisperModel(model, device=device, compute_type=compute_type), device
    except Exception as e:
        if device == "cuda":
            print(f"[speech2text] CUDA failed ({e!s:.80}), falling back to CPU int8", flush=True)
            return WhisperModel(model, device="cpu", compute_type="int8"), "cpu"
        raise

def transcribe_one(model, wav: Path, args, zh_convert) -> tuple[str, float, float]:
    segs, info = model.transcribe(
        str(wav),
        language=args.language or None,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
        condition_on_previous_text=False,
        initial_prompt=args.initial_prompt or None,
    )
    parts = [s.text for s in segs]
    text = "".join(parts).strip()
    if zh_convert is not None:
        text = zh_convert(text)
    return text, info.duration or 0.0

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = build_argparser()
    args = ap.parse_args(argv)

    input_wavs, per_wav_out, merge_target = resolve_targets(args.input, args.output)
    todo, skipped = filter_idempotent(input_wavs, per_wav_out, merge_target, args.force)

    # Banner
    print_banner(args, len(input_wavs), skipped, len(todo))

    if args.dry_run:
        for w in todo: print(f"  DRY  {w}")
        return 0
    if not todo:
        return 0

    # Lazy imports
    zh_convert = None
    if args.simplified:
        from zhconv import convert as _c
        zh_convert = lambda s: _c(s, "zh-cn")

    model, device_used = load_model(args.model, args.device, args.compute_type)
    print(f"[speech2text] model loaded on {device_used}", flush=True)

    # Loop
    t0 = time.time()
    ok = fail = 0
    total_audio = 0.0
    for i, wav in enumerate(todo, 1):
        # ... transcribe, write atomically or append, log progress + ETA

    print_summary(ok, fail, skipped, total_audio, time.time() - t0)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
```

**Sub-tasks for Task 2** (2–5 min each, TDD-lite):

1. **Argparse builder** — every flag from the "Design Decisions Q9" row + `--input` (Path, required), `--output` (Path, optional), `--force`, `--dry-run`, `--vad-filter/--no-vad-filter` (default on).
   *Verify:* `python speech2text.py --help` prints all flags.
2. **`is_txt_path` + `resolve_targets`** — pure function; unit-test the 6 combinations.
   *Verify:* Ad-hoc temp script under `%TEMP%/hermes-verify-*.py` exercises each row.
3. **`filter_idempotent`** — skip when target exists (except in merge mode, where existence just means append).
   *Verify:* create a fake target, ensure it's skipped; pass `--force`, ensure not skipped.
4. **`print_banner`** — includes the "don't kill process" line and ETA estimate. Formula: `eta = total_audio_seconds / 5.0` for cuda (baseline: 5x realtime rounded), `total_audio_seconds * 1.3` for cpu. Uses ffprobe to get audio duration for the ETA — OR simpler: assume 3 min per wav if probe is missing.
   *Verify:* Dry-run on a 3-wav directory prints a sensible ETA.
5. **`load_model`** with try/except CUDA fallback.
   *Verify:* Ad-hoc test: force `device='cuda_fake'`, confirm falls back gracefully.
6. **`transcribe_one`** — mirrors MediaCrawler's function 1:1.
7. **Batch loop** — atomic write via `.tmp` rename, append for merge mode with `## <stem>` header line, per-file progress log (`[i/N] OK stem  audio=Xs  wall=Ys  RTF=Z  ETA_remaining=HH:MM`).
8. **Summary line** — final total, speed, ok/fail/skipped counts, path to `.failed.log` if any.

**Verification for Task 2:**
- `python -m py_compile scripts/speech2text.py` — no syntax errors
- `python scripts/speech2text.py --help` — all flags present, defaults correct
- `python scripts/speech2text.py --input <one wav from MediaCrawler> --dry-run` — prints file list + ETA, does not import faster_whisper
- Full smoke on ONE 5-min wav — output text must match MediaCrawler's `wav-to-txt-fw.py` character-for-character (both scripts use the same model + defaults; any divergence is a bug)
- Directory smoke on 3 wavs with `--output merged.txt` — merged file has 3 `## <stem>` blocks in filename order, appended

**Estimated wall time:** 45–60 min drafting + 10 min smoke tests.

---

## Task 3 — Relocate sauc code to `legacy/`

**Objective:** Move 5 scripts + 2 references into `legacy/` without losing git history. Write a `legacy/README.md` that explains why they're there and how to reach for them.

**Steps:**

1. From `skills/speech2text/`:
   ```bash
   mkdir -p legacy/scripts legacy/references
   git mv scripts/voice_pipeline.py   legacy/scripts/
   git mv scripts/read_voice.py       legacy/scripts/
   git mv scripts/volc_asr.py         legacy/scripts/
   git mv scripts/trim_voice.py       legacy/scripts/
   git mv scripts/split_voice.py      legacy/scripts/
   git mv references/volcengine-asr-protocol.md legacy/references/
   git mv references/troubleshooting.md         legacy/references/
   rm -rf scripts/__pycache__
   ```

2. Write `legacy/README.md`:

   ```markdown
   # legacy/ — sauc streaming ASR (fallback)

   This directory holds the previous implementation of speech2text: a
   Volcengine sauc (`bigmodel_nostream`) streaming pipeline. It is no
   longer the default path — the new `scripts/speech2text.py` runs
   faster-whisper locally on GPU/CPU and covers 99% of the use cases
   the sauc path used to.

   ## When to reach for legacy

   - You have no GPU and CPU int8 is too slow for your batch size, AND
   - You have a Volcengine sauc-capable API key, AND
   - Your audio is Chinese/multilingual with speech content sauc handles
     particularly well.

   ## How to use

   The files here are untouched from the pre-2.0 implementation. Refer to
   `../SKILL.md` v1.0.0 (backed up as `../legacy/SKILL.md.old`) for full
   usage. In short:

   ```bash
   export VOLCENGINE_API_KEY=<key>
   python legacy/scripts/voice_pipeline.py \
       --input recording.mp3 \
       --output transcript.txt
   ```

   ## Retained files

   | File | Purpose |
   |---|---|
   | `scripts/voice_pipeline.py` | one-shot ffmpeg + trim + split + sauc |
   | `scripts/read_voice.py`     | sauc ASR wrapper (single wav or folder) |
   | `scripts/volc_asr.py`       | low-level sauc websocket client |
   | `scripts/trim_voice.py`     | clamp long silences (pure stdlib) |
   | `scripts/split_voice.py`    | chunk on silence (pure stdlib) |
   | `references/volcengine-asr-protocol.md` | sauc wire format cheat sheet |
   | `references/troubleshooting.md` | error codes / keepalive / endpoint permutations |
   ```

3. Copy the pre-refactor `SKILL.md` to `legacy/SKILL.md.old` before Task 1 rewrites it (this step is executed at the start of Task 1, not here — but noted here for the audit trail).

**Verification for Task 3:**
- `git status` shows exactly 7 renames + 1 new file (`legacy/README.md`)
- `git log --follow legacy/scripts/voice_pipeline.py` shows the pre-refactor history intact
- `ls scripts/` — should be one file only: `speech2text.py`
- `ls legacy/scripts/` — 5 files
- `ls legacy/references/` — 2 files

**Estimated wall time:** 10 min (mechanical).

---

## Task 4 — Populate `references/`

**Objective:** Write four new reference docs supporting the new fw-first flow.

**Files:**

### `references/faster-whisper-guide.md`
Model matrix: tiny/base/small/medium/large-v3 sizes, VRAM footprints, quality/speed tradeoffs on GTX 1650. Compute-type matrix: `int8 / int8_float16 / float16 / int8_float32`. Common errors (`Could not locate cudnn_ops64_9.dll`, OOM). Model cache location (`~/.cache/huggingface/hub/models--Systran--*`).

### `references/cuda-setup.md`
Symptoms of a too-old driver (the exact error message: `CUDA driver version is insufficient for CUDA runtime version`). NVIDIA driver download link. Minimum driver ≥ 527.41 for CUDA 12. GTX 1650 specifics (Turing, SM 7.5, no Tensor Core → int8 uses generic CUDA path). Post-install verification (`nvidia-smi` shows `CUDA Version: 12.x`).

### `references/chinese-simplification.md`
Why Whisper sometimes outputs Traditional Chinese (training data mix). Two-layer safeguard: `initial_prompt` biases decoder during inference; `zhconv.convert(text, 'zh-cn')` post-processes. Empirical result from MediaCrawler smoke: 434/1658 = 26% of characters still needed zhconv post-conversion even with the prompt, so both layers together are recommended, not one.

### `references/gtx-1650-benchmark.md`
Raw smoke-test data (copy from this planning session):
- `medium int8` GPU beam=1: 46.5 s / 5 min audio
- `medium int8` GPU beam=2: 115.4 s
- `medium int8` GPU beam=3: 157.5 s
- `medium int8` GPU beam=5: 134.3 s (baseline w/o prompt: 70.7 s)
- `medium int8` CPU beam=5: 373 s
Note that beam=1 with prompt outperformed beam=5 without on this hardware — the plan's default is `beam=1`.

### `references/prompt-cookbook.md`
Deep dive on Whisper's `initial_prompt` for the agent that will call this skill. This complements SKILL.md's short "Writing an effective initial_prompt" section — think of SKILL.md as the checklist and this file as the worked-examples appendix. Structure:

1. **Mental model** — Whisper's decoder is conditioned on the last 224 tokens of the prompt as if they were spoken in a prior segment. That's why proper nouns, jargon, punctuation patterns, and Simplified/Traditional bias transfer. It is **not** an instruction channel — do not write "please transcribe accurately" or "translate to English".

2. **Anatomy of a strong Chinese prompt**:
   ```
   以下是【场景】的中文转录，说话人：【人名1、人名2】，涉及【领域】术语：【术语1、术语2、术语3】，包含标点符号。
   ```
   - The genre cue anchors register (口播 vs 讲座 vs 访谈)
   - Speaker names are the highest-leverage — Whisper mis-transcribes uncommon Chinese names ~40% of the time without them
   - Jargon list biases token-level decisions on ambiguous phonemes
   - Trailing "包含标点符号" flips a switch: with it, Whisper emits ，。？！; without it, the output is a run-on sentence in many cases

3. **Anatomy of a strong English prompt**:
   ```
   The following is a recording from [context], with speakers [Name 1, Name 2]. Domain: [field]. Key terms: [Term 1, Term 2, Term 3]. Transcribed with punctuation and capitalization.
   ```

4. **Six worked examples with rationale** (200–300 words each, showing before/after transcript snippets):
   - **Meeting**: Bad prompt vs good prompt for a fictional 3-person product-review meeting. Shows how naming attendees fixes name mis-transcription.
   - **Podcast**: Named host+guest, show title, episode topic. Shows how a topic cue ("量化投资") suppresses homophonic errors like "量化" → "凉化".
   - **MediaCrawler / short-video** (based on 2026-07 Douyin smoke): Shows the empirically-measured 434/1658 → ~200/1658 character correction rate when adding brand names + speaker handle.
   - **Academic talk**: Latin-script term preservation ("propensity score" stays English inside Chinese transcript). Shows how listing English terms in the prompt prevents them being phonetically Sinicized.
   - **News broadcast**: Newsreader register, proper nouns for public figures, formatted numbers.
   - **Multilingual mixed** (中英夹杂 tech talk): Prompt in both languages, code names preserved.

5. **Do/Don't cheat sheet**:
   | Do | Don't |
   |---|---|
   | End the prompt with the most critical tokens | Start with "please" or instructions |
   | List 3–8 proper nouns; more is diminishing returns | Paste an entire prior transcript |
   | Match the target language (write Chinese prompts for Chinese audio) | Mix emoji/symbols |
   | Include punctuation samples in-prompt to bias output style | Write vague hopes ("output clearly") |
   | Test-and-tune: run one file, adjust prompt, re-run with `--force` | Assume defaults are fine for specialty content |

6. **Iteration workflow** — how an agent should approach a new corpus:
   1. Run one representative file with the generic default prompt.
   2. Diff the output against the audio (or spot-check 20 seconds).
   3. Note the 5 most-frequent errors — usually proper nouns and jargon.
   4. Write a scenario prompt with those terms placed at the end.
   5. Re-run with `--force` on the same file, verify improvement.
   6. Roll out to the batch.

7. **References** — links to the OpenAI Whisper prompt discussion, the faster-whisper `transcribe(initial_prompt=...)` API docs, and a note that this is NOT the same mechanism as OpenAI Chat prompts.

**Verification for Task 4:**
- All five files exist, non-empty, well-formed markdown
- SKILL.md's Reference section links resolve
- `prompt-cookbook.md` has all 7 subsections listed above; each of the 6 worked examples has both a bad-prompt and good-prompt block plus a rationale paragraph

**Estimated wall time:** 20 min drafting for the first 4 references + 15–25 min for `prompt-cookbook.md` (longer file, more examples).

---

## Tests / Validation (full-plan level)

Run in order after all four tasks are complete:

1. **Static:** `python -m py_compile scripts/speech2text.py`
2. **CLI parse:** `python scripts/speech2text.py --help` shows every documented flag
3. **Dry-run smoke (no model load):** Point at MediaCrawler's `data/douyin/videos/` and run `--dry-run`. Should print 200 file lines + ETA in under 2 seconds and never import faster_whisper.
4. **Single-file smoke (GPU):** Run against one MediaCrawler wav; compare output character-for-character with MediaCrawler's `wav-to-txt-fw.py` output for the same file. Zero divergence is required.
5. **CPU-fallback smoke:** Set `--device cpu` explicitly, confirm output text matches GPU output (may differ in <5% chars due to numerical drift — acceptable).
6. **Directory sidecar smoke:** Run on a directory of 3 wavs, no `--output`. Expect 3 sidecar txt files.
7. **Directory merge smoke:** Run on same 3 wavs with `--output merged.txt`. Expect one file with 3 `## <stem>` blocks in filename order.
8. **Idempotence smoke:** Re-run any of the above. Expect all files skipped.
9. **Skill validator:** Run the skill validator against `SKILL.md`. Zero errors.

---

## Risks & Open Questions

1. **CUDA context leak on Ctrl-C mid-batch** — Not fixable within Python (it's a CTranslate2/CUDA driver interaction). Best we can do is document it in SKILL.md and rely on the idempotent skip-if-exists behavior for cheap resume. Acceptable.
2. **`--input` accepting a directory of mixed mp4/wav** — v1 only globs `*.wav` in dir mode. If future scenario needs `*.mp4`, add a `--glob` flag or auto-detect. Deferred.
3. **Merge-mode append + concurrent runs** — v1 uses simple `open('a')` — not multi-process safe. Q10 fixed serial, so this is fine, but a `--lock` file would be a nice-to-have for the future.
4. **ffprobe for accurate ETA** — implementing this well requires shelling out to ffprobe per file, which is slow when scanning 200 files. Compromise: use `os.path.getsize(wav) / 32000` (bytes-per-second for mono 16k s16le) for a rough second-count in dry-run — accurate enough for a Header ETA. In real transcribe mode, ETA updates per-file with the actual duration reported by `info.duration`.
5. **Whisper direct mp4 input via ffmpeg subprocess** — Requires `ffmpeg` on PATH. If missing, error message must be actionable ("install ffmpeg or use `--input <wav>`"). Verify in Task 2.
6. **`--simplified` and encoding on Windows** — Ensure atomic writer uses `encoding="utf-8"`, not the system default (cp936 on Chinese Windows). Explicit encoding param on every `Path.write_text` / `open('w')`.
7. **`--initial-prompt` >224 token silent truncation** — Whisper drops from the head with no warning. If an agent chains a very long domain glossary, the front is discarded silently. Mitigation: SKILL.md + `references/prompt-cookbook.md` explicitly document the limit and the "put critical terms at the end" rule. Optional v2: emit a warning to stderr when the prompt is longer than ~180 汉字 or ~350 英文单词.
8. **`condition_on_previous_text=True` tail repetition risk** — Whisper's own default. On very long audio it can occasionally repeat the last phrase 2-3 times at the tail (self-conditioning loop). Observed empirically once on a 4-min video (out of 1,722 chars) — negligible failure mode compared to the punctuation-loss cost of turning it off. Do NOT preempt this by setting it to `False` (see Q16). If a specific corpus DOES repeat noticeably: (a) pass `no_repeat_ngram_size=3`, (b) switch to `large-v3`, or (c) leave `True` and post-process out consecutive-line duplicates. Never trade punctuation for anti-repetition.

---

## Non-Goals (v2.0.0 scope)

- No speaker diarization (would need pyannote or similar — separate skill)
- No timestamped output / SRT / VTT export (add later if requested)
- No streaming input from mic (this remains a batch tool)
- No `--workers` parallelism (single GPU is saturated)
- No `env-var config resolution` (v1 had `VOLCENGINE_ASR_ENDPOINT` etc.; v2 has no env-vars — decided in Q6)
- No auto-install of Python deps (documented in SKILL.md, not code)

---

## Commit Strategy

One commit per task, in order:

1. `feat(speech2text): rewrite SKILL.md for local faster-whisper (v2.0.0)`
2. `feat(speech2text): add scripts/speech2text.py — local fw CLI with GPU→CPU fallback, 6 output modes, dry-run`
3. `refactor(speech2text): relocate sauc pipeline to legacy/ (kept as fallback)`
4. `docs(speech2text): add references for fw/cuda-setup/simplification/gtx-1650-benchmark/prompt-cookbook`

If Task 3's `git mv` interleaves confusingly with Task 1's `SKILL.md.old` backup, split Task 3 into two commits — the mvs first, the README.md second.

---

## Execution Handoff

**Plan complete and saved to `skills/speech2text/2026-07-15_173418-speech2text-refactor.md`. Not scheduled for immediate execution — user reserved implementation for a future session.**

When the user is ready to execute:
1. Load the `subagent-driven-development` skill.
2. Dispatch one subagent per task with the full task section as its brief.
3. Two-stage review after each task: spec compliance → code quality.
4. Do NOT proceed to the next task until both reviews pass.
5. All work happens under `C:\Users\jinnn\Documents\more-skills\skills\speech2text\` — no changes outside that directory.
