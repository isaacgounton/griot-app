"""
User management service for handling user CRUD operations.
"""
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select, func, or_, and_
from app.database import User, UserRole, database_service
from app.utils.security import hash_password as _bcrypt_hash, verify_password as _bcrypt_verify
from loguru import logger


class UserService:
    """Service for managing users in the database."""

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return _bcrypt_hash(password)

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its bcrypt hash."""
        return _bcrypt_verify(password, hashed)
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        async for session in database_service.get_session():
            try:
                # Validate email
                if not self._validate_email(user_data["email"]):
                    raise ValueError("Invalid email format")
                
                # Check if user already exists
                result = await session.execute(
                    select(User).where(
                        or_(
                            User.email == user_data["email"],
                            User.username == user_data.get("username", user_data["email"])
                        )
                    )
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    raise ValueError("User with this email or username already exists")
                
                # Create new user
                user = User(
                    username=user_data.get("username", user_data["email"]),
                    email=user_data["email"],
                    full_name=user_data.get("full_name"),
                    hashed_password=self._hash_password(user_data["password"]),
                    role=UserRole(user_data.get("role", "user")),
                    is_active=user_data.get("is_active", True),
                    is_verified=user_data.get("is_verified", False)
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"Created user {user.email} with role {user.role.value}")
                
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login is not None else None
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create user: {e}")
                raise
        
        # Fallback return if session iteration fails
        raise RuntimeError("Failed to get database session")
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Count related data using the table classes directly
            from app.database import APIKey, Project
            
            api_keys_result = await session.execute(
                select(func.count()).select_from(APIKey).where(APIKey.user_id == user.id)
            )
            projects_result = await session.execute(
                select(func.count()).select_from(Project).where(Project.owner_id == user.id)
            )
            
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login is not None else None,
                "projects_count": projects_result.scalar() or 0,
                "api_keys_count": api_keys_result.scalar() or 0
                ,
                "subscription_status": user.subscription_status,
                "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
            }
        
        # Fallback return if session iteration fails
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login is not None else None,
                "subscription_status": user.subscription_status,
                "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
            }
        
        # Fallback return if session iteration fails
        return None
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing user."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                
                # Update fields
                if "username" in user_data:
                    user.username = user_data["username"]
                if "email" in user_data:
                    if not self._validate_email(user_data["email"]):
                        raise ValueError("Invalid email format")
                    user.email = user_data["email"]
                if "full_name" in user_data:
                    user.full_name = user_data["full_name"]
                if "password" in user_data:
                    user.hashed_password = self._hash_password(user_data["password"])
                if "role" in user_data:
                    user.role = UserRole(user_data["role"])
                if "is_active" in user_data:
                    user.is_active = user_data["is_active"]
                
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"Updated user {user.email}")
                
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login is not None else None
                }
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user {user_id}: {e}")
                raise
        
        # Fallback return if session iteration fails
        return None
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        async for session in database_service.get_session():
            try:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                await session.delete(user)
                await session.commit()
                
                logger.info(f"Deleted user {user.email}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete user {user_id}: {e}")
                raise
        
        # Fallback return if session iteration fails
        return False
    
    async def list_users(
        self, 
        page: int = 1, 
        limit: int = 50, 
        search: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List users with pagination and filtering."""
        try:
            async for session in database_service.get_session():
                # Build query
                query = select(User)
                
                # Apply filters
                if search:
                    search_term = f"%{search}%"
                    query = query.where(
                        or_(
                            User.email.ilike(search_term),
                            User.username.ilike(search_term),
                            User.full_name.ilike(search_term)
                        )
                    )
                
                if role_filter and role_filter != "all":
                    query = query.where(User.role == UserRole(role_filter))
                
                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total_count = total_result.scalar()
                
                # Apply pagination
                offset = (page - 1) * limit
                query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
                
                # Execute query
                result = await session.execute(query)
                users = result.scalars().all()
                
                # Convert to dict format
                users_data: list[Dict[str, Any]] = []
                for user in users:
                    # Get counts for each user
                    from app.database import APIKey, Project
                    
                    api_keys_result = await session.execute(
                        select(func.count()).select_from(APIKey).where(APIKey.user_id == user.id)
                    )
                    projects_result = await session.execute(
                        select(func.count()).select_from(Project).where(Project.owner_id == user.id)
                    )
                    
                    users_data.append({
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role.value,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat() if user.last_login is not None else None,
                        "projects_count": projects_result.scalar() or 0,
                        "api_keys_count": api_keys_result.scalar() or 0
                    })
                
                total_pages = ((total_count or 0) + limit - 1) // limit
                
                return {
                    "users": users_data,
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
            logger.warning(f"Database not available for list_users: {e}")
            pass
        
        # Fallback return if session iteration fails
        return {
            "users": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        async for session in database_service.get_session():
            # Total users
            total_result = await session.execute(select(func.count(User.id)))
            total_users = total_result.scalar()
            
            # Active users
            active_result = await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = active_result.scalar()
            
            # Users by role
            admin_result = await session.execute(
                select(func.count(User.id)).where(User.role == "admin")
            )
            admin_count = admin_result.scalar()
            
            user_result = await session.execute(
                select(func.count(User.id)).where(User.role == "user")
            )
            user_count = user_result.scalar()
            
            viewer_result = await session.execute(
                select(func.count(User.id)).where(User.role == "viewer")
            )
            viewer_count = viewer_result.scalar()
            
            # Users created this month
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            this_month_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= month_start)
            )
            this_month_count = this_month_result.scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "admin_count": admin_count,
                "user_count": user_count,
                "viewer_count": viewer_count,
                "this_month_count": this_month_count
            }
        
        # Fallback return if session iteration fails
        return {
            "total_users": 0,
            "active_users": 0,
            "admin_count": 0,
            "user_count": 0,
            "viewer_count": 0,
            "this_month_count": 0
        }
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with email and password."""
        async for session in database_service.get_session():
            result = await session.execute(
                select(User).where(
                    and_(User.email == email, User.is_active == True)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user or not self._verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            last_login_time = datetime.now(timezone.utc).replace(tzinfo=None)
            user.last_login = last_login_time
            await session.commit()
            
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": last_login_time.isoformat()  # Use the local variable, guaranteed not None
            }
        
        # Fallback return if session iteration fails
        return None


# Singleton instance
user_service = UserService()