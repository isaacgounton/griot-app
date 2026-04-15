"""
API Key management service for handling API key CRUD operations.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
import os
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import APIKey, APIKeyStatus, User, database_service
from loguru import logger


class APIKeyService:
    """Service for managing API keys in the database."""
    
    def _generate_key_id(self) -> str:
        """Generate a unique key ID."""
        return str(uuid.uuid4())
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        # Generate a 32-byte random key and format as oui_sk_<hex>
        random_bytes = secrets.token_bytes(32)
        return f"oui_sk_{random_bytes.hex()}"
    
    def _hash_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        if not isinstance(api_key, str):
            raise TypeError(f"api_key must be a string, got {type(api_key).__name__}")
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(self, key_data: Dict[str, Any], requester_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new API key."""
        async for session in database_service.get_session():
            try:
                # Validate user exists
                user_id = int(key_data["user_id"])
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    raise ValueError("User not found")
                
                # Rate limiting: block if user's created too many keys recently (simple throttle)
                # Allow admin callers (requester_info.user_role == 'admin') to bypass
                if requester_info and requester_info.get("user_role") == "admin":
                    allowed = True
                else:
                    allowed = True
                    try:
                        # Check how many keys were created for this user in the last hour
                        from datetime import timedelta, datetime as _datetime
                        now = _datetime.now(timezone.utc).replace(tzinfo=None)
                        hour_ago = (now - timedelta(hours=1))
                        count_result = await session.execute(select(func.count(APIKey.id)).where(APIKey.user_id == int(user_id), APIKey.created_at >= hour_ago))
                        recent_count = count_result.scalar() or 0
                        if recent_count >= int(os.getenv("CREATE_API_KEY_RATE_LIMIT_PER_HOUR", "5")):
                            allowed = False
                    except Exception:
                        allowed = True
                if not allowed:
                    raise ValueError("API key creation rate limit exceeded for this user")

                # Enforce total API key count per user (max per user)
                if requester_info and requester_info.get("user_role") == "admin":
                    total_allowed = True
                else:
                    try:
                        max_keys_env = os.getenv("MAX_API_KEYS_PER_USER")
                        max_keys_allowed = int(max_keys_env) if max_keys_env else 5
                    except Exception:
                        max_keys_allowed = 5
                    total_result = await session.execute(select(func.count(APIKey.id)).where(APIKey.user_id == int(user_id)))
                    total_count = total_result.scalar() or 0
                    if total_count >= max_keys_allowed:
                        raise ValueError(f"User already has {total_count} API keys which exceeds the allowed limit of {max_keys_allowed}")

                # Generate key
                new_key = self._generate_api_key()
                key_id = self._generate_key_id()
                
                # Create API key record
                api_key = APIKey(
                    key_id=key_id,
                    key_hash=self._hash_key(new_key),
                    name=key_data["name"],
                    user_id=user_id,
                    status=APIKeyStatus.ACTIVE if key_data.get("is_active", True) else APIKeyStatus.INACTIVE,
                    rate_limit_per_hour=key_data.get("rate_limit", 100),
                    monthly_quota=key_data.get("monthly_quota"),
                    expires_at=key_data.get("expires_at")
                )
                
                session.add(api_key)
                await session.commit()
                await session.refresh(api_key)
                
                logger.info(f"Created API key {api_key.name} for user {user.email}")
                
                return {
                    "id": str(api_key.id),
                    "key_id": api_key.key_id,
                    "name": api_key.name,
                    "key": new_key,  # Return the actual key only on creation
                    "user_id": str(api_key.user_id),
                    "user_email": user.email,
                    "status": api_key.status.value,
                    "is_active": api_key.status == APIKeyStatus.ACTIVE,
                    "rate_limit": api_key.rate_limit_per_hour,
                    "monthly_quota": api_key.monthly_quota,
                    "usage_count": api_key.total_requests,
                    "created_at": api_key.created_at.isoformat(),
                    "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "permissions": []  # TODO: Implement permissions system
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create API key: {e}")
                raise
        
        raise RuntimeError("Failed to get database session")
    
    async def get_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get an API key by ID."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(APIKey, User)
                .join(User, APIKey.user_id == User.id)
                .where(APIKey.key_id == key_id)
            )
            row = result.first()
            
            if not row:
                return None
            
            api_key, user = row
            
            return {
                "id": str(api_key.id),
                "key_id": api_key.key_id,
                "name": api_key.name,
                "key": f"{api_key.key_hash[:12]}{'*' * 20}{api_key.key_hash[-4:]}",  # Masked key
                "user_id": str(api_key.user_id),
                "user_email": user.email,
                "status": api_key.status.value,
                "is_active": api_key.status == APIKeyStatus.ACTIVE,
                "rate_limit": api_key.rate_limit_per_hour,
                "monthly_quota": api_key.monthly_quota,
                "usage_count": api_key.total_requests,
                "created_at": api_key.created_at.isoformat(),
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "permissions": []  # TODO: Implement permissions system
            }
        
        return None
    
    async def update_api_key(self, key_id: str, key_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing API key."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    select(APIKey, User)
                    .join(User, APIKey.user_id == User.id)
                    .where(APIKey.key_id == key_id)
                )
                row = result.first()
                
                if not row:
                    return None
                
                api_key, user = row
                
                # Update fields
                if "name" in key_data:
                    api_key.name = key_data["name"]
                if "is_active" in key_data:
                    api_key.status = APIKeyStatus.ACTIVE if key_data["is_active"] else APIKeyStatus.INACTIVE
                if "rate_limit" in key_data:
                    api_key.rate_limit_per_hour = key_data["rate_limit"]
                if "monthly_quota" in key_data:
                    api_key.monthly_quota = key_data["monthly_quota"]
                if "expires_at" in key_data:
                    api_key.expires_at = key_data["expires_at"]
                
                await session.commit()
                await session.refresh(api_key)
                
                logger.info(f"Updated API key {api_key.name}")
                
                return {
                    "id": str(api_key.id),
                    "key_id": api_key.key_id,
                    "name": api_key.name,
                    "key": f"{api_key.key_hash[:12]}{'*' * 20}{api_key.key_hash[-4:]}",  # Masked key
                    "user_id": str(api_key.user_id),
                    "user_email": user.email,
                    "status": api_key.status.value,
                    "is_active": api_key.status == APIKeyStatus.ACTIVE,
                    "rate_limit": api_key.rate_limit_per_hour,
                    "monthly_quota": api_key.monthly_quota,
                    "usage_count": api_key.total_requests,
                    "created_at": api_key.created_at.isoformat(),
                    "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "permissions": []  # TODO: Implement permissions system
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update API key {key_id}: {e}")
                raise
        
        return None
    
    async def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    select(APIKey).where(APIKey.key_id == key_id)
                )
                api_key = result.scalar_one_or_none()
                
                if not api_key:
                    return False
                
                await session.delete(api_key)
                await session.commit()
                
                logger.info(f"Deleted API key {api_key.name}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete API key {key_id}: {e}")
                raise
        
        return False
    
    async def list_api_keys(
        self, 
        page: int = 1, 
        limit: int = 50, 
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List API keys with pagination and filtering."""
        try:
            async for session in database_service.get_session():
                # Build query
                query = select(APIKey, User).join(User, APIKey.user_id == User.id)
                
                # Apply filters
                if search:
                    search_term = f"%{search}%"
                    query = query.where(
                        or_(
                            APIKey.name.ilike(search_term),
                            User.email.ilike(search_term),
                            APIKey.key_id.ilike(search_term)
                        )
                    )
                
                if status_filter and status_filter != "all":
                    if status_filter == "active":
                        query = query.where(APIKey.status == APIKeyStatus.ACTIVE)
                    elif status_filter == "inactive":
                        query = query.where(APIKey.status == APIKeyStatus.INACTIVE)
                    elif status_filter == "revoked":
                        query = query.where(APIKey.status == APIKeyStatus.REVOKED)
                    elif status_filter == "expired":
                        now = datetime.now(timezone.utc).replace(tzinfo=None)
                        query = query.where(
                            and_(APIKey.expires_at.is_not(None), APIKey.expires_at < now)
                        )
                
                if user_id:
                    query = query.where(APIKey.user_id == user_id)
                
                # Get total count - always use proper FROM clause with join
                count_query = select(func.count(APIKey.id)).select_from(APIKey).join(User, APIKey.user_id == User.id)
                
                # Apply search filter to count query
                if search:
                    search_term = f"%{search}%"
                    count_query = count_query.where(
                        or_(
                            APIKey.name.ilike(search_term),
                            User.email.ilike(search_term),
                            APIKey.key_id.ilike(search_term)
                        )
                    )
                
                if status_filter and status_filter != "all":
                    if status_filter == "active":
                        count_query = count_query.where(APIKey.status == APIKeyStatus.ACTIVE)
                    elif status_filter == "inactive":
                        count_query = count_query.where(APIKey.status == APIKeyStatus.INACTIVE)
                    elif status_filter == "revoked":
                        count_query = count_query.where(APIKey.status == APIKeyStatus.REVOKED)
                    elif status_filter == "expired":
                        now = datetime.now(timezone.utc).replace(tzinfo=None)
                        count_query = count_query.where(
                            and_(APIKey.expires_at.is_not(None), APIKey.expires_at < now)
                        )
                if user_id:
                    count_query = count_query.where(APIKey.user_id == user_id)
                
                total_result = await session.execute(count_query)
                total_count = total_result.scalar()
                
                # Apply pagination
                offset = (page - 1) * limit
                query = query.offset(offset).limit(limit).order_by(APIKey.created_at.desc())
                
                # Execute query
                result = await session.execute(query)
                rows = result.all()
                
                # Convert to dict format
                api_keys_data = []
                for api_key, user in rows:
                    # Check if expired
                    is_expired = (
                        api_key.expires_at is not None and 
                        api_key.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
                    )
                    
                    api_keys_data.append({
                        "id": str(api_key.id),
                        "key_id": api_key.key_id,
                        "name": api_key.name,
                        "key": f"oui_sk_{'*' * 20}{api_key.key_hash[-8:]}",  # Masked key
                        "user_id": str(api_key.user_id),
                        "user_email": user.email,
                        "status": api_key.status.value,
                        "is_active": api_key.status == APIKeyStatus.ACTIVE and not is_expired,
                        "is_expired": is_expired,
                        "rate_limit": api_key.rate_limit_per_hour,
                        "monthly_quota": api_key.monthly_quota,
                        "usage_count": api_key.total_requests,
                        "created_at": api_key.created_at.isoformat(),
                        "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                        "permissions": []  # TODO: Implement permissions system
                    })
                
                total_pages = ((total_count or 0) + limit - 1) // limit
                
                return {
                    "api_keys": api_keys_data,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total_count": total_count,
                        "total_pages": total_pages,
                        "has_next": page < total_pages,
                        "has_prev": page > 1
                    }
                }
        except (RuntimeError, Exception) as e:
            # Database not available or other error - return empty list
            logger.warning(f"Database not available for list_api_keys: {e}")
            pass
        
        # Fallback return if session iteration fails
        return {
            "api_keys": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
    
    async def get_api_key_stats(self) -> Dict[str, Any]:
        """Get API key statistics."""
        async for session in database_service.get_session():
            # Total API keys
            total_result = await session.execute(select(func.count(APIKey.id)))
            total_keys = total_result.scalar()
            
            # Active API keys
            active_result = await session.execute(
                select(func.count(APIKey.id)).where(APIKey.status == APIKeyStatus.ACTIVE)
            )
            active_keys = active_result.scalar()
            
            # Revoked API keys
            revoked_result = await session.execute(
                select(func.count(APIKey.id)).where(APIKey.status == APIKeyStatus.REVOKED)
            )
            revoked_keys = revoked_result.scalar()
            
            # Total usage
            total_usage_result = await session.execute(
                select(func.sum(APIKey.total_requests))
            )
            total_usage = total_usage_result.scalar() or 0
            
            # Keys created this month
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
            
            this_month_result = await session.execute(
                select(func.count(APIKey.id)).where(APIKey.created_at >= month_start)
            )
            this_month_count = this_month_result.scalar()
            
            # Expired keys
            expired_result = await session.execute(
                select(func.count(APIKey.id)).where(
                    and_(APIKey.expires_at.is_not(None), APIKey.expires_at < now.replace(tzinfo=None))
                )
            )
            expired_keys = expired_result.scalar()
            
            return {
                "total_keys": total_keys,
                "active_keys": active_keys,
                "revoked_keys": revoked_keys,
                "expired_keys": expired_keys,
                "total_usage": total_usage,
                "this_month_count": this_month_count
            }
        
        # Fallback return if session iteration fails
        return {
            "total_keys": 0,
            "active_keys": 0,
            "revoked_keys": 0,
            "expired_keys": 0,
            "total_usage": 0,
            "this_month_count": 0
        }
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return key info if valid."""
        # Type check to prevent encoding errors
        if not isinstance(api_key, str):
            logger.error(f"validate_api_key received non-string api_key: {type(api_key).__name__}")
            return None
            
        async for session in database_service.get_session():
            key_hash = self._hash_key(api_key)
            
            result = await session.execute(
                select(APIKey, User)
                .join(User, APIKey.user_id == User.id)
                .where(
                    and_(
                        APIKey.key_hash == key_hash,
                        APIKey.status == APIKeyStatus.ACTIVE,
                        User.is_active == True
                    )
                )
            )
            row = result.first()
            
            if not row:
                return None
            
            api_key_record, user = row
            
            # Check if expired
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if api_key_record.expires_at and api_key_record.expires_at < now:
                return None
            
            # Update last used
            api_key_record.last_used = now
            await session.commit()
            
            return {
                "id": str(api_key_record.id),
                "key_id": api_key_record.key_id,
                "name": api_key_record.name,
                "user_id": str(api_key_record.user_id),
                "user_email": user.email,
                "user_role": user.role.value,
                "rate_limit": api_key_record.rate_limit_per_hour,
                "monthly_quota": api_key_record.monthly_quota,
                "usage_count": api_key_record.total_requests
            }
        
        return None
    
    async def increment_usage(self, key_id: str) -> bool:
        """Increment usage count for an API key."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    select(APIKey).where(APIKey.key_id == key_id)
                )
                api_key = result.scalar_one_or_none()
                
                if not api_key:
                    return False
                
                api_key.total_requests += 1
                api_key.last_used = datetime.now(timezone.utc).replace(tzinfo=None)
                
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to increment usage for API key {key_id}: {e}")
                return False
        
        return False


# Singleton instance
api_key_service = APIKeyService()