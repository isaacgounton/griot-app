"""
Helper utilities for constructing agent chat models.
"""

from typing import Optional, Dict, Any

from agno.models.base import Model

from .anyllm_chat import AnyLLMChat


ALLOWED_MODEL_KWARGS = {
    "temperature",
    "top_p",
    "presence_penalty",
    "frequency_penalty",
    "max_tokens",
    "max_completion_tokens",
}


def _extract_model_kwargs(settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not settings:
        return {}
    return {k: settings[k] for k in ALLOWED_MODEL_KWARGS if settings.get(k) is not None}


def create_chat_model(
    model_id: str,
    provider: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> Model:
    """
    Return an Agno chat model configured for the requested provider.

    All providers (including OpenAI) are routed through AnyLLMChat which
    includes workarounds for the OpenAI API requiring a ``name`` field on
    tool-role messages.  Agno's native OpenAIChat strips None values and
    drops the field, causing 400 errors when agents use tools.

    Args:
        model_id: Model identifier (e.g., 'gpt-4o-mini', 'claude-3-sonnet').
        provider: AnyLLM provider name. Defaults to OpenAI when not supplied.
        settings: Optional session settings containing generation parameters.

    Returns:
        An Agno Model instance ready to be attached to an Agent.
    """
    provider_normalized = (provider or "openai").strip().lower() or "openai"
    model_kwargs = _extract_model_kwargs(settings)

    return AnyLLMChat(
        id=model_id,
        provider=provider_normalized,
        **model_kwargs,
    )
