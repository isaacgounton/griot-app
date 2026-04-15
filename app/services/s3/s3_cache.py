"""
Persistent S3 URL cache service for storing and retrieving cached S3 URLs.
This replaces in-memory caching with database-backed persistence.
"""
import hashlib
import os
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from app.database import S3URLCacheRecord, database_service
from loguru import logger


class S3CacheService:
    """Service for managing persistent S3 URL cache."""
    
    def __init__(self):
        self.cache_ttl_days = int(os.getenv("S3_CACHE_TTL_DAYS", "30"))
    
    async def get_cached_url(self, file_path: str) -> Optional[str]:
        """
        Retrieve a cached S3 URL for a file.
        
        Args:
            file_path: The S3 file path (e.g., "music/song.mp3")
            
        Returns:
            S3 URL if cached and valid, None otherwise
        """
        try:
            if not database_service.is_database_available():
                logger.debug("Database not available, skipping cache lookup")
                return None
            
            async for session in database_service.get_session():
                # Query for cached URL
                stmt = select(S3URLCacheRecord).where(
                    S3URLCacheRecord.file_path == file_path
                )
                result = await session.execute(stmt)
                cache_record = result.scalar_one_or_none()
                
                if cache_record:
                    # Check if URL has expired
                    if cache_record.expires_at and cache_record.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
                        logger.info(f"S3 URL cache expired for {file_path}, will re-upload")
                        await self.invalidate_cache(file_path)
                        return None
                    
                    logger.debug(f"Retrieved cached S3 URL for {file_path}")
                    return cache_record.s3_url
                
                return None
                
        except Exception as e:
            logger.warning(f"Error retrieving S3 cache for {file_path}: {e}")
            return None
    
    async def cache_url(
        self,
        file_path: str,
        s3_url: str,
        content_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        file_hash: Optional[str] = None,
        is_public: bool = True,
        ttl_days: Optional[int] = None
    ) -> bool:
        """
        Cache an S3 URL in the database using upsert (insert or update).
        
        Args:
            file_path: The S3 file path (e.g., "music/song.mp3")
            s3_url: The public S3 URL
            content_type: MIME type (e.g., "audio/mpeg")
            file_size_bytes: File size in bytes
            file_hash: File hash for change detection
            is_public: Whether the S3 object is public
            ttl_days: Custom TTL in days (defaults to S3_CACHE_TTL_DAYS env var)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            if not database_service.is_database_available():
                logger.debug("Database not available, skipping cache write")
                return False
            
            ttl = ttl_days or self.cache_ttl_days
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            expires_at = now + timedelta(days=ttl)
            
            async for session in database_service.get_session():
                # Use PostgreSQL's ON CONFLICT DO UPDATE for upsert
                stmt = pg_insert(S3URLCacheRecord).values(
                    file_path=file_path,
                    s3_url=s3_url,
                    content_type=content_type,
                    file_size_bytes=file_size_bytes,
                    file_hash=file_hash,
                    is_public=is_public,
                    expires_at=expires_at,
                    cached_at=now,
                    updated_at=now
                ).on_conflict_do_update(
                    index_elements=['file_path'],
                    set_={
                        'file_path': file_path,
                        's3_url': s3_url,
                        'content_type': content_type,
                        'file_size_bytes': file_size_bytes,
                        'file_hash': file_hash,
                        'is_public': is_public,
                        'expires_at': expires_at,
                        'updated_at': now
                    }
                )
                
                await session.execute(stmt)
                await session.commit()
                logger.debug(f"✅ Cached S3 URL for {file_path} (expires in {ttl} days)")
                return True
                    
        except Exception as e:
            logger.error(f"Error caching S3 URL for {file_path}: {e}")
            return False
    
    async def invalidate_cache(self, file_path: str) -> bool:
        """
        Invalidate cached URL for a file.
        
        Args:
            file_path: The S3 file path to invalidate
            
        Returns:
            True if invalidated, False otherwise
        """
        try:
            if not database_service.is_database_available():
                return False
            
            async for session in database_service.get_session():
                stmt = select(S3URLCacheRecord).where(
                    S3URLCacheRecord.file_path == file_path
                )
                result = await session.execute(stmt)
                cache_record = result.scalar_one_or_none()
                
                if cache_record:
                    await session.delete(cache_record)
                    await session.commit()
                    logger.info(f"✅ Invalidated S3 URL cache for {file_path}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error invalidating S3 cache for {file_path}: {e}")
            return False
    
    async def clear_expired_cache(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        try:
            if not database_service.is_database_available():
                return 0
            
            async for session in database_service.get_session():
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                
                stmt = select(S3URLCacheRecord).where(
                    S3URLCacheRecord.expires_at < now
                )
                result = await session.execute(stmt)
                expired_records = result.scalars().all()
                
                count = len(expired_records)
                for record in expired_records:
                    await session.delete(record)
                
                await session.commit()
                
                if count > 0:
                    logger.info(f"✅ Cleared {count} expired S3 URL cache entries")
                
                return count
                
        except Exception as e:
            logger.error(f"Error clearing expired S3 cache: {e}")
            return 0
    
    @staticmethod
    def compute_file_hash(file_path: str, hash_algorithm: str = "md5") -> Optional[str]:
        """
        Compute hash of a file for change detection.
        
        Args:
            file_path: Path to the file
            hash_algorithm: Hash algorithm to use (md5, sha256, etc.)
            
        Returns:
            Hex digest of the file hash
        """
        try:
            hasher = hashlib.new(hash_algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"Could not compute file hash for {file_path}: {e}")
            return None


# Global S3 cache service instance
s3_cache_service = S3CacheService()
