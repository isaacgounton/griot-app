"""Voice utility endpoints for the agents experience."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.services.media.transcription import get_transcription_service
from app.utils.auth import get_api_key, get_current_user


router = APIRouter(prefix="/speech-to-text", tags=["Agents"])


@router.post("", status_code=status.HTTP_200_OK)
async def speech_to_text(file: UploadFile = File(...), current_user: Dict[str, Any] = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must include a filename")

    suffix = Path(file.filename).suffix or ".wav"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            temp_path = tmp.name

        transcription_service = get_transcription_service()
        result = await transcription_service.transcribe(
            file_path=temp_path,
            include_text=True,
            include_srt=False,
            word_timestamps=False,
            include_segments=False,
        )

        text = result.get("text", "") if isinstance(result, dict) else ""
        return {"text": text}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
