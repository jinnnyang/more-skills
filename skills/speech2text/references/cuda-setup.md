# CUDA setup for faster-whisper on Windows/Linux

`speech2text.py` uses `faster-whisper >= 1.2`, which bundles CUDA 12 +
cuDNN 9 runtime wheels via `ctranslate2 >= 4.6`. You do **not** need to
install CUDA Toolkit or cuDNN separately — only the NVIDIA driver.

## Minimum NVIDIA driver

| Platform   | Minimum driver | Recommended |
|:-----------|:--------------:|:-----------:|
| Windows    | 527.41         | 551+        |
| Linux      | 525.60.13      | 550+        |

Anything older will fail at model load with:

```
RuntimeError: CUDA driver version is insufficient for CUDA runtime version
```

Check current driver:

```powershell
nvidia-smi
```

Expected output:

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 551.86       Driver Version: 551.86    CUDA Version: 12.4        |
+-----------------------------------------------------------------------------+
```

The `CUDA Version` field shows what CUDA runtime the driver can host. As
long as it's ≥ 12.0 (which requires ≥ 527.41 on Windows), you're set.

## GTX 1650 specifics (the reference hardware)

- Architecture: **Turing** (TU117)
- Compute capability: **SM 7.5**
- Tensor Cores: **none** (the 1650 is the entry-level Turing without them)
- VRAM: **4 GB GDDR5** (some SKUs 4 GB GDDR6)

Implications for this skill:

- Use `--compute-type int8`. No benefit from `int8_float16` without Tensor
  Cores, and the extra memory pressure can push you out of VRAM.
- `medium` fits comfortably (~2 GB VRAM at rest + ~500 MB per active
  transcribe). `large-v3` OOMs at load.
- Actual measured throughput: **4–6× realtime** for Chinese content,
  `medium int8 beam=1 vad-filter`. See [`gtx-1650-benchmark.md`](gtx-1650-benchmark.md).

## Upgrading the driver (Windows)

1. Identify your GPU generation:
   ```powershell
   nvidia-smi -L
   ```
2. Download the current Studio or Game Ready driver from
   https://www.nvidia.com/download/index.aspx — pick the exact GPU family.
3. **Clean install** is safer if you're jumping several major versions
   (uncheck "Perform a clean installation" in the installer's Advanced
   options → check it back on).
4. Reboot.
5. Verify: `nvidia-smi` shows the new version and `CUDA Version: 12.x`.

## Upgrading the driver (Linux)

Ubuntu / Debian:

```bash
sudo apt update
sudo ubuntu-drivers autoinstall   # picks the recommended proprietary driver
sudo reboot
nvidia-smi
```

RHEL / Fedora — use the CUDA repo per NVIDIA's install guide.

## Verify the full chain end-to-end

After driver install (or if you're troubleshooting):

```python
# In the Hermes venv or wherever you installed faster-whisper
python -c "
import ctranslate2
print('ctranslate2 version:', ctranslate2.__version__)
print('CUDA available:', ctranslate2.get_cuda_device_count() > 0)
print('Devices:', ctranslate2.get_cuda_device_count())
"
```

Expected:

```
ctranslate2 version: 4.6.0 (or newer)
CUDA available: True
Devices: 1
```

If `CUDA available: False` but `nvidia-smi` works, most likely
`ctranslate2` was installed as the CPU wheel. Fix:

```bash
pip install --upgrade --force-reinstall ctranslate2 faster-whisper
```

## No GPU — CPU fallback

If you don't have an NVIDIA GPU (or can't upgrade the driver), pass
`--device cpu --compute-type int8`. Expect ~0.8× realtime for `medium`
on a modern 8-core CPU. For large batches (many hours of audio) prefer
the `legacy/` sauc pipeline if you have a Volcengine key.

## References

- NVIDIA driver downloads: https://www.nvidia.com/download/index.aspx
- CUDA compatibility matrix: https://docs.nvidia.com/deploy/cuda-compatibility/
- CTranslate2 installation: https://opennmt.net/CTranslate2/installation.html
