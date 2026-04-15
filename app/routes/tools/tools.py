"""Tool calling endpoints for LLM function calling integration."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.tools.tool_registry import (
    execute_tool,
    get_system_prompt,
    get_tool_definitions,
)

router = APIRouter(prefix="/tools", tags=["System"])


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


class ToolExecuteResponse(BaseModel):
    result: dict[str, Any]


@router.get("")
async def list_tools():
    """Return all available tool definitions for LLM function calling."""
    return {
        "tools": get_tool_definitions(),
        "system_prompt": get_system_prompt(),
    }


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool_endpoint(request: ToolExecuteRequest):
    """Execute a tool call and return the result."""
    result = await execute_tool(request.name, request.arguments)
    if "error" in result and not any(
        k for k in result if k != "error"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return ToolExecuteResponse(result=result)
