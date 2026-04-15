"""Voice Activity Detection endpoints proxied to Speaches sidecar."""

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.speaches.speaches_client import speaches_client

router = APIRouter()


@router.post("/vad")
async def detect_speech(file: UploadFile = File(...)) -> list[dict]:
    """Detect speech timestamps in an audio file using Speaches VAD.

    Upload an audio file and get back a list of speech segments with
    start/end timestamps.
    """
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)

        return await speaches_client.detect_speech_timestamps(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speaches VAD failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
