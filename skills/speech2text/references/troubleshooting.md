# speech2text — Troubleshooting Guide

Real errors this skill's authors have hit. Each entry has: **symptom** →
**root cause** → **fix**.

## 1. `1011 keepalive-ping-timeout` mid-stream

**Symptom.** Any audio chunk ≥ 25 seconds fails with:
```
websockets.exceptions.ConnectionClosedError: sent 1011 (internal error) keepalive ping timeout
```

**Root cause.** `websockets.connect()` defaults to `ping_interval=20`,
`ping_timeout=20`. The sauc bigmodel_nostream server does NOT reliably
return pong frames while it's ingesting a long send burst — it tracks
liveness via its own application-layer sequence-frame protocol. Client-side
ping expires after 20 s → client closes with 1011.

**Fix.** In `_run_asr_websocket()`, pass `ping_interval=None`:
```python
async with websockets.connect(
    endpoint,
    additional_headers=headers,
    max_size=2**24,
    ping_interval=None,   # <-- required
) as websocket:
```

**Verification.** 225 s test clip split into 8 × ~28 s chunks: 8/8 pass on
first or second attempt with the fix; 4/8 fail with default ping_interval.

## 2. `45000081` waiting-next-packet timeout

**Symptom.** Server error frame code 45000081 mid-stream:
```
ASR API Error [45000081]: {"error": "waiting next packet timeout"}
```

**Root cause.** Server expects the next audio-only frame within 5 s of
receiving the previous one. Client stalled.

**Fix.** Two guards, both already in place:
1. `DEFAULT_CHUNK_SIZE = 3200` (100 ms per frame) — well inside 5 s window.
2. `await asyncio.sleep(0)` after each `await websocket.send()` — yields
   scheduler so keepalive/recv tasks can drain.

If it still happens, it's server-side flakiness. `read_voice.py` retries
up to 3 times with exponential backoff.

## 3. `45000010` Invalid X-Api-Key

**Symptom.** Handshake fails or first server frame:
```
ASR API Error [45000010]: {"error": "Invalid X-Api-Key"}
```

**Root cause.** Wrong key type for the endpoint.

- Coding-Plan keys (`ark-…-…22d4` style) work only with `/api/v3/plan/…`
  endpoints. Default: `wss://.../api/v3/plan/sauc/bigmodel_nostream` ✓
- openspeech.bytedance.com direct keys (`X-Api-App-Key` + `X-Api-Access-Key`)
  work with `/api/v3/…` endpoints WITHOUT the `plan/` prefix.

**Fix.** Match key type to endpoint. If you have a direct openspeech key,
override:
```bash
export VOLCENGINE_ASR_ENDPOINT=wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream
```

## 4. `45000030` Resource not granted

**Symptom.** Handshake OK, first frame returns:
```
ASR API Error [45000030]: {"error": "resource not granted"}
```

**Root cause.** Auth valid, but the resource ID (`X-Api-Resource-Id`)
isn't enabled for this key.

**Fix.** Either:
- Grant `volc.seedasr.sauc.duration` to the key in Volc console, OR
- Override `--resource` / `VOLCENGINE_ASR_RESOURCE` with a granted one.

The Coding-Plan key SKU includes sauc but not `volc.bigasr.auc_turbo`
(HTTP recording-file API). If you want async submit/poll, you need a
different key SKU entirely.

## 5. "audio input is not supported by this model"

**Symptom.** HTTP 400 from `/api/v3/chat/completions` with
`{"type": "input_audio", ...}` payload.

**Root cause.** This skill uses the sauc **streaming** ASR endpoint, not
the chat-completions audio-in feature. Some Volc audio models are
plumbed only through chat-completions; those need a different key type
and a different code path (base64-encode audio, POST to
`/api/v3/chat/completions`).

**Fix.** Don't route through chat-completions. Stick with sauc streaming
(default endpoint in this skill).

## 6. Empty transcript

**Symptom.** `RuntimeError: exhausted retries; ... ASR returned empty transcript`.

**Root cause.** Either:
1. The chunk really is silent / music-only.
2. Sauc returned data in a shape `_extract_transcript()` doesn't handle.

**Fix.**
1. Inspect the chunk with `ffplay chunk.wav` — if it's actually silent,
   this is expected. `voice_pipeline` should have trimmed it via
   trim_voice; if it slipped through, tune `--max-silence` down.
2. If it's real speech, dump the raw server response and add the new key
   to `_extract_transcript()` (see `references/volcengine-asr-protocol.md`
   "Payload Shape Reference").

## 7. split_voice / trim_voice: `mono` in stderr

**Symptom.**
```
split_voice: error: input must be mono / 16 kHz / 16-bit WAV; got ...
```

**Root cause.** Input WAV is stereo, 44.1 kHz, or 24-bit.

**Fix.** Pre-transcode:
```bash
ffmpeg -y -i src.wav -ac 1 -ar 16000 -c:a pcm_s16le mono.wav
```

`voice_pipeline` does this automatically in stage 1.

## 8. `ffmpeg not found on PATH`

**Symptom.** `voice_pipeline: error: ffmpeg not found on PATH`.

**Fix.** Install ffmpeg.

- Windows: `winget install ffmpeg` or `choco install ffmpeg`. Then reopen
  terminal so PATH refreshes.
- macOS: `brew install ffmpeg`.
- Linux: `sudo apt install ffmpeg` / `sudo dnf install ffmpeg`.

Verify: `ffmpeg -version`.

## 9. Retry-worthy vs fatal error classification

`read_voice.py` retries all `Exception` types up to 3× with exponential
backoff (3 s, 6 s). This is aggressive but correct for sauc, whose failure
modes are dominated by transient server scheduling issues.

**Fatal (no retry helps)** — abort the whole run:
- No API key
- Wrong endpoint / wrong resource
- Bad audio format (mono/16k/s16 check upstream)

**Retryable** — the loop handles these:
- 1011 keepalive
- 45000081 timeout
- Any `websockets.exceptions.*`
- Transient network errors

## 10. Cost / rate limits

sauc is billed per audio-second. `trim_voice` typically saves 0.5–5% on
long-form content (podcasts, lectures). For short clips (<30 s) trimming
often saves nothing — use `--skip-trim` to preserve pacing.

Rate limits are per-key. Parallel requests to sauc don't speed things up
(the queue is the bottleneck, not the wire); serial is by design.
