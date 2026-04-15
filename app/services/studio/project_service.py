"""CRUD service for Studio V2 projects, scenes, and audio tracks."""
from __future__ import annotations

import uuid
from typing import Any

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import (
    database_service,
    StudioProject,
    StudioScene,
    StudioAudioTrack,
    StudioProjectStatus,
    SceneStatus,
)
from app.services.studio.models import (
    CreateProjectRequest,
    UpdateProjectRequest,
    SceneCreateRequest,
    SceneUpdateRequest,
    AudioTrackCreateRequest,
    AudioTrackUpdateRequest,
    ProjectResponse,
    ProjectListItem,
    SceneResponse,
    AudioTrackResponse,
    WordTimestampDTO,
    DEFAULT_SETTINGS,
)


def _scene_to_response(scene: StudioScene) -> SceneResponse:
    wts = None
    if scene.word_timestamps:
        wts = [WordTimestampDTO(**w) for w in scene.word_timestamps]
    return SceneResponse(
        id=scene.id,
        order_index=scene.order_index,
        script_text=scene.script_text,
        status=scene.status.value if hasattr(scene.status, "value") else scene.status,
        tts_audio_url=scene.tts_audio_url,
        tts_audio_duration=scene.tts_audio_duration,
        word_timestamps=wts,
        media_source_type=scene.media_source_type,
        media_url=scene.media_url,
        media_search_terms=scene.media_search_terms,
        media_prompt=scene.media_prompt,
        media_provider=scene.media_provider,
        start_time=scene.start_time,
        duration=scene.duration,
        transition_type=scene.transition_type,
        transition_duration=scene.transition_duration,
        preview_url=scene.preview_url,
        thumbnail_url=scene.thumbnail_url,
    )


def _track_to_response(track: StudioAudioTrack) -> AudioTrackResponse:
    return AudioTrackResponse(
        id=track.id,
        track_type=track.track_type.value if hasattr(track.track_type, "value") else track.track_type,
        name=track.name,
        audio_url=track.audio_url,
        start_time=track.start_time,
        duration=track.duration,
        volume=track.volume,
        fade_in=track.fade_in,
        fade_out=track.fade_out,
    )


def _project_to_response(project: StudioProject) -> ProjectResponse:
    scenes = sorted(project.scenes, key=lambda s: s.order_index)
    total_dur = sum(s.duration for s in scenes)
    # Use first scene thumbnail as project thumbnail
    thumb = next((s.thumbnail_url for s in scenes if s.thumbnail_url), None)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status.value if hasattr(project.status, "value") else project.status,
        settings=project.settings or DEFAULT_SETTINGS.copy(),
        scenes=[_scene_to_response(s) for s in scenes],
        audio_tracks=[_track_to_response(t) for t in project.audio_tracks],
        total_duration=total_dur,
        final_video_url=project.final_video_url,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


class StudioProjectService:
    """CRUD operations for studio projects, scenes, and audio tracks."""

    # ── Project CRUD ──────────────────────────────────────────────────────

    async def create_project(self, user_id: str | int, data: CreateProjectRequest) -> ProjectResponse:
        async for session in database_service.get_session():
            project = StudioProject(
                id=str(uuid.uuid4()),
                name=data.name,
                description=data.description,
                settings=data.settings,
                user_id=user_id,
                status=StudioProjectStatus.DRAFT,
            )
            session.add(project)
            await session.commit()
            await session.refresh(project, attribute_names=["scenes", "audio_tracks"])
            return _project_to_response(project)

    async def get_project(self, project_id: str, user_id: str | int) -> ProjectResponse | None:
        async for session in database_service.get_session():
            result = await session.execute(
                select(StudioProject)
                .options(selectinload(StudioProject.scenes), selectinload(StudioProject.audio_tracks))
                .where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return None
            return _project_to_response(project)

    async def list_projects(self, user_id: str | int, skip: int = 0, limit: int = 50) -> list[ProjectListItem]:
        async for session in database_service.get_session():
            result = await session.execute(
                select(StudioProject)
                .options(selectinload(StudioProject.scenes))
                .where(StudioProject.user_id == user_id)
                .order_by(StudioProject.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            projects = result.scalars().all()
            items = []
            for p in projects:
                scenes = sorted(p.scenes, key=lambda s: s.order_index)
                thumb = next((s.thumbnail_url for s in scenes if s.thumbnail_url), None)
                items.append(ProjectListItem(
                    id=p.id,
                    name=p.name,
                    status=p.status.value if hasattr(p.status, "value") else p.status,
                    scene_count=len(scenes),
                    total_duration=sum(s.duration for s in scenes),
                    thumbnail_url=thumb,
                    created_at=p.created_at.isoformat(),
                    updated_at=p.updated_at.isoformat(),
                ))
            return items

    async def update_project(self, project_id: str, user_id: str | int, data: UpdateProjectRequest) -> ProjectResponse | None:
        async for session in database_service.get_session():
            result = await session.execute(
                select(StudioProject)
                .options(selectinload(StudioProject.scenes), selectinload(StudioProject.audio_tracks))
                .where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return None
            if data.name is not None:
                project.name = data.name
            if data.description is not None:
                project.description = data.description
            if data.settings is not None:
                # Merge settings (don't replace entirely — allow partial updates)
                merged = {**(project.settings or {}), **data.settings}
                project.settings = merged
            await session.commit()
            await session.refresh(project, attribute_names=["scenes", "audio_tracks"])
            return _project_to_response(project)

    async def delete_project(self, project_id: str, user_id: str | int) -> bool:
        async for session in database_service.get_session():
            result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                return False
            await session.delete(project)
            await session.commit()
            return True

    # ── Scene CRUD ────────────────────────────────────────────────────────

    async def add_scene(self, project_id: str, user_id: str | int, data: SceneCreateRequest) -> SceneResponse | None:
        async for session in database_service.get_session():
            # Verify ownership
            proj = await session.execute(
                select(StudioProject)
                .options(selectinload(StudioProject.scenes))
                .where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            project = proj.scalar_one_or_none()
            if not project:
                return None

            # Determine order_index
            if data.after_index is not None:
                new_index = data.after_index + 1
                # Shift subsequent scenes
                for s in project.scenes:
                    if s.order_index >= new_index:
                        s.order_index += 1
            else:
                new_index = len(project.scenes)

            status = SceneStatus.SCRIPTED if data.script_text.strip() else SceneStatus.EMPTY

            scene = StudioScene(
                id=str(uuid.uuid4()),
                studio_project_id=project_id,
                order_index=new_index,
                script_text=data.script_text,
                status=status,
                media_source_type=data.media_source_type,
                media_search_terms=data.media_search_terms,
                media_prompt=data.media_prompt,
                media_url=data.media_url,
                duration=data.duration,
                transition_type=data.transition_type,
                transition_duration=data.transition_duration,
            )
            session.add(scene)
            await session.commit()
            await session.refresh(scene)
            # Recalculate timeline
            await self._recalculate_timeline(session, project_id)
            return _scene_to_response(scene)

    async def update_scene(self, project_id: str, scene_id: str, user_id: str | int, data: SceneUpdateRequest) -> SceneResponse | None:
        async for session in database_service.get_session():
            # Verify ownership
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return None

            result = await session.execute(
                select(StudioScene).where(StudioScene.id == scene_id, StudioScene.studio_project_id == project_id)
            )
            scene = result.scalar_one_or_none()
            if not scene:
                return None

            # Snapshot old script to detect real changes
            old_script = scene.script_text or ""

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(scene, field, value)

            # Update status based on what changed
            if data.script_text is not None:
                if data.script_text.strip():
                    # Only reset TTS if the script text actually changed
                    script_changed = data.script_text.strip() != old_script.strip()
                    if script_changed and scene.status not in (SceneStatus.EMPTY, SceneStatus.SCRIPTED):
                        scene.status = SceneStatus.SCRIPTED
                        scene.tts_audio_url = None
                        scene.tts_audio_duration = None
                        scene.word_timestamps = None
                        scene.preview_url = None
                else:
                    scene.status = SceneStatus.EMPTY

            if data.media_url is not None:
                if scene.status == SceneStatus.AUDIO_READY:
                    scene.status = SceneStatus.MEDIA_READY

            await session.commit()
            await session.refresh(scene)
            if data.duration is not None:
                await self._recalculate_timeline(session, project_id)
            return _scene_to_response(scene)

    async def delete_scene(self, project_id: str, scene_id: str, user_id: str | int) -> bool:
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return False

            result = await session.execute(
                select(StudioScene).where(StudioScene.id == scene_id, StudioScene.studio_project_id == project_id)
            )
            scene = result.scalar_one_or_none()
            if not scene:
                return False

            deleted_index = scene.order_index
            await session.delete(scene)

            # Reindex remaining scenes
            remaining = await session.execute(
                select(StudioScene)
                .where(StudioScene.studio_project_id == project_id, StudioScene.order_index > deleted_index)
                .order_by(StudioScene.order_index)
            )
            for s in remaining.scalars().all():
                s.order_index -= 1

            await session.commit()
            await self._recalculate_timeline(session, project_id)
            return True

    async def reorder_scenes(self, project_id: str, user_id: str | int, scene_ids: list[str]) -> list[SceneResponse]:
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return []

            result = await session.execute(
                select(StudioScene).where(StudioScene.studio_project_id == project_id)
            )
            scenes_by_id = {s.id: s for s in result.scalars().all()}

            for i, sid in enumerate(scene_ids):
                if sid in scenes_by_id:
                    scenes_by_id[sid].order_index = i

            await session.commit()
            await self._recalculate_timeline(session, project_id)

            ordered = sorted(scenes_by_id.values(), key=lambda s: s.order_index)
            return [_scene_to_response(s) for s in ordered]

    # ── Audio Track CRUD ──────────────────────────────────────────────────

    async def add_audio_track(self, project_id: str, user_id: str | int, data: AudioTrackCreateRequest) -> AudioTrackResponse | None:
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return None

            from app.database import TrackType
            track = StudioAudioTrack(
                id=str(uuid.uuid4()),
                studio_project_id=project_id,
                track_type=TrackType(data.track_type),
                name=data.name,
                audio_url=data.audio_url,
                start_time=data.start_time,
                duration=data.duration,
                volume=data.volume,
                fade_in=data.fade_in,
                fade_out=data.fade_out,
            )
            session.add(track)
            await session.commit()
            await session.refresh(track)
            return _track_to_response(track)

    async def update_audio_track(self, project_id: str, track_id: str, user_id: str | int, data: AudioTrackUpdateRequest) -> AudioTrackResponse | None:
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return None

            result = await session.execute(
                select(StudioAudioTrack).where(StudioAudioTrack.id == track_id, StudioAudioTrack.studio_project_id == project_id)
            )
            track = result.scalar_one_or_none()
            if not track:
                return None

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(track, field, value)

            await session.commit()
            await session.refresh(track)
            return _track_to_response(track)

    async def delete_audio_track(self, project_id: str, track_id: str, user_id: str | int) -> bool:
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return False

            result = await session.execute(
                select(StudioAudioTrack).where(StudioAudioTrack.id == track_id, StudioAudioTrack.studio_project_id == project_id)
            )
            track = result.scalar_one_or_none()
            if not track:
                return False

            await session.delete(track)
            await session.commit()
            return True

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _recalculate_timeline(self, session, project_id: str) -> None:
        """Recalculate start_time for all scenes based on order and duration."""
        result = await session.execute(
            select(StudioScene)
            .where(StudioScene.studio_project_id == project_id)
            .order_by(StudioScene.order_index)
        )
        scenes = result.scalars().all()
        current_time = 0.0
        for scene in scenes:
            scene.start_time = current_time
            current_time += scene.duration
        await session.commit()

    async def get_raw_scenes(self, project_id: str, user_id: str | int, scene_ids: list[str] | None = None) -> list[dict]:
        """Get raw scene data for pipeline processing."""
        async for session in database_service.get_session():
            proj_result = await session.execute(
                select(StudioProject).where(StudioProject.id == project_id, StudioProject.user_id == user_id)
            )
            if not proj_result.scalar_one_or_none():
                return []

            query = select(StudioScene).where(StudioScene.studio_project_id == project_id)
            if scene_ids:
                query = query.where(StudioScene.id.in_(scene_ids))
            query = query.order_by(StudioScene.order_index)

            result = await session.execute(query)
            return [
                {
                    "id": s.id,
                    "order_index": s.order_index,
                    "script_text": s.script_text,
                    "status": s.status.value if hasattr(s.status, "value") else s.status,
                    "tts_audio_url": s.tts_audio_url,
                    "tts_audio_duration": s.tts_audio_duration,
                    "word_timestamps": s.word_timestamps,
                    "media_source_type": s.media_source_type,
                    "media_url": s.media_url,
                    "media_search_terms": s.media_search_terms,
                    "media_prompt": s.media_prompt,
                    "media_provider": s.media_provider,
                    "start_time": s.start_time,
                    "duration": s.duration,
                    "transition_type": s.transition_type,
                    "transition_duration": s.transition_duration,
                }
                for s in result.scalars().all()
            ]

    async def update_scene_after_tts(
        self, scene_id: str, audio_url: str, audio_duration: float, word_timestamps: list[dict],
    ) -> None:
        """Update scene after TTS generation + Whisper timestamp extraction."""
        async for session in database_service.get_session():
            result = await session.execute(select(StudioScene).where(StudioScene.id == scene_id))
            scene = result.scalar_one_or_none()
            if not scene:
                return
            scene.tts_audio_url = audio_url
            scene.tts_audio_duration = audio_duration
            scene.word_timestamps = word_timestamps
            scene.duration = audio_duration  # Duration driven by audio
            scene.status = SceneStatus.AUDIO_READY
            await session.commit()
            # Recalculate timeline
            await self._recalculate_timeline(session, scene.studio_project_id)

    async def update_scene_after_media(self, scene_id: str, media_url: str, media_provider: str) -> None:
        """Update scene after media sourcing."""
        async for session in database_service.get_session():
            result = await session.execute(select(StudioScene).where(StudioScene.id == scene_id))
            scene = result.scalar_one_or_none()
            if not scene:
                return
            scene.media_url = media_url
            scene.media_provider = media_provider
            if scene.status == SceneStatus.AUDIO_READY:
                scene.status = SceneStatus.MEDIA_READY
            await session.commit()

    async def update_project_status(self, project_id: str, status: StudioProjectStatus, **kwargs) -> None:
        """Update project status and optional fields."""
        async for session in database_service.get_session():
            result = await session.execute(select(StudioProject).where(StudioProject.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                return
            project.status = status
            for k, v in kwargs.items():
                if hasattr(project, k):
                    setattr(project, k, v)
            await session.commit()


studio_project_service = StudioProjectService()
