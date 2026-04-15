"""Agent session management endpoints."""

from typing import Optional, List, Dict, Any
import json
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from app.services.agents.agent_service import agent_service
from app.utils.auth import get_api_key, get_current_user

# Dedicated router for session-related routes mounted under /api/v1/agents.
router = APIRouter(prefix="/sessions", tags=["Agents"])


class CreateSessionRequest(BaseModel):
    """Request model for creating a new agent session."""
    agent_type: str
    model_id: str = "gpt-5-mini"
    provider: Optional[str] = "openai"
    title: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None
    metadata: Optional[dict] = None


class SessionResponse(BaseModel):
    """Response model for session information."""
    session_id: str
    agent_type: str
    user_id: Optional[str]
    model_id: str
    provider: str
    created_at: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[dict] = None
    settings: Optional[dict] = None


class MessageRequest(BaseModel):
    """Request payload for sending a message to an agent."""
    message: str
    stream: bool = True


class MessageResponse(BaseModel):
    """Streaming message response model."""
    content: str
    role: str
    timestamp: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    """Payload for updating session metadata or settings."""
    title: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None
    metadata: Optional[dict] = None
    messages: Optional[List[Dict[str, Any]]] = None


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    api_key: str = Depends(get_api_key),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new agent session and return metadata."""
    try:
        session_info = await agent_service.create_session(
            agent_type=request.agent_type,
            user_identifier=api_key,
            model_id=request.model_id,
            provider=request.provider,
            title=request.title,
            description=request.description,
            settings=request.settings,
            metadata=request.metadata,
        )
        return SessionResponse(**session_info)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(exc)}"
        ) from exc


@router.get("")
async def list_sessions(
    api_key: str = Depends(get_api_key),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all sessions for the authenticated user."""
    try:
        sessions = await agent_service.get_user_sessions(api_key)
        return {"sessions": sessions}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(exc)}"
        ) from exc


@router.post("/{session_id}/chat")
async def chat_with_agent(session_id: str, request: MessageRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Send a chat message to an agent session."""
    try:
        if request.stream:
            return StreamingResponse(
                _stream_agent_response(session_id, request.message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        response_content = await agent_service.send_message_sync(
            session_id=session_id,
            message=request.message,
        )
        return MessageResponse(content=response_content, role="assistant", timestamp=None)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(exc)}"
        ) from exc


async def _stream_agent_response(session_id: str, message: str):
    """Stream agent responses as server-sent events."""
    try:
        async for chunk in agent_service.send_message(session_id, message, stream=True):
            chunk_data = {"content": chunk}
            yield f"data: {json.dumps(chunk_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        error_message = f"Error: {str(exc)}"
        error_data = {"error": error_message}
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"


@router.get("/{session_id}/history")
async def get_session_history(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the stored history for a session."""
    try:
        history = await agent_service.get_session_history(session_id)
        return {"session_id": session_id, "messages": history}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session history: {str(exc)}"
        ) from exc


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    api_key: str = Depends(get_api_key),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update session metadata or settings."""
    try:
        updated = await agent_service.update_session(
            session_id=session_id,
            owner_identifier=api_key,
            settings=request.settings,
            metadata=request.metadata,
            title=request.title,
            description=request.description,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return {"session_id": session_id, "status": "updated"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(exc)}"
        ) from exc


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = "json",
    api_key: str = Depends(get_api_key),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Export a session history in the requested format."""
    session = await agent_service.get_session(session_id, api_key)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = await agent_service.get_session_history(session_id)
    fmt = format.lower()

    if fmt == "json":
        payload = {"session": session, "messages": messages}
        content = json.dumps(payload, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="session_{session_id}.json"'},
        )

    if fmt in {"markdown", "md", "txt"}:
        lines: List[str] = []
        title = session.get("title") or "Agent Session"
        if fmt in {"markdown", "md"}:
            lines.append(f"# {title}")
            lines.append("")
            lines.append(f"*Agent:* {session.get('agent_type')}")
            lines.append(f"*Model:* {session.get('model_id')}")
            lines.append("")
            for message in messages:
                prefix = message.get("role", "user").capitalize()
                lines.append(f"**{prefix}:** {message.get('content', '')}")
                lines.append("")
            media_type = "text/markdown"
            extension = "md"
        else:
            lines.append(f"Session: {title}")
            lines.append(f"Agent: {session.get('agent_type')}")
            lines.append(f"Model: {session.get('model_id')}")
            lines.append("Messages:")
            for message in messages:
                prefix = message.get("role", "user").capitalize()
                lines.append(f"- {prefix}: {message.get('content', '')}")
            media_type = "text/plain"
            extension = "txt"

        content = "\n".join(lines)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="session_{session_id}.{extension}"'},
        )

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["role", "content", "timestamp"])
        for message in messages:
            writer.writerow([
                message.get("role"),
                message.get("content"),
                message.get("created_at"),
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="session_{session_id}.csv"'},
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported export format: {format}")


@router.post("/import")
async def import_session(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Import a session from a JSON export file."""
    try:
        contents = await file.read()
        data = json.loads(contents.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session file. Expected JSON export.") from exc

    session_data = data.get("session", {})
    messages = data.get("messages", [])

    agent_type = session_data.get("agent_type") or "research_agent"
    model_id = session_data.get("model_id") or "gpt-5-mini"

    session_info = await agent_service.create_session(
        agent_type=agent_type,
        user_identifier=api_key,
        model_id=model_id,
        provider=session_data.get("provider"),
        title=session_data.get("title"),
        description=session_data.get("description"),
        settings=session_data.get("settings"),
        metadata=session_data.get("metadata"),
    )

    await agent_service.append_messages(session_info["session_id"], api_key, messages)

    return session_info


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a stored session."""
    try:
        success = await agent_service.delete_session(session_id)
        if success:
            return {"message": f"Session {session_id} deleted successfully"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(exc)}"
        ) from exc


__all__ = ["router"]
