"""Zyte proxy & web scraping tool for global patent search and research portals."""

import os
import re
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel, Field

from ai.config import get_ai_settings
from ai.shared.errors import MissingAPIKeyError, StartupOSAIError
from ai.shared.logger import ai_logger


class ScrapeResult(BaseModel):
    """Container for scraped web content."""

    url: str = Field(description="Target scraped URL.")
    status_code: int = Field(default=200, description="HTTP status code from target page.")
    clean_text: str = Field(description="Extracted clean text content from HTML.")
    html_content: Optional[str] = Field(default=None, description="Raw HTML response content.")


def strip_html_tags(html: str) -> str:
    """Strip HTML tags and convert script/style content to readable text."""
    # Remove script and style blocks
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class ZyteScraperTool:
    """Production-grade Zyte API client for proxy rendering & web scraping."""

    API_URL = "https://api.zyte.com/v1/extract"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0) -> None:
        """Initialize Zyte Scraper tool."""
        settings = get_ai_settings()
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.zyte_api_key or os.getenv("ZYTE_API_KEY", "")
        self.timeout = timeout

    def scrape_url(
        self,
        url: str,
        http_response_body: bool = True,
        browser_html: bool = False,
        mock_mode: bool = False,
    ) -> ScrapeResult:
        """Scrape webpage content via Zyte API using proxy rendering.

        Args:
            url: Target webpage URL (e.g. patent portal or research site).
            http_response_body: Extract standard HTTP body response.
            browser_html: Render JS using headless browser rendering if needed.
            mock_mode: If True, returns mock scrape content for testing without live API keys.

        Returns:
            ScrapeResult containing extracted clean text.
        """
        if mock_mode:
            ai_logger.info(f"[MOCK] Zyte scrape executed for URL: {url}")
            return ScrapeResult(
                url=url,
                status_code=200,
                clean_text=f"Mock patent document and research details extracted from {url}.",
                html_content=f"<html><body><h1>Patent Details</h1><p>Content for {url}</p></body></html>",
            )

        if not self.api_key:
            raise MissingAPIKeyError(key_name="ZYTE_API_KEY", provider_name="Zyte")

        payload: Dict[str, Any] = {"url": url}
        if browser_html:
            payload["browserHtml"] = True
        else:
            payload["httpResponseBody"] = True

        ai_logger.info(f"Scraping URL via Zyte: {url} (browserHtml={browser_html})")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.API_URL,
                    json=payload,
                    auth=(self.api_key, ""),
                )
                response.raise_for_status()
                data = response.json()

            raw_html = ""
            if "browserHtml" in data:
                raw_html = data["browserHtml"]
            elif "httpResponseBody" in data:
                import base64
                raw_html = base64.b64decode(data["httpResponseBody"]).decode("utf-8", errors="replace")

            clean_text = strip_html_tags(raw_html)

            return ScrapeResult(
                url=url,
                status_code=200,
                clean_text=clean_text,
                html_content=raw_html,
            )

        except httpx.HTTPStatusError as err:
            ai_logger.error(f"Zyte HTTP error ({err.response.status_code}): {err.response.text}")
            raise StartupOSAIError(
                f"Zyte scrape failed with status code {err.response.status_code}",
                details={"status_code": err.response.status_code, "url": url},
            ) from err
        except Exception as err:
            ai_logger.error(f"Zyte scrape failed: {str(err)}")
            raise StartupOSAIError(
                f"Zyte scrape failed: {str(err)}",
                details={"url": url, "error": str(err)},
            ) from err
