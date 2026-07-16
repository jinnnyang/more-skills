# Volcengine sauc bigmodel_nostream — Wire Protocol Cheat Sheet

**Canonical implementation:** `scripts/volc_asr.py` in this skill.

## Endpoint & Auth

```
wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream

Headers (all required):
  X-Api-Key: <VOLCENGINE_API_KEY>
  X-Api-Resource-Id: volc.seedasr.sauc.duration
  X-Api-Request-Id: <uuid4-per-session>
  X-Api-Connect-Id: <uuid4-per-session>
  X-Api-Sequence: -1
```

## WebSocket-Level Behaviour

**MUST set `ping_interval=None`** on `websockets.connect()`. The default
20s client-side keepalive ping expires while the server is buffering a
long send burst — server never returns pong within 20s. Server tracks
liveness via its own application-layer sequence-frame protocol, not
WebSocket-level pings.

## Frame Layout (all frames)

```
| byte 0                            | byte 1              | byte 2             | byte 3 |
| PROTOCOL_VERSION (4b) | HDR_SIZE  | MSG_TYPE | FLAGS    | SERIAL | COMPRESS  | RSVD   |
```

- `PROTOCOL_VERSION = 0x1`
- `HEADER_SIZE_WORDS = 0x1` (header is exactly 4 bytes)
- `MSG_TYPE`:
  - `0x1` = full-client-request (initial JSON config)
  - `0x2` = audio-only-request (audio chunk)
  - `0x9` = full-server-response (transcript / partial)
  - `0xB` = server-ack
  - `0xF` = error-response
- `FLAGS`:
  - `0x0` no sequence
  - `0x1` positive sequence
  - `0x2` negative sequence (last package indicator)
  - `0x3` negative-with-sequence (final frame from client)
- `SERIAL`: `0x0` raw / `0x1` json
- `COMPRESS`: `0x0` none / `0x1` gzip

## Send Order (client → server)

1. **full-client-request** (`seq=1`, json+gzip):
   ```json
   {
     "user": {"uid": "speech2text"},
     "audio": {"format": "wav", "codec": "raw", "rate": 16000, "bits": 16, "channel": 1},
     "request": {
       "model_name": "bigmodel",
       "enable_itn": true,
       "enable_punc": true,
       "result_type": "full"
     }
   }
   ```

2. **audio-only-requests** (`seq=2, 3, …`, raw+none):
   - Chunk size: **3200 bytes** = 100 ms of 16kHz mono s16le. Server per-packet
     timeout is 5 s (error `45000081`) — 100 ms leaves generous headroom.
   - `await asyncio.sleep(0)` after every send so keepalive/recv tasks yield.

3. **final empty audio-only** (`seq = -N`, raw+none, empty body, flag = 0x3):
   marks end-of-audio.

After step 3, `recv()` in a loop until a frame has `is_last_package=True`.

## Receive & Parse

- Server response payload: `[4-byte seq][4-byte size][payload bytes]`.
- If `MSG_TYPE == 0xF` (error): `[4-byte code][4-byte size][payload]`.
- Transcript text lives (at various shape versions) at one of:
  `result.text` / `result.Text` / `result.transcript` / `result.utterances[*].text`
- `_extract_transcript()` walks the tree and pulls whichever is populated.

## Payload Shape Reference (JSON keys sauc has actually emitted)

- `result.text` (str) — full transcript so far
- `result.utterances[].text` (list of str) — sentence-segmented
- `result.additions.*` — per-utterance metadata (start_time, end_time, confidence)
- `result.text_seg[]` — word-level segmentation (rarely used)

The client only needs `text` — everything else is bonus data.

## Error Codes Seen in the Wild

| Code       | Meaning                             | Action |
|------------|-------------------------------------|--------|
| `45000010` | Invalid X-Api-Key                   | Wrong key type or wrong endpoint prefix |
| `45000030` | Resource not granted                | Key doesn't have sauc access — contact Volc |
| `45000081` | Waiting-next-packet timeout         | Client stalled >5 s between audio frames — check yield / chunk size |
| `1011`     | (WebSocket close) keepalive timeout | Client-side ping; disable with `ping_interval=None` |

## Alternate Endpoints (NOT USED — recorded for future changes)

- `https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash` — HTTP
  POST single-shot, needs different key (X-Api-App-Key + X-Api-Access-Key) and
  `volc.bigasr.auc_turbo` resource permission.
- `https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit` + `/query` — HTTP
  async submit/poll, same permission constraint.

Both return 403 for Coding-Plan keys. See `troubleshooting.md` for the
resource-permission decision matrix.
