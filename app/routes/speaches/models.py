"""Model discovery and management endpoints proxied to Speaches sidecar."""

from typing import Any
from fastapi import APIRouter, HTTPException

from app.services.speaches.speaches_client import speaches_client

router = APIRouter()


@router.get("/models")
async def list_models() -> list[dict]:
    """List all models available in the Speaches sidecar."""
    try:
        return await speaches_client.get_models()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speaches unavailable: {e}")


@router.get("/voices")
async def list_voices() -> list[dict]:
    """List all TTS voices available in the Speaches sidecar."""
    try:
        return await speaches_client.get_voices()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speaches unavailable: {e}")


@router.post("/models/{model_id:path}")
async def download_model(model_id: str) -> dict[str, Any]:
    """Request the Speaches sidecar to download a model."""
    try:
        return await speaches_client.download_model(model_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speaches unavailable: {e}")


@router.delete("/models/{model_id:path}")
async def delete_model(model_id: str) -> dict[str, Any]:
    """Delete a model from the Speaches sidecar."""
    try:
        return await speaches_client.delete_model(model_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speaches unavailable: {e}")


@router.get("/health")
async def speaches_health() -> dict[str, Any]:
    """Check Speaches sidecar health."""
    healthy = await speaches_client.health_check()
    if healthy:
        return {"status": "ok", "service": "speaches"}
    raise HTTPException(status_code=503, detail="Speaches sidecar is not healthy")
