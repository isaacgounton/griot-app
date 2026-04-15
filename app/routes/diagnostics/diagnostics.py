"""
Diagnostic endpoints to check API configuration and service availability.
"""
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.utils.auth import get_current_user

router = APIRouter(prefix="/diagnostics", tags=["System"])

class APIKeyStatus(BaseModel):
    """Status of an API key configuration."""
    configured: bool
    length: int
    preview: Optional[str]

class ServiceStatus(BaseModel):
    """Status of a service configuration."""
    configured: bool
    value: Optional[str]

class DiagnosticsResponse(BaseModel):
    """Complete diagnostics response."""
    ai_services: Dict[str, Any]
    news_research: Dict[str, Any]
    video_services: Dict[str, Any]
    storage: Dict[str, Any]
    recommendations: Dict[str, Any]


@router.get("/api-keys", response_model=DiagnosticsResponse)
async def check_api_keys(_: Dict[str, Any] = Depends(get_current_user)):
    """
    Check which API keys are configured.
    
    Returns the status of all required API keys without exposing the actual keys.
    Useful for debugging service failures.
    """
    def key_status(key_name: str) -> dict:
        """Check if an API key is configured."""
        value = os.getenv(key_name)
        if value:
            return {
                "configured": True,
                "length": len(value),
                "preview": f"{value[:4]}..." if len(value) > 4 else "***"
            }
        return {"configured": False, "length": 0, "preview": None}
    
    return {
        "ai_services": {
            "openai": key_status("OPENAI_API_KEY"),
            "openai_alt": key_status("OPENAI_KEY"),
            "groq": key_status("GROQ_API_KEY"),
            "openai_base_url": {
                "configured": bool(os.getenv("OPENAI_BASE_URL")),
                "value": os.getenv("OPENAI_BASE_URL") or None
            }
        },
        "news_research": {
            "google_search_api": key_status("GOOGLE_SEARCH_API_KEY"),
            "google_search_engine_id": key_status("GOOGLE_SEARCH_ENGINE_ID"),
            "perplexity": key_status("PERPLEXITY_API_KEY")
        },
        "video_services": {
            "pexels": key_status("PEXELS_API_KEY"),
            "pexels_alt": key_status("PEXELS_KEY"),
            "together_ai": key_status("TOGETHER_API_KEY")
        },
        "storage": {
            "s3_access_key": key_status("S3_ACCESS_KEY"),
            "s3_secret_key": key_status("S3_SECRET_KEY"),
            "s3_bucket": {
                "configured": bool(os.getenv("S3_BUCKET_NAME")),
                "value": os.getenv("S3_BUCKET_NAME")
            },
            "s3_region": {
                "configured": bool(os.getenv("S3_REGION")),
                "value": os.getenv("S3_REGION")
            }
        },
        "recommendations": {
            "script_generation": _get_script_generation_recommendation(),
            "news_research": _get_news_research_recommendation(),
            "video_search": _get_video_search_recommendation()
        }
    }


def _get_script_generation_recommendation() -> dict:
    """Get recommendation for script generation setup."""
    openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    if openai_key or groq_key:
        return {
            "status": "configured",
            "message": "Script generation should work"
        }
    
    return {
        "status": "missing",
        "message": "Set OPENAI_API_KEY or GROQ_API_KEY to enable script generation",
        "options": [
            "OPENAI_API_KEY - For OpenAI GPT models",
            "GROQ_API_KEY - For Groq/Llama models (faster, free tier available)"
        ]
    }


def _get_news_research_recommendation() -> dict:
    """Get recommendation for news research setup."""
    google_keys = os.getenv('GOOGLE_SEARCH_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    perplexity_key = os.getenv('PERPLEXITY_API_KEY')
    
    if google_keys or perplexity_key:
        return {
            "status": "configured", 
            "message": "News research should work"
        }
    
    return {
        "status": "missing",
        "message": "Set Google Search or Perplexity API keys to enable news research",
        "options": [
            "GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_ENGINE_ID - For Google Custom Search",
            "PERPLEXITY_API_KEY - For Perplexity AI research"
        ]
    }


def _get_video_search_recommendation() -> dict:
    """Get recommendation for video search setup."""
    pexels_key = os.getenv('PEXELS_API_KEY') or os.getenv('PEXELS_KEY')
    
    if pexels_key:
        return {
            "status": "configured",
            "message": "Video search should work"
        }
    
    return {
        "status": "missing", 
        "message": "Set PEXELS_API_KEY to enable stock video search",
        "options": [
            "PEXELS_API_KEY - Free API key from pexels.com"
        ]
    }


async def _check_database_health() -> dict:
    """Check database connectivity and job persistence."""
    try:
        from app.database import database_service
        from sqlalchemy import text
        
        if not database_service.engine:
            return {
                "status": "down",
                "message": "Database not initialized",
                "details": "Database engine is None"
            }
        
        # Test basic connectivity
        async for session in database_service.get_session():
            try:
                # Test connection
                result = await session.execute(text("SELECT 1"))
                row = result.fetchone()
                
                # Test job table exists and is accessible
                result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
                job_count = result.scalar()
                
                return {
                    "status": "healthy",
                    "message": f"Database connected, {job_count} jobs in system",
                    "job_count": job_count
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Database query failed: {str(e)}",
                    "details": "Connection works but queries fail"
                }
                
    except Exception as e:
        return {
            "status": "down",
            "message": f"Database connection failed: {str(e)}",
            "details": "Cannot connect to database"
        }


@router.get("/service-health")
async def check_service_health(_: Dict[str, Any] = Depends(get_current_user)):
    """
    Check the health of all AI services and database connectivity.
    
    Returns the operational status of each service and any configuration issues.
    """
    health = {
        "database": await _check_database_health(),
        "script_generation": _check_script_generation_health(),
        "news_research": _check_news_research_health(),
        "video_search": _check_video_search_health(),
        "overall_status": "unknown"
    }
    
    # Determine overall status
    statuses = [service["status"] for service in health.values() if isinstance(service, dict) and "status" in service]
    if all(s == "healthy" for s in statuses):
        health["overall_status"] = "healthy"
    elif any(s == "healthy" for s in statuses):
        health["overall_status"] = "partial"
    else:
        health["overall_status"] = "degraded"
    
    return health


def _check_script_generation_health() -> dict:
    """Check script generation service health."""
    try:
        from app.services.ai.script_generator import script_generator
        
        openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
        groq_key = os.getenv('GROQ_API_KEY')
        
        if not (openai_key or groq_key):
            return {
                "status": "down",
                "message": "No AI API keys configured",
                "details": "Set OPENAI_API_KEY or GROQ_API_KEY"
            }
        
        return {
            "status": "healthy",
            "message": "Script generation is ready",
            "providers": {
                "openai": bool(openai_key),
                "groq": bool(groq_key)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Service initialization failed: {str(e)}"
        }


def _check_news_research_health() -> dict:
    """Check news research service health.""" 
    try:
        from app.services.ai.news_research_service import NewsResearchService
        service = NewsResearchService()
        
        google_configured = service.google_api_key and service.google_search_engine_id
        perplexity_configured = bool(service.perplexity_api_key)
        
        if not (google_configured or perplexity_configured):
            return {
                "status": "down",
                "message": "No news research APIs configured",
                "details": "Set Google Search or Perplexity API keys"
            }
        
        return {
            "status": "healthy",
            "message": "News research is ready",
            "providers": {
                "google_search": google_configured,
                "perplexity": perplexity_configured
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Service initialization failed: {str(e)}"
        }


def _check_video_search_health() -> dict:
    """Check video search service health."""
    try:
        from app.services.ai.pexels_service import pexels_service
        
        if not pexels_service.api_key:
            return {
                "status": "down", 
                "message": "Pexels API key not configured",
                "details": "Set PEXELS_API_KEY"
            }
        
        return {
            "status": "healthy",
            "message": "Video search is ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Service initialization failed: {str(e)}"
        }