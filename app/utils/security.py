"""
Security utilities for password hashing and token generation.
"""
import secrets
import string
import hashlib
from datetime import datetime, timedelta, timezone
from loguru import logger

# Try to import bcrypt directly first (more reliable)
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    logger.info("Using bcrypt directly for password hashing")
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available, will use passlib fallback")

# Fallback to passlib if bcrypt direct import fails
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12,
        bcrypt__ident="2b"
    )
    PASSLIB_AVAILABLE = True
except Exception as e:
    PASSLIB_AVAILABLE = False
    pwd_context = None
    logger.warning(f"passlib not available: {e}")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes will be truncated.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password
    """
    # Bcrypt has a 72-byte limit - truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    
    # Try bcrypt directly first (most reliable)
    if BCRYPT_AVAILABLE:
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password_bytes, salt)
            hashed_str = hashed.decode('utf-8')
            if hashed_str.startswith('$2'):
                return hashed_str
        except Exception as e:
            logger.warning(f"Direct bcrypt hashing failed: {e}")
    
    # Fallback to passlib
    if PASSLIB_AVAILABLE and pwd_context:
        try:
            hashed = pwd_context.hash(password)
            if hashed and hashed.startswith('$2'):
                return hashed
        except Exception as e:
            logger.warning(f"Passlib bcrypt hashing failed: {e}")
    
    # Last resort: SHA256 fallback (not secure, but prevents crashes)
    logger.error("All bcrypt methods failed, using SHA256 fallback (NOT SECURE)")
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode('utf-8'))
    fallback_hash = f"fallback${salt}${hash_obj.hexdigest()}"
    return fallback_hash

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Note: Passwords longer than 72 bytes will be truncated to match hashing behavior.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    # Handle fallback hashes (insecure, but prevents login failures)
    if hashed_password.startswith('fallback$'):
        try:
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                salt = parts[1]
                expected_hash = parts[2]
                hash_obj = hashlib.sha256((salt + plain_password).encode('utf-8'))
                return hash_obj.hexdigest() == expected_hash
        except Exception:
            pass
        return False
    
    # Check if this is a valid bcrypt hash (should start with $2)
    if not hashed_password.startswith('$2'):
        logger.warning(f"Invalid hash format detected (not bcrypt): {hashed_password[:20]}...")
        # This is not a valid bcrypt hash - reject the login
        # The user needs to reset their password
        return False
    
    # Apply same 72-byte truncation for verification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    
    # Try bcrypt directly first
    if BCRYPT_AVAILABLE:
        try:
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.warning(f"Direct bcrypt verification failed: {e}")
    
    # Fallback to passlib
    if PASSLIB_AVAILABLE and pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Passlib password verification failed: {e}")
    
    return False

def generate_verification_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure token for email verification.
    
    Args:
        length: Length of the token (default 32 characters)
        
    Returns:
        Random alphanumeric token
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_verification_token_expiry(hours: int = 24) -> datetime:
    """
    Get the expiry datetime for a verification token.
    
    Args:
        hours: Number of hours until token expires (default 24)
        
    Returns:
        Datetime when token should expire (UTC timezone-naive)
    """
    expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
    return expiry.replace(tzinfo=None)

def is_verification_token_expired(expiry_time: datetime) -> bool:
    """
    Check if a verification token has expired.
    
    Args:
        expiry_time: The token expiry datetime (UTC timezone-naive)
        
    Returns:
        True if token has expired, False otherwise
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now > expiry_time
