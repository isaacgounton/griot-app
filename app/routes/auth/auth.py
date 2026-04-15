"""
Authentication routes for username/password login and user registration.
Implements database-backed authentication instead of hardcoded credentials.
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Response, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import User, UserRole, database_service
from app.utils.security import hash_password, verify_password, generate_verification_token, get_verification_token_expiry
from app.utils.email import send_verification_email
from app.utils.auth import get_current_user
from app.utils.jwt_auth import create_access_token, set_auth_cookie, get_current_user_from_cookie
from app.services.api_key.api_key_service import api_key_service
from loguru import logger

router = APIRouter(tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_verified: Optional[bool] = None
    role: Optional[str] = None
    api_key: Optional[str] = None

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    username: str
    password: str

class RegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    token: str

class VerifyEmailResponse(BaseModel):
    success: bool
    message: str

class AdminSetupRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: str

class AdminSetupResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None


def strip_env_value(value: Optional[str]) -> str:
    """Strip quotes and whitespace from environment variable values."""
    if not value:
        return ""
    # Remove surrounding quotes (both single and double)
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value


@router.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest, response: Response) -> LoginResponse:
    """
    Authenticate with username/email and password against the database.
    
    Returns user info if authentication succeeds and email is verified.
    """
    if not request.username or not request.password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required"
        )
    
    # Check if database is available
    if not database_service.is_database_available():
        logger.warning("Database not available, cannot authenticate user")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        async for session in database_service.get_session():
            # Find user by username or email
            user_result = await session.execute(
                select(User).where(
                    (User.username == request.username) | (User.email == request.username)
                )
            )
            user = user_result.scalars().first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent username: {request.username}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid username or password"
                )
            
            # Check if password hash is valid format (accept bcrypt or fallback format)
            if not user.hashed_password or (not user.hashed_password.startswith('$2') and not user.hashed_password.startswith('fallback$')):
                logger.error(f"User {user.username} has invalid password hash format - needs reset")
                raise HTTPException(
                    status_code=401,
                    detail="Your account requires a password reset. Please contact support or use the forgot password feature."
                )
            
            # Verify password
            if not verify_password(request.password, user.hashed_password):
                logger.warning(f"Failed login attempt for user: {user.username}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid username or password"
                )
            
            # Check if email is verified
            if not user.is_verified:
                logger.info(f"Login attempt by unverified user: {user.username}")
                raise HTTPException(
                    status_code=403,
                    detail="Please verify your email before logging in. Check your inbox for the verification link."
                )
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt by inactive user: {user.username}")
                raise HTTPException(
                    status_code=403,
                    detail="Your account has been deactivated"
                )
            
            # Update last login time
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
            await session.commit()

            # Create JWT token instead of API key (no database pollution!)
            token_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }

            access_token = create_access_token(data=token_data)

            # Set HTTP-only cookie for web authentication
            set_auth_cookie(response, access_token)

            logger.info(f"✅ User logged in successfully: {user.username}")

            return LoginResponse(
                success=True,
                message="Login successful",
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_verified=user.is_verified,
                role=user.role.value,
                api_key=access_token  # Return JWT token (frontend can store if needed)
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Error during login")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during authentication"
        )

@router.get("/auth/status", tags=["Authentication"])
async def auth_status() -> Dict[str, Any]:
    """
    Check authentication status.
    """
    return {
        "isAuthenticated": False,
        "message": "Please login to access the dashboard"
    }

@router.post("/auth/validate", tags=["Authentication"])
async def validate_api_key(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate an API key for programmatic access.
    
    Checks both user-generated API keys and environment API key (for backward compatibility).
    """
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="API key is required"
        )
    
    # Check against environment API key (for backward compatibility)
    env_api_key = os.getenv('API_KEY', '').strip()
    if env_api_key and api_key == env_api_key:
        return {
            "success": True,
            "valid": True,
            "message": "API key is valid (environment key)"
        }
    
    # Validate against user API keys stored in the database
    try:
        api_key_obj = await api_key_service.validate_api_key(api_key)
        if api_key_obj:
            return {
                "success": True,
                "valid": True,
                "message": "API key is valid (user key)",
                "user_id": api_key_obj.get("user_id")
            }
    except Exception as e:
        logger.debug(f"User API key validation failed: {e}")
    
    # Invalid key
    logger.warning(f"Invalid API key validation attempt")
    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )

@router.post("/auth/register", response_model=RegisterResponse, tags=["Authentication"])
async def register(request: RegisterRequest) -> RegisterResponse:
    """
    Register a new user with email and password.
    
    The user will receive a verification email. They must verify their email
    before they can log in.
    """
    # Validate input
    if not request.full_name or not request.full_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Full name is required"
        )
    
    if not request.email or "@" not in request.email:
        raise HTTPException(
            status_code=400,
            detail="Valid email is required"
        )
    
    if not request.username or len(request.username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 3 characters"
        )
    
    if not request.password or len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
    
    # Check if database is available
    if not database_service.is_database_available():
        logger.warning("Database not available, cannot register user")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        # Get database session
        async for session in database_service.get_session():
            # Check if username already exists
            existing_username = await session.execute(
                select(User).where(User.username == request.username)
            )
            if existing_username.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Username already taken"
                )
            
            # Check if email already exists
            existing_email = await session.execute(
                select(User).where(User.email == request.email)
            )
            if existing_email.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # Generate verification token and expiry
            verification_token = generate_verification_token()
            token_expiry = get_verification_token_expiry(hours=24)
            
            # Create new user with hashed password
            hashed_pwd = hash_password(request.password)
            
            # Validate the hash is properly formatted (bcrypt or fallback)
            if not hashed_pwd or (not hashed_pwd.startswith('$2') and not hashed_pwd.startswith('fallback$')):
                logger.error(f"❌ Invalid password hash generated for user {request.username}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create user account. Please try again."
                )
            
            # Warn if using fallback hash
            if hashed_pwd.startswith('fallback$'):
                logger.warning(f"⚠️ User {request.username} registered with fallback hash (bcrypt unavailable)")
            
            new_user = User(
                username=request.username,
                email=request.email,
                full_name=request.full_name,
                hashed_password=hashed_pwd,
                is_verified=False,
                verification_token=verification_token,
                verification_token_expires_at=token_expiry
            )
            
            # Add and commit to database
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            user_id = new_user.id
            
            # Send verification email
            email_sent = await send_verification_email(
                email=request.email,
                full_name=request.full_name,
                verification_token=verification_token
            )

            if not email_sent:
                # Check if email provider is actually configured
                resend_configured = bool(os.getenv("RESEND_API_KEY", ""))
                if resend_configured:
                    # Provider exists but sending failed (transient error) — do NOT auto-verify
                    logger.error(f"❌ Verification email failed to send to {request.email} (Resend configured but send failed)")
                    return RegisterResponse(
                        success=True,
                        message="Registration successful! We had trouble sending the verification email. Please try again later or contact support.",
                        user_id=str(user_id)
                    )
                else:
                    # No email provider configured — auto-verify so the user can log in
                    logger.warning(f"No email provider configured — auto-verifying user {request.username}")
                    new_user.is_verified = True
                    new_user.verification_token = None
                    new_user.verification_token_expires_at = None
                    await session.commit()

                    logger.info(f"✅ User registered and auto-verified: {request.username} ({request.email})")
                    return RegisterResponse(
                        success=True,
                        message="Registration successful! You can now log in.",
                        user_id=str(user_id)
                    )

            logger.info(f"✅ User registered successfully: {request.username} ({request.email})")

            return RegisterResponse(
                success=True,
                message="Registration successful! Please check your email to verify your account.",
                user_id=str(user_id)
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during registration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration"
        )

@router.post("/auth/verify-email", response_model=VerifyEmailResponse, tags=["Authentication"])
async def verify_email(request: VerifyEmailRequest) -> VerifyEmailResponse:
    """
    Verify user email using the token sent via email.
    """
    if not request.token:
        raise HTTPException(
            status_code=400,
            detail="Verification token is required"
        )
    
    # Check if database is available
    if not database_service.is_database_available():
        logger.warning("Database not available, cannot verify email")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        async for session in database_service.get_session():
            # Find user by verification token
            user_result = await session.execute(
                select(User).where(User.verification_token == request.token)
            )
            user = user_result.scalars().first()
            
            if not user:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid verification token"
                )
            
            # Check if token has expired
            if user.verification_token_expires_at:
                from app.utils.security import is_verification_token_expired
                if is_verification_token_expired(user.verification_token_expires_at):
                    raise HTTPException(
                        status_code=400,
                        detail="Verification token has expired. Please request a new one."
                    )
            
            # Check if already verified
            if user.is_verified:
                raise HTTPException(
                    status_code=400,
                    detail="Email already verified"
                )
            
            # Mark user as verified
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires_at = None
            
            await session.commit()
            
            logger.info(f"✅ Email verified successfully for user: {user.username}")
            
            return VerifyEmailResponse(
                success=True,
                message="Email verified successfully! You can now log in with your credentials."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error verifying email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during email verification"
        )

@router.post("/auth/admin/setup", response_model=AdminSetupResponse, tags=["Authentication"])
async def setup_admin(request: AdminSetupRequest) -> AdminSetupResponse:
    """
    Create the initial admin user.
    
    This endpoint can only be used if no admin users exist in the system.
    It creates a verified admin user that can immediately log in.
    """
    # Validate input
    if not request.full_name or not request.full_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Full name is required"
        )
    
    if not request.email or "@" not in request.email:
        raise HTTPException(
            status_code=400,
            detail="Valid email is required"
        )
    
    if not request.username or len(request.username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 3 characters"
        )
    
    if not request.password or len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
    
    # Check if database is available
    if not database_service.is_database_available():
        logger.warning("Database not available, cannot setup admin")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        async for session in database_service.get_session():
            # Check if any admin users already exist
            admin_count_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            existing_admins = admin_count_result.scalars().all()
            
            if existing_admins:
                raise HTTPException(
                    status_code=403,
                    detail="Admin user already exists. This endpoint can only be used to create the initial admin."
                )
            
            # Check if username already exists
            existing_username = await session.execute(
                select(User).where(User.username == request.username)
            )
            if existing_username.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Username already taken"
                )
            
            # Check if email already exists
            existing_email = await session.execute(
                select(User).where(User.email == request.email)
            )
            if existing_email.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # Create admin user (pre-verified, no email verification needed)
            new_admin = User(
                username=request.username,
                email=request.email,
                full_name=request.full_name,
                hashed_password=hash_password(request.password),
                role=UserRole.ADMIN,
                is_verified=True,  # Admin is pre-verified
                is_active=True
            )
            
            # Add and commit to database
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            
            user_id = new_admin.id
            
            logger.info(f"✅ Admin user created successfully: {request.username} ({request.email})")
            
            return AdminSetupResponse(
                success=True,
                message="Admin user created successfully! You can now log in with your credentials.",
                user_id=user_id
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during admin setup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during admin setup"
        )


# Profile Management Endpoints

class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool


def _user_to_profile(user: User) -> ProfileResponse:
    """Convert a User DB object to ProfileResponse."""
    return ProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        avatar_url=getattr(user, 'avatar_url', None),
        role=user.role.value,
        created_at=user.created_at,
        last_login=user.last_login,
        is_active=user.is_active
    )


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str


@router.get("/auth/profile", response_model=ProfileResponse, tags=["Authentication"])
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> ProfileResponse:
    """
    Get the current user's profile information.
    
    This endpoint requires authentication via API key or session.
    For single-user systems, returns the admin user profile.
    """
    # Check if database is available
    if not database_service.is_database_available():
        logger.warning("Database not available for profile lookup, returning default profile")
        # Return a default profile for single-user systems
        return ProfileResponse(
            id=1,
            username="admin",
            email="admin@griot.ai",
            full_name="Admin User",
            role="admin",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_login=None,
            is_active=True
        )
    
    try:
        async for session in database_service.get_session():
            # For single-user systems with global API key, return the admin user
            user_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN).limit(1)
            )
            user = user_result.scalars().first()
            
            if user:
                return _user_to_profile(user)

            # If no admin user exists, check for any user
            user_result = await session.execute(select(User).limit(1))
            user = user_result.scalars().first()

            if user:
                logger.info(f"Returning profile for user: {user.username} (no admin user found)")
                return _user_to_profile(user)
            
            # If no users exist at all, return a default profile for development
            logger.warning("No users found in database, returning default profile")
            return ProfileResponse(
                id=1,
                username="admin",
                email="admin@griot.ai", 
                full_name="Admin User",
                role="admin",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                last_login=None,
                is_active=True
            )
    
    except Exception as e:
        logger.error(f"❌ Error getting profile: {str(e)}")
        # Return a fallback profile on database errors
        logger.warning("Database error, returning fallback profile")
        return ProfileResponse(
            id=1,
            username="admin",
            email="admin@griot.ai",
            full_name="Admin User", 
            role="admin",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_login=None,
            is_active=True
        )


@router.put("/auth/profile", response_model=ProfileResponse, tags=["Authentication"])
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProfileResponse:
    """
    Update the current user's profile information.
    
    This endpoint requires authentication via API key or session.
    """
    if not database_service.is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        async for session in database_service.get_session():
            # Get first admin user as default (for development)
            user_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN).limit(1)
            )
            user = user_result.scalars().first()
            
            if not user:
                # If no admin, get any user
                user_result = await session.execute(select(User).limit(1))
                user = user_result.scalars().first()
            
            if not user:
                # Return default profile for development when no users exist
                logger.warning("No users found in database, cannot update profile")
                raise HTTPException(
                    status_code=404,
                    detail="User not found - please initialize the database first"
                )
            
            # Update fields if provided
            if request.username:
                # Check if username is already taken by another user
                existing = await session.execute(
                    select(User).where(
                        User.username == request.username,
                        User.id != user.id
                    )
                )
                if existing.scalars().first():
                    raise HTTPException(
                        status_code=400,
                        detail="Username already taken"
                    )
                user.username = request.username
            
            if request.email:
                # Check if email is already taken by another user
                existing = await session.execute(
                    select(User).where(
                        User.email == request.email,
                        User.id != user.id
                    )
                )
                if existing.scalars().first():
                    raise HTTPException(
                        status_code=400,
                        detail="Email already registered"
                    )
                user.email = request.email
            
            if request.full_name is not None:
                user.full_name = request.full_name
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"✅ Profile updated for user: {user.username}")
            return _user_to_profile(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile"
        )


@router.post("/auth/change-password", response_model=ChangePasswordResponse, tags=["Authentication"])
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChangePasswordResponse:
    """
    Change the current user's password.
    
    This endpoint requires authentication via API key or session.
    """
    # Validate password length
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters long"
        )
    
    if not database_service.is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
    
    try:
        async for session in database_service.get_session():
            # Get first admin user as default (for development)
            user_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN).limit(1)
            )
            user = user_result.scalars().first()
            
            if not user:
                # If no admin, get any user
                user_result = await session.execute(select(User).limit(1))
                user = user_result.scalars().first()
            
            if not user:
                # Return error when no users exist
                logger.warning("No users found in database, cannot change password")
                raise HTTPException(
                    status_code=404,
                    detail="User not found - please initialize the database first"
                )
            
            # Verify current password
            if not verify_password(request.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=401,
                    detail="Current password is incorrect"
                )
            
            # Update password
            new_hashed_pwd = hash_password(request.new_password)
            
            # Validate the hash is properly formatted (accept bcrypt or fallback format)
            if not new_hashed_pwd or (not new_hashed_pwd.startswith('$2') and not new_hashed_pwd.startswith('fallback$')):
                logger.error(f"❌ Invalid password hash generated for password change")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update password. Please try again."
                )
            
            user.hashed_password = new_hashed_pwd
            await session.commit()
            
            logger.info(f"✅ Password changed for user: {user.username}")
            
            return ChangePasswordResponse(
                success=True,
                message="Password changed successfully"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error changing password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to change password"
        )


@router.post("/auth/profile/avatar", response_model=ProfileResponse, tags=["Authentication"])
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProfileResponse:
    """Upload a profile avatar image. Accepts JPEG, PNG, GIF, or WebP (max 5MB)."""
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File must be JPEG, PNG, GIF, or WebP")

    # Validate file size (5MB max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 5MB")

    if not database_service.is_database_available():
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    try:
        import tempfile
        from app.services.s3.s3 import s3_service

        # Save to temp file for S3 upload
        ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Upload to S3
        async for session in database_service.get_session():
            user_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN).limit(1)
            )
            user = user_result.scalars().first()
            if not user:
                user_result = await session.execute(select(User).limit(1))
                user = user_result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            object_name = f"avatars/user_{user.id}.{ext}"
            avatar_url = await s3_service.upload_file(
                file_path=tmp_path,
                object_name=object_name,
                content_type=file.content_type,
                public=True,
            )

            # Clean up temp file
            import os
            os.unlink(tmp_path)

            # Update user record
            user.avatar_url = avatar_url
            await session.commit()
            await session.refresh(user)

            logger.info(f"✅ Avatar uploaded for user: {user.username}")
            return _user_to_profile(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")