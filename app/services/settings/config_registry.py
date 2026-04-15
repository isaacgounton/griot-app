"""
Configurable settings registry.

Defines all settings that can be managed via the dashboard UI
instead of (or in addition to) environment variables.

AI provider keys are used by AnyLLM (mozilla-ai/any-llm) which discovers
providers by checking os.environ for their API key. Setting a key here
immediately makes that provider available through AnyLLM.
"""
import os
from typing import Any


# Each entry: env var name -> metadata
# type: "password" (masked in GET), "string", "number", "boolean"
CONFIGURABLE_SETTINGS: dict[str, dict[str, Any]] = {

    # ── AI Providers (AnyLLM-compatible) ─────────────────────────
    # Env var names match AnyLLM's ENV_API_KEY_NAME / ENV_API_BASE_NAME
    # so setting them here makes the provider available for chat.

    # OpenAI
    "OPENAI_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "OpenAI"},
    "OPENAI_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.openai.com/v1", "provider": "OpenAI"},
    "OPENAI_MODEL": {"category": "ai_providers", "label": "Default Model", "type": "string", "default": "gpt-4o-mini", "provider": "OpenAI"},
    "OPENAI_VISION_MODEL": {"category": "ai_providers", "label": "Vision Model", "type": "string", "provider": "OpenAI"},

    # DeepSeek
    "DEEPSEEK_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "DeepSeek"},
    "DEEPSEEK_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.deepseek.com", "provider": "DeepSeek"},

    # Anthropic
    "ANTHROPIC_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Anthropic"},
    "ANTHROPIC_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Anthropic"},

    # Groq
    "GROQ_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Groq"},
    "GROQ_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Groq"},
    "GROQ_MODEL": {"category": "ai_providers", "label": "Default Model", "type": "string", "provider": "Groq"},

    # Google / Gemini
    "GEMINI_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Gemini"},
    "GOOGLE_GEMINI_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Gemini"},
    "GEMINI_MODEL": {"category": "ai_providers", "label": "Default Model", "type": "string", "default": "gemini-2.0-flash", "provider": "Gemini"},

    # Mistral
    "MISTRAL_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Mistral"},
    "MISTRAL_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Mistral"},

    # Perplexity
    "PERPLEXITY_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Perplexity"},
    "PERPLEXITY_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.perplexity.ai", "provider": "Perplexity"},
    "PERPLEXITY_MODEL": {"category": "ai_providers", "label": "Default Model", "type": "string", "default": "sonar", "provider": "Perplexity"},

    # OpenRouter
    "OPENROUTER_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "OpenRouter"},
    "OPENROUTER_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://openrouter.ai/api/v1", "provider": "OpenRouter"},

    # xAI (Grok)
    "XAI_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "xAI"},
    "XAI_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.x.ai/v1", "provider": "xAI"},

    # Cohere
    "COHERE_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Cohere"},
    "COHERE_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Cohere"},

    # Cerebras
    "CEREBRAS_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Cerebras"},
    "CEREBRAS_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Cerebras"},

    # Fireworks
    "FIREWORKS_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Fireworks"},
    "FIREWORKS_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.fireworks.ai/inference/v1", "provider": "Fireworks"},

    # Together (also used for image gen)
    "TOGETHER_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Together"},
    "TOGETHER_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "Together"},

    # HuggingFace
    "HF_TOKEN": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "HuggingFace"},
    "HUGGINGFACE_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "provider": "HuggingFace"},

    # Moonshot
    "MOONSHOT_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Moonshot"},
    "MOONSHOT_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.moonshot.ai/v1", "provider": "Moonshot"},

    # SambaNova
    "SAMBANOVA_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "SambaNova"},
    "SAMBANOVA_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.sambanova.ai/v1/", "provider": "SambaNova"},

    # Nebius
    "NEBIUS_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Nebius"},
    "NEBIUS_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.studio.nebius.ai/v1", "provider": "Nebius"},

    # Inception
    "INCEPTION_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Inception"},
    "INCEPTION_API_BASE": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.inceptionlabs.ai/v1", "provider": "Inception"},

    # Z.AI (Zhipu)
    "ZAI_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Z.AI"},
    "ZAI_BASE_URL": {"category": "ai_providers", "label": "Base URL", "type": "string", "placeholder": "https://api.z.ai/api/paas/v4/", "provider": "Z.AI"},

    # Pollinations (app-specific, not AnyLLM)
    "POLLINATIONS_API_KEY": {"category": "ai_providers", "label": "API Key", "type": "password", "provider": "Pollinations"},

    # AnyLLM routing (app-specific)
    "ANYLLM_DEFAULT_PROVIDER": {"category": "ai_providers", "label": "Default Provider", "type": "string", "default": "deepseek", "provider": "AnyLLM"},

    # ── Speech & Media ────────────────────────────────────────────

    # TTS
    "TTS_PROVIDER": {"category": "speech_media", "label": "Default TTS Provider", "type": "string", "default": "edge"},
    "TTS_VOICE": {"category": "speech_media", "label": "Default TTS Voice", "type": "string"},

    # Speaches sidecar
    "SPEACHES_BASE_URL": {"category": "speech_media", "label": "Speaches Service URL", "type": "string", "placeholder": "http://speaches:8000/v1"},
    "SPEACHES_API_KEY": {"category": "speech_media", "label": "Speaches API Key", "type": "password"},

    # Stock media
    "PEXELS_API_KEY": {"category": "speech_media", "label": "Pexels API Key", "type": "password"},
    "PIXABAY_API_KEY": {"category": "speech_media", "label": "Pixabay API Key", "type": "password"},

    # Together AI (image gen settings — API key is in AI Providers)
    "TOGETHER_DEFAULT_MODEL": {"category": "speech_media", "label": "Together Default Model", "type": "string", "default": "black-forest-labs/FLUX.1-schnell"},
    "TOGETHER_DEFAULT_WIDTH": {"category": "speech_media", "label": "Together Default Width", "type": "number", "default": 576},
    "TOGETHER_DEFAULT_HEIGHT": {"category": "speech_media", "label": "Together Default Height", "type": "number", "default": 1024},
    "TOGETHER_DEFAULT_STEPS": {"category": "speech_media", "label": "Together Default Steps", "type": "number", "default": 4},
    "TOGETHER_MODELS": {"category": "speech_media", "label": "Together Models (comma-sep)", "type": "string"},
    "TOGETHER_MAX_RPS": {"category": "speech_media", "label": "Together Max RPS", "type": "number", "default": 20},
    "TOGETHER_MAX_CONCURRENT": {"category": "speech_media", "label": "Together Max Concurrent", "type": "number", "default": 5},
    "TOGETHER_RETRY_ATTEMPTS": {"category": "speech_media", "label": "Together Retry Attempts", "type": "number", "default": 2},
    "TOGETHER_BASE_DELAY": {"category": "speech_media", "label": "Together Base Delay (s)", "type": "string", "default": "1.0"},

    # ComfyUI
    "COMFYUI_URL": {"category": "speech_media", "label": "ComfyUI Server URL", "type": "string"},
    "COMFYUI_API_KEY": {"category": "speech_media", "label": "ComfyUI API Key", "type": "password"},
    "COMFYUI_USERNAME": {"category": "speech_media", "label": "ComfyUI Username", "type": "string"},
    "COMFYUI_PASSWORD": {"category": "speech_media", "label": "ComfyUI Password", "type": "password"},

    # WaveSpeed AI
    "WAVESPEEDAI_API_KEY": {"category": "speech_media", "label": "WaveSpeed AI API Key", "type": "password"},

    # Modal (image/video)
    "MODAL_IMAGE_API_KEY": {"category": "speech_media", "label": "Modal Image API Key", "type": "password"},
    "MODAL_IMAGE_API_URL": {"category": "speech_media", "label": "Modal Image API URL", "type": "string"},
    "MODAL_VIDEO_API_KEY": {"category": "speech_media", "label": "Modal Video API Key", "type": "password"},
    "MODAL_VIDEO_API_URL": {"category": "speech_media", "label": "Modal Video API URL", "type": "string"},

    # ── Email & Auth ──────────────────────────────────────────────

    "RESEND_API_KEY": {"category": "email_auth", "label": "Resend API Key", "type": "password"},
    "EMAIL_FROM_ADDRESS": {"category": "email_auth", "label": "Email From Address", "type": "string"},
    "EMAIL_FROM_NAME": {"category": "email_auth", "label": "Email From Name", "type": "string"},

    # OAuth
    "GOOGLE_CLIENT_ID": {"category": "email_auth", "label": "Google OAuth Client ID", "type": "string"},
    "GOOGLE_CLIENT_SECRET": {"category": "email_auth", "label": "Google OAuth Client Secret", "type": "password"},
    "GITHUB_CLIENT_ID": {"category": "email_auth", "label": "GitHub OAuth Client ID", "type": "string"},
    "GITHUB_CLIENT_SECRET": {"category": "email_auth", "label": "GitHub OAuth Client Secret", "type": "password"},
    "DISCORD_CLIENT_ID": {"category": "email_auth", "label": "Discord OAuth Client ID", "type": "string"},
    "DISCORD_CLIENT_SECRET": {"category": "email_auth", "label": "Discord OAuth Client Secret", "type": "password"},

    # ── Integrations ──────────────────────────────────────────────

    # Social media
    "POSTIZ_API_KEY": {"category": "integrations", "label": "Postiz API Key", "type": "password"},
    "POSTIZ_API_URL": {"category": "integrations", "label": "Postiz API URL", "type": "string", "default": "https://api.postiz.com/public/v1"},

    # Payments
    "STRIPE_PRICE_ID": {"category": "integrations", "label": "Stripe Price ID", "type": "string"},
    "STRIPE_WEBHOOK_SECRET": {"category": "integrations", "label": "Stripe Webhook Secret", "type": "password"},

    # Analytics
    "API_ANALYTICS_KEY": {"category": "integrations", "label": "API Analytics Key", "type": "password"},
    "API_ANALYTICS_LOG_LEVEL": {"category": "integrations", "label": "API Analytics Log Level", "type": "string", "default": "info"},

    # Search & Web
    "NEWS_API_KEY": {"category": "integrations", "label": "News API Key", "type": "password"},
    "GOOGLE_SEARCH_API_KEY": {"category": "integrations", "label": "Google Search API Key", "type": "password"},
    "GOOGLE_SEARCH_ENGINE_ID": {"category": "integrations", "label": "Google Search Engine ID", "type": "string"},
    "BROWSERLESS_BASE_URL": {"category": "integrations", "label": "Browserless URL", "type": "string"},
    "BROWSERLESS_TOKEN": {"category": "integrations", "label": "Browserless Token", "type": "password"},

    # Internal
    "AGENT_INTERNAL_API_BASE_URL": {"category": "integrations", "label": "Agent Internal API URL", "type": "string"},

    # ── General / Defaults ────────────────────────────────────────

    "CLEANUP_INTERVAL_HOURS": {"category": "general", "label": "Cleanup Interval (hours)", "type": "number", "default": 6},
    "JOB_RETENTION_HOURS": {"category": "general", "label": "Job Retention (hours)", "type": "number", "default": 24},
    "S3_CACHE_TTL_DAYS": {"category": "general", "label": "S3 Cache TTL (days)", "type": "number", "default": 30},
    "ENABLE_S3_CLEANUP": {"category": "general", "label": "Enable S3 Cleanup", "type": "boolean", "default": False},
}

# Category labels for frontend display
CATEGORY_LABELS: dict[str, str] = {
    "ai_providers": "AI Providers",
    "speech_media": "Speech & Media",
    "email_auth": "Email & Auth",
    "integrations": "Integrations",
    "general": "General",
}


def _mask_value(value: str) -> str:
    """Mask a secret value, showing only last 4 characters."""
    if not value or len(value) <= 4:
        return "****"
    return "*" * min(len(value) - 4, 12) + value[-4:]


def get_current_config() -> dict[str, dict[str, Any]]:
    """
    Return all configurable settings grouped by category.

    For each setting, returns current value (masked for passwords),
    whether it's configured, and metadata.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for env_key, meta in CONFIGURABLE_SETTINGS.items():
        category = meta["category"]
        if category not in grouped:
            grouped[category] = {
                "label": CATEGORY_LABELS.get(category, category),
                "settings": {},
            }

        raw_value = os.getenv(env_key, "")
        is_configured = bool(raw_value)

        if meta["type"] == "password" and raw_value:
            display_value = _mask_value(raw_value)
        else:
            display_value = raw_value or meta.get("default", "")

        # Convert to proper type for display
        if meta["type"] == "number" and display_value != "":
            try:
                display_value = int(display_value) if isinstance(display_value, str) else display_value
            except (ValueError, TypeError):
                pass
        elif meta["type"] == "boolean":
            if isinstance(display_value, str):
                display_value = display_value.lower() in ("true", "1", "yes", "on")

        setting_data: dict[str, Any] = {
            "value": display_value,
            "configured": is_configured,
            "type": meta["type"],
            "label": meta["label"],
            "default": meta.get("default", ""),
            "placeholder": meta.get("placeholder", ""),
        }
        if "provider" in meta:
            setting_data["provider"] = meta["provider"]

        grouped[category]["settings"][env_key] = setting_data

    return grouped


def apply_config_values(values: dict[str, str]) -> list[str]:
    """
    Apply config values to os.environ and return list of updated keys.

    Skips password fields whose value is a mask (unchanged).
    """
    updated: list[str] = []

    for key, value in values.items():
        if key not in CONFIGURABLE_SETTINGS:
            continue

        meta = CONFIGURABLE_SETTINGS[key]

        # Skip masked password values (user didn't change them)
        if meta["type"] == "password":
            if not value or value.startswith("*"):
                continue

        str_value = str(value)

        # Empty string = clear the override
        if str_value == "":
            os.environ.pop(key, None)
        else:
            os.environ[key] = str_value

        updated.append(key)

    return updated
