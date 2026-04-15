"""Studio — Scene management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import uuid

from app.utils.auth import get_current_user


def _uid(user: dict) -> str:
    """Extract user ID from auth dict (works for both JWT and API key auth)."""
    return str(user.get("id") or user.get("user_id") or "anonymous")
from app.services.studio.project_service import studio_project_service
from app.services.studio.models import SceneCreateRequest, SceneUpdateRequest, ReorderScenesRequest

router = APIRouter(prefix="/projects/{project_id}/scenes")


@router.post("")
async def add_scene(project_id: str, data: SceneCreateRequest, user=Depends(get_current_user)):
    scene = await studio_project_service.add_scene(project_id, user_id=_uid(user), data=data)
    if not scene:
        raise HTTPException(status_code=404, detail="Project not found")
    return scene


@router.patch("/{scene_id}")
async def update_scene(project_id: str, scene_id: str, data: SceneUpdateRequest, user=Depends(get_current_user)):
    scene = await studio_project_service.update_scene(project_id, scene_id, user_id=_uid(user), data=data)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.delete("/{scene_id}")
async def delete_scene(project_id: str, scene_id: str, user=Depends(get_current_user)):
    deleted = await studio_project_service.delete_scene(project_id, scene_id, user_id=_uid(user))
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"ok": True}


@router.post("/reorder")
async def reorder_scenes(project_id: str, data: ReorderScenesRequest, user=Depends(get_current_user)):
    scenes = await studio_project_service.reorder_scenes(project_id, user_id=_uid(user), scene_ids=data.scene_ids)
    if not scenes:
        raise HTTPException(status_code=404, detail="Project not found")
    return scenes


@router.post("/{scene_id}/upload-media")
async def upload_scene_media(project_id: str, scene_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload a user media file for a scene."""
    from app.services.s3.s3 import s3_service
    import tempfile
    import os

    contents = await file.read()
    ext = os.path.splitext(file.filename or "media")[1] or ".mp4"
    tmp_path = tempfile.mktemp(suffix=ext)
    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)
        s3_key = f"studio/uploads/{project_id}/{scene_id}_{uuid.uuid4().hex[:8]}{ext}"
        media_url = await s3_service.upload_file(tmp_path, s3_key)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    scene = await studio_project_service.update_scene(
        project_id, scene_id, user_id=_uid(user),
        data=SceneUpdateRequest(media_url=media_url, media_source_type="user_upload"),
    )
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene
