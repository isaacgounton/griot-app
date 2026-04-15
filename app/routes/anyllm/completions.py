"""AnyLLM completion routes - universal LLM provider integration."""

from typing import Any, Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.anyllm_service import anyllm_service

router = APIRouter(prefix="/anyllm", tags=["AnyLLM"])


class ListModelsRequest(BaseModel):
    provider: str


class MediaContent(BaseModel):
    type: str
    text: str | None = None
    url: str | None = None
    alt_text: str | None = None
    filename: str | None = None
    size: int | None = None
    mime_type: str | None = None


class ToolCallFunction(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: ToolCallFunction


class Message(BaseModel):
    role: str
    content: list[MediaContent] | str
    thinking: str | None = None
    model: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class CompletionRequest(BaseModel):
    provider: str
    model: str
    messages: list[dict[str, Any]]
    messages_multimodal: list[Message] | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None
    stream: bool | None = True
    n: int | None = None
    stop: Union[str, list[str]] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    seed: int | None = None
    user: str | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: Union[str, dict[str, Any]] | None = None
    parallel_tool_calls: bool | None = None
    logprobs: bool | None = None
    top_logprobs: int | None = None
    logit_bias: dict[str, float] | None = None
    max_completion_tokens: int | None = None
    reasoning_effort: str | None = None


@router.get("/")
async def root():
    """AnyLLM integration endpoint"""
    return {"message": "AnyLLM integration for Griot", "version": "1.0.0"}


@router.get("/providers")
async def get_providers():
    """Get all providers that support list_models"""
    try:
        return await anyllm_service.get_providers()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list-models")
async def get_models(request: ListModelsRequest):
    """List available models for a provider"""
    try:
        return await anyllm_service.get_models(request.provider)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()

        # Handle API key errors (missing)
        if "api key is required" in error_msg or "missing api key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "API_KEY_MISSING",
                    "message": f"API key is required for provider '{request.provider}'. Please set the environment variable (e.g., ANTHROPIC_API_KEY for Anthropic) and restart the server.",
                    "provider": request.provider,
                    "suggestion": f"Set environment variable: {request.provider.upper()}_API_KEY"
                }
            )

        # Handle invalid provider errors
        if "provider not found" in error_msg or "unsupported provider" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PROVIDER_NOT_SUPPORTED",
                    "message": f"Provider '{request.provider}' is not supported or not available.",
                    "provider": request.provider
                }
            )

        # Handle authentication errors (invalid or expired API keys)
        if ("unauthorized" in error_msg or "authentication" in error_msg or 
            "invalid api key" in error_msg or "api key expired" in error_msg or
            "api key invalid" in error_msg or "expired" in error_msg):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "INVALID_API_KEY",
                    "message": f"The API key for provider '{request.provider}' is invalid or expired. Please update your API key.",
                    "provider": request.provider
                }
            )

        # Generic server error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SERVER_ERROR",
                "message": f"Failed to fetch models for provider '{request.provider}': {str(e)}",
                "provider": request.provider
            }
        )


@router.post("/completions")
async def create_completion(request: CompletionRequest):
    """Create a streaming completion using the specified model and provider"""
    try:
        return StreamingResponse(
            anyllm_service.stream_completion(request.model_dump()),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()

        # Handle API key errors
        if "api key is required" in error_msg or "missing api key" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "API_KEY_MISSING",
                    "message": f"API key is required for provider '{request.provider}'. Please set the environment variable (e.g., ANTHROPIC_API_KEY for Anthropic) and restart the server.",
                    "provider": request.provider,
                    "suggestion": f"Set environment variable: {request.provider.upper()}_API_KEY"
                }
            )

        # Handle authentication errors
        if "unauthorized" in error_msg or "authentication" in error_msg or "invalid api key" in error_msg:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "INVALID_API_KEY",
                    "message": f"The API key for provider '{request.provider}' is invalid or expired.",
                    "provider": request.provider
                }
            )

        # Handle model not found errors
        if "model not found" in error_msg or "invalid model" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MODEL_NOT_FOUND",
                    "message": f"Model '{request.model}' is not available for provider '{request.provider}'.",
                    "provider": request.provider,
                    "model": request.model
                }
            )

        # Generic server error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SERVER_ERROR",
                "message": f"Failed to create completion: {str(e)}",
                "provider": request.provider,
                "model": request.model
            }
        )