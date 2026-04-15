"""
Music service for handling background music selection and management.
"""
import os
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MusicMood(str, Enum):
    """Music mood categories."""
    sad = "sad"
    melancholic = "melancholic"
    happy = "happy"
    euphoric = "euphoric"
    excited = "excited"
    chill = "chill"
    uneasy = "uneasy"
    angry = "angry"
    dark = "dark"
    hopeful = "hopeful"
    contemplative = "contemplative"
    funny = "funny"

class MusicTrack:
    """Represents a music track with metadata."""
    def __init__(self, file: str, start: int, end: int, mood: MusicMood, title: str | None = None, base_url: str | None = None):
        self.file = file
        self.start = start
        self.end = end
        self.mood = mood
        self.title = title or file.replace('.mp3', '')
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def to_dict(self, s3_url: Optional[str] = None) -> Dict[str, Any]:
        url = s3_url if s3_url else f"{self.base_url}/api/v1/music/file/{self.file}"
        return {
            "file": self.file,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "mood": self.mood.value,
            "duration": self.end - self.start,
            "url": url
        }

class MusicService:
    """Service for managing background music tracks."""
    
    def __init__(self):
        # Try multiple possible paths for music directory
        possible_paths = [
            "/app/static/music",  # Docker environment
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "static", "music"),  # Local development
            os.path.join(os.getcwd(), "app", "static", "music"),  # Alternative local path
        ]
        
        self.music_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                self.music_dir = path
                break
        
        if not self.music_dir:
            # Default to the first path if none exist
            self.music_dir = possible_paths[0]
        
        logger.info(f"Music service initialized with directory: {self.music_dir}")
        logger.info(f"Music directory exists: {os.path.exists(self.music_dir)}")
        if os.path.exists(self.music_dir):
            files = os.listdir(self.music_dir)
            logger.info(f"Found {len(files)} music files in directory")
        else:
            logger.warning(f"Music directory not found: {self.music_dir}")
        self.tracks = self._initialize_tracks()
    
    def _initialize_tracks(self) -> List[MusicTrack]:
        """Initialize the music track list."""
        return [
            MusicTrack("sly_sky_-_telecasted.mp3", 0, 152, MusicMood.melancholic, "Sly Sky"),
            MusicTrack("no.2_remembering_her_-_esther_abrami.mp3", 2, 134, MusicMood.melancholic, "Remembering Her"),
            MusicTrack("champion_-_telecasted.mp3", 0, 142, MusicMood.chill, "Champion"),
            MusicTrack("oh_please_-_telecasted.mp3", 0, 154, MusicMood.chill, "Oh Please"),
            MusicTrack("jetski_-_telecasted.mp3", 0, 142, MusicMood.uneasy, "Jetski"),
            MusicTrack("phantom_-_density_&_time.mp3", 0, 178, MusicMood.uneasy, "Phantom"),
            MusicTrack("on_the_hunt_-_andrew_langdon.mp3", 0, 95, MusicMood.uneasy, "On The Hunt"),
            MusicTrack("name_the_time_and_place_-_telecasted.mp3", 0, 142, MusicMood.excited, "Name The Time And Place"),
            MusicTrack("delayed_baggage_-_ryan_stasik.mp3", 3, 108, MusicMood.euphoric, "Delayed Baggage"),
            MusicTrack("like_it_loud_-_dyalla.mp3", 4, 160, MusicMood.euphoric, "Like It Loud"),
            MusicTrack("organic_guitar_house_-_dyalla.mp3", 2, 160, MusicMood.euphoric, "Organic Guitar House"),
            MusicTrack("honey,_i_dismembered_the_kids_-_ezra_lipp.mp3", 2, 144, MusicMood.dark, "Honey, I Dismembered The Kids"),
            MusicTrack("night_hunt_-_jimena_contreras.mp3", 0, 88, MusicMood.dark, "Night Hunt"),
            MusicTrack("curse_of_the_witches_-_jimena_contreras.mp3", 0, 102, MusicMood.dark, "Curse of the Witches"),
            MusicTrack("restless_heart_-_jimena_contreras.mp3", 0, 94, MusicMood.sad, "Restless Heart"),
            MusicTrack("heartbeat_of_the_wind_-_asher_fulero.mp3", 0, 124, MusicMood.sad, "Heartbeat Of The Wind"),
            MusicTrack("hopeless_-_jimena_contreras.mp3", 0, 250, MusicMood.sad, "Hopeless"),
            MusicTrack("touch_-_anno_domini_beats.mp3", 0, 165, MusicMood.happy, "Touch"),
            MusicTrack("cafecito_por_la_manana_-_cumbia_deli.mp3", 0, 184, MusicMood.happy, "Cafecito por la Manana"),
            MusicTrack("aurora_on_the_boulevard_-_national_sweetheart.mp3", 0, 130, MusicMood.happy, "Aurora on the Boulevard"),
            MusicTrack("buckle_up_-_jeremy_korpas.mp3", 0, 128, MusicMood.angry, "Buckle Up"),
            MusicTrack("twin_engines_-_jeremy_korpas.mp3", 0, 120, MusicMood.angry, "Twin Engines"),
            MusicTrack("hopeful_-_nat_keefe.mp3", 0, 175, MusicMood.hopeful, "Hopeful"),
            MusicTrack("hopeful_freedom_-_asher_fulero.mp3", 1, 172, MusicMood.hopeful, "Hopeful Freedom"),
            MusicTrack("crystaline_-_quincas_moreira.mp3", 0, 140, MusicMood.contemplative, "Crystaline"),
            MusicTrack("final_soliloquy_-_asher_fulero.mp3", 1, 178, MusicMood.contemplative, "Final Soliloquy"),
            MusicTrack("seagull_-_telecasted.mp3", 0, 123, MusicMood.funny, "Seagull"),
            MusicTrack("banjo_doops_-_joel_cummins.mp3", 0, 98, MusicMood.funny, "Banjo Doops"),
            MusicTrack("baby_animals_playing_-_joel_cummins.mp3", 0, 124, MusicMood.funny, "Baby Animals Playing"),
            MusicTrack("sinister_-_anno_domini_beats.mp3", 0, 215, MusicMood.dark, "Sinister"),
            MusicTrack("traversing_-_godmode.mp3", 0, 95, MusicMood.dark, "Traversing"),
        ]
    
    async def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Get all available music tracks with S3 URLs."""
        tracks = []
        for track in self.tracks:
            s3_url = await self.get_s3_url_for_track(track.file)
            tracks.append(track.to_dict(s3_url))
        return tracks
    
    async def get_tracks_by_mood(self, mood: str) -> List[Dict[str, Any]]:
        """Get tracks filtered by mood with S3 URLs."""
        try:
            mood_enum = MusicMood(mood.lower())
            tracks = []
            for track in self.tracks:
                if track.mood == mood_enum:
                    s3_url = await self.get_s3_url_for_track(track.file)
                    tracks.append(track.to_dict(s3_url))
            return tracks
        except ValueError:
            logger.warning(f"Invalid mood: {mood}")
            return []
    
    async def get_track_by_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get a specific track by filename with S3 URL."""
        for track in self.tracks:
            if track.file == filename:
                # Try to get S3 URL
                s3_url = await self.get_s3_url_for_track(filename)
                return track.to_dict(s3_url)
        return None
    
    def get_track_path(self, filename: str) -> Optional[str]:
        """Get the full path to a music file."""
        if self.music_dir is None:
            return None
            
        track_path = os.path.join(self.music_dir, filename)
        if os.path.exists(track_path):
            return track_path
        
        # Check for case sensitivity issues
        if os.path.exists(self.music_dir):
            files_in_dir = os.listdir(self.music_dir)
            matching_files = [f for f in files_in_dir if f.lower() == filename.lower()]
            if matching_files:
                actual_path = os.path.join(self.music_dir, matching_files[0])
                if os.path.exists(actual_path):
                    return actual_path
        
        return None
    
    def get_available_moods(self) -> List[str]:
        """Get list of available music moods."""
        return [mood.value for mood in MusicMood]
    
    def validate_track_exists(self, filename: str) -> bool:
        """Check if a music track file exists."""
        if not filename or self.music_dir is None:
            return False
        return os.path.exists(os.path.join(self.music_dir, filename))
    
    async def get_s3_url_for_track(self, filename: str) -> Optional[str]:
        """Get or create S3 URL for a music track with persistent caching."""
        from app.services.s3.s3 import s3_service
        from app.services.s3.s3_cache import s3_cache_service

        try:
            s3_path = f"music/{filename}"

            # 1. Check persistent database cache first
            cached_url = await s3_cache_service.get_cached_url(s3_path)
            if cached_url:
                logger.info(f"✅ Using cached S3 URL for {filename}")
                return cached_url

            # 2. Get the local file path
            file_path = self.get_track_path(filename)
            if not file_path:
                logger.error(f"Could not find local file path for {filename}")
                return None

            # 3. Upload to S3
            logger.info(f"📤 Uploading {filename} to S3...")

            # Compute file hash for change detection
            file_hash = s3_cache_service.compute_file_hash(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

            upload_result = await s3_service.upload_file_with_metadata(
                file_path=file_path,
                object_name=s3_path,
                content_type="audio/mpeg",
                public=True
            )

            s3_url = upload_result["file_url"]

            # 4. Cache the URL persistently
            await s3_cache_service.cache_url(
                file_path=s3_path,
                s3_url=s3_url,
                content_type="audio/mpeg",
                file_size_bytes=file_size,
                file_hash=file_hash,
                is_public=True
            )

            logger.info(f"✅ Successfully uploaded {filename} to S3 and cached")
            return s3_url

        except Exception as e:
            logger.error(f"Failed to get S3 URL for {filename}: {str(e)}")
            return None

    def add_track(self, file: str, start: int, end: int, mood: MusicMood, title: str) -> MusicTrack:
        """Add a new track to the library."""
        new_track = MusicTrack(file=file, start=start, end=end, mood=mood, title=title)
        self.tracks.append(new_track)
        logger.info(f"Added new track: {title} ({file}) - Mood: {mood.value}, Duration: {end-start}s")
        return new_track

# Global music service instance
music_service = MusicService()
