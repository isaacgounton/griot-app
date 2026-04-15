from fastapi import Request, Depends
from app.utils.auth import get_api_key


async def require_active_subscription(request: Request, api_key: str = Depends(get_api_key)) -> bool:
    """All features are free — no subscription check needed.

    This dependency is kept as a no-op so that the 43+ route files
    importing it continue to work without modification.
    """
    return True
