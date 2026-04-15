"""
FastAPI application for media generation.
"""
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import asyncio
import logging
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize enhanced logging and hardware optimization
from app.utils.logging import configure_enhanced_logging, get_logger
from app.utils.hardware import apply_hardware_optimizations, get_device_info

# Configure enhanced logging system
configure_enhanced_logging()

# Apply hardware optimizations
apply_hardware_optimizations()

# Get enhanced logger
logger = get_logger(module="main", component="fastapi_app")

# Initialize with minimal logging for production
device_info = get_device_info()
if os.environ.get('DEBUG', 'false').lower() == 'true':
    logger.bind(**device_info).info("Griot initialization")

# Import authentication and middleware
from app.utils.auth import get_api_key, get_current_user
from app.middleware import SecurityMiddleware


# Dynamic route discovery system
from app.utils.route_discovery import register_discovered_routes, get_route_summary

# Import routers that are manually registered (excluded from auto-discovery)
from app.routes.auth.auth import router as auth_router
from app.routes.auth.oauth import router as oauth_router
from app.routes.admin.admin import router as admin_router
from app.routes.admin import admin_jobs_router, admin_users_router
from app.routes.audio import router as audio_router
from app.routes.media import router as media_router
from app.routes.video import router as video_router
from app.routes.pollinations import router as pollinations_router
from app.routes.dashboard.dashboard import router as dashboard_router
from app.routes.dashboard.library import router as library_router
from app.routes.anyllm import router as anyllm_router
from app.routes.jobs import router as jobs_router
from app.routes.chat import sessions_router as chat_sessions_router, completions_router as chat_completions_router
from app.routes.tools.tools import router as tools_router
from app.routes.text.completions import router as text_router
from app.routes.text.article_to_script import router as article_to_script_router
from app.routes.research.news import router as research_news_router
from app.routes.research.web import router as research_web_router
from app.routes.research.image_search import router as research_image_search_router
from app.routes.research.video_search import router as research_video_search_router

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create application
app = FastAPI(
    title="Griot",
    description="API for generating media content without coding",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# Add proxy middleware for HTTPS handling
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to handle X-Forwarded-* headers when behind a proxy."""

    async def dispatch(self, request: Request, call_next):
        # Handle X-Forwarded-Proto header
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            request.scope["scheme"] = forwarded_proto

        # Handle X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP from the comma-separated list
            client_ip = forwarded_for.split(",")[0].strip()
            request.scope["client"] = (client_ip, None)

        # Handle X-Forwarded-Host header
        forwarded_host = request.headers.get("X-Forwarded-Host")
        if forwarded_host:
            request.scope["server"] = (forwarded_host, 80)

        response = await call_next(request)
        return response

# Add proxy headers middleware to handle X-Forwarded-* headers
app.add_middleware(ProxyHeadersMiddleware)

# Add trusted host middleware (allows specific host(s))
# Includes Docker internal names (api, speaches) and Coolify-generated domains
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "api", "speaches", "*"]
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for request validation errors to prevent binary data encoding issues
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without exposing binary data"""
    try:
        # Log the full error for debugging
        logger.error(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        
        # Extract only safe error information
        safe_errors = []
        for error in exc.errors():
            safe_error = {
                "type": error.get("type", "validation_error"),
                "loc": error.get("loc", []),
                "msg": error.get("msg", "Validation error")
            }
            # Don't include input data which might contain binary content
            safe_errors.append(safe_error)
        
        return JSONResponse(
            status_code=422,
            content={"detail": safe_errors}
        )
    except Exception as e:
        # Fallback error response if anything goes wrong
        logger.error(f"Error in validation exception handler: {e}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Request validation failed"}
        )

# Add security middleware
app.add_middleware(SecurityMiddleware)


# Add API key security scheme to OpenAPI documentation
app.openapi_schema = None  # Reset schema to rebuild it
app.swagger_ui_init_oauth = None
app.openapi_tags = [
    # Authentication & Admin
    {"name": "Authentication", "description": "User registration, login, OAuth, and session management"},
    {"name": "Admin", "description": "System administration, user management, and job maintenance"},
    {"name": "Dashboard", "description": "Dashboard statistics and analytics"},
    # Media Creation
    {"name": "Images", "description": "Image generation, editing, enhancement, and screenshots"},
    {"name": "Audio", "description": "Text-to-speech, transcription, and music generation"},
    {"name": "Video", "description": "Video processing, generation, captions, and manipulation"},
    {"name": "Media", "description": "Media download, metadata, search, and format conversion"},
    # AI Services
    {"name": "AI Content", "description": "AI text generation, script writing, and video creation"},
    {"name": "Research", "description": "Web research, news, and stock media search"},
    {"name": "AnyLLM", "description": "Universal LLM provider integration (multi-provider chat)"},
    {"name": "OpenAI Compatibility", "description": "OpenAI-compatible API endpoints"},
    {"name": "Pollinations AI", "description": "Pollinations image generation, vision, TTS, and transcription"},
    # Agents & Chat
    {"name": "Agents", "description": "AI agent management, sessions, knowledge, and voice"},
    {"name": "Chat", "description": "Chat session management and history"},
    # Content Tools
    {"name": "Content Tools", "description": "Simone (video-to-blog), YT Shorts, documents, and speech processing"},
    {"name": "Studio", "description": "Studio project workflows and scene management"},
    # Infrastructure
    {"name": "Storage & Jobs", "description": "Job tracking, content library, and S3 storage"},
    {"name": "System", "description": "FFmpeg, code execution, diagnostics, and integrations"},
]

def custom_openapi():
    if app.openapi_schema:  # Use the cached schema if it exists
        return app.openapi_schema

    # Create the base OpenAPI schema
    openapi_schema = get_openapi(
        title="Griot",
        version="1.0.0",
        description="AI-powered media processing and generation API",
        routes=app.routes,
    )

    # Add tags to the schema
    openapi_schema["tags"] = app.openapi_tags

    # Cache the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Replace FastAPI's default openapi() with our custom one
app.openapi = custom_openapi

# Ensure temporary files directory exists
os.makedirs("temp", exist_ok=True)
os.makedirs("temp/output", exist_ok=True)

# Dynamic route discovery and registration
logger.info("🔍 Starting dynamic route discovery...")
registration_results = register_discovered_routes(app, "app/routes")

# Manual registration for special routers that require custom configuration
logger.info("🔧 Registering special routers with custom configuration...")

# Auth router (no authentication dependency for login/register - these are public endpoints)
app.include_router(auth_router, prefix="/api/v1")

# OAuth router (OAuth login/callback endpoints)
app.include_router(oauth_router, prefix="/api/v1")

# Admin router (no authentication dependency for login pages, but endpoints handle auth internally)
app.include_router(admin_router)

# Routers that need specific prefixes
app.include_router(audio_router, prefix="/api/v1/audio", dependencies=[Depends(get_current_user)])
app.include_router(media_router, prefix="/api/v1/media", dependencies=[Depends(get_current_user)])
app.include_router(video_router, prefix="/api/v1/videos", dependencies=[Depends(get_current_user)])
app.include_router(pollinations_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(dashboard_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(library_router, prefix="/api/v1/library", dependencies=[Depends(get_current_user)])
app.include_router(anyllm_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(jobs_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(chat_sessions_router, prefix="/api/v1/chat", dependencies=[Depends(get_current_user)])
app.include_router(chat_completions_router, prefix="/api/v1/chat", dependencies=[Depends(get_current_user)])
app.include_router(tools_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

# Studio router
try:
    from app.routes.studio import router as studio_router
    app.include_router(studio_router, prefix="/api/v1/studio", dependencies=[Depends(get_current_user)])
    logger.info("✅ Studio router registered at /api/v1/studio")
except Exception as e:
    logger.warning(f"⚠️ Could not register Studio router: {e}")

# Text generation router
app.include_router(text_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(article_to_script_router, prefix="/api/v1/text", dependencies=[Depends(get_current_user)])

# Research routers
app.include_router(research_news_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(research_web_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(research_image_search_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(research_video_search_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])

# Admin sub-routers
app.include_router(admin_jobs_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(admin_users_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])


# Log route registration summary
route_summary = get_route_summary(registration_results)
logger.info(f"\n{route_summary}")
logger.info("✅ Route registration completed successfully!")

# Serve static files for the React frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_path):
    # Mount static assets at /assets for Vite build output
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    # Mount all static files at /static as well (fallback)
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    logger.info(f"Serving React frontend from: {frontend_path}")

    # Serve favicon directly from root
    @app.get("/favicon.svg", include_in_schema=False)
    async def serve_favicon():
        """Serve the favicon from the frontend build directory."""
        favicon_path = os.path.join(frontend_path, "favicon.svg")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return {"error": "Favicon not found"}
    
    # Serve the React app at /dashboard/* and /dashboard (SPA routing)
    @app.get("/dashboard/{path:path}", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    async def serve_dashboard(path: str = ""):
        """Serve the React frontend for the dashboard."""
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built. Run 'cd frontend && npm run build'"}
    
    # Serve frontend routes directly (for direct navigation)
    @app.get("/login", include_in_schema=False)
    @app.get("/register", include_in_schema=False)
    @app.get("/verify-email", include_in_schema=False)
    @app.get("/auth/callback", include_in_schema=False)
    @app.get("/research", include_in_schema=False)
    @app.get("/create", include_in_schema=False)
    @app.get("/video/{video_id}", include_in_schema=False)
    @app.get("/videos", include_in_schema=False)
    @app.get("/library", include_in_schema=False)
    @app.get("/users", include_in_schema=False)
    @app.get("/jobs", include_in_schema=False)
    @app.get("/api-keys", include_in_schema=False)
    @app.get("/settings", include_in_schema=False)
    async def serve_frontend_routes():
        """Serve the React frontend for direct route navigation."""
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built. Run 'cd frontend && npm run build' to build the frontend."}
else:
    logger.warning(f"Frontend not found at {frontend_path}. Run 'cd frontend && npm install && npm run build' to build the frontend.")

# Simple health check endpoint (no authentication required)
@app.get("/health", include_in_schema=False)
async def health_check():
    """Simple health check endpoint for container health monitoring."""
    logger.debug("🏥 Health check endpoint called")
    return {"status": "healthy", "service": "griot"}

# Security monitoring endpoint
@app.get("/security/stats", include_in_schema=False)
@limiter.limit("10/minute")
async def get_security_stats(request: Request, _: str = Depends(get_api_key)):
    """Get current security statistics (requires API key)."""
    # Get middleware instance
    from app.middleware.security import SecurityMiddleware
    instance = SecurityMiddleware.get_instance()
    if instance:
        return instance.get_security_stats()
    return {"error": "Security middleware not found"}


# Serve landing page at root
@app.get("/", include_in_schema=False)
async def serve_landing():
    """Serve the landing page."""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Welcome to Griot",
        "description": "AI-powered media generation and processing API",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "api": "/api",
        "status": "operational",
        "note": "Frontend not built. Run 'cd frontend && npm run build' to build the frontend."
    }


@app.on_event("startup")
async def startup_event():
    """Run startup events."""
    # Initialize database service with comprehensive setup
    from app.database import database_service
    try:
        await database_service.initialize()
        await database_service.create_tables()
        await database_service.update_enums()
        await database_service.migrate_schema()

        # Fix userrole enum if needed (database migration)
        try:
            from sqlalchemy import text
            if database_service.engine is not None:
                async with database_service.engine.begin() as conn:
                    # Check if userrole enum exists and has correct values
                    result = await conn.execute(text("""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
                        ORDER BY enumsortorder;
                    """))
                    current_values = [row[0] for row in result.fetchall()]
                    expected_values = ['admin', 'user', 'viewer']

                    # Check if we have uppercase role values in the data
                    try:
                        result = await conn.execute(text("SELECT DISTINCT role FROM users;"))
                        used_values = [row[0] for row in result.fetchall()]
                        has_uppercase = any(val.upper() in ['ADMIN', 'USER', 'VIEWER'] and val != val.lower() for val in used_values)
                    except Exception:
                        has_uppercase = False

                    if set(current_values) != set(expected_values) or has_uppercase:
                        # Convert role column to text temporarily
                        await conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE text;"))

                        # Fix any uppercase role values
                        await conn.execute(text("UPDATE users SET role = LOWER(role) WHERE role IN ('ADMIN', 'USER', 'VIEWER');"))

                        # Drop and recreate enum
                        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE;"))
                        await conn.execute(text("CREATE TYPE userrole AS ENUM ('admin', 'user', 'viewer');"))

                        # Convert column back to enum
                        await conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole;"))
                    
        except Exception as e:
            logger.warning(f"⚠️ userrole enum fix failed (may not be needed): {e}")
        
        # Load dashboard config overrides into os.environ
        try:
            from app.services.settings import settings_service
            count = await settings_service.load_config_overrides()
            if count:
                logger.info(f"✓ Loaded {count} config overrides from dashboard settings")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load config overrides: {e}")

        # Initialize music files if needed
        try:
            import subprocess
            subprocess.run(["/app/scripts/init-music.sh"], capture_output=True, text=True, check=False)
        except Exception:
            pass  # Music initialization is non-critical
        
        # Create initial admin user if none exists
        try:
            from app.services.settings.user_service import user_service
            from app.services.api_key import api_key_service
            
            users_result = await user_service.list_users(limit=1)
            admin_user = None
            
            if users_result['pagination']['total_count'] == 0:
                # Only create admin user if environment variables are set
                admin_username = os.getenv('ADMIN_USERNAME')
                admin_password = os.getenv('ADMIN_PASSWORD')
                admin_email = os.getenv('ADMIN_EMAIL', 'admin@griot.com')
                
                if admin_username and admin_password:
                    admin_user = await user_service.create_user({
                        'username': admin_username,
                        'email': admin_email,
                        'full_name': 'System Administrator',
                        'password': admin_password,
                        'role': 'admin',
                        'is_active': True,
                        'is_verified': True
                    })
                    logger.info("Admin user created from environment variables")
                else:
                    logger.warning("No admin credentials found in environment variables. Skipping admin user creation.")
            else:
                # Get admin user for API key creation
                admin_user = await user_service.get_user_by_email('admin@griot.com')

                # Fix existing admin users: rehash non-bcrypt passwords and ensure verified
                admin_username = os.getenv('ADMIN_USERNAME')
                admin_password = os.getenv('ADMIN_PASSWORD')
                if admin_user and admin_username and admin_password:
                    from app.utils.security import hash_password as _hash_pw
                    from app.database import User as _User, database_service as _db_svc
                    async for session in _db_svc.get_session():
                        from sqlalchemy import select as _select
                        result = await session.execute(_select(_User).where(_User.id == int(admin_user['id'])))
                        db_user = result.scalar_one_or_none()
                        if db_user:
                            needs_update = False
                            if not db_user.hashed_password.startswith('$2'):
                                db_user.hashed_password = _hash_pw(admin_password)
                                needs_update = True
                                logger.info("Rehashed admin password to bcrypt")
                            if not db_user.is_verified:
                                db_user.is_verified = True
                                needs_update = True
                                logger.info("Marked admin user as verified")
                            if needs_update:
                                await session.commit()
            
            # Create admin API key if none exists for admin user
            if admin_user:
                existing_keys = await api_key_service.list_api_keys(user_id=int(admin_user['id']))
                if not existing_keys['api_keys']:
                    from datetime import datetime, timezone, timedelta
                    await api_key_service.create_api_key({
                        'name': 'Admin API Key',
                        'user_id': admin_user['id'],
                        'rate_limit': 1000,
                        'expires_at': (datetime.now(timezone.utc) + timedelta(days=365)).replace(tzinfo=None),
                        'is_active': True
                    }, requester_info={"user_role": "admin", "user_id": admin_user['id']})
                    
        except Exception as e:
            logger.warning(f"⚠️ User/API key service check failed: {e}")

        # Initialize video service
        try:
            from app.services.video import video_service
            await video_service.get_video_stats()
        except Exception:
            pass  # Video service check is non-critical

    except Exception as e:
        logger.warning(f"⚠️ Database initialization failed during startup: {e}")
        logger.warning("💡 Database will be initialized on first use - this is normal during container startup")
        # Don't crash the application - database will be initialized lazily

    # Start background scheduler service
    try:
        from app.services.settings.scheduler_service import scheduler_service
        await scheduler_service.start()
    except Exception:
        pass  # Non-critical service
    
    # Initialize Redis and job queue
    from app.services.redis import redis_service
    from app.services.job_queue import job_queue
    
    try:
        await redis_service.connect()
        job_queue.set_redis_service(redis_service)
        await job_queue.recover_jobs()
    except Exception:
        pass  # Non-critical services
    
    # Start background persistence flush task for deferred session/message persistence
    try:
        from app.services.agents.agent_service import agent_service
        await agent_service.start_background_persistence_flush()
        logger.info("✓ Background persistence flush task started")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start background persistence flush: {e}")
    
    # Initialize S3 URL cache with persistent database backend
    try:
        from app.services.s3.s3_cache import s3_cache_service
        from app.services.music.music_service import music_service

        async def warm_s3_cache():
            """Background task to warm up S3 URL cache on startup."""
            try:
                cached_count = 0
                for track in music_service.tracks:
                    try:
                        s3_url = await music_service.get_s3_url_for_track(track.file)
                        if s3_url:
                            cached_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to cache {track.file}: {e}")

                logger.info(f"S3 cache warmed: {cached_count}/{len(music_service.tracks)} music tracks")

                expired_count = await s3_cache_service.clear_expired_cache()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired S3 cache entries")

            except Exception as e:
                logger.warning(f"Error warming S3 cache: {e}")

        asyncio.create_task(warm_s3_cache())
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize S3 cache: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown events."""
    # Stop background persistence flush task
    try:
        from app.services.agents.agent_service import agent_service
        await agent_service.stop_background_persistence_flush()
        logger.info("✓ Background persistence flush task stopped")
    except Exception as e:
        logger.warning(f"Error stopping persistence flush: {e}")
    
    # Stop background scheduler service
    try:
        from app.services.settings.scheduler_service import scheduler_service
        await scheduler_service.stop()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")
    
    # Close database service
    from app.database import database_service
    try:
        await database_service.close()
        logger.info("Database service disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting database: {e}")
    
    # Disconnect Redis service
    from app.services.redis import redis_service
    try:
        await redis_service.disconnect()
        logger.info("Redis service disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting Redis: {e}")
    
    # Import job queue service
    from app.services.job_queue import job_queue
    
    # Clean up resources
    for task in job_queue.processing_tasks.values():
        task.cancel()
    
    logger.info("All job processing tasks cancelled")


if __name__ == "__main__":
    import uvicorn
    
    # Use multiple workers to better handle concurrent requests
    # Workers should be 2-4 times the number of CPU cores
    workers = int(os.environ.get("UVICORN_WORKERS", 4))
    
    # In development, use a single worker with reload=True
    if os.environ.get("DEBUG", "False").lower() == "true":
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True
        )
    else:
        # In production, use multiple workers with no reload
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000, 
            workers=workers
        ) 
