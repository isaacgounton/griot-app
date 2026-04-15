"""Chat session management endpoints.

Reuses the agent service for session persistence but provides a simpler API
tailored for the general chat interface (not agent-specific).
"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.agents.agent_service import agent_service
from app.utils.auth import get_current_user

# Dedicated router for chat sessions mounted under /api/v1/chat.
router = APIRouter(prefix="/sessions", tags=["Chat"])


class CreateChatSessionRequest(BaseModel):
    """Request model for creating a new chat session."""
    model_id: str = "deepseek-chat"
    provider: Optional[str] = "deepseek"
    title: Optional[str] = None
    settings: Optional[dict] = None


class ChatSessionResponse(BaseModel):
    """Response model for chat session information."""
    session_id: str
    user_id: Optional[str]
    model_id: str
    provider: str
    created_at: str
    updated_at: Optional[str] = None
    title: Optional[str] = None
    settings: Optional[dict] = None


class UpdateChatSessionRequest(BaseModel):
    """Payload for updating chat session."""
    title: Optional[str] = None
    settings: Optional[dict] = None
    messages: Optional[List[Dict[str, Any]]] = None


class GenerateTitleRequest(BaseModel):
    """Request payload for generating AI-based chat title."""
    message: str
    model_id: str = "deepseek-chat"
    provider: str = "deepseek"


class GenerateTitleResponse(BaseModel):
    """Response model for generated title."""
    title: str
    session_id: str


def _get_user_id(current_user: Dict[str, Any]) -> str:
    """Extract user_id from current_user, falling back to a stable identifier."""
    user_id = current_user.get("user_id")
    if user_id:
        return str(user_id)
    # Fallback for env API key auth where user_id is None
    return current_user.get("key_id") or "anonymous"


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: CreateChatSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new chat session and return metadata."""
    user_id = _get_user_id(current_user)
    try:
        session_info = await agent_service.create_session(
            agent_type="chat",
            user_identifier=user_id,
            model_id=request.model_id,
            provider=request.provider,
            title=request.title,
            settings=request.settings,
        )
        return ChatSessionResponse(
            session_id=session_info["session_id"],
            user_id=session_info.get("user_id"),
            model_id=session_info["model_id"],
            provider=session_info.get("provider", request.provider),
            created_at=session_info["created_at"],
            updated_at=session_info.get("updated_at"),
            title=session_info.get("title"),
            settings=session_info.get("settings"),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(exc)}"
        ) from exc


@router.get("")
async def list_chat_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all chat sessions for the authenticated user."""
    user_id = _get_user_id(current_user)
    try:
        sessions = await agent_service.get_user_sessions(user_id)
        chat_sessions = [s for s in sessions if s.get("agent_type") == "chat"]
        return {"sessions": chat_sessions}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat sessions: {str(exc)}"
        ) from exc


@router.get("/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific chat session by ID."""
    user_id = _get_user_id(current_user)
    try:
        session = await agent_service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.get("agent_type") != "chat":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
        return session
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat session: {str(exc)}"
        ) from exc


@router.get("/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get messages for a chat session."""
    user_id = _get_user_id(current_user)
    try:
        session = await agent_service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.get("agent_type") != "chat":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

        messages = await agent_service.get_session_history(session_id)
        return {"session_id": session_id, "messages": messages}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat messages: {str(exc)}"
        ) from exc


@router.put("/{session_id}")
async def update_chat_session(
    session_id: str,
    request: UpdateChatSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update chat session title or settings."""
    user_id = _get_user_id(current_user)
    try:
        updated = await agent_service.update_session(
            session_id=session_id,
            owner_identifier=user_id,
            title=request.title,
            settings=request.settings,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # If messages are provided, append them to the session
        if request.messages:
            appended = await agent_service.append_messages(session_id, user_id, request.messages)
            if not appended:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist chat messages"
                )

        return {"session_id": session_id, "status": "updated"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chat session: {str(exc)}"
        ) from exc


@router.delete("/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a chat session."""
    try:
        success = await agent_service.delete_session(session_id)
        if success:
            return {"message": f"Chat session {session_id} deleted successfully"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or could not be deleted"
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(exc)}"
        ) from exc


@router.post("/generate-title", response_model=GenerateTitleResponse)
async def generate_chat_title(
    request: GenerateTitleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate an AI-based title for a chat session from the first message."""
    try:
        from app.services.anyllm_service import anyllm_service
        from loguru import logger as log

        message_preview = request.message[:500]
        if len(request.message) > 500:
            message_preview += "..."

        title_instructions = (
            "Generate a concise 2-5 word title for this chat message. "
            "Use title case. Do NOT include quotes, punctuation, or extra text - just the title."
        )

        raw_title = ""

        # Try with user's selected model first, then fallback
        attempts = [
            (request.model_id, request.provider),
            ("gpt-4o-mini", "openai"),
        ]

        for model_id, provider in attempts:
            try:
                log.debug(f"Generating title with {provider}/{model_id}")
                result = await anyllm_service.response({
                    "provider": provider,
                    "model": model_id,
                    "input_data": message_preview,
                    "instructions": title_instructions,
                    "messages": [{"role": "user", "content": message_preview}],
                    "temperature": 0.3,
                    "max_tokens": 50,
                })
                raw_title = (result.get("content") or "").strip()
                if raw_title:
                    break
            except Exception as e:
                log.warning(f"Title generation failed with {provider}/{model_id}: {e}")
                continue

        title = raw_title
        for prefix in ["Title:", "The title is", "Here is a title", "A suitable title would be"]:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()

        title = title.strip('"').strip("'").strip("`").strip(",").strip(".")

        if len(title) > 50:
            title = title[:50].strip()

        # If AI failed completely, use first words of the message
        if not title or len(title) < 3:
            words = request.message.split()[:5]
            title = " ".join(words)[:40].strip()
            if not title:
                title = "New Chat"

        return GenerateTitleResponse(title=title, session_id="")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate title: {str(exc)}"
        ) from exc


__all__ = ["router"]
