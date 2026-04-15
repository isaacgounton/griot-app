"""
OAuth authentication routes using Authlib.
Supports Google, GitHub, Discord, and other OAuth providers.
"""
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from loguru import logger

from app.database import User, UserRole, OAuthAccount, database_service
from app.utils.oauth_config import oauth, FRONTEND_URL, is_provider_configured
from app.utils.jwt_auth import create_access_token, set_auth_cookie

router = APIRouter(prefix="/auth/oauth", tags=["Authentication"])

@router.get("/providers")
async def get_oauth_providers():
    """Get list of configured OAuth providers."""
    from app.utils.oauth_config import get_configured_providers

    providers = get_configured_providers()

    return {
        "success": True,
        "providers": providers,
        "available": {
            "google": "google" in providers,
            "github": "github" in providers,
            "discord": "discord" in providers
        }
    }

@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """
    Initiate OAuth login flow.

    Supported providers: google, github, discord
    """
    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=400,
            detail=f"OAuth provider '{provider}' is not configured"
        )

    # Get the OAuth client for this provider
    client = oauth.create_client(provider)

    if not client:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize OAuth client for {provider}"
        )

    # Generate redirect URI — use BASE_URL if set (for production behind reverse proxy)
    import os
    base_url = os.getenv("BASE_URL", "").rstrip("/")
    if base_url:
        redirect_uri = f"{base_url}/api/v1/auth/oauth/{provider}/callback"
    else:
        redirect_uri = str(request.url_for('oauth_callback', provider=provider))

    logger.info(f"🔐 Initiating {provider} OAuth login, redirect: {redirect_uri}")

    # Redirect to provider's authorization page
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    """
    Handle OAuth callback from provider.

    This endpoint receives the authorization code from the OAuth provider,
    exchanges it for an access token, fetches user info, and creates/logs in the user.
    """
    if not is_provider_configured(provider):
        raise HTTPException(
            status_code=400,
            detail=f"OAuth provider '{provider}' is not configured"
        )

    try:
        # Get OAuth client
        client = oauth.create_client(provider)

        # Exchange authorization code for access token
        token = await client.authorize_access_token(request)

        # Fetch user info from provider
        if provider == 'google':
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
                user_info = user_info.json()

            provider_user_id = user_info.get('sub')
            email = user_info.get('email')
            name = user_info.get('name')
            avatar = user_info.get('picture')

        elif provider == 'github':
            # GitHub doesn't include user info in token response
            user_resp = await client.get('https://api.github.com/user', token=token)
            user_info = user_resp.json()

            provider_user_id = str(user_info.get('id'))
            email = user_info.get('email')
            name = user_info.get('name') or user_info.get('login')
            avatar = user_info.get('avatar_url')

            # If email is null, fetch from emails endpoint
            if not email:
                emails_resp = await client.get('https://api.github.com/user/emails', token=token)
                emails = emails_resp.json()
                # Get primary verified email
                for email_data in emails:
                    if email_data.get('primary') and email_data.get('verified'):
                        email = email_data.get('email')
                        break
                # If no primary verified email, use first email
                if not email and emails:
                    email = emails[0].get('email')

        elif provider == 'discord':
            user_resp = await client.get('https://discord.com/api/users/@me', token=token)
            user_info = user_resp.json()

            provider_user_id = user_info.get('id')
            email = user_info.get('email')
            name = user_info.get('username')
            avatar_hash = user_info.get('avatar')
            avatar = f"https://cdn.discordapp.com/avatars/{provider_user_id}/{avatar_hash}.png" if avatar_hash else None

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {provider}"
            )

        if not provider_user_id or not email:
            logger.error(f"❌ Missing required user info from {provider}: {user_info}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get required user information from {provider}"
            )

        logger.info(f"✅ Received OAuth callback from {provider} for user: {email}")

        # Database operations
        async for session in database_service.get_session():
            # Check if OAuth account already exists
            oauth_result = await session.execute(
                select(OAuthAccount).where(
                    OAuthAccount.provider == provider,
                    OAuthAccount.provider_user_id == provider_user_id
                )
            )
            oauth_account = oauth_result.scalars().first()

            if oauth_account:
                # OAuth account exists - log in the linked user
                user = oauth_account.user
                logger.info(f"🔗 Existing OAuth account found, logging in user: {user.username}")

                # Update OAuth account info
                oauth_account.provider_email = email
                oauth_account.provider_name = name
                oauth_account.provider_avatar = avatar
                oauth_account.access_token = token.get('access_token')
                oauth_account.refresh_token = token.get('refresh_token')
                oauth_account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            else:
                # Check if user exists with this email
                user_result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = user_result.scalars().first()

                if user:
                    logger.info(f"👤 User exists with email {email}, linking OAuth account")
                else:
                    # Create new user
                    logger.info(f"✨ Creating new user from {provider} OAuth: {email}")

                    # Generate username from email or name
                    base_username = email.split('@')[0] if email else name.lower().replace(' ', '_')
                    username = base_username

                    # Ensure username is unique
                    counter = 1
                    while True:
                        existing = await session.execute(
                            select(User).where(User.username == username)
                        )
                        if not existing.scalars().first():
                            break
                        username = f"{base_username}{counter}"
                        counter += 1

                    user = User(
                        username=username,
                        email=email,
                        full_name=name,
                        hashed_password=None,  # OAuth users don't have password
                        is_verified=True,  # OAuth emails are pre-verified
                        is_active=True,
                        role=UserRole.USER
                    )
                    session.add(user)
                    await session.flush()  # Get user.id

                # Create OAuth account link
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_email=email,
                    provider_name=name,
                    provider_avatar=avatar,
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token')
                )
                session.add(oauth_account)

            # Update last login
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)

            await session.commit()
            await session.refresh(user)

            # Create JWT token
            token_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }

            access_token = create_access_token(data=token_data)

            # Set HTTP-only cookie
            set_auth_cookie(response, access_token)

            logger.info(f"✅ {provider.title()} OAuth login successful for user: {user.username}")

            # Redirect to frontend with token
            redirect_url = f"/auth/callback?token={access_token}&success=true"
            return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OAuth callback error for {provider}: {str(e)}", exc_info=True)
        # Redirect to frontend with error
        redirect_url = f"/auth/callback?error=oauth_failed&message={str(e)}"
        return RedirectResponse(url=redirect_url)

@router.post("/{provider}/link")
async def link_oauth_account(provider: str, request: Request):
    """
    Link an OAuth provider to an existing authenticated user.

    This allows users to add additional OAuth providers to their account.
    """
    # TODO: Implement linking OAuth accounts to existing users
    # This requires getting the current authenticated user from JWT
    raise HTTPException(
        status_code=501,
        detail="OAuth account linking not yet implemented"
    )

@router.delete("/{provider}/unlink")
async def unlink_oauth_account(provider: str, request: Request):
    """
    Unlink an OAuth provider from the current user.

    This removes the OAuth account connection but keeps the user account.
    """
    # TODO: Implement unlinking OAuth accounts
    raise HTTPException(
        status_code=501,
        detail="OAuth account unlinking not yet implemented"
    )
