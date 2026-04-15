"""Server-side chat completions with automatic tool execution."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel

from app.services.anyllm_service import anyllm_service
from app.services.tools.tool_registry import (
    execute_tool,
    get_system_prompt,
    get_tool_definitions,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/completions", tags=["Chat"])

MAX_TOOL_ITERATIONS = 10


class ChatCompletionRequest(BaseModel):
    message: str
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    session_id: str | None = None


class ToolUsed(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ChatCompletionResponse(BaseModel):
    response: str
    tools_used: list[ToolUsed] = []
    session_id: str


@router.post("", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    user=Depends(get_current_user),
):
    """Complete a chat message with automatic tool execution.

    Sends the message to an LLM with all available tools. If the LLM
    requests tool calls, they are executed server-side and the results
    fed back until a final text response is produced.
    """
    session_id = request.session_id or str(uuid.uuid4())

    system_prompt = get_system_prompt()
    tools = get_tool_definitions()

    tools_used: list[dict[str, Any]] = []
    result: dict[str, Any] = {}
    previous_response_id: str | None = None
    use_responses = anyllm_service._supports_responses(request.provider)

    if use_responses:
        # ── Responses API path: use previous_response_id for chaining ──
        # First call with user message
        result = await anyllm_service.response({
            "provider": request.provider,
            "model": request.model,
            "input_data": request.message,
            "instructions": system_prompt,
            "tools": tools,
            "tool_choice": "auto",
            "store": True,
        })
        previous_response_id = result.get("response_id")

        for _ in range(MAX_TOOL_ITERATIONS):
            tool_calls = result.get("tool_calls")
            if not tool_calls:
                break

            # Execute each tool and build output items
            tool_outputs: list[dict[str, Any]] = []
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}

                logger.info(f"Chat completions: executing tool '{name}'")
                tool_result = await execute_tool(name, args)
                tools_used.append({"name": name, "arguments": args, "result": tool_result})

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": tc.get("id", ""),
                    "output": json.dumps(tool_result),
                })

            # Chain with previous_response_id — no resending full history
            result = await anyllm_service.response({
                "provider": request.provider,
                "model": request.model,
                "input_data": tool_outputs,
                "instructions": system_prompt,
                "tools": tools,
                "tool_choice": "auto",
                "previous_response_id": previous_response_id,
                "store": True,
            })
            previous_response_id = result.get("response_id")
    else:
        # ── Completions API fallback: accumulate messages ──
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message},
        ]

        for _ in range(MAX_TOOL_ITERATIONS):
            result = await anyllm_service.completion({
                "provider": request.provider,
                "model": request.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            })

            tool_calls = result.get("tool_calls")
            if not tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": result.get("content") or None,
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}

                logger.info(f"Chat completions: executing tool '{name}'")
                tool_result = await execute_tool(name, args)
                tools_used.append({"name": name, "arguments": args, "result": tool_result})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", str(uuid.uuid4())),
                    "content": json.dumps(tool_result),
                })

    final_text = result.get("content") or "I completed the requested actions."
    return ChatCompletionResponse(
        response=final_text,
        tools_used=[ToolUsed(**t) for t in tools_used],
        session_id=session_id,
    )
