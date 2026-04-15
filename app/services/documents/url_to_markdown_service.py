"""
URL to Markdown conversion service.

Fetches any web page and converts it to structured Markdown.
Optionally extracts only the article content (stripping nav, ads, boilerplate).
"""

import logging
import asyncio
from typing import Any

import aiohttp
import trafilatura
from markdownify import markdownify as html_to_md
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class UrlToMarkdownService:
    """Converts web page URLs to clean, structured Markdown."""

    async def convert(
        self,
        url: str,
        use_browser: bool = False,
        article_only: bool = False,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch a web page and convert it to Markdown.

        Args:
            url: The web page URL
            use_browser: Use Browserless for JS-rendered pages
            article_only: If True, extract only article content (strip nav/ads).
                          If False (default), convert the full page.
            include_metadata: Include title, author, date when available

        Returns:
            Dict with markdown content, metadata, and word count
        """
        logger.info("Converting URL to markdown: %s (browser=%s, article_only=%s)", url, use_browser, article_only)

        html = await self._fetch_html(url, use_browser)
        if not html:
            raise ValueError(f"Failed to fetch content from {url}")

        if article_only:
            result = await asyncio.to_thread(
                self._extract_article, html, url, include_metadata
            )
            if not result or not result.get("markdown"):
                raise ValueError(
                    f"Could not extract article content from {url}. "
                    "The page may not contain article content, or try disabling 'article only' mode."
                )
        else:
            result = await asyncio.to_thread(
                self._convert_full_page, html, url, include_metadata
            )
            if not result or not result.get("markdown"):
                raise ValueError(f"Could not convert page content from {url}")

        return result

    # ── Fetching ──────────────────────────────────────────────

    async def _fetch_html(self, url: str, use_browser: bool = False) -> str | None:
        if use_browser:
            return await self._fetch_with_browserless(url)
        return await self._fetch_with_aiohttp(url)

    async def _fetch_with_aiohttp(self, url: str) -> str | None:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.warning("HTTP %d fetching %s", response.status, url)
                        return None
                    return await response.text()
        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)
            return None

    async def _fetch_with_browserless(self, url: str) -> str | None:
        try:
            from app.services.browserless_service import browserless_service

            if not browserless_service.is_available():
                logger.warning("Browserless not available, falling back to aiohttp")
                return await self._fetch_with_aiohttp(url)

            result = await browserless_service.get_page_content(url, timeout=30000)
            if result.success and result.data:
                return result.data if isinstance(result.data, str) else str(result.data)

            logger.warning("Browserless failed for %s: %s", url, result.error)
            return await self._fetch_with_aiohttp(url)
        except Exception as e:
            logger.warning("Browserless error, falling back to aiohttp: %s", e)
            return await self._fetch_with_aiohttp(url)

    # ── Full page conversion ──────────────────────────────────

    def _convert_full_page(
        self, html: str, url: str, include_metadata: bool
    ) -> dict[str, Any]:
        """Convert entire HTML page to structured Markdown via markdownify."""
        soup = BeautifulSoup(html, "lxml")

        # Extract metadata from <head>
        metadata: dict[str, Any] = {}
        if include_metadata:
            metadata = self._extract_html_metadata(soup)

        # Remove script/style/nav noise before converting
        for tag in soup.find_all(["script", "style", "noscript"]):
            tag.decompose()

        # Remove images before conversion (can't use strip + convert together)
        for img in soup.find_all("img"):
            img.decompose()

        markdown = html_to_md(
            str(soup),
            heading_style="ATX",
        )

        # Clean up excessive blank lines
        import re
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

        title = metadata.get("title", "")
        word_count = len(markdown.split())

        return {
            "markdown": markdown,
            "word_count": word_count,
            "source_url": url,
            **metadata,
        }

    def _extract_html_metadata(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract title, author, date, description from HTML meta tags."""
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        def meta_content(name: str) -> str:
            tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
            content = tag.get("content", "") if tag else ""
            return str(content).strip() if content else ""

        return {
            "title": title,
            "author": meta_content("author") or meta_content("article:author"),
            "date": meta_content("date") or meta_content("article:published_time"),
            "description": meta_content("description") or meta_content("og:description"),
            "sitename": meta_content("og:site_name"),
        }

    # ── Article-only extraction ───────────────────────────────

    def _extract_article(
        self, html: str, url: str, include_metadata: bool
    ) -> dict[str, Any] | None:
        """Extract article content only using trafilatura."""
        markdown = trafilatura.extract(
            html,
            url=url,
            output_format="txt",
            include_links=True,
            include_images=False,
            include_tables=True,
        )

        if not markdown:
            return None

        metadata: dict[str, Any] = {}
        if include_metadata:
            meta = trafilatura.bare_extraction(html, url=url)
            if meta:
                metadata = {
                    "title": getattr(meta, "title", "") or "",
                    "author": getattr(meta, "author", "") or "",
                    "date": getattr(meta, "date", "") or "",
                    "description": getattr(meta, "description", "") or "",
                    "sitename": getattr(meta, "sitename", "") or "",
                }

        title = metadata.get("title", "")
        if title and not markdown.startswith(f"# {title}"):
            markdown = f"# {title}\n\n{markdown}"

        word_count = len(markdown.split())

        return {
            "markdown": markdown,
            "word_count": word_count,
            "source_url": url,
            **metadata,
        }


# Singleton
url_to_markdown_service = UrlToMarkdownService()
