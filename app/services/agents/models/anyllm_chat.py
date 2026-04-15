"""
AnyLLM-backed chat model for Agno agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Type, Union

# Import any_llm functions with comprehensive fallback handling
try:
    from any_llm import acompletion, aresponses, completion, responses
    from any_llm import AnyLLM, LLMProvider
except ImportError as e:
    print(f"Warning: any_llm import failed: {e}")
    try:
        from any_llm_sdk import acompletion, completion
        aresponses = None  # type: ignore[assignment]
        responses = None  # type: ignore[assignment]
        AnyLLM = None  # type: ignore[assignment,misc]
        LLMProvider = None  # type: ignore[assignment,misc]
        print("Using any_llm_sdk import instead of any_llm (responses API unavailable)")
    except ImportError as e2:
        print(f"Warning: any_llm_sdk import also failed: {e2}")
        async def acompletion(**kwargs):  # type: ignore[misc]
            raise ImportError("any_llm not available - please install any-llm-sdk")

        def completion(**kwargs):  # type: ignore[misc]
            raise ImportError("any_llm not available - please install any-llm-sdk")

        aresponses = None  # type: ignore[assignment]
        responses = None  # type: ignore[assignment]
        AnyLLM = None  # type: ignore[assignment,misc]
        LLMProvider = None  # type: ignore[assignment,misc]
from pydantic import BaseModel

from agno.models.base import Model
from agno.models.message import Message
from agno.models.metrics import Metrics
from agno.models.response import ModelResponse
from agno.run.agent import RunOutput
from agno.utils.log import log_debug, log_error


@dataclass
class AnyLLMChat(Model):
    """
    Agno Model wrapper that routes requests through AnyLLM.

    This allows agents to leverage any provider supported by AnyLLM while keeping the
    standard Agno Agent tooling and streaming behaviour intact.
    """

    provider: str = "openai"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    request_params: Optional[Dict[str, Any]] = None

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Agno messages to the OpenAI-style payload AnyLLM expects."""
        formatted_messages: List[Dict[str, Any]] = []

        for i, msg in enumerate(messages):
            # Ensure content is always a string (never None or null)
            content = msg.content if msg.content is not None else ""
            if not isinstance(content, str):
                content = str(content)
            
            message_payload: Dict[str, Any] = {"role": msg.role, "content": content}

            if msg.tool_calls:
                message_payload["tool_calls"] = [
                    {
                        "id": tc.get("id"),
                        "type": tc.get("type", "function"),
                        "function": {
                            "name": tc.get("function", {}).get("name"),
                            "arguments": tc.get("function", {}).get("arguments", "{}"),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            if msg.role in {"tool", "function"}:
                tool_name: Optional[str] = None

                if msg.tool_call_id:
                    message_payload["tool_call_id"] = msg.tool_call_id
                # For tool/function messages, the name field is required by OpenAI API
                if msg.name:
                    tool_name = msg.name.strip() or None
                elif getattr(msg, "tool_name", None):
                    tool_name = str(getattr(msg, "tool_name")).strip() or None

                if not tool_name and msg.role == "tool":
                    # If name is missing, try to find it from tool_calls in previous messages
                    # This is a fallback to ensure OpenAI API compliance
                    for prev_msg in reversed(messages[:i]):
                        if prev_msg.tool_calls:
                            for tc in prev_msg.tool_calls:
                                if tc.get("id") == msg.tool_call_id:
                                    tool_name = tc.get("function", {}).get("name")
                                    if tool_name:
                                        break
                            if tool_name:
                                break

                if not tool_name:
                    # Final fallback: synthesize a deterministic but valid name
                    prefix = "tool" if msg.role == "tool" else "function"
                    if msg.tool_call_id:
                        tool_name = f"{prefix}_{msg.tool_call_id}"
                    else:
                        tool_name = f"{prefix}_response"

                message_payload["name"] = tool_name

            formatted_messages.append(message_payload)

        return formatted_messages

    def _sanitize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize messages to ensure all values are JSON-serializable and valid."""
        import json
        
        sanitized: List[Dict[str, Any]] = []
        raw_messages: List[Dict[str, Any]] = []
        for msg in messages:
            raw_messages.append(msg)
            sanitized_msg = {}
            for key, value in msg.items():
                # Ensure no null values in critical fields
                if value is None:
                    if key == "content":
                        sanitized_msg[key] = ""
                    elif key == "name" and msg.get("role") in {"tool", "function"}:
                        # For tool/function messages, name is required - skip this field if missing
                        continue  # Skip the name field when it's None; fallback logic should have filled it
                    else:
                        continue  # Skip None values for other fields
                elif isinstance(value, list):
                    # Handle lists (like tool_calls)
                    sanitized_list = []
                    for item in value:
                        if isinstance(item, dict):
                            sanitized_item = {}
                            for k, v in item.items():
                                if v is None:
                                    if k == "content":
                                        sanitized_item[k] = ""
                                    # else skip None values
                                elif isinstance(v, dict):
                                    # Recursively handle nested dicts (like 'function' in tool_calls)
                                    sanitized_dict = {}
                                    for nk, nv in v.items():
                                        if nv is None:
                                            if nk == "content":
                                                sanitized_dict[nk] = ""
                                            # else skip None
                                        else:
                                            sanitized_dict[nk] = nv
                                    if sanitized_dict:  # Only add if not empty
                                        sanitized_item[k] = sanitized_dict
                                else:
                                    sanitized_item[k] = v
                            if sanitized_item:  # Only add if not empty
                                sanitized_list.append(sanitized_item)
                        else:
                            sanitized_list.append(item)
                    if sanitized_list:
                        sanitized_msg[key] = sanitized_list
                elif isinstance(value, dict):
                    # Handle nested dicts
                    sanitized_dict = {}
                    for k, v in value.items():
                        if v is None:
                            if k == "content":
                                sanitized_dict[k] = ""
                            # else skip None values
                        else:
                            sanitized_dict[k] = v
                    if sanitized_dict:
                        sanitized_msg[key] = sanitized_dict
                else:
                    sanitized_msg[key] = value
            
            sanitized.append(sanitized_msg)

        # Ensure tool/function messages always have a valid `name` field
        for idx, sanitized_msg in enumerate(sanitized):
            role = sanitized_msg.get("role")
            if role not in {"tool", "function"}:
                continue

            if sanitized_msg.get("name"):
                continue

            raw_msg = raw_messages[idx]
            tool_name: Optional[str] = None

            # Prefer any explicit name provided on the raw message
            raw_name = raw_msg.get("name") or raw_msg.get("tool_name")
            if isinstance(raw_name, str) and raw_name.strip():
                tool_name = raw_name.strip()

            # Attempt to resolve from a matching tool_call_id in prior messages
            if not tool_name:
                tool_call_id = sanitized_msg.get("tool_call_id") or raw_msg.get("tool_call_id")
                if tool_call_id:
                    for prev in reversed(sanitized[:idx]):
                        for tool_call in prev.get("tool_calls", []):
                            if tool_call.get("id") == tool_call_id:
                                candidate = (tool_call.get("function") or {}).get("name")
                                if isinstance(candidate, str) and candidate.strip():
                                    tool_name = candidate.strip()
                                    break
                        if tool_name:
                            break

            # Fall back to a deterministic placeholder if still unresolved
            if not tool_name:
                tool_call_id = (
                    sanitized_msg.get("tool_call_id")
                    or raw_msg.get("tool_call_id")
                    or raw_msg.get("id")
                )
                suffix = f"_{tool_call_id}" if tool_call_id else "_response"
                tool_name = f"{role}{suffix}"

            sanitized_msg["name"] = tool_name

        return sanitized

    def _build_request_params(
        self,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build the keyword arguments for AnyLLM completion calls."""
        params: Dict[str, Any] = {
            "provider": self.provider,
            "model": self.id,
        }

        # Generation controls
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.max_completion_tokens is not None:
            params["max_completion_tokens"] = self.max_completion_tokens
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty

        if tools:
            params["tools"] = tools
            # Align with OpenAI behaviour: default to auto when tools provided
            params["tool_choice"] = tool_choice or "auto"
        elif tool_choice is not None:
            params["tool_choice"] = tool_choice

        if self.request_params:
            params.update(self.request_params)

        log_debug(f"Calling AnyLLM provider '{self.provider}' with params: {list(params.keys())}", log_level=2)
        return params

    # ── Responses API helpers ─────────────────────────────────────────

    _responses_support_cache: dict[str, bool] = field(default_factory=dict, repr=False, init=False)

    def _supports_responses(self) -> bool:
        """Check if the current provider supports the Responses API."""
        if AnyLLM is None or LLMProvider is None:
            return False
        if self.provider in self._responses_support_cache:
            return self._responses_support_cache[self.provider]
        try:
            provider_key = LLMProvider.from_string(self.provider)
            provider_class = AnyLLM.get_provider_class(provider_key)
            supported = getattr(provider_class, "SUPPORTS_RESPONSES", False)
        except Exception:
            supported = False
        self._responses_support_cache[self.provider] = supported
        return supported

    def _build_request_params_responses(
        self,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build keyword arguments for AnyLLM responses() calls."""
        params: Dict[str, Any] = {
            "provider": self.provider,
            "model": self.id,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.max_tokens is not None:
            params["max_output_tokens"] = self.max_tokens
        if self.max_completion_tokens is not None:
            params["max_output_tokens"] = self.max_completion_tokens
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice or "auto"
        elif tool_choice is not None:
            params["tool_choice"] = tool_choice
        if self.request_params:
            params.update(self.request_params)
        return params

    def _format_input(
        self, messages: List[Message]
    ) -> tuple[Any, str | None]:
        """Convert Agno messages to Responses API input_data + instructions."""
        instructions: str | None = None
        input_items: list[dict[str, Any]] = []

        for i, msg in enumerate(messages):
            content = msg.content if msg.content is not None else ""
            if not isinstance(content, str):
                content = str(content)

            if msg.role == "system":
                instructions = content
                continue

            if msg.role in ("tool", "function"):
                input_items.append({
                    "type": "function_call_output",
                    "call_id": msg.tool_call_id or "",
                    "output": content,
                })
                continue

            if msg.role == "assistant" and msg.tool_calls:
                for tc in msg.tool_calls:
                    fn = tc.get("function", {})
                    input_items.append({
                        "type": "function_call",
                        "call_id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "arguments": fn.get("arguments", "{}"),
                    })
                if content:
                    input_items.append({"role": "assistant", "content": content})
                continue

            input_items.append({"role": msg.role, "content": content})

        return input_items or "", instructions

    def _parse_responses_response(self, response: Any, **kwargs: Any) -> ModelResponse:
        """Convert a Responses API result into an Agno ModelResponse."""
        model_response = ModelResponse()

        # Extract text
        if hasattr(response, "output_text") and response.output_text:
            model_response.content = response.output_text
        elif hasattr(response, "output"):
            for item in response.output:
                if getattr(item, "type", "") == "message":
                    for part in getattr(item, "content", []):
                        if getattr(part, "type", "") == "output_text":
                            model_response.content = part.text
                            break
                    if model_response.content:
                        break

        # Extract tool calls
        if hasattr(response, "output"):
            calls = []
            for item in response.output:
                if getattr(item, "type", "") == "function_call":
                    calls.append({
                        "id": getattr(item, "call_id", getattr(item, "id", "")),
                        "type": "function",
                        "function": {
                            "name": getattr(item, "name", ""),
                            "arguments": getattr(item, "arguments", "{}"),
                        },
                    })
            if calls:
                model_response.tool_calls = calls

        # Extract usage
        if hasattr(response, "usage") and response.usage:
            model_response.response_usage = self._get_metrics_from_responses(response.usage)

        return model_response

    def _get_metrics_from_responses(self, usage: Any) -> Metrics:
        """Convert Responses API usage into Agno Metrics."""
        metrics = Metrics()
        metrics.input_tokens = getattr(usage, "input_tokens", 0) or 0
        metrics.output_tokens = getattr(usage, "output_tokens", 0) or 0
        metrics.total_tokens = getattr(usage, "total_tokens", 0) or (
            (metrics.input_tokens or 0) + (metrics.output_tokens or 0)
        )
        return metrics

    # ── Invocation methods ────────────────────────────────────────────

    def invoke(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Synchronous invocation — uses Responses API when supported."""
        if run_response and run_response.metrics:
            run_response.metrics.set_time_to_first_token()
        assistant_message.metrics.start_timer()

        if self._supports_responses() and responses is not None:
            params = self._build_request_params_responses(tools=tools, tool_choice=tool_choice)
            input_data, instructions = self._format_input(messages)
            provider_response = responses(
                input_data=input_data,
                instructions=instructions,
                **params,
            )
            assistant_message.metrics.stop_timer()
            return self._parse_responses_response(provider_response, response_format=response_format)

        completion_kwargs = self._build_request_params(tools=tools, tool_choice=tool_choice)
        completion_kwargs["messages"] = self._sanitize_messages(self._format_messages(messages))
        completion_kwargs["stream"] = False
        provider_response = completion(**completion_kwargs)  # type: ignore[arg-type]
        assistant_message.metrics.stop_timer()
        return self._parse_provider_response(provider_response, response_format=response_format)

    def invoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        **kwargs: Any,
    ) -> Iterator[ModelResponse]:
        """Synchronous streaming invocation."""
        completion_kwargs = self._build_request_params(tools=tools, tool_choice=tool_choice)
        completion_kwargs["messages"] = self._sanitize_messages(self._format_messages(messages))
        completion_kwargs["stream"] = True

        if run_response and run_response.metrics:
            run_response.metrics.set_time_to_first_token()
        assistant_message.metrics.start_timer()

        stream = completion(**completion_kwargs)  # type: ignore[arg-type]
        for chunk in stream:
            yield self._parse_provider_response_delta(chunk)

        assistant_message.metrics.stop_timer()

    async def ainvoke(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Asynchronous invocation — uses Responses API when supported."""
        if run_response and run_response.metrics:
            run_response.metrics.set_time_to_first_token()
        assistant_message.metrics.start_timer()

        if self._supports_responses() and aresponses is not None:
            params = self._build_request_params_responses(tools=tools, tool_choice=tool_choice)
            input_data, instructions = self._format_input(messages)
            provider_response = await aresponses(
                input_data=input_data,
                instructions=instructions,
                **params,
            )
            assistant_message.metrics.stop_timer()
            return self._parse_responses_response(provider_response, response_format=response_format)

        # Fallback to completions API
        completion_kwargs = self._build_request_params(tools=tools, tool_choice=tool_choice)
        completion_kwargs["messages"] = self._sanitize_messages(self._format_messages(messages))
        completion_kwargs["stream"] = False
        provider_response = await acompletion(**completion_kwargs)
        assistant_message.metrics.stop_timer()
        return self._parse_provider_response(provider_response, response_format=response_format)

    async def ainvoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ModelResponse]:
        """Asynchronous streaming — uses Responses API events when supported."""
        if run_response and run_response.metrics:
            run_response.metrics.set_time_to_first_token()
        assistant_message.metrics.start_timer()

        try:
            if self._supports_responses() and aresponses is not None:
                params = self._build_request_params_responses(tools=tools, tool_choice=tool_choice)
                input_data, instructions = self._format_input(messages)
                stream = await aresponses(
                    input_data=input_data,
                    instructions=instructions,
                    stream=True,
                    **params,
                )
                # Accumulate tool call fragments by output_index
                pending_tool_calls: dict[int, dict[str, Any]] = {}

                async for event in stream:
                    event_type = getattr(event, "type", "")

                    if event_type == "response.output_text.delta":
                        yield ModelResponse(content=event.delta)

                    elif event_type == "response.function_call_arguments.delta":
                        idx = event.output_index
                        if idx not in pending_tool_calls:
                            pending_tool_calls[idx] = {
                                "id": event.item_id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        pending_tool_calls[idx]["function"]["arguments"] += event.delta

                    elif event_type == "response.function_call_arguments.done":
                        idx = event.output_index
                        tc = pending_tool_calls.pop(idx, {
                            "id": event.item_id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        })
                        tc["function"]["name"] = event.name
                        tc["function"]["arguments"] = event.arguments
                        tc["id"] = event.item_id
                        yield ModelResponse(tool_calls=[tc])

                    elif event_type == "response.completed":
                        if hasattr(event.response, "usage") and event.response.usage:
                            mr = ModelResponse()
                            mr.response_usage = self._get_metrics_from_responses(event.response.usage)
                            yield mr

                assistant_message.metrics.stop_timer()
                return

            # Fallback to completions API streaming
            completion_kwargs = self._build_request_params(tools=tools, tool_choice=tool_choice)
            completion_kwargs["messages"] = self._sanitize_messages(self._format_messages(messages))
            completion_kwargs["stream"] = True

            async_stream = await acompletion(**completion_kwargs)
            async for chunk in async_stream:
                yield self._parse_provider_response_delta(chunk)

            assistant_message.metrics.stop_timer()
        except Exception as exc:  # pragma: no cover - defensive logging
            log_error(f"AnyLLM streaming error: {exc}")
            raise

    def _parse_provider_response(self, response: Any, **kwargs: Any) -> ModelResponse:
        """Convert a full AnyLLM response into an Agno ModelResponse."""
        model_response = ModelResponse()

        if not response.choices:
            return model_response

        response_message = response.choices[0].message

        if getattr(response_message, "content", None) is not None:
            model_response.content = response_message.content

        if getattr(response_message, "tool_calls", None):
            model_response.tool_calls = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name if tool_call.function else None,
                        "arguments": tool_call.function.arguments if tool_call.function and tool_call.function.arguments else "{}",
                    },
                }
                for tool_call in response_message.tool_calls
            ]

        if getattr(response, "usage", None) is not None:
            model_response.response_usage = self._get_metrics(response.usage)

        return model_response

    def _parse_provider_response_delta(self, response_delta: Any) -> ModelResponse:
        """Convert a streaming AnyLLM chunk into an Agno ModelResponse delta."""
        model_response = ModelResponse()

        if getattr(response_delta, "choices", None):
            choice_delta = response_delta.choices[0].delta

            if getattr(choice_delta, "content", None) is not None:
                model_response.content = choice_delta.content

            if getattr(choice_delta, "tool_calls", None):
                processed_tool_calls = []
                for tool_call in choice_delta.tool_calls:
                    tool_call_dict: Dict[str, Any] = {
                        "index": getattr(tool_call, "index", 0) or 0,
                        "type": getattr(tool_call, "type", "function") or "function",
                        "function": {},
                    }

                    if getattr(tool_call, "id", None):
                        tool_call_dict["id"] = tool_call.id

                    function_data = getattr(tool_call, "function", None)
                    if function_data is not None:
                        if getattr(function_data, "name", None):
                            tool_call_dict["function"]["name"] = function_data.name
                        if getattr(function_data, "arguments", None):
                            current_args = tool_call_dict["function"].get("arguments", "")
                            new_args = function_data.arguments or ""
                            if isinstance(current_args, str) and isinstance(new_args, str):
                                tool_call_dict["function"]["arguments"] = current_args + new_args
                            else:
                                tool_call_dict["function"]["arguments"] = new_args

                    processed_tool_calls.append(tool_call_dict)

                model_response.tool_calls = processed_tool_calls

        if getattr(response_delta, "usage", None) is not None:
            model_response.response_usage = self._get_metrics(response_delta.usage)

        return model_response

    def parse_tool_calls(self, tool_calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge streaming tool call deltas by index into complete tool calls.

        Streaming returns partial fragments: only the first chunk per tool call
        carries the ``id``.  The base class just returns the flat list, so
        downstream messages end up with fragments missing ``id`` — which
        violates the OpenAI/DeepSeek API contract.
        """
        tool_calls: List[Dict[str, Any]] = []
        for tc in tool_calls_data:
            _index = tc.get("index", 0) or 0
            _id = tc.get("id")
            _type = tc.get("type")
            _fn = tc.get("function") or {}
            _name = _fn.get("name")
            _args = _fn.get("arguments")

            # Grow list so that _index is valid
            while len(tool_calls) <= _index:
                tool_calls.append({})

            entry = tool_calls[_index]
            if not entry:
                # First fragment for this index — initialise
                entry["id"] = _id
                entry["type"] = _type or "function"
                entry["function"] = {
                    "name": _name or "",
                    "arguments": _args or "",
                }
                tool_calls[_index] = entry
            else:
                # Subsequent fragment — accumulate
                if _name:
                    entry["function"]["name"] += _name
                if _args:
                    entry["function"]["arguments"] += _args
                if _id:
                    entry["id"] = _id
                if _type:
                    entry["type"] = _type

        return tool_calls

    def _get_metrics(self, response_usage: Any) -> Metrics:
        """Convert usage payloads into Agno metrics."""
        metrics = Metrics()

        if isinstance(response_usage, dict):
            metrics.input_tokens = response_usage.get("prompt_tokens") or 0
            metrics.output_tokens = response_usage.get("completion_tokens") or 0
        else:
            metrics.input_tokens = getattr(response_usage, "prompt_tokens", 0) or 0
            metrics.output_tokens = getattr(response_usage, "completion_tokens", 0) or 0

        metrics.total_tokens = (metrics.input_tokens or 0) + (metrics.output_tokens or 0)
        return metrics
