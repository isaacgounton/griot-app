"""
OAuth 2.0 configuration using Authlib.
Supports Google, GitHub, and other OAuth providers.
"""
import os
import logging
from typing import Optional
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

logger = logging.getLogger(__name__)

# Load environment variables
config = Config(environ=os.environ)

# OAuth client configuration
oauth = OAuth(config)

# Get base URL for OAuth callbacks
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def get_oauth_redirect_uri(provider: str) -> str:
    """Get the OAuth redirect URI for a specific provider."""
    return f"{BASE_URL}/auth/oauth/{provider}/callback"

# Register Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account',  # Always show account selector
        },
        redirect_uri=get_oauth_redirect_uri('google')
    )
    logger.info("Google OAuth configured")
else:
    logger.warning("Google OAuth not configured (missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET)")

# Register GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params={'scope': 'user:email'},
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        client_kwargs={'scope': 'user:email'},
        redirect_uri=get_oauth_redirect_uri('github')
    )
    logger.info("GitHub OAuth configured")
else:
    logger.warning("GitHub OAuth not configured (missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET)")

# Register Discord OAuth
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

if DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET:
    oauth.register(
        name='discord',
        client_id=DISCORD_CLIENT_ID,
        client_secret=DISCORD_CLIENT_SECRET,
        authorize_url='https://discord.com/api/oauth2/authorize',
        authorize_params={'scope': 'identify email'},
        access_token_url='https://discord.com/api/oauth2/token',
        client_kwargs={'scope': 'identify email'},
        redirect_uri=get_oauth_redirect_uri('discord')
    )
    logger.info("Discord OAuth configured")
else:
    logger.warning("Discord OAuth not configured (missing DISCORD_CLIENT_ID or DISCORD_CLIENT_SECRET)")

def get_configured_providers() -> list[str]:
    """Get list of configured OAuth providers."""
    providers = []
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        providers.append('google')
    if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        providers.append('github')
    if DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET:
        providers.append('discord')
    return providers

def is_provider_configured(provider: str) -> bool:
    """Check if a specific OAuth provider is configured."""
    return provider in get_configured_providers()
