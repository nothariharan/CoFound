"""Deepgram STT/TTS helpers — API key stays server-side."""

from __future__ import annotations

import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_STT_MODEL = "nova-2"
DEFAULT_TTS_MODEL = "aura-asteria-en"


class DeepgramError(RuntimeError):
    pass


def _api_key() -> str:
    return os.getenv("DEEPGRAM_API_KEY", "").strip()


async def transcribe_audio(audio_bytes: bytes, content_type: str = "audio/webm") -> str:
    key = _api_key()
    if not key:
        return ""
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, content_type, key)


async def synthesize_speech(text: str) -> bytes:
    key = _api_key()
    if not key:
        return b""
    return await asyncio.to_thread(_synthesize_sync, text, key)


def _transcribe_sync(audio_bytes: bytes, content_type: str, key: str) -> str:
    params = urlencode({"model": DEFAULT_STT_MODEL, "smart_format": "true"})
    url = f"https://api.deepgram.com/v1/listen?{params}"
    request = Request(
        url,
        data=audio_bytes,
        headers={
            "Authorization": f"Token {key}",
            "Content-Type": content_type,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise DeepgramError(f"Deepgram STT HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise DeepgramError(f"Deepgram STT network error: {exc}") from exc

    try:
        return str(data["results"]["channels"][0]["alternatives"][0]["transcript"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise DeepgramError(f"Unexpected Deepgram STT response: {data}") from exc


def _synthesize_sync(text: str, key: str) -> bytes:
    payload = json.dumps({"text": text.strip()}).encode("utf-8")
    params = urlencode({"model": DEFAULT_TTS_MODEL})
    url = f"https://api.deepgram.com/v1/speak?{params}"
    request = Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Token {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:  # noqa: S310
            return response.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise DeepgramError(f"Deepgram TTS HTTP {exc.code}: {body[:500]}") from exc
    except URLError as exc:
        raise DeepgramError(f"Deepgram TTS network error: {exc}") from exc
