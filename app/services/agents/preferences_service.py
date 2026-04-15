"""
User preference management for the agents experience.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import (
    database_service,
    AgentUserPreferenceRecord,
)
from app.services.agents.utils import normalize_owner_identifier
from loguru import logger


DEFAULT_PREFERENCES: Dict[str, Any] = {
    "model": "gpt-4",
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 0.0,
    "max_tokens": 2048,
    "stream": True,
    "memory_enabled": True,
    "knowledge_base_enabled": False,
    "reasoning_enabled": True,
    "tool_metadata_enabled": True,
    "theme": "auto",
    "language": "en",
    "export_format": "json",
    "auto_save": True,
    "auto_title": True,
    "smart_completions": True,
    "voice_input": False,
    "voice_output": False,
    "sound_effects": True,
    "notifications": True,
    "privacy_mode": False,
    "debug_mode": False,
    "experimental_features": False,
}


class AgentPreferenceService:
    """Persistence for agent user preferences."""

    async def get_preferences(self, owner_identifier: Optional[str]) -> Dict[str, Any]:
        if not database_service.is_database_available():
            logger.warning("Database not available, returning default preferences")
            return DEFAULT_PREFERENCES.copy()
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return DEFAULT_PREFERENCES.copy()

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentUserPreferenceRecord).where(AgentUserPreferenceRecord.owner_hash == owner_hash)
                )
                record = result.scalar_one_or_none()
                if record:
                    merged = DEFAULT_PREFERENCES.copy()
                    merged.update(record.preferences or {})
                    return merged
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to load agent preferences: %s", exc)

        return DEFAULT_PREFERENCES.copy()

    async def update_preferences(self, owner_identifier: Optional[str], preferences: Dict[str, Any]) -> Dict[str, Any]:
        if not database_service.is_database_available():
            logger.warning("Database not available, cannot save preferences")
            # Return merged preferences without saving
            merged = DEFAULT_PREFERENCES.copy()
            merged.update(preferences or {})
            return merged
            
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            raise ValueError("Owner identifier required to save preferences")

        merged = DEFAULT_PREFERENCES.copy()
        merged.update(preferences or {})

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentUserPreferenceRecord).where(AgentUserPreferenceRecord.owner_hash == owner_hash)
                )
                record = result.scalar_one_or_none()

                if record:
                    record.preferences = merged
                    record.updated_at = datetime.utcnow()
                else:
                    record = AgentUserPreferenceRecord(
                        id=uuid.uuid4(),
                        owner_hash=owner_hash,
                        preferences=merged,
                    )
                    session.add(record)

                await session.commit()
                return merged
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to update agent preferences: %s", exc)
            raise


agent_preferences_service = AgentPreferenceService()
