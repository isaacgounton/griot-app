"""
AnyLLM Service - Universal LLM provider integration

Supports both the Chat Completions API (acompletion) and the newer
Responses API (aresponses). The service auto-detects provider support
and routes to the right API, falling back to completions when responses
are not available.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List

from any_llm import AnyLLM, LLMProvider, acompletion, aresponses, alist_models
from any_llm.exceptions import MissingApiKeyError
from loguru import logger


class AnyLLMService:
    """Service for integrating with AnyLLM universal LLM provider"""

    def __init__(self):
        self.supported_providers = self._get_supported_providers()
        self.model_parameter_rules = self._get_model_parameter_rules()
        self._responses_support_cache: dict[str, bool] = {}

    def _get_model_parameter_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define parameter compatibility rules for different model patterns"""
        return {
            # OpenAI reasoning models (o1, o1-preview, gpt-5)
            "o1": {
                "max_tokens_param": "max_completion_tokens",
                "supports_reasoning": True,
                "unsupported_params": ["temperature", "top_p"]
            },
            "gpt-5": {
                "max_tokens_param": "max_completion_tokens",
                "supports_reasoning": False,
                "unsupported_params": ["temperature", "top_p", "presence_penalty", "frequency_penalty"]
            },
            # Standard OpenAI models
            "gpt-": {
                "max_tokens_param": "max_completion_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            },
            # Claude models (Anthropic API doesn't accept penalty params)
            "claude-": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": ["presence_penalty", "frequency_penalty"]
            },
            # Gemini models
            "gemini-": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            },
            # Groq models
            "llama": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            },
            "mixtral": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            },
            "gemma": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            },
            # Default fallback for unknown models
            "default": {
                "max_tokens_param": "max_tokens",
                "supports_reasoning": False,
                "unsupported_params": []
            }
        }

    def _get_model_rule(self, model_name: str) -> Dict[str, Any]:
        """Get parameter rules for a specific model"""
        model_lower = model_name.lower()

        # Check more specific patterns first (longer patterns have higher priority)
        specific_patterns = ["gpt-5", "o1", "claude-3", "gemini-2"]
        for pattern in specific_patterns:
            if pattern in model_lower:
                return self.model_parameter_rules.get(pattern, self.model_parameter_rules["default"])
        
        # Then check general patterns
        for pattern, rules in self.model_parameter_rules.items():
            if pattern != "default" and pattern not in specific_patterns and pattern in model_lower:
                return rules

        # Return default rules if no specific match
        return self.model_parameter_rules["default"]

    def _filter_parameters_for_model(self, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and map parameters based on model compatibility"""
        model_rule = self._get_model_rule(model_name)
        filtered_params = {}

        # Handle max_tokens vs max_completion_tokens mapping
        if "max_tokens" in params and params["max_tokens"] is not None:
            max_tokens_param = model_rule["max_tokens_param"]
            filtered_params[max_tokens_param] = params["max_tokens"]
        elif "max_completion_tokens" in params and params["max_completion_tokens"] is not None:
            filtered_params["max_completion_tokens"] = params["max_completion_tokens"]

        # Filter out unsupported parameters
        unsupported_params = set(model_rule["unsupported_params"])

        # Include supported parameters
        supported_params = [
            "temperature", "top_p", "response_format", "n", "stop",
            "presence_penalty", "frequency_penalty", "seed", "user",
            "tools", "tool_choice", "parallel_tool_calls", "logprobs",
            "top_logprobs", "logit_bias", "reasoning_effort"
        ]

        for param in supported_params:
            if param in params and params[param] is not None and param not in unsupported_params:
                # Special handling for reasoning_effort
                if param == "reasoning_effort" and not model_rule["supports_reasoning"]:
                    continue
                filtered_params[param] = params[param]

        logger.info(f"Filtered parameters for {model_name}: {list(filtered_params.keys())}")
        return filtered_params

    # ── Responses API support ──────────────────────────────────────────

    def _supports_responses(self, provider: str) -> bool:
        """Check if a provider supports the Responses API (cached)."""
        if provider in self._responses_support_cache:
            return self._responses_support_cache[provider]
        try:
            provider_key = LLMProvider.from_string(provider)
            provider_class = AnyLLM.get_provider_class(provider_key)
            supported = getattr(provider_class, "SUPPORTS_RESPONSES", False)
        except Exception:
            supported = False
        self._responses_support_cache[provider] = supported
        return supported

    def _messages_to_input(
        self, messages: list[dict[str, Any]], model: str
    ) -> tuple[Any, str | None]:
        """Convert chat-completion messages into Responses API input_data + instructions.

        Returns (input_data, instructions) where instructions is the extracted
        system message (if any).
        """
        instructions: str | None = None
        input_items: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Last system message wins as instructions
                if isinstance(content, list):
                    instructions = " ".join(
                        item.get("text", "") for item in content
                        if isinstance(item, dict) and item.get("type") == "text"
                    )
                else:
                    instructions = str(content) if content else None
                continue

            if role == "tool":
                input_items.append({
                    "type": "function_call_output",
                    "call_id": msg.get("tool_call_id", ""),
                    "output": str(content) if content else "",
                })
                continue

            # Assistant messages that made tool calls → emit function_call items
            if role == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    input_items.append({
                        "type": "function_call",
                        "call_id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "arguments": fn.get("arguments", "{}"),
                    })
                # Also include text content if any
                if content:
                    input_items.append({
                        "role": "assistant",
                        "content": str(content) if not isinstance(content, str) else content,
                    })
                continue

            # Standard user/assistant messages
            input_items.append({
                "role": role,
                "content": str(content) if not isinstance(content, str) else content,
            })

        return input_items or "", instructions

    def _filter_parameters_for_responses(
        self, model_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Filter and map parameters for the Responses API."""
        model_rule = self._get_model_rule(model_name)
        filtered: dict[str, Any] = {}
        unsupported = set(model_rule["unsupported_params"])

        # max_tokens / max_completion_tokens → max_output_tokens
        for key in ("max_tokens", "max_completion_tokens", "max_output_tokens"):
            if key in params and params[key] is not None:
                filtered["max_output_tokens"] = params[key]
                break

        # reasoning_effort → reasoning dict
        if "reasoning_effort" in params and params["reasoning_effort"] is not None:
            if model_rule["supports_reasoning"]:
                filtered["reasoning"] = {"effort": params["reasoning_effort"]}

        # Pass-through params supported by both APIs
        responses_params = [
            "temperature", "top_p", "presence_penalty", "frequency_penalty",
            "tools", "tool_choice", "parallel_tool_calls", "user",
        ]
        for param in responses_params:
            if param in params and params[param] is not None and param not in unsupported:
                filtered[param] = params[param]

        return filtered

    def _normalize_response(self, result: Any) -> dict[str, Any]:
        """Normalize Response / ResponseResource into a standard dict."""
        # Extract text content
        content = ""
        if hasattr(result, "output_text") and result.output_text:
            content = result.output_text
        elif hasattr(result, "output"):
            for item in result.output:
                item_type = getattr(item, "type", "")
                if item_type == "message":
                    for part in getattr(item, "content", []):
                        if getattr(part, "type", "") == "output_text":
                            content = part.text
                            break
                    if content:
                        break

        # Extract tool calls
        tool_calls = None
        if hasattr(result, "output"):
            calls = []
            for item in result.output:
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
                tool_calls = calls

        # Extract usage
        usage = {}
        if hasattr(result, "usage") and result.usage:
            u = result.usage
            usage = {
                "prompt_tokens": getattr(u, "input_tokens", 0) or 0,
                "completion_tokens": getattr(u, "output_tokens", 0) or 0,
                "total_tokens": getattr(u, "total_tokens", 0) or 0,
            }

        # Determine finish reason
        finish_reason = "tool_calls" if tool_calls else "stop"

        return {
            "content": content,
            "tool_calls": tool_calls,
            "response_id": getattr(result, "id", None),
            "model": getattr(result, "model", ""),
            "usage": usage,
            "finish_reason": finish_reason,
        }

    async def response(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Non-streaming response — uses Responses API when supported, falls back to completion."""
        provider = request_data["provider"]
        model = request_data["model"]

        if not self._supports_responses(provider):
            # Fallback: delegate to existing completion path
            return await self.completion(request_data)

        try:
            # Build messages (handle multimodal)
            if "messages_multimodal" in request_data and request_data["messages_multimodal"]:
                messages = self._convert_multimodal_to_legacy(
                    request_data["messages_multimodal"], model
                )
            elif "messages" in request_data:
                messages = request_data["messages"]
            else:
                messages = None

            # If caller provides input_data directly, use it
            if "input_data" in request_data and request_data["input_data"] is not None:
                input_data = request_data["input_data"]
                instructions = request_data.get("instructions")
            elif messages is not None:
                input_data, instructions = self._messages_to_input(messages, model)
            else:
                input_data = request_data.get("input_data", "")
                instructions = request_data.get("instructions")

            # Allow caller to override instructions
            if "instructions" in request_data and request_data["instructions"] is not None:
                instructions = request_data["instructions"]

            # Filter params for responses API
            provided_params = {k: v for k, v in request_data.items() if k not in {
                "provider", "model", "messages", "messages_multimodal",
                "input_data", "instructions", "stream",
            }}
            filtered_params = self._filter_parameters_for_responses(model, provided_params)

            # Pass through responses-specific params
            for key in ("previous_response_id", "store", "metadata", "conversation",
                        "truncation", "service_tier"):
                if key in request_data and request_data[key] is not None:
                    filtered_params[key] = request_data[key]

            logger.info(f"Starting response with provider: {provider}, model: {model}")

            result = await aresponses(
                model=model,
                provider=provider,
                input_data=input_data,
                instructions=instructions,
                **filtered_params,
            )

            return self._normalize_response(result)

        except NotImplementedError:
            logger.warning(f"Provider {provider} doesn't support responses, falling back to completion")
            self._responses_support_cache[provider] = False
            return await self.completion(request_data)
        except MissingApiKeyError as e:
            logger.error(f"Missing API key for response: {e}")
            raise Exception(
                f"API key is required for this provider. "
                f"Please set the environment variable and restart the server."
            )
        except Exception as e:
            logger.error(f"Error in response: {e}")
            raise

    async def stream_response(self, request_data: dict[str, Any]) -> Any:
        """Streaming response — translates Responses API events to SSE StreamChunk format."""
        provider = request_data["provider"]
        model = request_data["model"]

        if not self._supports_responses(provider):
            async for chunk in self.stream_completion(request_data):
                yield chunk
            return

        try:
            # Build messages (handle multimodal)
            if "messages_multimodal" in request_data and request_data["messages_multimodal"]:
                messages = self._convert_multimodal_to_legacy(
                    request_data["messages_multimodal"], model
                )
            elif "messages" in request_data:
                messages = request_data["messages"]
            else:
                messages = None

            # If caller provides input_data directly, use it
            if "input_data" in request_data and request_data["input_data"] is not None:
                input_data = request_data["input_data"]
                instructions = request_data.get("instructions")
            elif messages is not None:
                input_data, instructions = self._messages_to_input(messages, model)
            else:
                input_data = request_data.get("input_data", "")
                instructions = request_data.get("instructions")

            if "instructions" in request_data and request_data["instructions"] is not None:
                instructions = request_data["instructions"]

            # Filter params
            provided_params = {k: v for k, v in request_data.items() if k not in {
                "provider", "model", "messages", "messages_multimodal",
                "input_data", "instructions", "stream",
            }}
            filtered_params = self._filter_parameters_for_responses(model, provided_params)

            for key in ("previous_response_id", "store", "metadata", "conversation",
                        "truncation", "service_tier"):
                if key in request_data and request_data[key] is not None:
                    filtered_params[key] = request_data[key]

            logger.info(f"Starting stream response with provider: {provider}, model: {model}")

            stream = await aresponses(
                model=model,
                provider=provider,
                input_data=input_data,
                instructions=instructions,
                stream=True,
                **filtered_params,
            )

            response_id = None
            ts = int(time.time())

            async for event in stream:
                event_type = getattr(event, "type", "")

                if event_type == "response.created":
                    response_id = event.response.id
                    # Emit metadata chunk with response_id
                    yield f"data: {json.dumps({'response_id': response_id})}\n\n"

                elif event_type == "response.output_text.delta":
                    chunk_data = {
                        "id": response_id or "resp_stream",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": event.delta},
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    await asyncio.sleep(0.01)

                elif event_type == "response.reasoning_text.delta":
                    chunk_data = {
                        "id": response_id or "resp_stream",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"thinking": event.delta},
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    await asyncio.sleep(0.01)

                elif event_type == "response.function_call_arguments.delta":
                    chunk_data = {
                        "id": response_id or "resp_stream",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "tool_calls": [{
                                    "index": event.output_index,
                                    "id": event.item_id,
                                    "type": "function",
                                    "function": {"arguments": event.delta},
                                }]
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                elif event_type == "response.function_call_arguments.done":
                    chunk_data = {
                        "id": response_id or "resp_stream",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "tool_calls": [{
                                    "index": event.output_index,
                                    "id": event.item_id,
                                    "type": "function",
                                    "function": {
                                        "name": event.name,
                                        "arguments": event.arguments,
                                    },
                                }]
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                elif event_type == "response.completed":
                    chunk_data = {
                        "id": response_id or "resp_stream",
                        "object": "chat.completion.chunk",
                        "created": ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop",
                        }],
                        "response_id": event.response.id,
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

            yield "data: [DONE]\n\n"

        except NotImplementedError:
            logger.warning(f"Provider {provider} doesn't support responses streaming, falling back")
            self._responses_support_cache[provider] = False
            async for chunk in self.stream_completion(request_data):
                yield chunk
        except MissingApiKeyError as e:
            logger.error(f"Missing API key for stream response: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Error in stream response: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # ── Provider discovery ───────────────────────────────────────────

    def _get_supported_providers(self) -> List[Dict[str, str]]:
        """Get all providers that support list_models"""
        supported_providers = []

        for provider_name in LLMProvider:
            provider_class = AnyLLM.get_provider_class(provider_name)
            if provider_class.SUPPORTS_LIST_MODELS:
                supported_providers.append({
                    "name": provider_name.value,
                    "display_name": provider_name.value.replace("_", " ").title()
                })

        return supported_providers

    async def get_providers(self) -> Dict[str, Any]:
        """Get all providers that support list_models"""
        try:
            default_provider = os.getenv("ANYLLM_DEFAULT_PROVIDER", "deepseek")
            return {
                "providers": self.supported_providers,
                "default_provider": default_provider,
            }
        except Exception as e:
            logger.error(f"Error getting providers: {e}")
            raise

    async def get_models(self, provider: str) -> Dict[str, Any]:
        """List available models for a provider"""
        try:
            models = await alist_models(provider=provider)

            return {
                "models": [
                    {
                        "id": model.id,
                        "object": model.object,
                        "created": getattr(model, "created", None),
                        "owned_by": getattr(model, "owned_by", None),
                        "parameter_info": self._get_model_parameter_info(model.id),
                    }
                    for model in models
                ]
            }
        except MissingApiKeyError as e:
            logger.error(f"Missing API key for provider {provider}: {e}")
            raise Exception(f"API key is required for provider {provider}. Please set the environment variable and restart the server.")
        except Exception as e:
            logger.error(f"Error getting models for provider {provider}: {e}")
            raise

    def _get_model_parameter_info(self, model_name: str) -> Dict[str, Any]:
        """Get parameter compatibility information for a model"""
        model_rule = self._get_model_rule(model_name)

        return {
            "max_tokens_param": model_rule["max_tokens_param"],
            "supports_reasoning": model_rule["supports_reasoning"],
            "unsupported_params": model_rule["unsupported_params"],
            "recommended_defaults": {
                "temperature": 0.7 if "temperature" not in model_rule["unsupported_params"] else None,
                "top_p": 1.0 if "top_p" not in model_rule["unsupported_params"] else None,
                "max_tokens": 2048,
            }
        }

    def _convert_multimodal_to_legacy(self, messages_multimodal: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """Convert multimodal message format to legacy format for different providers"""
        if not messages_multimodal:
            return []

        legacy_messages = []

        for message in messages_multimodal:
            role = message.get("role")

            # Handle tool result messages (content is a string)
            if role == "tool":
                legacy_messages.append({
                    "role": "tool",
                    "content": message.get("content", ""),
                    "tool_call_id": message.get("tool_call_id", ""),
                })
                continue

            # Handle assistant messages with tool_calls
            if role == "assistant" and message.get("tool_calls"):
                content = message.get("content", "")
                # Extract text from content list if needed
                if isinstance(content, list):
                    content = " ".join(
                        item.get("text", "") for item in content
                        if item.get("type") == "text" and item.get("text")
                    )
                legacy_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": [
                        {
                            "id": tc.get("id", ""),
                            "type": tc.get("type", "function"),
                            "function": {
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": tc.get("function", {}).get("arguments", ""),
                            }
                        }
                        for tc in message["tool_calls"]
                    ],
                }
                legacy_messages.append(legacy_msg)
                continue

            if role == "system":
                # System messages are usually just text
                content_list = message.get("content", [])
                if isinstance(content_list, str):
                    legacy_messages.append({"role": "system", "content": content_list})
                    continue
                text_content = " ".join([
                    item.get("text", "") for item in content_list
                    if item.get("type") == "text" and item.get("text")
                ])
                legacy_messages.append({
                    "role": "system",
                    "content": text_content
                })
            else:
                # Handle user and assistant messages with multimodal content
                content = message.get("content", [])
                # If content is already a string, pass through
                if isinstance(content, str):
                    legacy_messages.append({"role": role or "user", "content": content})
                    continue
                content_list = content

                # Check if this model supports vision
                model_lower = model.lower()
                supports_vision = any(pattern in model_lower for pattern in [
                    "gpt-4-vision", "gpt-4o", "claude-3", "gemini-pro-vision", "llava"
                ])

                if supports_vision and any(item.get("type") in ["image", "video"] for item in content_list):
                    # Format for vision models (OpenAI format)
                    formatted_content = []
                    for item in content_list:
                        if item.get("type") == "text":
                            formatted_content.append({
                                "type": "text",
                                "text": item.get("text", "")
                            })
                        elif item.get("type") == "image":
                            image_url = item.get("url")
                            if image_url:  # Only add if URL is not None or empty
                                formatted_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_url,
                                        "detail": "auto"
                                    }
                                })
                            else:
                                logger.warning(f"Image item missing URL, skipping")
                        elif item.get("type") == "video":
                            video_url = item.get("url")
                            if video_url:  # Only add if URL is not None or empty
                                # Some models might support video, treat as image for now
                                formatted_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": video_url,
                                        "detail": "auto"
                                    }
                                })
                            else:
                                logger.warning(f"Video item missing URL, skipping")
                        elif item.get("type") == "audio":
                            # Audio is typically not supported in chat completion, but we can include a reference
                            formatted_content.append({
                                "type": "text",
                                "text": f"[Audio file: {item.get('filename', 'audio')}]"
                            })

                    legacy_messages.append({
                        "role": message.get("role", "user"),
                        "content": formatted_content
                    })
                else:
                    # Fallback to text-only format for non-vision models
                    text_parts = []
                    for item in content_list:
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") in ["image", "video", "audio"]:
                            text_parts.append(f"[{item.get('type', 'media').title()}: {item.get('filename', 'file')}]")

                    legacy_messages.append({
                        "role": message.get("role", "user"),
                        "content": " ".join(text_parts)
                    })

        return legacy_messages

    async def completion(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Non-streaming completion that returns the complete response.

        Args:
            request_data: Dictionary containing:
                - provider: LLM provider name
                - model: Model name
                - messages: List of message dictionaries
                - temperature: Sampling temperature (optional)
                - max_tokens: Maximum tokens to generate (optional)
                - Other completion parameters

        Returns:
            Dictionary with content, model, usage metadata
        """
        try:
            provider = request_data["provider"]
            model = request_data["model"]

            # Handle both legacy and multimodal message formats
            if "messages_multimodal" in request_data and request_data["messages_multimodal"]:
                messages = self._convert_multimodal_to_legacy(
                    request_data["messages_multimodal"],
                    model
                )
            else:
                messages = request_data["messages"]

            # Extract all completion parameters from request_data
            raw_params = {
                "temperature", "top_p", "max_tokens", "response_format",
                "n", "stop", "presence_penalty", "frequency_penalty",
                "seed", "user", "tools", "tool_choice", "parallel_tool_calls",
                "logprobs", "top_logprobs", "logit_bias", "max_completion_tokens",
                "reasoning_effort"
            }

            # Filter parameters based on model compatibility
            provided_params = {k: v for k, v in request_data.items() if k in raw_params}
            filtered_params = self._filter_parameters_for_model(model, provided_params)

            # Build completion parameters
            completion_params = {
                "model": model,
                "messages": messages,
                "provider": provider,
                **filtered_params
            }

            logger.info(f"Starting completion with provider: {provider}, model: {model}")

            # Use async completion directly to avoid event loop cleanup issues
            result = await acompletion(**completion_params)

            # Extract tool_calls if present
            tool_calls_raw = getattr(result.choices[0].message, "tool_calls", None)
            tool_calls = None
            if tool_calls_raw:
                tool_calls = []
                for tc in tool_calls_raw:
                    tool_calls.append({
                        "id": tc.id,
                        "type": getattr(tc, "type", "function"),
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    })

            return {
                "content": result.choices[0].message.content,
                "tool_calls": tool_calls,
                "model": result.model,
                "usage": {
                    "prompt_tokens": result.usage.prompt_tokens if result.usage else 0,
                    "completion_tokens": result.usage.completion_tokens if result.usage else 0,
                    "total_tokens": result.usage.total_tokens if result.usage else 0,
                } if result.usage else {},
                "finish_reason": result.choices[0].finish_reason if result.choices else None,
            }

        except MissingApiKeyError as e:
            logger.error(f"Missing API key for completion: {e}")
            raise Exception(f"API key is required for this provider. Please set the environment variable and restart the server.")
        except Exception as e:
            logger.error(f"Error in completion: {e}")
            raise

    async def stream_completion(self, request_data: Dict[str, Any]) -> Any:
        """Stream completion chunks as Server-Sent Events"""
        try:
            provider = request_data["provider"]
            model = request_data["model"]

            # Handle both legacy and multimodal message formats
            if "messages_multimodal" in request_data and request_data["messages_multimodal"]:
                messages = self._convert_multimodal_to_legacy(
                    request_data["messages_multimodal"],
                    model
                )
            else:
                messages = request_data["messages"]

            # Extract all completion parameters from request_data
            raw_params = {
                "temperature", "top_p", "max_tokens", "response_format",
                "n", "stop", "presence_penalty", "frequency_penalty",
                "seed", "user", "tools", "tool_choice", "parallel_tool_calls",
                "logprobs", "top_logprobs", "logit_bias", "max_completion_tokens",
                "reasoning_effort"
            }

            # Filter parameters based on model compatibility
            provided_params = {k: v for k, v in request_data.items() if k in raw_params}
            filtered_params = self._filter_parameters_for_model(model, provided_params)

            # Build completion parameters
            completion_params = {
                "model": model,
                "messages": messages,
                "provider": provider,
                "stream": True,
                **filtered_params
            }

            logger.info(f"Starting completion with provider: {provider}, model: {model}")
            logger.debug(f"Filtered parameters: {list(filtered_params.keys())}")

            stream = await acompletion(**completion_params)
            last_chunk_sent = False

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta_data = {}

                    # Handle content
                    if choice.delta and hasattr(choice.delta, "content") and choice.delta.content:
                        delta_data["content"] = choice.delta.content

                    # Handle thinking/reasoning
                    if choice.delta and hasattr(choice.delta, "reasoning") and choice.delta.reasoning:
                        delta_data["thinking"] = choice.delta.reasoning.content

                    # Handle tool_calls
                    if choice.delta and hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                        delta_data["tool_calls"] = [
                            {
                                "index": getattr(tc, "index", 0),
                                "id": getattr(tc, "id", None),
                                "type": getattr(tc, "type", "function"),
                                "function": {
                                    "name": getattr(tc.function, "name", None) if getattr(tc, "function", None) else None,
                                    "arguments": getattr(tc.function, "arguments", "") if getattr(tc, "function", None) else ""
                                }
                            }
                            for tc in choice.delta.tool_calls
                        ]

                    # Send chunk if we have delta data OR a finish_reason (needed for tool_calls finish)
                    if delta_data or choice.finish_reason:
                        chunk_data = {
                            "id": chunk.id,
                            "object": chunk.object,
                            "created": chunk.created,
                            "model": chunk.model,
                            "choices": [
                                {"index": choice.index, "delta": delta_data, "finish_reason": choice.finish_reason}
                            ],
                        }
                        chunk_json = json.dumps(chunk_data)
                        yield f"data: {chunk_json}\n\n"
                        last_chunk_sent = True

                        # Add a small delay to help with browser rendering
                        await asyncio.sleep(0.01)

            yield "data: [DONE]\n\n"

        except MissingApiKeyError as e:
            logger.error(f"Missing API key for completion: {e}")
            error_data = {"error": f"API key is required for this provider. Please set the environment variable and restart the server."}
            yield f"data: {json.dumps(error_data)}\n\n"
        except Exception as e:
            logger.error(f"Error in completion stream: {e}")
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"


# Global instance
anyllm_service = AnyLLMService()