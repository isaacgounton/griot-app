"""
Utility helpers for agent features.
"""
import hashlib
from typing import Optional


def normalize_owner_identifier(raw_identifier: Optional[str]) -> Optional[str]:
    """
    Convert a user identifier (API key, user id, etc.) into a stable hash used for storage.

    Args:
        raw_identifier: Original identifier value. None is returned if input is falsy.

    Returns:
        A SHA-256 hexadecimal digest string or None if identifier is not provided.
    """
    if not raw_identifier:
        return None
    if isinstance(raw_identifier, str):
        value = raw_identifier.strip()
    else:
        value = str(raw_identifier)
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
