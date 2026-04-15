"""
Unified AI Service using AnyLLM for universal LLM provider access.
Provides intelligent provider selection and automatic failover capabilities.
"""
import os
import logging
from typing import Any, Dict, List, Optional

from app.services.anyllm_service import anyllm_service

logger = logging.getLogger(__name__)


class UnifiedAIService:
    """
    Unified AI service that uses AnyLLM for universal LLM provider access.

    Supports multiple providers through a single interface:
    - OpenAI (openai)
    - Anthropic (anthropic)
    - Google Gemini (gemini)
    - Groq (groq)
    - DeepSeek (deepseek)
    - Mistral (mistral)
    - Local models (ollama, llama_cpp)
    - And many more via AnyLLM
    """

    def __init__(self):
        self.default_provider = os.getenv('ANYLLM_DEFAULT_PROVIDER', 'auto')
        self.default_model = os.getenv('ANYLLM_DEFAULT_MODEL', None)
        logger.info("Unified AI Service initialized with AnyLLM backend")

    def get_provider_status(self) -> Dict[str, Any]:
        """Get the status of all available AI providers."""
        try:
            # Access the cached provider list directly (sync-safe)
            providers = getattr(anyllm_service, 'supported_providers', [])

            # Build status dictionary for known providers
            status = {}

            # Check environment variables for common providers
            provider_env_vars = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY',
                'gemini': 'GEMINI_API_KEY',
                'groq': 'GROQ_API_KEY',
                'deepseek': 'DEEPSEEK_API_KEY',
                'mistral': 'MISTRAL_API_KEY',
            }

            for provider_info in providers:
                provider_name = provider_info["name"]
                env_var = provider_env_vars.get(provider_name)
                status[provider_name] = {
                    'available': bool(os.getenv(env_var)) if env_var else True,
                    'api_key_configured': bool(os.getenv(env_var)) if env_var else True,
                    'display_name': provider_info.get('display_name', provider_name)
                }

            # Add legacy provider names for compatibility
            if 'openai' in status:
                status['pollinations'] = status['openai']

            return status

        except Exception as e:
            logger.error(f"Error getting provider status: {e}")
            return {}

    def _get_provider_and_model(self, provider: str = "auto", model: Optional[str] = None) -> tuple[str, str]:
        """
        Get the appropriate provider and model based on preference.

        Args:
            provider: Preferred provider ('auto', 'openai', 'groq', 'pollinations', etc.)
            model: Optional model override

        Returns:
            Tuple of (provider_name, model_name)

        Raises:
            ValueError: If no AI provider is available
        """
        # Map legacy provider names to AnyLLM provider names
        provider_mapping = {
            'pollinations': 'openai',  # Griot AI uses OpenAI-compatible API
            'auto': 'auto',
        }

        # Normalize provider name
        normalized_provider = provider_mapping.get(provider, provider)

        if model:
            # Use explicitly specified model
            return normalized_provider, model

        # Use environment-configured defaults
        if normalized_provider != 'auto':
            return normalized_provider, self._get_default_model_for_provider(normalized_provider)

        # Auto-select: try providers in priority order
        priority_providers = ['deepseek', 'openai', 'anthropic', 'groq', 'gemini', 'mistral']

        for provider_name in priority_providers:
            env_var = f"{provider_name.upper()}_API_KEY"
            if os.getenv(env_var):
                model = self._get_default_model_for_provider(provider_name)
                return provider_name, model

        # Fallback to anyllm helper's default
        return 'auto', self.default_model or 'deepseek-chat'

    def _get_default_model_for_provider(self, provider: str) -> str:
        """Get default model for a specific provider."""
        default_models = {
            'openai': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'anthropic': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            'gemini': os.getenv('GEMINI_MODEL', 'gemini-pro'),
            'groq': os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile'),
            'deepseek': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            'mistral': os.getenv('MISTRAL_MODEL', 'mistral-small-latest'),
        }

        return default_models.get(provider, 'gpt-4o-mini')

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "auto",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion with automatic provider selection and fallback.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            provider: Preferred provider ('auto', 'pollinations', 'openai', 'groq', etc.)
            model: Optional model override (uses provider's default if not specified)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API

        Returns:
            Dictionary containing the response and metadata
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        # Get provider and model
        actual_provider, actual_model = self._get_provider_and_model(provider, model)

        logger.info(f"Attempting chat completion with provider: {actual_provider}, model: {actual_model}")

        try:
            # Build request data for AnyLLM
            request_data = {
                "provider": actual_provider,
                "model": actual_model,
                "messages": messages,
                "temperature": temperature,
            }

            # Add optional parameters
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens

            # Add any additional kwargs
            request_data.update(kwargs)

            # Call AnyLLM completion
            result = await anyllm_service.completion(request_data)

            return {
                'content': result.get('content'),
                'provider_used': actual_provider,
                'model_used': actual_model,
                'usage': result.get('usage', {}),
                'fallback_used': False
            }

        except Exception as primary_error:
            logger.warning(f"Primary provider {actual_provider} failed: {primary_error}")

            # Try fallback providers
            tried_providers = [actual_provider]
            priority_providers = ['deepseek', 'openai', 'anthropic', 'groq', 'gemini', 'mistral']

            for fallback_provider in priority_providers:
                if fallback_provider in tried_providers:
                    continue

                try:
                    fallback_model = self._get_default_model_for_provider(fallback_provider)

                    request_data = {
                        "provider": fallback_provider,
                        "model": fallback_model,
                        "messages": messages,
                        "temperature": temperature,
                    }

                    if max_tokens is not None:
                        request_data["max_tokens"] = max_tokens

                    request_data.update(kwargs)

                    logger.info(f"Trying fallback provider: {fallback_provider}, model: {fallback_model}")

                    result = await anyllm_service.completion(request_data)

                    return {
                        'content': result.get('content'),
                        'provider_used': fallback_provider,
                        'model_used': fallback_model,
                        'usage': result.get('usage', {}),
                        'fallback_used': True,
                        'primary_error': str(primary_error)
                    }

                except Exception as fallback_error:
                    logger.warning(f"Fallback provider {fallback_provider} also failed: {fallback_error}")
                    tried_providers.append(fallback_provider)
                    continue

            # If all providers failed
            raise ValueError(f"All AI providers failed. Primary error: {primary_error}")

    async def create_response(
        self,
        input_data: Any = None,
        instructions: Optional[str] = None,
        provider: str = "auto",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a response using the Responses API with automatic provider selection and fallback.

        Auto-routes to the Responses API when the provider supports it,
        otherwise falls back to the completions API transparently.

        Args:
            input_data: User input (string or list of input items for Responses API)
            instructions: System-level instructions (replaces system message role)
            provider: Preferred provider ('auto', 'openai', 'deepseek', etc.)
            model: Optional model override
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            previous_response_id: Chain with a previous response (Responses API only)
            messages: Fallback messages list (used when input_data not provided)
            **kwargs: Additional parameters (tools, tool_choice, store, etc.)

        Returns:
            Normalized dict: {content, tool_calls, response_id, model, usage, ...}
        """
        if not input_data and not messages:
            raise ValueError("Either input_data or messages must be provided")

        actual_provider, actual_model = self._get_provider_and_model(provider, model)

        logger.info(f"Attempting response with provider: {actual_provider}, model: {actual_model}")

        try:
            request_data: Dict[str, Any] = {
                "provider": actual_provider,
                "model": actual_model,
                "temperature": temperature,
            }

            if input_data is not None:
                request_data["input_data"] = input_data
            if instructions:
                request_data["instructions"] = instructions
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens
            if previous_response_id:
                request_data["previous_response_id"] = previous_response_id
            if messages:
                request_data["messages"] = messages

            request_data.update(kwargs)

            result = await anyllm_service.response(request_data)

            return {
                **result,
                'provider_used': actual_provider,
                'model_used': actual_model,
                'fallback_used': False,
            }

        except Exception as primary_error:
            logger.warning(f"Primary provider {actual_provider} failed: {primary_error}")

            tried_providers = [actual_provider]
            priority_providers = ['deepseek', 'openai', 'anthropic', 'groq', 'gemini', 'mistral']

            for fallback_provider in priority_providers:
                if fallback_provider in tried_providers:
                    continue

                try:
                    fallback_model = self._get_default_model_for_provider(fallback_provider)

                    request_data = {
                        "provider": fallback_provider,
                        "model": fallback_model,
                        "temperature": temperature,
                    }

                    if input_data is not None:
                        request_data["input_data"] = input_data
                    if instructions:
                        request_data["instructions"] = instructions
                    if max_tokens is not None:
                        request_data["max_tokens"] = max_tokens
                    if messages:
                        request_data["messages"] = messages
                    # Don't pass previous_response_id to fallback — it's provider-specific

                    request_data.update(kwargs)

                    logger.info(f"Trying fallback provider: {fallback_provider}, model: {fallback_model}")

                    result = await anyllm_service.response(request_data)

                    return {
                        **result,
                        'provider_used': fallback_provider,
                        'model_used': fallback_model,
                        'fallback_used': True,
                        'primary_error': str(primary_error),
                    }

                except Exception as fallback_error:
                    logger.warning(f"Fallback provider {fallback_provider} also failed: {fallback_error}")
                    tried_providers.append(fallback_provider)
                    continue

            raise ValueError(f"All AI providers failed. Primary error: {primary_error}")

    def is_available(self) -> bool:
        """Check if any AI provider is available."""
        try:
            status = self.get_provider_status()
            return any(p.get('available', False) for p in status.values())
        except Exception:
            return False

    def get_primary_provider(self) -> str:
        """Get the name of the primary provider that will be used."""
        try:
            provider, _ = self._get_provider_and_model("auto")
            return provider
        except ValueError:
            return "none"


# Create singleton instance
unified_ai_service = UnifiedAIService()
