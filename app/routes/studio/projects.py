"""Studio — Project CRUD routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.utils.auth import get_current_user


def _uid(user: dict) -> str:
    """Extract user ID from auth dict (works for both JWT and API key auth)."""
    return str(user.get("id") or user.get("user_id") or "anonymous")
from app.services.studio.project_service import studio_project_service
from app.services.studio.models import (
    CreateProjectRequest,
    UpdateProjectRequest,
    AudioTrackCreateRequest,
    AudioTrackUpdateRequest,
)

router = APIRouter(prefix="/projects")


@router.post("")
async def create_project(data: CreateProjectRequest, user=Depends(get_current_user)):
    return await studio_project_service.create_project(user_id=_uid(user), data=data)


@router.get("")
async def list_projects(skip: int = 0, limit: int = 50, user=Depends(get_current_user)):
    return await studio_project_service.list_projects(user_id=_uid(user), skip=skip, limit=limit)


@router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(get_current_user)):
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}")
async def update_project(project_id: str, data: UpdateProjectRequest, user=Depends(get_current_user)):
    project = await studio_project_service.update_project(project_id, user_id=_uid(user), data=data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, user=Depends(get_current_user)):
    deleted = await studio_project_service.delete_project(project_id, user_id=_uid(user))
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


# ── Audio Tracks ──────────────────────────────────────────────────────────────

@router.post("/{project_id}/audio-tracks")
async def add_audio_track(project_id: str, data: AudioTrackCreateRequest, user=Depends(get_current_user)):
    track = await studio_project_service.add_audio_track(project_id, user_id=_uid(user), data=data)
    if not track:
        raise HTTPException(status_code=404, detail="Project not found")
    return track


@router.patch("/{project_id}/audio-tracks/{track_id}")
async def update_audio_track(project_id: str, track_id: str, data: AudioTrackUpdateRequest, user=Depends(get_current_user)):
    track = await studio_project_service.update_audio_track(project_id, track_id, user_id=_uid(user), data=data)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.delete("/{project_id}/audio-tracks/{track_id}")
async def delete_audio_track(project_id: str, track_id: str, user=Depends(get_current_user)):
    deleted = await studio_project_service.delete_audio_track(project_id, track_id, user_id=_uid(user))
    if not deleted:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"ok": True}
