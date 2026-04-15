"""
System settings service for managing application configuration.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import database_service
from loguru import logger


class SettingsService:
    """Service for managing system settings in the database."""
    
    def __init__(self):
        self.default_settings = {
            "auto_refresh": True,
            "email_notifications": True,
            "api_logging": True,
            "max_concurrent_jobs": 5,
            "default_video_resolution": "1080x1920",
            "storage_retention_days": 90,
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "updated_by": "system"
        }
    
    async def _ensure_settings_table(self):
        """Ensure the settings table exists."""
        async for session in database_service.get_session():
            try:
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        data_type VARCHAR(20) NOT NULL DEFAULT 'string',
                        description TEXT,
                        category VARCHAR(50) DEFAULT 'general',
                        is_public BOOLEAN DEFAULT false,
                        updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_by VARCHAR(100) DEFAULT 'system'
                    );
                """))
                
                # Create index for faster lookups
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_system_settings_key 
                    ON system_settings(key);
                """))
                
                await session.commit()
                logger.info("Settings table created/verified successfully")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create settings table: {e}")
                raise
            break
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all system settings."""
        await self._ensure_settings_table()
        
        async for session in database_service.get_session():
            try:
                result = await session.execute(text("""
                    SELECT key, value, data_type FROM system_settings
                    ORDER BY category, key
                """))
                
                settings = {}
                for row in result:
                    key, value, data_type = row
                    settings[key] = self._parse_value(value, data_type)
                
                # Merge with defaults for any missing keys
                final_settings = self.default_settings.copy()
                final_settings.update(settings)
                
                return final_settings
                
            except Exception as e:
                logger.error(f"Failed to get settings: {e}")
                return self.default_settings.copy()
            break
        
        return self.default_settings.copy()
    
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        await self._ensure_settings_table()
        
        async for session in database_service.get_session():
            try:
                result = await session.execute(text("""
                    SELECT value, data_type FROM system_settings WHERE key = :key
                """), {"key": key})
                
                row = result.first()
                if row:
                    value, data_type = row
                    return self._parse_value(value, data_type)
                
                # Return default from defaults or provided default
                return self.default_settings.get(key, default)
                
            except Exception as e:
                logger.error(f"Failed to get setting {key}: {e}")
                return self.default_settings.get(key, default)
            break
        
        return self.default_settings.get(key, default)
    
    async def set_setting(self, key: str, value: Any, data_type: str = None, updated_by: str = "system") -> bool:
        """Set a specific setting value."""
        await self._ensure_settings_table()
        
        if data_type is None:
            data_type = self._infer_type(value)
        
        value_str = self._serialize_value(value)
        
        async for session in database_service.get_session():
            try:
                # Use UPSERT (INSERT ... ON CONFLICT)
                await session.execute(text("""
                    INSERT INTO system_settings (key, value, data_type, updated_at, updated_by)
                    VALUES (:key, :value, :data_type, :updated_at, :updated_by)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        data_type = EXCLUDED.data_type,
                        updated_at = EXCLUDED.updated_at,
                        updated_by = EXCLUDED.updated_by
                """), {
                    "key": key,
                    "value": value_str,
                    "data_type": data_type,
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                    "updated_by": updated_by
                })
                
                await session.commit()
                logger.info(f"Setting {key} updated to {value} by {updated_by}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to set setting {key}: {e}")
                return False
            break
        
        return False
    
    async def update_settings(self, settings: Dict[str, Any], updated_by: str = "system") -> bool:
        """Update multiple settings at once."""
        try:
            success_count = 0
            total_count = len(settings)
            
            for key, value in settings.items():
                if key in ['updated_at', 'updated_by']:  # Skip metadata
                    continue
                    
                success = await self.set_setting(key, value, updated_by=updated_by)
                if success:
                    success_count += 1
            
            logger.info(f"Updated {success_count}/{total_count} settings successfully")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information and health status."""
        try:
            # Database status
            db_status = "connected"
            db_info = {}
            
            try:
                async for session in database_service.get_session():
                    # Get database version
                    result = await session.execute(text("SELECT version()"))
                    db_version = result.scalar()
                    
                    # Get database size
                    result = await session.execute(text("""
                        SELECT pg_database_size(current_database()) as size
                    """))
                    db_size_bytes = result.scalar()
                    db_size_mb = round(db_size_bytes / (1024 * 1024), 2) if db_size_bytes else 0
                    
                    # Get table count
                    result = await session.execute(text("""
                        SELECT count(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """))
                    table_count = result.scalar()
                    
                    db_info = {
                        "version": db_version.split('\n')[0] if db_version else "Unknown",
                        "size_mb": db_size_mb,
                        "tables": table_count
                    }
                    break
                    
            except Exception as e:
                db_status = "error"
                logger.warning(f"Database info collection failed: {e}")
            
            # Redis status
            redis_status = "unknown"
            try:
                from app.services.redis import redis_service
                await redis_service.ping()
                redis_status = "connected"
            except Exception:
                redis_status = "disconnected"
            
            # Storage status
            storage_status = "available"
            storage_info = {}
            try:
                import shutil
                disk_usage = shutil.disk_usage('/')
                storage_info = {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round((disk_usage.total - disk_usage.free) / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "usage_percent": round(((disk_usage.total - disk_usage.free) / disk_usage.total) * 100, 1)
                }
            except Exception as e:
                storage_status = "error"
                logger.warning(f"Storage info collection failed: {e}")
            
            # Job statistics
            job_stats = {}
            try:
                from app.services.database.database_service import db_job_service
                job_counts = await db_job_service.get_job_count_by_status()
                job_stats = {
                    "active": job_counts.get("processing", 0) + job_counts.get("pending", 0),
                    "completed": job_counts.get("completed", 0),
                    "failed": job_counts.get("failed", 0),
                    "total": sum(job_counts.values())
                }
            except Exception as e:
                logger.warning(f"Job stats collection failed: {e}")
            
            # API key statistics
            api_key_stats = {}
            try:
                from app.services.api_key import api_key_service
                stats = await api_key_service.get_api_key_stats()
                api_key_stats = {
                    "total": stats.get("total_keys", 0),
                    "active": stats.get("active_keys", 0),
                    "total_usage": stats.get("total_usage", 0)
                }
            except Exception as e:
                logger.warning(f"API key stats collection failed: {e}")
            
            return {
                "version": "1.0.0",
                "api_status": "operational",
                "database": {
                    "status": db_status,
                    **db_info
                },
                "redis": {
                    "status": redis_status
                },
                "storage": {
                    "status": storage_status,
                    **storage_info
                },
                "jobs": job_stats,
                "api_keys": api_key_stats,
                "uptime": "Unknown",  # Could implement actual uptime tracking
                "last_updated": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                "version": "1.0.0",
                "api_status": "error",
                "database": {"status": "error"},
                "redis": {"status": "unknown"},
                "storage": {"status": "error"},
                "jobs": {},
                "api_keys": {},
                "error": str(e)
            }
    
    def _infer_type(self, value: Any) -> str:
        """Infer the data type of a value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (dict, list)):
            return "json"
        else:
            return "string"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize a value for storage."""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return str(value)
    
    def _parse_value(self, value_str: str, data_type: str) -> Any:
        """Parse a stored value based on its type."""
        try:
            if data_type == "boolean":
                return value_str.lower() in ('true', '1', 'yes', 'on')
            elif data_type == "integer":
                return int(value_str)
            elif data_type == "float":
                return float(value_str)
            elif data_type == "json":
                return json.loads(value_str)
            else:
                return value_str
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse value '{value_str}' as {data_type}: {e}")
            return value_str


    async def load_config_overrides(self) -> int:
        """Load config:* settings from DB into os.environ.

        Called on startup so that dashboard-configured values override
        environment defaults for the current process.

        Returns the number of overrides applied.
        """
        import os
        await self._ensure_settings_table()

        count = 0
        async for session in database_service.get_session():
            try:
                result = await session.execute(text("""
                    SELECT key, value FROM system_settings
                    WHERE key LIKE 'config:%'
                """))
                for row in result:
                    db_key, db_value = row
                    env_key = db_key.removeprefix("config:")
                    if db_value:
                        os.environ[env_key] = db_value
                        count += 1
            except Exception as e:
                logger.warning(f"Failed to load config overrides: {e}")
            break

        if count:
            logger.info(f"Loaded {count} config overrides from database")
        return count


# Singleton instance
settings_service = SettingsService()