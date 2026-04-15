"""
Comprehensive Browserless automation service.

Provides cloud-based browser automation for:
- Screenshots (web pages, elements)
- PDF generation
- Web scraping
- Page content extraction
- Form automation
- Performance monitoring
- SEO audits
"""
import os
import uuid
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
import aiofiles

from app.services.s3 import s3_service
from app.utils.logging import get_logger

logger = get_logger(module="browserless", component="service")


class BrowserlessFeature(str, Enum):
    """Available Browserless features."""
    SCREENSHOT = "screenshot"
    PDF = "pdf"
    CONTENT = "content"
    SCRAPE = "scrape"
    FUNCTION = "function"
    PERFORMANCE = "performance"
    STATS = "stats"


@dataclass
class BrowserlessResult:
    """Result from Browserless operation."""
    success: bool
    data: Optional[Any] = None
    file_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class BrowserlessService:
    """Comprehensive Browserless automation service."""

    def __init__(self):
        self.base_url = os.getenv('BROWSERLESS_BASE_URL', 'https://chrome.browserless.io')
        self.token = os.getenv('BROWSERLESS_TOKEN', '')

        if not self.token:
            logger.warning("⚠️  BROWSERLESS_TOKEN not set. Browserless features will be unavailable.")
        else:
            logger.info(f"✅ Browserless service configured: {self.base_url}")

    def is_available(self) -> bool:
        """Check if Browserless service is configured."""
        return bool(self.token)

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        binary_response: bool = False,
        text_response: bool = False,
        timeout: int = 30000
    ) -> Any:
        """Make request to Browserless API."""
        url = f"{self.base_url}/{endpoint}"

        headers = {"Content-Type": "application/json"}
        params = {"token": self.token}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout / 1000 + 10)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Browserless API error ({response.status}): {error_text}")

                if binary_response:
                    return await response.read()
                elif text_response:
                    return await response.text()
                else:
                    return await response.json()

    # ==================== SCREENSHOT ====================

    async def screenshot(
        self,
        url: str,
        full_page: bool = False,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        format: str = "png",
        quality: Optional[int] = None,
        selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        wait_time: int = 0,
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        device_scale_factor: float = 1.0,
        is_mobile: bool = False,
        has_touch: bool = False,
        cookies: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        css_inject: Optional[str] = None,
        js_inject: Optional[str] = None,
        color_scheme: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> BrowserlessResult:
        """
        Take a screenshot of a webpage with advanced options.

        Args:
            url: Target URL
            full_page: Capture full scrollable page
            viewport_width: Browser width
            viewport_height: Browser height
            format: 'png' or 'jpeg'
            quality: JPEG quality (1-100)
            selector: CSS selector to screenshot specific element
            wait_for_selector: Wait for this selector before screenshot
            wait_time: Additional wait time in ms
            timeout: Request timeout in ms
            user_agent: Custom user agent string
            device_scale_factor: Device pixel ratio
            is_mobile: Enable mobile viewport
            has_touch: Enable touch events
            cookies: Custom cookies to set
            headers: Custom HTTP headers
            css_inject: CSS to inject into page
            js_inject: JavaScript to inject into page
            color_scheme: Color scheme preference ('light', 'dark', 'no-preference')
            media_type: Media type emulation ('screen', 'print')
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "url": url,
                "options": {
                    "type": format,
                    "fullPage": full_page,
                },
                "viewport": {
                    "width": viewport_width,
                    "height": viewport_height,
                    "deviceScaleFactor": device_scale_factor,
                    "isMobile": is_mobile,
                    "hasTouch": has_touch
                },
                "gotoOptions": {
                    "timeout": timeout,
                    "waitUntil": "networkidle2"
                }
            }

            # Add quality for JPEG
            if quality and format == "jpeg":
                payload["options"]["quality"] = quality

            # Add selector if specified
            if selector:
                payload["selector"] = selector

            # Add wait for selector if specified
            if wait_for_selector:
                payload["waitForSelector"] = wait_for_selector

            # Add wait time if specified (in milliseconds)
            if wait_time > 0:
                payload["waitForTimeout"] = wait_time

            # Add custom cookies
            if cookies:
                payload["cookies"] = cookies

            # Add custom headers and user agent
            if headers or user_agent:
                extra_headers = headers.copy() if headers else {}
                if user_agent:
                    extra_headers["User-Agent"] = user_agent
                payload["setExtraHTTPHeaders"] = extra_headers

            # Add content injection
            if css_inject or js_inject:
                if js_inject:
                    payload["addScriptTag"] = [{"content": js_inject}]
                if css_inject:
                    payload["addStyleTag"] = [{"content": css_inject}]

            # Add emulation settings
            if color_scheme:
                payload["emulateMediaFeatures"] = [{
                    "name": "prefers-color-scheme",
                    "value": color_scheme
                }]

            if media_type:
                payload["emulateMediaType"] = media_type

            screenshot_bytes = await self._make_request(
                "screenshot",
                payload,
                binary_response=True,
                timeout=timeout
            )

            # Save to S3
            screenshot_id = str(uuid.uuid4())
            filename = f"screenshot_{screenshot_id}.{format}"
            temp_path = os.path.join(tempfile.gettempdir(), filename)

            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(screenshot_bytes)

            s3_key = f"browserless/screenshots/{filename}"
            file_url = await s3_service.upload_file(temp_path, s3_key)

            os.remove(temp_path)

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                file_url=file_url,
                metadata={
                    "url": url,
                    "format": format,
                    "full_page": full_page,
                    "viewport": {
                        "width": viewport_width,
                        "height": viewport_height
                    },
                    "file_size": len(screenshot_bytes),
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== PDF GENERATION ====================

    async def generate_pdf(
        self,
        url: str,
        format: str = "A4",
        print_background: bool = True,
        landscape: bool = False,
        margin_top: str = "0",
        margin_bottom: str = "0",
        margin_left: str = "0",
        margin_right: str = "0",
        header_template: Optional[str] = None,
        footer_template: Optional[str] = None,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Generate PDF from webpage.

        Args:
            url: Target URL
            format: Paper format (A4, Letter, Legal, etc.)
            print_background: Include background graphics
            landscape: Landscape orientation
            margin_*: Page margins
            header_template: HTML template for header
            footer_template: HTML template for footer
            timeout: Request timeout in ms
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "url": url,
                "options": {
                    "format": format,
                    "printBackground": print_background,
                    "landscape": landscape,
                    "margin": {
                        "top": margin_top,
                        "bottom": margin_bottom,
                        "left": margin_left,
                        "right": margin_right
                    }
                },
                "gotoOptions": {
                    "timeout": timeout,
                    "waitUntil": "networkidle2"
                }
            }

            if header_template:
                payload["options"]["headerTemplate"] = header_template

            if footer_template:
                payload["options"]["footerTemplate"] = footer_template

            pdf_bytes = await self._make_request(
                "pdf",
                payload,
                binary_response=True,
                timeout=timeout
            )

            # Save to S3
            pdf_id = str(uuid.uuid4())
            filename = f"pdf_{pdf_id}.pdf"
            temp_path = os.path.join(tempfile.gettempdir(), filename)

            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(pdf_bytes)

            s3_key = f"browserless/pdfs/{filename}"
            file_url = await s3_service.upload_file(temp_path, s3_key)

            os.remove(temp_path)

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                file_url=file_url,
                metadata={
                    "url": url,
                    "format": format,
                    "file_size": len(pdf_bytes),
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== WEB SCRAPING ====================

    async def scrape_content(
        self,
        url: str,
        elements: Optional[List[Dict[str, str]]] = None,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Scrape content from webpage.

        Args:
            url: Target URL
            elements: List of elements to scrape
                      [{"selector": "h1", "attribute": "textContent"}]
            wait_for_selector: Wait for this selector
            timeout: Request timeout in ms
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "url": url,
                "gotoOptions": {
                    "timeout": timeout,
                    "waitUntil": "networkidle2"
                }
            }

            if wait_for_selector:
                payload["waitForSelector"] = wait_for_selector

            if elements:
                payload["elements"] = elements

            result = await self._make_request(
                "scrape",
                payload,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                data=result,
                metadata={
                    "url": url,
                    "elements_count": len(elements) if elements else 0,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== PAGE CONTENT ====================

    async def get_page_content(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Get full page HTML content.

        Args:
            url: Target URL
            wait_for_selector: Wait for this selector
            timeout: Request timeout in ms
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "url": url,
                "gotoOptions": {
                    "timeout": timeout,
                    "waitUntil": "networkidle2"
                }
            }

            if wait_for_selector:
                payload["waitForSelector"] = wait_for_selector

            result = await self._make_request(
                "content",
                payload,
                text_response=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                data=result,
                metadata={
                    "url": url,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== PERFORMANCE MONITORING ====================

    async def get_performance_metrics(
        self,
        url: str,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Get page performance metrics.

        Args:
            url: Target URL
            timeout: Request timeout in ms

        Returns:
            Performance metrics including:
            - Page load time
            - Time to first byte
            - DOM content loaded
            - Network requests
            - Resource sizes
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "url": url,
                "gotoOptions": {
                    "timeout": timeout,
                    "waitUntil": "networkidle2"
                }
            }

            result = await self._make_request(
                "performance",
                payload,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                data=result,
                metadata={
                    "url": url,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== CUSTOM AUTOMATION ====================

    async def execute_function(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Execute custom JavaScript in browser context.

        Args:
            code: JavaScript code to execute
            context: Variables to pass to the function
            timeout: Request timeout in ms

        Example:
            code = '''
            async ({ page }) => {
                await page.goto('https://example.com');
                const title = await page.title();
                return { title };
            }
            '''
        """
        import time
        start_time = time.time()

        try:
            payload = {
                "code": code,
                "context": context or {}
            }

            result = await self._make_request(
                "function",
                payload,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return BrowserlessResult(
                success=True,
                data=result,
                metadata={
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ==================== SERVICE HEALTH ====================

    async def get_stats(self) -> BrowserlessResult:
        """Get Browserless service statistics and health."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/stats",
                    params={"token": self.token}
                ) as response:
                    if response.status == 200:
                        stats = await response.json()
                        return BrowserlessResult(
                            success=True,
                            data=stats
                        )
                    else:
                        return BrowserlessResult(
                            success=False,
                            error=f"Stats endpoint returned {response.status}"
                        )
        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e)
            )

    # ==================== FORM AUTOMATION ====================

    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit_selector: Optional[str] = None,
        wait_after_submit: int = 3000,
        timeout: int = 30000
    ) -> BrowserlessResult:
        """
        Fill and submit a form.

        Args:
            url: Target URL
            form_data: {"selector": "value"} mapping
            submit_selector: CSS selector for submit button
            wait_after_submit: Wait time after submission (ms)
            timeout: Request timeout in ms
        """
        import time
        start_time = time.time()

        try:
            # Build automation code
            form_fills = "\n".join([
                f"await page.fill('{selector}', `{value}`);"
                for selector, value in form_data.items()
            ])

            submit_code = ""
            if submit_selector:
                submit_code = f"""
                await page.click('{submit_selector}');
                await page.waitForTimeout({wait_after_submit});
                """

            code = f"""
            async ({{ page }}) => {{
                await page.goto('{url}', {{ waitUntil: 'networkidle2' }});
                {form_fills}
                {submit_code}
                const content = await page.content();
                const url = page.url();
                return {{ content, url }};
            }}
            """

            result = await self.execute_function(code, timeout=timeout)
            result.metadata = {
                "url": url,
                "form_fields": len(form_data),
                "execution_time": time.time() - start_time
            }

            return result

        except Exception as e:
            return BrowserlessResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


# Global service instance
browserless_service = BrowserlessService()
