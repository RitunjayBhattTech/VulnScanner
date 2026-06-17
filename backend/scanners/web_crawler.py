"""
Lightweight web crawler using httpx (no Playwright dependency).
Finds links and forms from HTML using regex - fast, no browser needed.
Playwright is no longer required for basic crawling.
"""
import httpx
import re
import logging
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    urls: list = field(default_factory=list)
    forms: list = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    cookies: list = field(default_factory=list)
    technologies: list = field(default_factory=list)


class WebCrawler(BaseScanner):
    """Lightweight web crawler using httpx. No Playwright/Chromium needed."""

    def __init__(self, scan_id: str, target: str, scope: list, rate_limiter, max_depth: int = 3):
        super().__init__(scan_id, target, scope, rate_limiter)
        self.max_depth = max_depth
        self.crawl_result = CrawlResult()

    def get_scanner_name(self) -> str:
        return "web_crawler"

    async def run(self) -> List[RawFinding]:
        """Crawl the target URL and return findings from analysis."""
        crawl_result = await self._run_crawl()
        self.crawl_result = crawl_result
        return self._analyze_crawl_result()

    async def _run_crawl(self) -> CrawlResult:
        """Run the httpx-based crawl."""
        urls_found = set()
        forms_found = []
        headers_found = {}
        technologies = []

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False,
                headers={"User-Agent": "VulnAI-Scanner/1.0 (Authorised Security Testing)"}
            ) as client:
                logger.info(f"[Crawler] Fetching {self.target}")
                resp = await client.get(self.target)
                headers_found = dict(resp.headers)

                # Detect technologies from headers
                server = resp.headers.get("server", "").lower()
                powered_by = resp.headers.get("x-powered-by", "").lower()
                if "nginx" in server:
                    technologies.append("nginx")
                if "apache" in server:
                    technologies.append("apache")
                if "cloudflare" in server:
                    technologies.append("cloudflare")
                if "express" in powered_by:
                    technologies.append("express")
                if "php" in powered_by or "php" in server:
                    technologies.append("php")
                if "asp.net" in powered_by or "iis" in server:
                    technologies.append("asp.net")

                # Extract links from HTML using regex
                html = resp.text
                href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
                target_host = urlparse(self.target).hostname

                for match in href_pattern.findall(html):
                    full_url = urljoin(self.target, match)
                    parsed = urlparse(full_url)
                    if parsed.scheme in ('http', 'https'):
                        if parsed.hostname == target_host:
                            urls_found.add(full_url)

                # Extract forms
                form_pattern = re.compile(
                    r'<form[^>]*action=["\']([^"\']*)["\'][^>]*method=["\']([^"\']*)["\']',
                    re.IGNORECASE
                )
                for action, method in form_pattern.findall(html):
                    forms_found.append({
                        "action": urljoin(self.target, action),
                        "method": method.upper()
                    })

                logger.info(
                    f"[Crawler] Found {len(urls_found)} URLs, "
                    f"{len(forms_found)} forms"
                )

        except Exception as e:
            logger.error(f"[Crawler] Error crawling {self.target}: {e}")

        return CrawlResult(
            urls=list(urls_found)[:50],
            forms=forms_found,
            headers=headers_found,
            cookies=[],
            technologies=technologies,
        )

    def _analyze_crawl_result(self) -> List[RawFinding]:
        """Analyze crawl result and generate findings."""
        findings = []

        # Check for forms without HTTPS
        for form in self.crawl_result.forms:
            if form.get("action", "").startswith("http://"):
                findings.append(RawFinding(
                    title="Form Submits Over Unencrypted HTTP",
                    description=f"Form action URL uses HTTP instead of HTTPS: {form.get('action')}",
                    severity="medium",
                    affected_component=form.get("action", ""),
                    evidence=str(form),
                    scanner_source=self.get_scanner_name(),
                ))

        # Report URL count
        if self.crawl_result.urls:
            findings.append(RawFinding(
                title=f"Crawl Discovered {len(self.crawl_result.urls)} URLs",
                description=f"Web crawler discovered {len(self.crawl_result.urls)} unique URLs on {self.target}.",
                severity="informational",
                affected_component=self.target,
                evidence=f"URLs found: {len(self.crawl_result.urls)}",
                scanner_source=self.get_scanner_name(),
            ))

        return findings