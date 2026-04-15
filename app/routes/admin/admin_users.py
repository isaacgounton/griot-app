"""
Admin endpoints for user management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.settings.user_service import user_service


router = APIRouter(prefix="/admin/users", tags=["Admin"])


class CreateUserRequest(BaseModel):
    username: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    password: str
    role: str = "user"
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/")
async def create_user(
    request: CreateUserRequest,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        request: User creation data
        
    Returns:
        Created user information
    """
    try:
        # Validate role
        valid_roles = ["admin", "user", "viewer"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        user_data = {
            "username": request.username,
            "email": request.email,
            "full_name": request.full_name,
            "password": request.password,
            "role": request.role,
            "is_active": request.is_active
        }
        
        user = await user_service.create_user(user_data)
        
        return {
            "success": True,
            "message": "User created successfully",
            "user": user
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email, username, or full name"),
    role: Optional[str] = Query(None, description="Filter by role (admin, user, viewer, all)"),
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List users with pagination and filtering.
    
    Args:
        page: Page number (1-based)
        limit: Number of users per page
        search: Search term for email, username, or full name
        role: Role filter
        
    Returns:
        List of users with pagination info
    """
    try:
        # Validate role filter
        if role and role not in ["admin", "user", "viewer", "all"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid role filter. Must be one of: admin, user, viewer, all"
            )
        
        result = await user_service.list_users(
            page=page,
            limit=limit,
            search=search,
            role_filter=role
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/stats")
async def get_user_stats(
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user statistics.
    
    Returns:
        User statistics including totals by role, active users, etc.
    """
    try:
        stats = await user_service.get_user_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific user by ID.
    
    Args:
        user_id: The user ID
        
    Returns:
        User information
    """
    try:
        user = await user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing user.
    
    Args:
        user_id: The user ID to update
        request: User update data
        
    Returns:
        Updated user information
    """
    try:
        # Validate role if provided
        if request.role and request.role not in ["admin", "user", "viewer"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Must be one of: admin, user, viewer"
            )
        
        # Build update data (only include fields that are not None)
        user_data = {}
        if request.username is not None:
            user_data["username"] = request.username
        if request.email is not None:
            user_data["email"] = request.email
        if request.full_name is not None:
            user_data["full_name"] = request.full_name
        if request.password is not None:
            user_data["password"] = request.password
        if request.role is not None:
            user_data["role"] = request.role
        if request.is_active is not None:
            user_data["is_active"] = request.is_active
        
        user = await user_service.update_user(user_id, user_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "message": "User updated successfully",
            "user": user
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a user.
    
    Args:
        user_id: The user ID to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        success = await user_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "message": f"User {user_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.post("/authenticate")
async def authenticate_user(
    email: str,
    password: str,
    _: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User information if authentication successful
    """
    try:
        user = await user_service.authenticate_user(email, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "success": True,
            "message": "Authentication successful",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")