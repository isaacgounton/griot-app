"""
Utility helper for backend services to use AnyLLM
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.services.anyllm_service import anyllm_service


class AnyLLMHelper:
    """Helper class for backend services to easily use AnyLLM"""

    @staticmethod
    async def get_default_provider() -> Optional[str]:
        """Get a default provider for general use"""
        try:
            providers = await anyllm_service.get_providers()
            if not providers["providers"]:
                return None

            # Try to find OpenAI first, then use first available
            for provider in providers["providers"]:
                if "openai" in provider["name"].lower():
                    return provider["name"]

            return providers["providers"][0]["name"]
        except Exception as e:
            logger.error(f"Error getting default provider: {e}")
            return None

    @staticmethod
    async def get_default_model(provider: str) -> Optional[str]:
        """Get a default model for a provider"""
        try:
            models = await anyllm_service.get_models(provider)
            if not models["models"]:
                return None

            # Try to find gpt models first
            for model in models["models"]:
                if "gpt-3.5-turbo" in model["id"] or "gpt-4" in model["id"]:
                    return model["id"]

            return models["models"][0]["id"]
        except Exception as e:
            logger.error(f"Error getting default model for {provider}: {e}")
            return None

    @staticmethod
    async def simple_complete(
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Simple text completion with automatic provider/model selection

        Args:
            prompt: The text prompt to complete
            provider: Optional provider name (auto-selected if not provided)
            model: Optional model name (auto-selected if not provided)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            The completed text
        """
        try:
            # Auto-select provider if not provided
            if not provider:
                provider = await AnyLLMHelper.get_default_provider()
                if not provider:
                    raise Exception("No providers available")

            # Auto-select model if not provided
            if not model:
                model = await AnyLLMHelper.get_default_model(provider)
                if not model:
                    raise Exception("No models available for provider")

            # Create completion
            messages = [{"role": "user", "content": prompt}]
            request_data = {
                "provider": provider,
                "model": model,
                "messages": messages,
                "temperature": temperature
            }

            result = []
            async for chunk in anyllm_service.stream_completion(request_data):
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data == "[DONE]":
                        break
                    if data and data.strip():
                        try:
                            import json
                            chunk_data = json.loads(data)
                            if chunk_data.get("choices") and chunk_data["choices"][0].get("delta", {}).get("content"):
                                result.append(chunk_data["choices"][0]["delta"]["content"])
                        except json.JSONDecodeError:
                            continue

            return "".join(result)

        except Exception as e:
            logger.error(f"Error in simple completion: {e}")
            raise

    @staticmethod
    async def chat_complete(
        messages: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion with message history

        Args:
            messages: List of messages with role and content
            provider: Optional provider name (auto-selected if not provided)
            model: Optional model name (auto-selected if not provided)
            temperature: Temperature for generation (0.0 to 2.0)

        Returns:
            The assistant's response
        """
        try:
            # Auto-select provider if not provided
            if not provider:
                provider = await AnyLLMHelper.get_default_provider()
                if not provider:
                    raise Exception("No providers available")

            # Auto-select model if not provided
            if not model:
                model = await AnyLLMHelper.get_default_model(provider)
                if not model:
                    raise Exception("No models available for provider")

            # Create completion
            request_data = {
                "provider": provider,
                "model": model,
                "messages": messages,
                "temperature": temperature
            }

            result = []
            async for chunk in anyllm_service.stream_completion(request_data):
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data == "[DONE]":
                        break
                    if data and data.strip():
                        try:
                            import json
                            chunk_data = json.loads(data)
                            if chunk_data.get("choices") and chunk_data["choices"][0].get("delta", {}).get("content"):
                                result.append(chunk_data["choices"][0]["delta"]["content"])
                        except json.JSONDecodeError:
                            continue

            return "".join(result)

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise

    @staticmethod
    async def simple_response(
        prompt: str,
        instructions: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
    ) -> str:
        """
        Simple text generation using the Responses API with automatic fallback.

        Uses anyllm_service.response() which auto-routes to the Responses API
        when the provider supports it, or falls back to completions otherwise.

        Args:
            prompt: The text prompt
            instructions: System-level instructions (separated from user input)
            provider: Optional provider name (auto-selected if not provided)
            model: Optional model name (auto-selected if not provided)
            temperature: Temperature for generation (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            previous_response_id: Chain with a previous response (Responses API only)

        Returns:
            The generated text content
        """
        try:
            if not provider:
                provider = await AnyLLMHelper.get_default_provider()
                if not provider:
                    raise Exception("No providers available")

            if not model:
                model = await AnyLLMHelper.get_default_model(provider)
                if not model:
                    raise Exception("No models available for provider")

            request_data: Dict[str, Any] = {
                "provider": provider,
                "model": model,
                "input_data": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            if instructions:
                request_data["instructions"] = instructions
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens
            if previous_response_id:
                request_data["previous_response_id"] = previous_response_id

            result = await anyllm_service.response(request_data)
            return result.get("content") or ""

        except Exception as e:
            logger.error(f"Error in simple response: {e}")
            raise

    @staticmethod
    async def is_available() -> bool:
        """Check if AnyLLM service is available"""
        try:
            providers = await anyllm_service.get_providers()
            return len(providers["providers"]) > 0
        except Exception as e:
            logger.error(f"Error checking AnyLLM availability: {e}")
            return False

    @staticmethod
    async def get_available_providers() -> List[str]:
        """Get list of available provider names"""
        try:
            providers = await anyllm_service.get_providers()
            return [p["name"] for p in providers["providers"]]
        except Exception as e:
            logger.error(f"Error getting available providers: {e}")
            return []

    @staticmethod
    async def get_available_models(provider: str) -> List[str]:
        """Get list of available model names for a provider"""
        try:
            models = await anyllm_service.get_models(provider)
            return [m["id"] for m in models["models"]]
        except Exception as e:
            logger.error(f"Error getting available models for {provider}: {e}")
            return []


# Export convenience functions
simple_complete = AnyLLMHelper.simple_complete
simple_response = AnyLLMHelper.simple_response
chat_complete = AnyLLMHelper.chat_complete
is_available = AnyLLMHelper.is_available
get_default_provider = AnyLLMHelper.get_default_provider
get_default_model = AnyLLMHelper.get_default_model