"""Unified error handling utilities for route handlers."""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def handle_service_error(e: Exception, operation: str) -> HTTPException:
    """Convert a service exception to an appropriate HTTP error.

    Usage in routes:
        except HTTPException:
            raise
        except Exception as e:
            raise handle_service_error(e, "video generation")
    """
    logger.error(f"Error in {operation}: {type(e).__name__}: {e}", exc_info=True)

    if isinstance(e, HTTPException):
        return e
    if isinstance(e, ValueError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(e))
    if isinstance(e, PermissionError):
        return HTTPException(status_code=403, detail="Permission denied")

    return HTTPException(status_code=500, detail=f"Internal error during {operation}")
