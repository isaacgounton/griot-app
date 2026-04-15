"""
Advanced webpage screenshot service using Browserless cloud service.
Supports various screenshot formats, device emulation, and element targeting without local browser installation.
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.models import JobType, JobStatus
from app.services.job_queue import job_queue
from app.services.browserless_service import browserless_service
from app.utils.logging import get_logger

logger = get_logger(module="web_screenshot", component="service")

class ScreenshotFormat(str, Enum):
    """Supported screenshot formats."""
    PNG = "png"
    JPEG = "jpeg"

class DeviceType(str, Enum):
    """Predefined device types for emulation."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    CUSTOM = "custom"

@dataclass
class ViewportSize:
    """Viewport dimensions."""
    width: int
    height: int

@dataclass
class DeviceConfig:
    """Device configuration for emulation."""
    name: str
    viewport: ViewportSize
    user_agent: str
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False

# Predefined device configurations
DEVICES = {
    DeviceType.DESKTOP: DeviceConfig(
        name="Desktop",
        viewport=ViewportSize(width=1920, height=1080),
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    DeviceType.MOBILE: DeviceConfig(
        name="Mobile",
        viewport=ViewportSize(width=375, height=667),
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True
    ),
    DeviceType.TABLET: DeviceConfig(
        name="Tablet",
        viewport=ViewportSize(width=768, height=1024),
        user_agent="Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True
    )
}

@dataclass
class ScreenshotRequest:
    """Request parameters for webpage screenshot."""
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    device_type: DeviceType = DeviceType.DESKTOP
    format: ScreenshotFormat = ScreenshotFormat.PNG
    quality: Optional[int] = None  # For JPEG only (1-100)
    wait_for_selector: Optional[str] = None
    wait_time: int = 3000  # milliseconds
    full_page: bool = False
    selector: Optional[str] = None  # Screenshot specific element
    cookies: Optional[List[Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None
    html_inject: Optional[str] = None
    css_inject: Optional[str] = None
    js_inject: Optional[str] = None
    color_scheme: Optional[str] = None  # "light", "dark", "no-preference"
    media_type: Optional[str] = None  # "screen", "print"
    ignore_https_errors: bool = True
    timeout: int = 30000  # milliseconds

@dataclass
class ScreenshotResult:
    """Result of webpage screenshot operation."""
    success: bool
    screenshot_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class WebScreenshotService:
    """Advanced webpage screenshot service using Browserless cloud API."""

    def __init__(self):
        # Use the comprehensive browserless service
        self.browserless = browserless_service

    def is_available(self) -> bool:
        """Check if Browserless service is configured."""
        return self.browserless.is_available()

    async def take_screenshot(self, request: ScreenshotRequest) -> ScreenshotResult:
        """Take a webpage screenshot using Browserless service."""
        if not self.is_available():
            return ScreenshotResult(
                success=False,
                error="Browserless service not configured. Please set BROWSERLESS_TOKEN environment variable.",
                execution_time=0
            )

        try:
            # Get device configuration
            device_config = DEVICES.get(request.device_type, DEVICES[DeviceType.DESKTOP])

            # Override viewport if custom dimensions provided
            viewport_width = request.width or device_config.viewport.width
            viewport_height = request.height or device_config.viewport.height

            # Log screenshot operation
            if request.selector:
                logger.info(f"🎯 Taking screenshot of element: {request.selector}")
            if request.wait_for_selector:
                logger.info(f"⏳ Waiting for selector: {request.wait_for_selector}")

            logger.info(f"📸 Taking screenshot via Browserless: {request.url}")

            # Delegate to comprehensive browserless service
            result = await self.browserless.screenshot(
                url=request.url,
                full_page=request.full_page,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
                format=request.format.value,
                quality=request.quality,
                selector=request.selector,
                wait_for_selector=request.wait_for_selector,
                wait_time=request.wait_time,
                timeout=request.timeout,
                user_agent=device_config.user_agent,
                device_scale_factor=device_config.device_scale_factor,
                is_mobile=device_config.is_mobile,
                has_touch=device_config.has_touch,
                cookies=request.cookies,
                headers=request.headers,
                css_inject=request.css_inject,
                js_inject=request.js_inject,
                color_scheme=request.color_scheme,
                media_type=request.media_type
            )

            # Convert BrowserlessResult to ScreenshotResult
            if result.success:
                # Enhance metadata with device info and screenshot ID
                enhanced_metadata = {
                    **result.metadata,
                    "device_type": request.device_type.value,
                    "screenshot_id": result.file_url.split('/')[-1].replace(f'.{request.format.value}', '').replace('screenshot_', ''),
                    "service": "browserless"
                }

                logger.info(f"✅ Screenshot captured successfully in {result.execution_time:.2f}s")

                return ScreenshotResult(
                    success=True,
                    screenshot_url=result.file_url,
                    metadata=enhanced_metadata,
                    execution_time=result.execution_time
                )
            else:
                logger.error(f"❌ Screenshot failed: {result.error}")
                return ScreenshotResult(
                    success=False,
                    error=result.error,
                    execution_time=result.execution_time
                )

        except asyncio.TimeoutError:
            error_msg = "Screenshot timeout"
            logger.error(f"❌ {error_msg}")
            return ScreenshotResult(
                success=False,
                error=error_msg,
                execution_time=0
            )

        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return ScreenshotResult(
                success=False,
                error=error_msg,
                execution_time=0
            )

    def get_device_info(self) -> List[Dict[str, Any]]:
        """Get information about available device configurations."""
        return [
            {
                "type": device_type.value,
                "name": config.name,
                "viewport": {
                    "width": config.viewport.width,
                    "height": config.viewport.height
                },
                "user_agent": config.user_agent,
                "device_scale_factor": config.device_scale_factor,
                "is_mobile": config.is_mobile,
                "has_touch": config.has_touch
            }
            for device_type, config in DEVICES.items()
        ]

# Global service instance
web_screenshot_service = WebScreenshotService()

# Job queue wrapper function
async def process_web_screenshot_job(_job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a web screenshot job through the job queue."""
    try:
        request = ScreenshotRequest(**data)
        result = await web_screenshot_service.take_screenshot(request)

        if result.success:
            return {
                "success": True,
                "screenshot_url": result.screenshot_url,
                "file_url": result.screenshot_url,  # For media library compatibility
                "image_url": result.screenshot_url,  # For media library compatibility
                "metadata": result.metadata,
                "execution_time": result.execution_time
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "execution_time": result.execution_time
            }

    except Exception as e:
        logger.error(f"❌ Web screenshot job processing failed: {e}")
        return {
            "success": False,
            "error": f"Job processing failed: {str(e)}"
        }
