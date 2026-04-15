"""Studio — Generation and export routes (async jobs)."""
from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException

from app.utils.auth import get_current_user


def _uid(user: dict) -> str:
    """Extract user ID from auth dict (works for both JWT and API key auth)."""
    return str(user.get("id") or user.get("user_id") or "anonymous")
from app.models import JobType, JobStatus
from app.services.studio.project_service import studio_project_service
from app.services.studio.models import (
    GenerateTTSRequest,
    GenerateMediaRequest,
    GenerateAIScenesRequest,
    ExportRequest,
    JobStatusResponse,
)

router = APIRouter(prefix="/projects/{project_id}")


def _get_job_queue():
    from app.services.job_queue.job_queue import job_queue
    return job_queue


# ── TTS Generation ────────────────────────────────────────────────────────────

@router.post("/generate-tts")
async def generate_tts(project_id: str, data: GenerateTTSRequest, user=Depends(get_current_user)):
    """Generate TTS audio + word timestamps for scenes."""
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get scenes to process
    scenes = await studio_project_service.get_raw_scenes(project_id, _uid(user), data.scene_ids)
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to process")

    job_id = str(uuid.uuid4())
    job_queue = _get_job_queue()

    async def _process_tts(_job_id: str, _data: dict[str, Any]) -> dict[str, Any]:
        from app.services.studio.tts_pipeline import generate_project_tts

        results = await generate_project_tts(
            project_id=project_id,
            scenes=scenes,
            settings=project.settings,
        )

        # Update each scene in DB
        for r in results:
            if r.get("audio_url"):
                await studio_project_service.update_scene_after_tts(
                    scene_id=r["scene_id"],
                    audio_url=r["audio_url"],
                    audio_duration=r["audio_duration"],
                    word_timestamps=r["word_timestamps"],
                )

        return {
            "scenes_processed": len(results),
            "results": results,
        }

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.STUDIO_TTS_GENERATION,
        process_func=_process_tts,
        data={"project_id": project_id},
    )

    return {"job_id": job_id, "status": "processing", "scenes_count": len(scenes)}


# ── Media Generation ──────────────────────────────────────────────────────────

@router.post("/generate-media")
async def generate_media(project_id: str, data: GenerateMediaRequest, user=Depends(get_current_user)):
    """Source/generate media for scenes."""
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = await studio_project_service.get_raw_scenes(project_id, _uid(user), data.scene_ids)
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to process")

    job_id = str(uuid.uuid4())
    job_queue = _get_job_queue()

    async def _process_media(_job_id: str, _data: dict[str, Any]) -> dict[str, Any]:
        from app.services.studio.media_pipeline import source_project_media

        results = await source_project_media(scenes=scenes, settings=project.settings)

        # Update scenes in DB
        for r in results:
            if r.get("media_url"):
                await studio_project_service.update_scene_after_media(
                    scene_id=r["scene_id"],
                    media_url=r["media_url"],
                    media_provider=r["media_provider"],
                )

        return {
            "scenes_processed": len(results),
            "results": results,
        }

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.STUDIO_MEDIA_GENERATION,
        process_func=_process_media,
        data={"project_id": project_id},
    )

    return {"job_id": job_id, "status": "processing", "scenes_count": len(scenes)}


# ── AI Scene Generation ──────────────────────────────────────────────────────

@router.post("/generate-scenes")
async def generate_ai_scenes(project_id: str, data: GenerateAIScenesRequest, user=Depends(get_current_user)):
    """Let AI generate scenes from a topic or script."""
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_id = str(uuid.uuid4())
    job_queue = _get_job_queue()

    async def _process_ai_scenes(_job_id: str, _data: dict[str, Any]) -> dict[str, Any]:
        from app.services.studio.ai_scene_generator import generate_scenes_from_topic

        scenes_data = await generate_scenes_from_topic(
            topic=data.topic,
            script=data.script,
            scene_count=data.scene_count,
            language=data.language,
            settings=project.settings,
        )

        # Create scenes in project
        from app.services.studio.models import SceneCreateRequest
        created_scenes = []
        for i, scene_data in enumerate(scenes_data):
            scene = await studio_project_service.add_scene(
                project_id=project_id,
                user_id=_uid(user),
                data=SceneCreateRequest(
                    script_text=scene_data.get("text", ""),
                    media_search_terms=scene_data.get("search_terms", []),
                    duration=scene_data.get("duration", 3.0),
                ),
            )
            if scene:
                created_scenes.append(scene.model_dump())

        return {"scenes_created": len(created_scenes), "scenes": created_scenes}

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.STUDIO_AI_SCENES,
        process_func=_process_ai_scenes,
        data={"project_id": project_id},
    )

    return {"job_id": job_id, "status": "processing"}


# ── Export ─────────────────────────────────────────────────────────────────────

@router.post("/export")
async def export_video(project_id: str, data: ExportRequest, user=Depends(get_current_user)):
    """Export the final video."""
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.scenes:
        raise HTTPException(status_code=400, detail="Project has no scenes")

    scenes = await studio_project_service.get_raw_scenes(project_id, _uid(user))
    audio_tracks = [t.model_dump() for t in project.audio_tracks] if project.audio_tracks else []
    old_video_url = project.final_video_url  # Track for cleanup on re-export

    job_id = str(uuid.uuid4())
    job_queue = _get_job_queue()

    async def _process_export(_job_id: str, _data: dict[str, Any]) -> dict[str, Any]:
        from app.services.studio.export_pipeline import export_project
        from app.database import StudioProjectStatus

        await studio_project_service.update_project_status(
            project_id, StudioProjectStatus.GENERATING,
        )

        try:
            result = await export_project(
                project_id=project_id,
                scenes=scenes,
                audio_tracks=audio_tracks,
                settings=project.settings,
                include_captions=data.include_captions,
                include_background_music=data.include_background_music,
                caption_style_override=data.caption_style_override,
                caption_properties_override=data.caption_properties_override,
            )

            await studio_project_service.update_project_status(
                project_id, StudioProjectStatus.COMPLETED,
                final_video_url=result["video_url"],
                final_video_duration=result["duration"],
                export_job_id=job_id,
            )

            # Clean up old S3 export file on re-export
            if old_video_url and old_video_url != result["video_url"]:
                try:
                    from urllib.parse import urlparse
                    from app.services.s3.s3 import s3_service
                    old_key = urlparse(old_video_url).path.lstrip("/")
                    if old_key:
                        await s3_service.delete_file(old_key)
                        logger.info(f"Cleaned up old export: {old_key}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to clean up old export {old_video_url}: {cleanup_err}")

            return result
        except Exception as e:
            await studio_project_service.update_project_status(
                project_id, StudioProjectStatus.FAILED,
            )
            raise

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.STUDIO_EXPORT,
        process_func=_process_export,
        data={"project_id": project_id},
    )

    return {"job_id": job_id, "status": "processing", "scenes_count": len(scenes)}


# ── Stock Media Search (sync — returns results for user to pick) ──────────────

@router.post("/scenes/{scene_id}/search-media")
async def search_scene_media(
    project_id: str,
    scene_id: str,
    user=Depends(get_current_user),
):
    """Search stock media for a scene and return all results for user selection."""
    project = await studio_project_service.get_project(project_id, user_id=_uid(user))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = await studio_project_service.get_raw_scenes(project_id, _uid(user), [scene_id])
    if not scenes:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene = scenes[0]
    source_type = scene.get("media_source_type") or project.settings.get("media_type", "video")
    search_terms = scene.get("media_search_terms") or []
    duration = scene.get("duration", 5.0)
    provider = project.settings.get("footage_provider", "pexels")

    # Derive orientation from project resolution
    resolution = project.settings.get("resolution", "1080x1920")
    try:
        w, h = map(int, resolution.split("x"))
        orientation = "portrait" if h > w else "landscape" if w > h else "square"
    except (ValueError, AttributeError):
        orientation = "portrait"

    # Auto-generate search terms from script if none provided
    if not search_terms and scene.get("script_text"):
        from app.services.studio.ai_scene_generator import _extract_search_terms_simple
        search_terms = _extract_search_terms_simple(scene["script_text"])

    from app.services.studio.media_pipeline import search_stock_results
    results = await search_stock_results(
        search_terms=search_terms,
        source_type=source_type,
        provider=provider,
        duration=duration,
        orientation=orientation,
    )

    return {"results": results, "query": " ".join(search_terms[:3]), "provider": provider}


# ── Job Status ─────────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
async def get_job_status(project_id: str, job_id: str, user=Depends(get_current_user)):
    """Check status of a studio job (TTS, media, export)."""
    job_queue = _get_job_queue()
    job_info = await job_queue.get_job_info(job_id)

    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")

    status_str = job_info.status.value if hasattr(job_info.status, "value") else str(job_info.status)

    return JobStatusResponse(
        job_id=job_id,
        status=status_str,
        progress=str(job_info.progress) if job_info.progress else None,
        result=job_info.result,
        error=job_info.error,
    )
