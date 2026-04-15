"""
Routes to manage agent user preferences.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.agents.preferences_service import (
    agent_preferences_service,
    DEFAULT_PREFERENCES,
)
from app.utils.auth import get_api_key, get_current_user


router = APIRouter(prefix="/users/preferences", tags=["Agents"])


class PreferenceUpdateRequest(BaseModel):
    preferences: dict


@router.get("")
async def get_preferences(current_user: Dict[str, Any] = Depends(get_current_user)):
    preferences = await agent_preferences_service.get_preferences(current_user["user_id"])
    return preferences


@router.put("", status_code=status.HTTP_200_OK)
async def update_preferences(payload: PreferenceUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        updated = await agent_preferences_service.update_preferences(current_user["user_id"], payload.preferences)
        return updated
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
