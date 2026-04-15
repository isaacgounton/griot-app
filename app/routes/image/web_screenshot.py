"""
Routes for webpage screenshot capture using Playwright.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Any
import uuid

from app.models import JobType
from app.services.job_queue import job_queue
from app.services.web_screenshot import (
    web_screenshot_service, ScreenshotRequest, ScreenshotFormat,
    DeviceType, process_web_screenshot_job
)
from app.utils.logging import get_logger
from app.utils.auth import get_current_user

logger = get_logger(module="web_screenshot", component="routes")

router = APIRouter(prefix="/web_screenshot", tags=["Images"])

# Pydantic models for API requests/responses
class CookieModel(BaseModel):
    name: str
    value: str
    domain: str | None = None
    path: str | None = "/"
    expires: float | None = None
    http_only: bool | None = False
    secure: bool | None = False
    same_site: str | None = None

class ScreenshotRequestModel(BaseModel):
    url: str = Field(..., description="URL to capture screenshot of")
    width: int | None = Field(None, ge=100, le=4000, description="Custom viewport width (pixels)")
    height: int | None = Field(None, ge=100, le=4000, description="Custom viewport height (pixels)")
    device_type: DeviceType = Field(DeviceType.DESKTOP, description="Device type for emulation")
    format: ScreenshotFormat = Field(ScreenshotFormat.PNG, description="Screenshot format")
    quality: int | None = Field(None, ge=1, le=100, description="JPEG quality (1-100)")
    wait_for_selector: str | None = Field(None, description="CSS selector to wait for")
    wait_time: int = Field(3000, ge=0, le=30000, description="Wait time in milliseconds")
    full_page: bool = Field(False, description="Capture full page or viewport")
    selector: str | None = Field(None, description="CSS selector for element screenshot")
    cookies: list[CookieModel] | None = Field(None, description="Cookies to set")
    headers: dict[str, str] | None = Field(None, description="Custom headers")
    html_inject: str | None = Field(None, description="HTML to inject into page")
    css_inject: str | None = Field(None, description="CSS to inject into page")
    js_inject: str | None = Field(None, description="JavaScript to inject into page")
    color_scheme: str | None = Field(None, pattern="^(light|dark|no-preference)$", description="Color scheme preference")
    media_type: str | None = Field(None, pattern="^(screen|print)$", description="Media type emulation")
    ignore_https_errors: bool = Field(True, description="Ignore HTTPS certificate errors")
    timeout: int = Field(30000, ge=1000, le=120000, description="Request timeout in milliseconds")
    sync: bool = Field(default=False, description="If True, return response immediately.")

    @field_validator('quality')
    def validate_quality_for_jpeg(cls, v, info):
        # If quality is provided but format is not JPEG, ignore the quality value
        if v is not None and info.data.get('format') != ScreenshotFormat.JPEG:
            return None  # Ignore quality for non-JPEG formats instead of raising error
        return v

    def to_service_request(self) -> ScreenshotRequest:
        """Convert API model to service request."""
        cookies_dict = None
        if self.cookies:
            cookies_dict = [
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "expires": cookie.expires,
                    "httpOnly": cookie.http_only,
                    "secure": cookie.secure,
                    "sameSite": cookie.same_site
                }
                for cookie in self.cookies
            ]

        return ScreenshotRequest(
            url=self.url,
            width=self.width,
            height=self.height,
            device_type=self.device_type,
            format=self.format,
            quality=self.quality,
            wait_for_selector=self.wait_for_selector,
            wait_time=self.wait_time,
            full_page=self.full_page,
            selector=self.selector,
            cookies=cookies_dict,
            headers=self.headers,
            html_inject=self.html_inject,
            css_inject=self.css_inject,
            js_inject=self.js_inject,
            color_scheme=self.color_scheme,
            media_type=self.media_type,
            ignore_https_errors=self.ignore_https_errors,
            timeout=self.timeout
        )

class ScreenshotResponse(BaseModel):
    success: bool
    screenshot_url: str | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float | None = None

class DeviceInfoModel(BaseModel):
    type: str
    name: str
    viewport: dict[str, int]
    user_agent: str
    device_scale_factor: float
    is_mobile: bool
    has_touch: bool

@router.post("/capture", response_model=dict[str, str])
async def capture_webpage_screenshot(
    request: ScreenshotRequestModel,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Capture a webpage screenshot with device emulation, content injection, and custom wait conditions."""
    try:
        if request.sync:
            # Process synchronously
            logger.info(f"Capturing synchronous screenshot of: {request.url}")
            service_request = request.to_service_request()
            result = await web_screenshot_service.take_screenshot(service_request)

            if result.success:
                return {
                    "success": True,
                    "screenshot_url": result.screenshot_url,
                    "metadata": result.metadata,
                    "execution_time": result.execution_time,
                    "message": "Screenshot captured successfully"
                }
            else:
                raise HTTPException(status_code=500, detail=result.error)

        else:
            # Create async job
            job_id = str(uuid.uuid4())

            # Convert request to service format
            service_request = request.to_service_request()
            request_data = service_request.__dict__

            # Add job to queue
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.WEB_SCREENSHOT,
                process_func=process_web_screenshot_job,
                data=request_data
            )

            logger.info(f"Async webpage screenshot job created: {job_id}")
            return {
                "job_id": job_id,
                "message": "Screenshot job started. Use /api/v1/jobs/{job_id}/status to check progress.",
                "status_endpoint": f"/api/v1/jobs/{job_id}/status"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        raise HTTPException(status_code=500, detail=f"Screenshot capture failed: {str(e)}")


@router.get("/devices", response_model=list[DeviceInfoModel])
async def get_available_devices():
    """List available device configurations for screenshot emulation."""
    try:
        devices = web_screenshot_service.get_device_info()
        return [DeviceInfoModel(**device) for device in devices]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get device info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device info: {str(e)}")

@router.post("/capture/element", response_model=dict[str, str])
async def capture_element_screenshot(
    url: str = Query(..., description="URL of the page"),
    selector: str = Query(..., description="CSS selector of the element to capture"),
    device_type: DeviceType = Query(DeviceType.DESKTOP, description="Device type for emulation"),
    format: ScreenshotFormat = Query(ScreenshotFormat.PNG, description="Screenshot format"),
    quality: int | None = Query(None, ge=1, le=100, description="JPEG quality (1-100)"),
    wait_time: int = Query(3000, ge=0, le=30000, description="Wait time in milliseconds")
):
    """Capture a screenshot of a specific page element by CSS selector."""
    try:
        logger.info(f"Capturing element screenshot: {url} -> {selector}")

        service_request = ScreenshotRequest(
            url=url,
            selector=selector,
            device_type=device_type,
            format=format,
            quality=quality,
            wait_time=wait_time
        )

        result = await web_screenshot_service.take_screenshot(service_request)

        if result.success:
            return {
                "success": True,
                "screenshot_url": result.screenshot_url,
                "metadata": result.metadata,
                "execution_time": result.execution_time,
                "message": "Element screenshot captured successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Element screenshot capture failed: {e}")
        raise HTTPException(status_code=500, detail=f"Element screenshot capture failed: {str(e)}")

@router.post("/capture/fullpage", response_model=dict[str, str])
async def capture_full_page_screenshot(
    url: str = Query(..., description="URL of the page"),
    device_type: DeviceType = Query(DeviceType.DESKTOP, description="Device type for emulation"),
    format: ScreenshotFormat = Query(ScreenshotFormat.PNG, description="Screenshot format"),
    quality: int | None = Query(None, ge=1, le=100, description="JPEG quality (1-100)"),
    wait_time: int = Query(3000, ge=0, le=30000, description="Wait time in milliseconds")
):
    """Capture a full scrollable page screenshot."""
    try:
        logger.info(f"Capturing full page screenshot: {url}")

        service_request = ScreenshotRequest(
            url=url,
            device_type=device_type,
            format=format,
            quality=quality,
            wait_time=wait_time,
            full_page=True
        )

        result = await web_screenshot_service.take_screenshot(service_request)

        if result.success:
            return {
                "success": True,
                "screenshot_url": result.screenshot_url,
                "metadata": result.metadata,
                "execution_time": result.execution_time,
                "message": "Full page screenshot captured successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full page screenshot capture failed: {e}")
        raise HTTPException(status_code=500, detail=f"Full page screenshot capture failed: {str(e)}")