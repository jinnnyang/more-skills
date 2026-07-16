# faster-whisper — model & compute-type reference

Deep dive on tuning `speech2text.py` for different hardware/quality budgets.
SKILL.md sticks to `medium int8` on CUDA; this file explains why and when to
deviate.

## Model matrix

| Model     | Params | Disk  | VRAM (int8) | Quality (Chinese CER) | GTX 1650 speed (int8 beam=1) |
|-----------|-------:|------:|------------:|:----------------------|:-----------------------------|
| `tiny`    | 39 M   | 74 MB | ~0.5 GB     | Very rough — many homophones | ~20× realtime |
| `base`    | 74 M   | 145 MB| ~0.7 GB     | Rough — usable for keyword extraction only | ~15× realtime |
| `small`   | 244 M  | 461 MB| ~1.2 GB     | Passable for clean speech | ~10× realtime |
| **`medium`** | **769 M** | **1.5 GB** | **~2.0 GB** | **Good — production baseline** | **~5× realtime** |
| `large-v3`| 1.55 B | 3.0 GB| ~4.5 GB     | Best available today | (OOM on 4 GB VRAM) |

CER = character error rate. Chinese-content numbers approximate; exact
values depend on domain, prompt, and audio quality.

**Recommendation.** For 中文 短视频/播客/会议, `medium` is the sweet spot.
`small` is worth trying only if `medium` is too slow AND accuracy loss is
acceptable (e.g. keyword-only workflows). `large-v3` needs an 8 GB+ card,
or CPU (~10× slower than `medium int8` CPU).

## Compute-type matrix

`--compute-type` controls how `CTranslate2` (the faster-whisper backend)
quantizes the model in memory:

| Compute type    | VRAM footprint | Speed on Turing GPU | When to use |
|-----------------|---------------:|:--------------------|:------------|
| `int8`          | Smallest       | Best on non-Tensor-Core GPUs (GTX 10xx / 16xx) | 4 GB VRAM cards, GTX 1650, older cards |
| `int8_float16`  | Small          | Fast on cards WITH Tensor Cores (RTX 20xx+, T4, A100) | 6 GB+ RTX card |
| `float16`       | Medium         | Balanced          | 8 GB+ RTX cards, when quality > speed |
| `int8_float32`  | Larger         | Slower, best CPU quality | CPU-only path with sufficient RAM |

**GTX 1650 note.** Turing SM 7.5 has no Tensor Cores. `int8` uses the
generic INT8 CUDA kernel path, which is what makes 1.5 GB of `medium`
weights fit inside 4 GB VRAM with headroom for the KV cache. Do not
switch to `int8_float16` on GTX 1650 — you'll trade nothing for extra
VRAM pressure.

## Model cache location

First run downloads weights to your HuggingFace cache:

```
Windows:   %USERPROFILE%\.cache\huggingface\hub\models--Systran--faster-whisper-medium\
macOS/Linux: ~/.cache/huggingface/hub/models--Systran--faster-whisper-medium/
```

Override with `--model-dir DIR` if you have a shared cache location. The
first-time download for `medium` is ~1.5 GB; subsequent runs load from
cache in 3–11 s depending on disk.

## Common errors

**`Could not locate cudnn_ops64_9.dll` (Windows)**
> Missing cuDNN 9 runtime. `faster-whisper >= 1.2` bundles cuDNN 9 wheels
> automatically. Fix: `pip install --upgrade --force-reinstall faster-whisper ctranslate2`.
> If the error persists, verify `pip show ctranslate2` reports `>= 4.6`.

**`CUDA driver version is insufficient for CUDA runtime version`**
> Your NVIDIA driver is too old for the bundled CUDA 12 runtime.
> Upgrade to driver ≥ 527.41. See [`cuda-setup.md`](cuda-setup.md).

**`CUDA out of memory` at model load**
> The model + KV cache + your inputs don't fit. Options: (a) switch to
> `--model small` (or `medium` if you were trying `large-v3` on 4 GB),
> (b) close other GPU-using apps (browser hardware accel counts),
> (c) fall back to `--device cpu --compute-type int8`.

**Silent hang at first transcribe**
> Not usually a bug — first-ever transcribe includes JIT warmup for the
> CUDA kernels (~5–10 s longer than subsequent files). If it hangs for
> >60 s, kill and check `nvidia-smi` for a zombie process.

## VAD (voice activity detection)

`--vad-filter` is on by default. It runs Silero VAD to skip silence
regions before decoding — the wall-time win is real when your inputs have
long silences (e.g. lecture recordings with pauses). Downsides: adds ~0.3
s of overhead per file, and can rarely clip the first/last syllable if a
speaker starts abruptly. Disable with `--no-vad-filter` if you notice
truncation.

## References

- faster-whisper GitHub: https://github.com/SYSTRAN/faster-whisper
- CTranslate2 quantization docs: https://opennmt.net/CTranslate2/quantization.html
- Systran model hub: https://huggingface.co/Systran (all `faster-whisper-*` variants)
