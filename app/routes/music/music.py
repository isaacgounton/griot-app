"""
Music management endpoints for the API.
"""
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.services.music import music_service
import os
import logging
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)


class MusicTrackUploadRequest(BaseModel):
    title: str
    mood: str
    start: int | None = 0
    end: int | None = None

router = APIRouter(prefix="/music", tags=["Audio"])

@router.get("/tracks", response_model=dict)
async def list_music_tracks(
    mood: str | None = Query(None, description="Filter tracks by mood (sad, happy, chill, etc.)"),
    page: int | None = Query(1, ge=1, description="Page number for pagination"),
    per_page: int | None = Query(12, ge=1, le=100, description="Number of tracks per page"),
    search: str | None = Query(None, description="Search tracks by title")
):
    """List background music tracks with pagination, mood filtering, and search."""
    try:
        # Get all tracks first
        if mood:
            tracks = await music_service.get_tracks_by_mood(mood)
            if not tracks:
                available_moods = music_service.get_available_moods()
                raise HTTPException(
                    status_code=404,
                    detail=f"No tracks found for mood '{mood}'. Available moods: {', '.join(available_moods)}"
                )
        else:
            tracks = await music_service.get_all_tracks()

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            tracks = [t for t in tracks if search_lower in t.get('title', '').lower()]

        total = len(tracks)
        total_pages = (total + per_page - 1) // per_page

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tracks = tracks[start_idx:end_idx]

        return {
            "success": True,
            "tracks": paginated_tracks,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "moods": music_service.get_available_moods()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get music tracks: {str(e)}")

@router.get("/moods", response_model=dict)
async def list_music_moods(
):
    """List available music mood categories with track counts."""
    try:
        moods = music_service.get_available_moods()
        
        # Get track counts by mood
        mood_counts = {}
        for mood in moods:
            tracks = await music_service.get_tracks_by_mood(mood)
            mood_counts[mood] = len(tracks)
        
        return {
            "success": True,
            "moods": moods,
            "mood_counts": mood_counts,
            "total_moods": len(moods)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get music moods: {str(e)}")

@router.get("/tracks/{filename}", response_model=dict)
async def get_music_track(
    filename: str,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Get details for a specific music track by filename."""
    try:
        track = await music_service.get_track_by_file(filename)
        if not track:
            raise HTTPException(status_code=404, detail=f"Music track not found: {filename}")
        
        return {
            "success": True,
            "track": track
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get music track: {str(e)}")

@router.get("/file/{filename}")
async def serve_music_file(
    filename: str
):
    """Serve a music file directly for streaming or download."""
    try:
        # Validate that the track exists in our database
        track = await music_service.get_track_by_file(filename)
        if not track:
            raise HTTPException(status_code=404, detail=f"Music track not found: {filename}")
        
        # Get the file path
        file_path = music_service.get_track_path(filename)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Music file not found: {filename}")
        
        # Return the file with appropriate headers
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve music file: {str(e)}")


@router.post("/upload", response_model=dict)
async def upload_music_track(
    file: UploadFile = File(..., description="MP3 audio file to upload"),
    title: str = Query(..., description="Title of the music track"),
    mood: str = Query(..., description="Mood category (sad, happy, chill, etc.)"),
    start: int | None = Query(0, description="Start time in seconds"),
    end: int | None = Query(None, description="End time in seconds (auto-detected if not provided)"),
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """Upload an MP3 track to the music library with mood and timing metadata."""
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.mp3'):
            raise HTTPException(
                status_code=400,
                detail="Only MP3 files are supported"
            )

        # Validate mood
        from app.services.music.music_service import MusicMood
        try:
            mood_enum = MusicMood(mood.lower())
        except ValueError:
            available_moods = music_service.get_available_moods()
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mood '{mood}'. Available moods: {', '.join(available_moods)}"
            )

        # Generate safe filename - prevent path traversal
        import re as _re
        raw_filename = os.path.basename(file.filename or "upload.mp3")
        safe_filename = _re.sub(r'[^\w\-.]', '_', raw_filename)
        if not safe_filename or safe_filename.startswith('.'):
            safe_filename = f"upload_{int(time.time())}.mp3"
        if not safe_filename.endswith('.mp3'):
            safe_filename += '.mp3'

        # Ensure music directory exists
        music_dir = music_service.music_dir
        if not music_dir:
            os.makedirs(music_dir, exist_ok=True)
            music_service.music_dir = music_dir

        file_path = os.path.join(music_dir, safe_filename)
        # Verify resolved path stays inside music_dir
        if not os.path.realpath(file_path).startswith(os.path.realpath(music_dir)):
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Check if file already exists
        if os.path.exists(file_path):
            # Add timestamp to make unique
            import time
            base_name = safe_filename.replace('.mp3', '')
            safe_filename = f"{base_name}_{int(time.time())}.mp3"
            file_path = os.path.join(music_dir, safe_filename)

        # Save uploaded file
        logger.info(f"Saving uploaded file to {file_path}")
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # Get audio duration if end not provided
        if end is None:
            try:
                from mutagen.mp3 import MP3
                audio = MP3(file_path)
                duration = int(audio.info.length)
                end = duration
                logger.info(f"Auto-detected duration: {duration}s for {safe_filename}")
            except ImportError:
                logger.warning("mutagen not installed, using default duration")
                end = 180  # Default 3 minutes
            except Exception as e:
                logger.warning(f"Failed to get duration: {e}, using default")
                end = 180

        # Validate start/end times
        if start >= end:
            raise HTTPException(
                status_code=400,
                detail="Start time must be less than end time"
            )

        # Create new track
        new_track = music_service.add_track(
            file=safe_filename,
            start=start,
            end=end,
            mood=mood_enum,
            title=title
        )

        # Get S3 URL for the new track
        s3_url = await music_service.get_s3_url_for_track(safe_filename)

        logger.info(f"Successfully uploaded new track: {title} ({safe_filename})")

        return {
            "success": True,
            "track": new_track.to_dict(s3_url),
            "message": f"Track '{title}' uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload music track: {str(e)}")
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to upload music track: {str(e)}")

