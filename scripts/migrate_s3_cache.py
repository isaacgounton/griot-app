"""
Script to clean up old in-memory S3 URL caches and prepare for database migration.
Run this after deploying the persistent cache updates.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.database import database_service, S3URLCacheRecord
from app.services.music.music_service import music_service
from loguru import logger


async def migrate_s3_cache():
    """
    Migrate from in-memory S3 cache to database-backed cache.
    Pre-warms the database cache on startup.
    """
    logger.info("🔄 Starting S3 cache migration to database...")
    
    try:
        # Initialize database
        await database_service.initialize()
        await database_service.create_tables()
        
        logger.info("✅ Database initialized")
        
        # Check if database is available
        if not database_service.is_database_available():
            logger.warning("⚠️  Database not available, skipping cache migration")
            return
        
        # Get all music tracks and pre-cache their S3 URLs
        logger.info(f"📚 Found {len(music_service.tracks)} music tracks")
        logger.info("🔄 Pre-warming S3 URL cache...")
        
        cached_count = 0
        for i, track in enumerate(music_service.tracks, 1):
            logger.info(f"[{i}/{len(music_service.tracks)}] Getting S3 URL for: {track.file}")
            s3_url = await music_service.get_s3_url_for_track(track.file)
            if s3_url:
                cached_count += 1
        
        logger.info(f"✅ Successfully cached {cached_count}/{len(music_service.tracks)} music tracks")
        
        # Clean up any expired entries
        from app.services.s3.s3_cache import s3_cache_service
        expired_count = await s3_cache_service.clear_expired_cache()
        if expired_count > 0:
            logger.info(f"🧹 Cleaned up {expired_count} expired cache entries")
        
        logger.info("✅ S3 cache migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during S3 cache migration: {e}")
        raise
    finally:
        await database_service.close()


if __name__ == "__main__":
    asyncio.run(migrate_s3_cache())
