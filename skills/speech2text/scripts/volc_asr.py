# -*- coding: utf-8 -*-
"""Volcengine sauc bigmodel_nostream WebSocket ASR client — vendored, self-contained.

Wire protocol matches ``volcengine-hermes-plugin/plugins/transcription/volcengine/``.
Endpoint / auth constants:

- Endpoint:  ``wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream``
- Auth:      ``X-Api-Key`` from ``VOLCENGINE_API_KEY`` (fallback ``ARK_API_KEY``)
- Resource:  ``X-Api-Resource-Id: volc.seedasr.sauc.duration``
- Framing:   full-client-request (gzip-JSON) → audio-only frames (positive seq)
             → final empty audio frame with negated seq.

Public surface used by read_voice.py:

- ``ASR_ENDPOINT``, ``DEFAULT_RESOURCE_ID`` — module constants
- ``_build_headers(resource_id=...)`` — headers dict for a session
- ``_run_asr_websocket(audio_bytes, headers=..., ...)`` async → transcript str
- ``_resolve_api_key()``, ``_prepare_wav_bytes(path)`` — helpers

Requires runtime deps: ``websockets`` (pip), ``ffmpeg`` (system, only for
``_prepare_wav_bytes`` — read_voice bypasses it and reads .wav directly).
"""
from __future__ import annotations

import gzip
import json
import os
import struct
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import websockets  # runtime dep


# ---------------------------------------------------------------------------
# Endpoint / auth constants
# ---------------------------------------------------------------------------

ASR_ENDPOINT = "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream"
DEFAULT_RESOURCE_ID = "volc.seedasr.sauc.duration"
DEFAULT_CHUNK_SIZE = 3200  # bytes — 100ms of 16kHz s16le mono. Server's
# per-packet timeout is 5s (error 45000081); we're well inside the window.


# ---------------------------------------------------------------------------
# Binary protocol constants (kept verbatim from upstream so wire-format tests
# apply as-is — see volcengine-hermes-plugin/.../protocol.py).
# ---------------------------------------------------------------------------

PROTOCOL_VERSION = 0x1
HEADER_SIZE_WORDS = 0x1

MESSAGE_TYPE_FULL_CLIENT_REQUEST = 0x1
MESSAGE_TYPE_AUDIO_ONLY_REQUEST = 0x2
MESSAGE_TYPE_FULL_SERVER_RESPONSE = 0x9
MESSAGE_TYPE_SERVER_ACK = 0xB
MESSAGE_TYPE_ERROR_RESPONSE = 0xF

FLAG_NO_SEQUENCE = 0x0
FLAG_POS_SEQUENCE = 0x1
FLAG_NEG_SEQUENCE = 0x2
FLAG_NEG_WITH_SEQUENCE = 0x3

MESSAGE_SERIALIZATION_RAW = 0x0
MESSAGE_SERIALIZATION_JSON = 0x1
MESSAGE_COMPRESSION_NONE = 0x0
MESSAGE_COMPRESSION_GZIP = 0x1
RESERVED = 0x0


def _header(
    message_type: int,
    *,
    flags: int = FLAG_NO_SEQUENCE,
    serialization: int = MESSAGE_SERIALIZATION_JSON,
    compression: int = MESSAGE_COMPRESSION_GZIP,
) -> bytes:
    return bytes([
        (PROTOCOL_VERSION << 4) | HEADER_SIZE_WORDS,
        (message_type << 4) | flags,
        (serialization << 4) | compression,
        RESERVED,
    ])


def build_full_client_request(payload: Dict[str, Any], *, sequence: int = 1) -> bytes:
    """Build a gzip-compressed JSON full-client request frame with sequence."""
    raw_payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    compressed_payload = gzip.compress(raw_payload)
    return b"".join([
        _header(
            MESSAGE_TYPE_FULL_CLIENT_REQUEST,
            flags=FLAG_POS_SEQUENCE if sequence >= 0 else FLAG_NEG_WITH_SEQUENCE,
            serialization=MESSAGE_SERIALIZATION_JSON,
            compression=MESSAGE_COMPRESSION_GZIP,
        ),
        struct.pack(">i", sequence),
        struct.pack(">I", len(compressed_payload)),
        compressed_payload,
    ])


def build_audio_only_request(
    audio: bytes,
    *,
    sequence: int,
    final: bool = False,
    compress: bool = False,
) -> bytes:
    """Build an ASR audio-only request frame.

    Volcengine ASR V3 expects audio chunks wrapped in AUDIO_ONLY_REQUEST frames,
    not naked websocket binary payloads. The final empty audio frame carries a
    negated sequence number to mark end-of-audio.
    """
    payload = gzip.compress(audio) if compress and audio else audio
    final_sequence = -abs(sequence) if final else sequence
    return b"".join([
        _header(
            MESSAGE_TYPE_AUDIO_ONLY_REQUEST,
            flags=FLAG_NEG_WITH_SEQUENCE if final else FLAG_POS_SEQUENCE,
            serialization=MESSAGE_SERIALIZATION_RAW,
            compression=MESSAGE_COMPRESSION_GZIP if compress and audio else MESSAGE_COMPRESSION_NONE,
        ),
        struct.pack(">i", final_sequence),
        struct.pack(">I", len(payload)),
        payload,
    ])


def parse_server_response(message: bytes) -> Dict[str, Any]:
    """Parse a Volcengine ASR V3 server frame.

    Handles full server responses, server ACKs, error frames, sequence flags,
    gzip payloads, and last-package markers.
    """
    if len(message) < 4:
        raise ValueError("Volcengine ASR response is too short")

    header_size = message[0] & 0x0F
    header_bytes = header_size * 4
    if len(message) < header_bytes:
        raise ValueError("Volcengine ASR response has an invalid header")

    message_type = message[1] >> 4
    flags = message[1] & 0x0F
    serialization = message[2] >> 4
    compression = message[2] & 0x0F
    payload = message[header_bytes:]
    result: Dict[str, Any] = {"is_last_package": bool(flags & FLAG_NEG_SEQUENCE)}
    payload_message: Any = None
    payload_size = 0

    if message_type == MESSAGE_TYPE_FULL_SERVER_RESPONSE:
        if flags & FLAG_POS_SEQUENCE:
            if len(payload) < 4:
                raise ValueError("Volcengine ASR response is missing sequence")
            sequence = struct.unpack(">i", payload[:4])[0]
            result["sequence"] = sequence
            if sequence < 0:
                result["is_last_package"] = True
            payload = payload[4:]
        if len(payload) < 4:
            raise ValueError("Volcengine ASR response is missing payload size")
        payload_size = struct.unpack(">i", payload[:4])[0]
        payload_message = payload[4:4 + abs(payload_size)]

    elif message_type == MESSAGE_TYPE_SERVER_ACK:
        if len(payload) < 4:
            return result
        sequence = struct.unpack(">i", payload[:4])[0]
        result["sequence"] = sequence
        if sequence < 0:
            result["is_last_package"] = True
        payload = payload[4:]
        if len(payload) >= 4:
            payload_size = struct.unpack(">I", payload[:4])[0]
            payload_message = payload[4:4 + payload_size]
        else:
            return result

    elif message_type == MESSAGE_TYPE_ERROR_RESPONSE:
        if len(payload) < 8:
            raise ValueError("Volcengine ASR error response is missing code or payload size")
        result["code"] = struct.unpack(">I", payload[:4])[0]
        payload_size = struct.unpack(">I", payload[4:8])[0]
        payload_message = payload[8:8 + payload_size]

    else:
        raise ValueError(f"Unsupported Volcengine ASR message type: {message_type}")

    if payload_message is None:
        return result
    if compression == MESSAGE_COMPRESSION_GZIP:
        payload_message = gzip.decompress(payload_message)
    if serialization == MESSAGE_SERIALIZATION_JSON:
        payload_message = json.loads(payload_message.decode("utf-8"))
    elif serialization != MESSAGE_SERIALIZATION_RAW:
        payload_message = str(payload_message)

    result["message"] = payload_message
    result["size"] = payload_size
    return result


# ---------------------------------------------------------------------------
# Auth / headers
# ---------------------------------------------------------------------------

def _prepare_wav_bytes(src: Path) -> bytes:
    """ffmpeg-convert any audio file to mono 16kHz pcm_s16le wav, return raw bytes.

    Kept for completeness; ``read_voice.py`` bypasses this and reads .wav files
    directly (voice_pipeline runs ffmpeg once up-front).
    """
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is required to transcode audio to mono 16kHz pcm_s16le WAV "
            "before uploading to Volc ASR."
        )
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(src),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            "-f", "wav",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout


def _resolve_api_key() -> str:
    """Return the Volcengine API key.

    Precedence:

        VOLCENGINE_API_KEY > ARK_API_KEY > "" (empty = not configured).

    Empty-string env values are treated as "not set".
    """
    for name in ("VOLCENGINE_API_KEY", "ARK_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _build_headers(*, resource_id: str = DEFAULT_RESOURCE_ID) -> Dict[str, str]:
    """Build the headers the ASR gateway requires."""
    api_key = _resolve_api_key()
    return {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Connect-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1",  # Volc doc: fixed -1 for sauc
    }


# ---------------------------------------------------------------------------
# Transcript extraction (server response shape varies)
# ---------------------------------------------------------------------------

def _extract_transcript(response: Any) -> str:
    """Best-effort pull of the recognised text out of a parsed server frame.

    Volcengine's V3 response shape has drifted a few times: sometimes the text
    lives at ``result.text``, sometimes at ``result.utterances[*].text``,
    sometimes capitalised. Walk the structure until we find something.
    """
    if not isinstance(response, dict):
        return ""

    message = response.get("message")
    if isinstance(message, dict):
        nested = _extract_transcript(message)
        if nested:
            return nested

    result = response.get("result") or response.get("Result") or response
    if isinstance(result, list):
        return "".join(
            _extract_transcript(item) for item in result if isinstance(item, dict)
        )
    if isinstance(result, dict):
        for key in ("text", "Text", "transcript", "Transcript"):
            value = result.get(key)
            if value:
                return str(value)
        utterances = result.get("utterances") or result.get("Utterances")
        if isinstance(utterances, list):
            return "".join(
                str(item.get("text") or item.get("Text") or "")
                for item in utterances
                if isinstance(item, dict)
            )
    return ""


def _build_full_client_payload(*, language: Optional[str] = None) -> Dict[str, Any]:
    """Initial JSON payload sent as the full-client-request frame.

    - ``language: auto`` (default — omit the field entirely for auto detection)
    - ``enable_itn: true``   digits normalisation (\"三分之一\" -> \"1/3\")
    - ``enable_punc: true``  auto punctuation
    - ``result_type: full``
    """
    payload: Dict[str, Any] = {
        "user": {"uid": "speech2text"},
        "audio": {
            "format": "wav",
            "codec": "raw",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
            "result_type": "full",
        },
    }
    if language:
        payload["audio"]["language"] = language
    return payload


async def _run_asr_websocket(
    audio_bytes: bytes,
    *,
    headers: Dict[str, str],
    endpoint: str = ASR_ENDPOINT,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    language: Optional[str] = None,
) -> str:
    """Open a WebSocket to Volcengine ASR V3 and return the recognised text.

    Frames sent, in order:
        1. full-client-request (gzip-JSON, sequence=1)
        2. audio-only frames (sequence=2..N)
        3. final audio-only frame with empty body + negated sequence
    """
    transcript = ""
    last_response: Dict[str, Any] = {}
    request_id = headers.get("X-Api-Request-Id", "?")

    async with websockets.connect(
        endpoint,
        additional_headers=headers,
        max_size=2**24,
        # Disable client-side WebSocket-level keepalive pings. The sauc
        # bigmodel_nostream endpoint does not reliably return pong frames
        # while it is buffering audio for a long send burst — the server
        # tracks liveness via its own application-layer sequence-frame
        # protocol, not via ws PING/PONG. Leaving the default 20s ping
        # interval on caused reproducible client-side 1011 "keepalive ping
        # timeout" closes on ≥25s clips.
        ping_interval=None,
    ) as websocket:
        # Serial send-all then recv-all — exact shape of upstream provider
        # which is known to work. Concurrent producer/consumer + pacing were
        # dead-ends caused by our earlier incorrect assumption of format=mp3.
        import asyncio

        sequence = 1
        await websocket.send(
            build_full_client_request(
                _build_full_client_payload(language=language),
                sequence=sequence,
            )
        )
        offset = 0
        total = len(audio_bytes)
        while offset < total:
            chunk = audio_bytes[offset:offset + chunk_size]
            offset += chunk_size
            sequence += 1
            await websocket.send(
                build_audio_only_request(chunk, sequence=sequence, final=False)
            )
            await asyncio.sleep(0)  # yield so keepalive/recv tasks can run
        sequence += 1
        await websocket.send(
            build_audio_only_request(b"", sequence=sequence, final=True)
        )

        while True:
            response = parse_server_response(await websocket.recv())
            last_response = response
            if response.get("code") and int(response["code"]) != 0:
                message = response.get("message") or {}
                raise RuntimeError(
                    f"ASR API Error [{response['code']}]: {message}; "
                    f"request_id={request_id}"
                )
            candidate = _extract_transcript(response)
            if candidate:
                transcript = candidate
            if response.get("is_last_package"):
                break

    if not transcript:
        transcript = _extract_transcript(last_response)

    return transcript
