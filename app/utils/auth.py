"""
Authentication utilities for API key verification.
"""
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import APIKeyHeader
import logging

logger = logging.getLogger(__name__)


async def _enforce_rate_limits(key_info: Dict[str, Any]) -> None:
    """Enforce hourly rate limits and monthly quotas for database API keys.

    Skipped for env keys and JWT tokens (no limits).
    Uses Redis INCR for atomic hourly counters and checks monthly_quota
    against the DB usage_count.  Also increments the persistent usage counter.
    """
    key_id = key_info.get("key_id")
    if not key_id or key_id in ("env", "jwt"):
        return

    rate_limit = key_info.get("rate_limit")
    monthly_quota = key_info.get("monthly_quota")
    usage_count = key_info.get("usage_count", 0)

    # Monthly quota check (DB-tracked total_requests)
    if monthly_quota and usage_count >= monthly_quota:
        raise HTTPException(
            status_code=429,
            detail="Monthly API quota exceeded. Please upgrade your plan or wait until next month."
        )

    # Hourly rate limit check (Redis counter)
    if rate_limit:
        try:
            from app.services.redis.redis_service import redis_service
            if redis_service.redis_client:
                rate_key = f"rate_limit:{key_id}:hourly"
                current = await redis_service.redis_client.incr(rate_key)
                if current == 1:
                    # First request this hour — set 1-hour TTL
                    await redis_service.redis_client.expire(rate_key, 3600)
                if current > rate_limit:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded ({rate_limit} requests/hour). Try again later."
                    )
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is down, allow the request (fail-open)
            logger.warning(f"Rate limit check failed (allowing request): {e}")

    # Increment persistent usage counter in DB
    try:
        from app.services.api_key.api_key_service import api_key_service
        await api_key_service.increment_usage(key_id)
    except Exception as e:
        logger.warning(f"Failed to increment usage counter: {e}")

# Define API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Get API key from environment variable
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    logger.warning("API_KEY environment variable is not set. Falling back to DB API key validation only.")


async def get_api_key(
    request: Request,
    api_key_header: Optional[str] = Security(API_KEY_HEADER)
) -> str:
    """
    Validate the API key from X-API-Key header or Authorization header.
    Supports multiple authentication methods for compatibility with different MCP clients including n8n.
    Validates against both environment API key and database-generated API keys.

    Args:
        request: FastAPI request object
        api_key_header: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If API_KEY is not set in environment, don't bypass authentication silently.
    # We'll still try to validate via database API keys.

    # Extract API key from various possible sources
    provided_key = None

    # 1. Check X-API-Key header (case-insensitive)
    if api_key_header and isinstance(api_key_header, str):
        provided_key = api_key_header
        logger.debug(f"API key found in X-API-Key header")

    # 2. Check Authorization header (for n8n and other MCP clients)
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        logger.debug(f"Authorization header found: {auth_header[:20]}...")

        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]  # Remove "Bearer " prefix
        elif auth_header.startswith("bearer "):
            provided_key = auth_header[7:]  # Remove "bearer " prefix
        else:
            # Support direct API key in Authorization header
            provided_key = auth_header

    # 3. Check for alternative headers that n8n might use
    elif request.headers.get("x-api-key"):
        provided_key = request.headers.get("x-api-key")
        logger.debug("API key found in x-api-key header (lowercase)")

    # 4. Check for any header containing 'api-key' (case-insensitive)
    else:
        for header_name, header_value in request.headers.items():
            if "api-key" in header_name.lower():
                provided_key = header_value
                logger.debug(f"API key found in header: {header_name}")
                break

    # Check if any API key was provided
    if not provided_key:
        logger.warning("No API key found in any supported header format")
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Please provide a valid API key in the X-API-Key header or Authorization header."
        )

    # Validate API key - check environment key first
    key_info = None
    if API_KEY and provided_key == API_KEY:
        logger.debug("Environment API key validated successfully")
        key_info = {
            "id": "env",
            "key_id": "env",
            "name": "Environment API Key",
            "user_id": None,
            "user_email": None,
            "user_role": "admin",
            "rate_limit": None,
            "monthly_quota": None,
            "usage_count": 0,
        }
        # Preserve backward compatibility: still return the string
        request.state.api_key_info = key_info
        return provided_key

    # Check if the provided key is a valid JWT token (for web UI compatibility)
    try:
        from app.utils.jwt_auth import verify_token
        token_data = verify_token(provided_key)
        if token_data:
            logger.debug(f"JWT token validated successfully for user: {token_data.username}")
            key_info = {
                "id": "jwt",
                "key_id": "jwt",
                "name": "JWT Token",
                "user_id": str(token_data.user_id),
                "user_email": token_data.email,
                "user_role": token_data.role,
                "rate_limit": None,
                "monthly_quota": None,
                "usage_count": 0,
            }
            request.state.api_key_info = key_info
            return provided_key
    except Exception as e:
        logger.debug(f"JWT validation failed: {e}")
        # Continue to database API key validation

    # Check database API keys if JWT doesn't match
    try:
        from app.services.api_key.api_key_service import api_key_service
        key_info = await api_key_service.validate_api_key(provided_key)
        if key_info:
            logger.debug(f"Database API key validated successfully for user: {key_info['user_email']}")
            # Enforce rate limits and monthly quotas
            await _enforce_rate_limits(key_info)
            request.state.api_key_info = key_info
            return provided_key
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Error validating database API key: {e}")
        # Continue to environment key validation if database validation fails

    # If we get here, the key is invalid
    logger.warning(f"Invalid API key provided: {provided_key[:10]}...")
    raise HTTPException(
        status_code=403,
        detail="Invalid API Key. Please provide a valid API key."
    )


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Unified authentication dependency supporting both JWT tokens and API keys.

    Priority:
    1. Try JWT token from cookie (web UI authentication)
    2. Fall back to API key from header (programmatic access)

    Returns:
        Dict with user_id, user_role, and user_email

    Raises:
        HTTPException: If authentication fails
    """
    # Try JWT authentication first (for web UI)
    cookie_token = request.cookies.get("access_token")

    if cookie_token:
        try:
            # Remove "Bearer " prefix if present
            token_to_verify = cookie_token[7:] if cookie_token.startswith("Bearer ") else cookie_token

            from app.utils.jwt_auth import verify_token
            token_data = verify_token(token_to_verify)

            logger.debug(f"✅ JWT authentication successful for user: {token_data.username}")

            # Store in request state for backward compatibility
            user_info = {
                "user_id": str(token_data.user_id),
                "user_role": token_data.role,
                "user_email": token_data.email
            }
            request.state.api_key_info = user_info
            return user_info
        except Exception as e:
            logger.debug(f"JWT cookie authentication failed: {e}")

    # Check if there's a JWT token in headers (sometimes sent by frontend)
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        token_to_check = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header

        # Check if it's a JWT token (starts with "eyJ")
        if token_to_check.startswith("eyJ"):
            try:
                from app.utils.jwt_auth import verify_token
                token_data = verify_token(token_to_check)

                logger.debug(f"✅ JWT header authentication successful for user: {token_data.username}")

                user_info = {
                    "user_id": str(token_data.user_id),
                    "user_role": token_data.role,
                    "user_email": token_data.email
                }
                request.state.api_key_info = user_info
                return user_info
            except Exception as e:
                logger.debug(f"JWT header authentication failed: {e}")
                # Don't fall through to API key validation for JWT tokens
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired JWT token. Please login again."
                )

    # Fall back to API key authentication (for programmatic access)
    # Only check for actual API keys (not JWT tokens)
    api_key_header = (
        request.headers.get("X-API-Key") or
        request.headers.get("x-api-key")
    )

    # Also check for any header containing "api-key"
    if not api_key_header:
        for header_name, header_value in request.headers.items():
            if "api-key" in header_name.lower() and header_name.lower() != "authorization":
                api_key_header = header_value
                break

    if api_key_header:
        # Remove "Bearer " prefix if present
        if api_key_header.startswith("Bearer "):
            api_key_header = api_key_header[7:]

        # Skip if it looks like a JWT token
        if api_key_header.startswith("eyJ"):
            logger.debug("Skipping JWT token in API key header")
        else:
            try:
                # Validate API key directly (inline from get_api_key logic)
                provided_key = api_key_header
                
                # Check environment key first
                if API_KEY and provided_key == API_KEY:
                    logger.debug("Environment API key validated successfully")
                    key_info = {
                        "id": "env",
                        "key_id": "env",
                        "name": "Environment API Key",
                        "user_id": None,
                        "user_email": None,
                        "user_role": "admin",
                        "rate_limit": None,
                        "monthly_quota": None,
                        "usage_count": 0,
                    }
                    request.state.api_key_info = key_info
                    return key_info
                
                # Check database API keys
                from app.services.api_key.api_key_service import api_key_service
                key_info = await api_key_service.validate_api_key(provided_key)
                if key_info:
                    logger.debug(f"Database API key validated successfully for user: {key_info['user_email']}")
                    # Enforce rate limits and monthly quotas
                    await _enforce_rate_limits(key_info)
                    request.state.api_key_info = key_info
                    return key_info

            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.debug(f"API key authentication failed: {e}")

    # If both methods fail, raise authentication error
    logger.warning(f"Authentication failed - no valid credentials found. Path: {request.url.path}")
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please login or provide a valid API key."
    )