"""
Service layer for Agno agent integration.
Handles session persistence, knowledge integration, and conversation history.

Architecture:
- Sessions are cached in Redis and memory (fast, always available)
- Database persistence is deferred via background tasks (non-blocking)
- Messages are queued in Redis and flushed periodically to database
- This ensures the system works even if the database is temporarily unavailable
"""

from __future__ import annotations

import uuid
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Any

from sqlalchemy import select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from agno.agent import Agent

from app.database import (
    database_service,
    AgentSessionRecord,
    AgentMessageRecord,
    AgentSessionStatus,
    AgentMessageRole,
)
from app.services.agents.selector import AgentType, get_agent, get_available_agents
from app.services.agents.utils import normalize_owner_identifier
from app.services.redis.redis_service import redis_service
from loguru import logger


DEFAULT_SESSION_STATUS = AgentSessionStatus.ACTIVE.value

# Redis keys for queuing
PENDING_SESSIONS_QUEUE = "agent:pending_sessions"
PENDING_MESSAGES_QUEUE = "agent:pending_messages"


class AgentService:
    """Service for managing Agno agents and interactions."""

    def __init__(self) -> None:
        # Simple in-memory cache to reduce database lookups
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._flush_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Agent & session discovery
    # ------------------------------------------------------------------
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their details."""
        return get_available_agents()

    async def get_agent_details(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent."""
        agents = await self.get_available_agents()
        for agent in agents:
            if agent["id"] == agent_type:
                return agent
        return None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    async def create_session(
        self,
        agent_type: str,
        user_identifier: Optional[str] = None,
        model_id: str = "gpt-5-mini",
        provider: Optional[str] = "openai",
        title: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Create a new agent session and persist it.
        """
        normalized_provider = (provider or "openai").strip().lower() or "openai"
        session_metadata = {**(metadata or {}), "provider": normalized_provider}
        session_settings = settings or {}

        if not database_service.is_database_available():
            # Create a mock session for when database is not available
            session_id = uuid.uuid4()
            owner_hash = normalize_owner_identifier(user_identifier)
            now_iso = datetime.utcnow().isoformat()
            
            session_info = {
                "session_id": str(session_id),
                "agent_type": agent_type,
                "user_id": owner_hash,
                "model_id": model_id,
                "provider": normalized_provider,
                "created_at": now_iso,
                "updated_at": now_iso,
                "status": DEFAULT_SESSION_STATUS,
                "title": title,
                "description": description,
                "metadata": session_metadata,
                "settings": session_settings,
            }
            
            # Store in memory cache
            self.active_sessions[str(session_id)] = session_info
            logger.info(f"Created in-memory session {session_id} (database not available)")
            return session_info
            
        try:
            agent_enum = AgentType(agent_type)
        except ValueError as exc:
            raise ValueError(f"Invalid agent type: {agent_type}") from exc

        session_id = uuid.uuid4()
        owner_hash = normalize_owner_identifier(user_identifier)
        now_iso = datetime.utcnow().isoformat()

        session_info = {
            "session_id": str(session_id),
            "agent_type": agent_enum.value,
            "user_id": owner_hash,
            "model_id": model_id,
            "provider": normalized_provider,
            "created_at": now_iso,
            "updated_at": now_iso,
            "status": DEFAULT_SESSION_STATUS,
            "title": title,
            "description": description,
            "metadata": session_metadata,
            "settings": session_settings,
        }

        # Queue session for deferred persistence to database (non-blocking)
        await self._queue_session_for_persistence(
            session_id=session_id,
            owner_hash=owner_hash,
            agent_type=agent_enum.value,
            model_id=model_id,
            title=session_info["title"],
            description=session_info["description"],
            settings=session_settings,
            metadata=session_metadata,
        )

        # Cache in Redis & memory for faster lookups (immediate, non-blocking)
        await redis_service.set(
            f"agent_session:{session_id}",
            session_info,
            expire=3600 * 24,
        )
        self.active_sessions[str(session_id)] = session_info

        return session_info

    async def get_user_sessions(self, user_identifier: Optional[str]) -> List[Dict[str, Any]]:
        """Return all sessions belonging to the current user."""
        if not database_service.is_database_available():
            # Return in-memory sessions for the user
            owner_hash = normalize_owner_identifier(user_identifier)
            if owner_hash is None:
                return []
            
            user_sessions = []
            for session_id, session_info in self.active_sessions.items():
                if session_info.get("user_id") == owner_hash:
                    user_sessions.append(session_info)
            
            logger.info(f"Returning {len(user_sessions)} in-memory sessions for user {owner_hash}")
            return user_sessions
            
        owner_hash = normalize_owner_identifier(user_identifier)
        if owner_hash is None:
            return []

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentSessionRecord).where(AgentSessionRecord.owner_hash == owner_hash).order_by(
                        AgentSessionRecord.updated_at.desc()
                    )
                )
                records = result.scalars().all()
                return [self._record_to_session_info(record) for record in records]
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to load user sessions: %s", exc)
        return []

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages."""
        cache_removed = False
        if session_id in self.active_sessions:
            cache_removed = True

        # Always clear Redis cache entry; this is idempotent
        await redis_service.delete(f"agent_session:{session_id}")

        # Short-circuit when database is not available; rely on cache removal
        if not database_service.is_database_available():
            if cache_removed:
                self.active_sessions.pop(session_id, None)
            return cache_removed

        rows_deleted = 0
        try:
            # Validate and parse session_id as UUID
            try:
                session_uuid = uuid.UUID(session_id)
            except ValueError as e:
                logger.error(f"Invalid session_id format '{session_id}': {e}")
                # Still remove from cache if present
                if cache_removed:
                    self.active_sessions.pop(session_id, None)
                return cache_removed

            async for db_session in database_service.get_session():
                # Delete the session - CASCADE will handle messages automatically
                delete_result = await db_session.execute(
                    delete(AgentSessionRecord).where(AgentSessionRecord.id == session_uuid)
                )
                await db_session.commit()
                rows_deleted = delete_result.rowcount or 0
                break  # We only need the first available session/connection

            logger.info(f"Deleted agent session {session_id}: {rows_deleted} row(s) deleted")

            if rows_deleted or cache_removed:
                self.active_sessions.pop(session_id, None)
            return bool(rows_deleted or cache_removed)
        except (SQLAlchemyError, ValueError, RuntimeError) as exc:
            logger.exception("Failed to delete agent session %s: %s", session_id, exc)
            return False

    async def get_agent_for_session(self, session_id: str) -> Agent:
        """Get agent instance for a given session."""
        session_info = await self._get_session_info(session_id)
        if not session_info:
            raise ValueError(f"Session not found: {session_id}")

        try:
            agent_enum = AgentType(session_info["agent_type"])
        except ValueError:
            raise ValueError(f"Unsupported agent type for session: {session_info['agent_type']}")

        agent = get_agent(
            agent_type=agent_enum,
            user_id=session_info.get("user_id"),
            session_id=session_id,
            model_id=session_info.get("model_id", "gpt-5-mini"),
            provider=session_info.get("provider"),
            settings=session_info.get("settings"),
            debug_mode=False,
        )
        return agent

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------
    async def send_message(
        self,
        session_id: str,
        message: str,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Send a message to an agent and stream / return the response.
        Loads session history to provide context to the agent.
        """
        session_info = await self._get_session_info(session_id)
        if not session_info:
            yield "Session not found"
            return

        owner_hash = session_info.get("user_id")
        agent = await self.get_agent_for_session(session_id)

        # Agno handles history natively via add_history_to_context=True + db on each agent.
        # No need to manually prepend history — Agno's context engine includes recent runs automatically.

        # Only store messages if database is available
        if database_service.is_database_available():
            await self._store_message(
                session_id=session_id,
                role=AgentMessageRole.USER,
                content=message,
                tool_calls=None,
            )

        if stream:
            assistant_text = ""
            try:
                run_response = agent.arun(message, stream=True)
                async for chunk in run_response:
                    if chunk.content:
                        assistant_text += chunk.content
                        yield chunk.content

                # Only store assistant message if database is available
                if database_service.is_database_available():
                    await self._store_message(
                        session_id=session_id,
                        role=AgentMessageRole.ASSISTANT,
                        content=assistant_text,
                        tool_calls=None,
                    )
                    await self._touch_session(session_id)

            except Exception as exc:  # pragma: no cover - safety net
                logger.exception("Error streaming response for session %s: %s", session_id, exc)
                error_msg = f"I apologize, but I encountered an error: {exc}"
                # Only store error message if database is available
                if database_service.is_database_available():
                    await self._store_message(
                        session_id=session_id,
                        role=AgentMessageRole.ASSISTANT,
                        content=error_msg,
                        tool_calls=None,
                    )
                yield error_msg
        else:
            try:
                response = await agent.arun(message, stream=False)
                assistant_text = response.content if response else ""
            except Exception as exc:  # pragma: no cover - safety net
                logger.exception("Error generating response for session %s: %s", session_id, exc)
                assistant_text = f"I apologize, but I encountered an error: {exc}"

            # Only store messages if database is available
            if database_service.is_database_available():
                await self._store_message(
                    session_id=session_id,
                    role=AgentMessageRole.ASSISTANT,
                    content=assistant_text,
                    tool_calls=None,
                )
                await self._touch_session(session_id)
            yield assistant_text

    async def send_message_sync(self, session_id: str, message: str) -> str:
        """
        Send a message to an agent and get a complete (non-streaming) response.
        """
        response_chunks = []
        async for chunk in self.send_message(session_id, message, stream=False):
            response_chunks.append(chunk)
        return "".join(response_chunks)

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        Flushes any pending messages from Redis first to ensure completeness.
        """
        if not database_service.is_database_available():
            logger.warning("Database not available, returning empty history")
            return []

        # Flush pending messages so recently sent messages are included
        try:
            await self._flush_pending_messages()
        except Exception as exc:
            logger.warning("Failed to flush pending messages before history load: %s", exc)

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentMessageRecord)
                    .where(AgentMessageRecord.session_id == uuid.UUID(session_id))
                    .order_by(AgentMessageRecord.created_at.asc())
                )
                records = result.scalars().all()
                return [
                    {
                        "id": str(record.id),
                        "role": record.role.value,
                        "content": record.content,
                        "tool_calls": record.tool_calls or [],
                        "metadata": record.meta or {},
                        "created_at": record.created_at.isoformat(),
                        "token_count": record.token_count,
                    }
                    for record in records
                ]
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to load session history for %s: %s", session_id, exc)
        return []

    async def get_session(self, session_id: str, owner_identifier: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return session information if owned by the requester."""
        owner_hash = normalize_owner_identifier(owner_identifier)
        session_info = await self._get_session_info(session_id)
        if not session_info:
            return None
        if owner_hash and session_info.get("user_id") != owner_hash:
            return None
        return session_info

    async def update_session(
        self,
        session_id: str,
        owner_identifier: Optional[str],
        *,
        settings: Optional[dict] = None,
        metadata: Optional[dict] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Update session metadata/settings for the owning user."""
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return False

        # Get current session info
        session_info = await self._get_session_info(session_id)
        if not session_info:
            return False
        
        # Verify ownership
        if session_info.get("user_id") != owner_hash:
            return False

        current_settings = dict(session_info.get("settings") or {})
        current_metadata = dict(session_info.get("metadata") or {})

        new_settings = dict(settings) if settings is not None else dict(current_settings)
        new_metadata = dict(current_metadata)
        if metadata is not None:
            new_metadata.update(metadata)

        provider_override = new_settings.get("provider") or new_metadata.get("provider")
        normalized_provider = (provider_override or session_info.get("provider") or "openai").strip().lower()

        if new_settings.get("provider") != normalized_provider:
            new_settings["provider"] = normalized_provider
        if new_metadata.get("provider") != normalized_provider:
            new_metadata["provider"] = normalized_provider

        model_override = new_settings.get("model") or new_metadata.get("model")
        if model_override is None:
            model_override = session_info.get("model_id")
        new_model_id = str(model_override).strip() if model_override else None
        if new_model_id:
            new_settings["model"] = new_model_id

        provider_changed = normalized_provider != session_info.get("provider")
        model_changed = bool(new_model_id) and new_model_id != session_info.get("model_id")
        settings_changed = new_settings != current_settings
        metadata_changed = new_metadata != current_metadata

        # Update session info in memory
        update_values: Dict[str, Any] = {
            "updated_at": datetime.utcnow().isoformat(),
            "last_activity_at": datetime.utcnow().isoformat(),
        }
        if settings_changed:
            update_values["settings"] = new_settings
        if metadata_changed:
            update_values["metadata"] = new_metadata
        if provider_changed:
            update_values["provider"] = normalized_provider
        if model_changed:
            update_values["model_id"] = new_model_id
        if title is not None:
            update_values["title"] = title
        if description is not None:
            update_values["description"] = description

        # Merge updates into session info
        session_info.update(update_values)

        # Update caches immediately (always works)
        self.active_sessions[session_id] = session_info
        await redis_service.set(
            f"agent_session:{session_id}",
            session_info,
            expire=3600 * 24,
        )

        # Update database if available
        if database_service.is_database_available():
            try:
                db_update_values = {
                    "updated_at": datetime.utcnow(),
                    "last_activity_at": datetime.utcnow(),
                }
                if settings_changed:
                    db_update_values["settings"] = new_settings
                if metadata_changed:
                    db_update_values["meta"] = new_metadata
                if model_changed:
                    db_update_values["model_id"] = new_model_id
                if title is not None:
                    db_update_values["title"] = title
                if description is not None:
                    db_update_values["description"] = description

                async for db_session in database_service.get_session():
                    await db_session.execute(
                        update(AgentSessionRecord)
                        .where(
                            AgentSessionRecord.id == uuid.UUID(session_id),
                            AgentSessionRecord.owner_hash == owner_hash,
                        )
                        .values(**db_update_values)
                    )
                    await db_session.commit()
                    
                logger.debug(f"Updated session {session_id} in database")
            except (SQLAlchemyError, ValueError) as exc:
                logger.exception("Failed to update session %s in database: %s", session_id, exc)
                # Database update failed, but we already updated caches, so return success
                # The caches will be refreshed when the session is next loaded
        
        return True

    async def append_messages(
        self,
        session_id: str,
        owner_identifier: Optional[str],
        messages: List[Dict[str, Any]],
    ) -> bool:
        owner_hash = normalize_owner_identifier(owner_identifier)
        if not owner_hash:
            return False

        session_info = await self._get_session_info(session_id)
        if not session_info or session_info.get("user_id") != owner_hash:
            return False

        try:
            for message in messages:
                role_value = message.get("role")
                content = message.get("content")
                if not role_value or not content:
                    continue

                try:
                    role_enum = AgentMessageRole(role_value)
                except ValueError:
                    logger.debug("Skipping unknown message role: %s", role_value)
                    continue

                await self._store_message(
                    session_id=session_id,
                    role=role_enum,
                    content=content,
                    tool_calls=message.get("tool_calls"),
                )

            await self._touch_session(session_id)
            return True
        except Exception as exc:
            logger.exception("Failed to append messages to session %s: %s", session_id, exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    
    # ---- Deferred Persistence Methods ----
    # These queue data for async persistence instead of blocking immediately
    
    async def _queue_session_for_persistence(
        self,
        session_id: uuid.UUID,
        owner_hash: Optional[str],
        agent_type: str,
        model_id: str,
        title: Optional[str],
        description: Optional[str],
        settings: Optional[dict],
        metadata: Optional[dict],
    ) -> None:
        """Queue a session for deferred persistence to database (non-blocking)."""
        session_data = {
            "session_id": str(session_id),
            "owner_hash": owner_hash or "anonymous",
            "agent_type": agent_type,
            "model_id": model_id,
            "title": title,
            "description": description,
            "settings": settings or {},
            "metadata": metadata or {},
        }
        try:
            await redis_service.enqueue_job(PENDING_SESSIONS_QUEUE, session_data)
            logger.debug(f"Queued session {session_id} for persistence")
        except Exception as exc:
            logger.warning(f"Failed to queue session {session_id}: {exc}")
            # Fallback: try to persist immediately if queuing fails
            await self._persist_session_record_blocking(
                session_id, owner_hash, agent_type, model_id, title, description, settings, metadata
            )

    async def _queue_message_for_persistence(
        self,
        session_id: str,
        role: AgentMessageRole,
        content: str,
        tool_calls: Optional[list],
    ) -> None:
        """Queue a message for deferred persistence to database (non-blocking)."""
        message_data = {
            "session_id": session_id,
            "role": role.value,
            "content": content,
            "tool_calls": tool_calls or [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await redis_service.enqueue_job(PENDING_MESSAGES_QUEUE, message_data)
            logger.debug(f"Queued message for session {session_id}")
        except Exception as exc:
            logger.warning(f"Failed to queue message for {session_id}: {exc}")

    async def start_background_persistence_flush(self) -> None:
        """Start background task that periodically flushes pending sessions and messages to database."""
        if self._flush_task is not None:
            return  # Already running
        
        async def flush_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(30)  # Flush every 30 seconds
                    await self._flush_pending_sessions()
                    await self._flush_pending_messages()
                except Exception as exc:
                    logger.error(f"Error in persistence flush loop: {exc}")

        self._flush_task = asyncio.create_task(flush_loop())
        logger.info("Started background persistence flush task")

    async def stop_background_persistence_flush(self) -> None:
        """Stop the background persistence flush task."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
            logger.info("Stopped background persistence flush task")

    async def _flush_pending_sessions(self) -> None:
        """Flush all pending sessions from Redis queue to database."""
        if not database_service.is_database_available():
            logger.debug("Database not available, skipping session flush")
            return

        try:
            while True:
                session_data = await redis_service.dequeue_job(PENDING_SESSIONS_QUEUE, timeout=1)
                if not session_data:
                    break

                try:
                    session_id_str = session_data["session_id"]
                    session_id = uuid.UUID(session_id_str)

                    # Merge with current in-memory state which may have been
                    # updated since queuing (e.g. title generated after creation)
                    current_state = self.active_sessions.get(session_id_str, {})
                    title = current_state.get("title") or session_data.get("title")
                    description = current_state.get("description") or session_data.get("description")
                    settings = current_state.get("settings") or session_data.get("settings")
                    metadata = current_state.get("metadata") or session_data.get("metadata")

                    await self._persist_session_record_blocking(
                        session_id=session_id,
                        owner_hash=session_data.get("owner_hash"),
                        agent_type=session_data.get("agent_type"),
                        model_id=session_data.get("model_id"),
                        title=title,
                        description=description,
                        settings=settings,
                        metadata=metadata,
                    )
                    logger.debug(f"Flushed session {session_id} to database")
                except Exception as exc:
                    logger.error(f"Failed to flush session: {exc}")
                    # Re-queue for retry
                    await redis_service.enqueue_job(PENDING_SESSIONS_QUEUE, session_data)
        except Exception as exc:
            logger.warning(f"Error flushing pending sessions: {exc}")

    async def _flush_pending_messages(self) -> None:
        """Flush all pending messages from Redis queue to database."""
        if not database_service.is_database_available():
            logger.debug("Database not available, skipping message flush")
            return

        try:
            while True:
                message_data = await redis_service.dequeue_job(PENDING_MESSAGES_QUEUE, timeout=1)
                if not message_data:
                    break
                
                try:
                    session_id = message_data.get("session_id")
                    role = AgentMessageRole(message_data.get("role"))
                    content = message_data.get("content")
                    tool_calls = message_data.get("tool_calls")

                    # Use the original timestamp from when the message was sent,
                    # not the current time, to preserve correct message ordering
                    original_timestamp = message_data.get("timestamp")
                    created_at = (
                        datetime.fromisoformat(original_timestamp)
                        if original_timestamp
                        else datetime.utcnow()
                    )

                    message = AgentMessageRecord(
                        session_id=uuid.UUID(session_id),
                        role=role,
                        content=content,
                        tool_calls=tool_calls or [],
                        metadata={},
                        token_count=self._estimate_tokens(content),
                        created_at=created_at,
                    )
                    async for db_session in database_service.get_session():
                        db_session.add(message)
                        await db_session.commit()
                    logger.debug(f"Flushed message to database for session {session_id}")
                except Exception as exc:
                    logger.error(f"Failed to flush message: {exc}")
                    # Re-queue for retry
                    await redis_service.enqueue_job(PENDING_MESSAGES_QUEUE, message_data)
        except Exception as exc:
            logger.warning(f"Error flushing pending messages: {exc}")

    async def _persist_session_record_blocking(
        self,
        session_id: uuid.UUID,
        owner_hash: Optional[str],
        agent_type: str,
        model_id: str,
        title: Optional[str],
        description: Optional[str],
        settings: Optional[dict],
        metadata: Optional[dict],
    ) -> None:
        """Directly persist a session record to database (blocking). Use sparingly."""
        record = AgentSessionRecord(
            id=session_id,
            owner_hash=owner_hash or "anonymous",
            agent_type=agent_type,
            model_id=model_id,
            title=title,
            description=description,
            status=AgentSessionStatus.ACTIVE,
            settings=settings or {},
            meta=metadata or {},
        )
        try:
            async for session in database_service.get_session():
                await session.merge(record)
                await session.commit()
        except SQLAlchemyError as exc:
            logger.exception("Failed to persist agent session %s: %s", session_id, exc)

    async def _get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id in self.active_sessions:
            return self._normalize_session_info(self.active_sessions[session_id])

        # Try Redis cache first (if available)
        redis_key = f"agent_session:{session_id}"
        session_info = await redis_service.get(redis_key)
        if session_info:
            normalized = self._normalize_session_info(session_info)
            self.active_sessions[session_id] = normalized
            return normalized

        # If database is not available, check if we have it in memory
        if not database_service.is_database_available():
            cached = self.active_sessions.get(session_id)
            return self._normalize_session_info(cached) if cached else None

        try:
            async for session in database_service.get_session():
                result = await session.execute(
                    select(AgentSessionRecord).where(AgentSessionRecord.id == uuid.UUID(session_id))
                )
                record = result.scalar_one_or_none()
                if not record:
                    return None
                session_info = self._record_to_session_info(record)
                normalized = self._normalize_session_info(session_info)
                self.active_sessions[session_id] = normalized
                await redis_service.set(redis_key, normalized, expire=3600 * 24)
                return normalized
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("Failed to load session info for %s: %s", session_id, exc)
        return None

    def _record_to_session_info(self, record: AgentSessionRecord) -> Dict[str, Any]:
        return {
            "session_id": str(record.id),
            "agent_type": record.agent_type,
            "user_id": record.owner_hash,
            "model_id": record.model_id,
            "provider": (record.meta or {}).get("provider", "openai"),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "status": record.status.value,
            "title": record.title,
            "description": record.description,
            "metadata": record.meta or {},
            "settings": record.settings or {},
        }

    @staticmethod
    def _normalize_session_info(session_info: Dict[str, Any]) -> Dict[str, Any]:
        session_info.setdefault("provider", "openai")
        session_info.setdefault("metadata", {})
        session_info.setdefault("settings", {})
        return session_info

    async def _store_message(
        self,
        session_id: str,
        role: AgentMessageRole,
        content: str,
        tool_calls: Optional[list],
    ) -> None:
        """
        Store a message in Redis queue for deferred persistence.
        Messages are flushed to database periodically by background task.
        This is non-blocking and ensures responsiveness even if database is slow.
        """
        try:
            # Verify session exists in cache
            session_info = await self._get_session_info(session_id)
            if not session_info:
                logger.warning("Cannot store message: session %s not found", session_id)
                return

            # Queue message for async persistence (non-blocking)
            await self._queue_message_for_persistence(
                session_id=session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
            )
        except Exception as exc:
            logger.exception("Failed to queue message for session %s: %s", session_id, exc)

    async def _touch_session(self, session_id: str) -> None:
        """
        Update session activity timestamp.
        This is queued for deferred persistence to avoid blocking.
        """
        try:
            session_info = await self._get_session_info(session_id)
            if not session_info:
                return
            
            # Update in-memory cache immediately
            session_info["updated_at"] = datetime.utcnow().isoformat()
            session_info["last_activity_at"] = datetime.utcnow().isoformat()
            
            # Cache in Redis
            await redis_service.set(
                f"agent_session:{session_id}",
                session_info,
                expire=3600 * 24,
            )
        except Exception as exc:
            logger.warning("Failed to update session activity for %s: %s", session_id, exc)

    @staticmethod
    def _estimate_tokens(content: str) -> int:
        """Rough token estimation used for metrics."""
        if not content:
            return 0
        return max(1, len(content) // 4)


# Global service instance
agent_service = AgentService()
