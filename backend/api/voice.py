"""Voice proxy routes — Deepgram STT/TTS without exposing API key to browser."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from tools.deepgram import DeepgramError, synthesize_speech, transcribe_audio

router = APIRouter(tags=["voice"])


class TtsRequest(BaseModel):
    text: str


class SttResponse(BaseModel):
    transcript: str


@router.post("/voice/stt", response_model=SttResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    content_type = audio.content_type or "audio/webm"
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio payload")
    try:
        transcript = await transcribe_audio(data, content_type=content_type)
    except DeepgramError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SttResponse(transcript=transcript)


@router.post("/voice/tts")
async def text_to_speech(payload: TtsRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        audio = await synthesize_speech(text)
    except DeepgramError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not audio:
        raise HTTPException(status_code=503, detail="DEEPGRAM_API_KEY not configured")
    return Response(content=audio, media_type="audio/mpeg")
