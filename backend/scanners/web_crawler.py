import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Structured result from web crawling."""
    urls: List[str] = field(default_factory=list)
    forms: List[dict] = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    cookies: List[dict] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


class WebCrawler(BaseScanner):
    """Playwright async web crawler that collects URLs, forms, headers, and cookies."""

    def __init__(self, scan_id: str, target: str, scope: list, rate_limiter, max_depth: int = 3):
        super().__init__(scan_id, target, scope, rate_limiter)
        self.max_depth = max_depth
        self.visited = set()
        self.crawl_result = CrawlResult()

    def get_scanner_name(self) -> str:
        return "web_crawler"

    async def run(self) -> List[RawFinding]:
        """Crawl the target URL and collect information. Returns findings from analysis."""
        findings = []

        try:
            validate_scope(self.target, self.scope)

            async with self.rate_limiter.limit():
                from playwright.async_api import async_playwright

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()

                    # Initial navigation
                    try:
                        response = await page.goto(self.target, wait_until="networkidle", timeout=30000)
                        if response:
                            self.crawl_result.headers = dict(response.headers)
                    except Exception as e:
                        logger.warning(f"Navigation error to {self.target}: {e}")

                    # Collect cookies
                    cookies = await page.context.cookies()
                    self.crawl_result.cookies = cookies

                    # Collect forms
                    forms = await page.evaluate("""
                        () => Array.from(document.forms).map(f => ({
                            action: f.action,
                            method: f.method,
                            inputs: Array.from(f.elements).map(e => ({
                                name: e.name,
                                type: e.type,
                                placeholder: e.placeholder
                            }))
                        }))
                    """)
                    self.crawl_result.forms = forms or []

                    # Crawl links up to max_depth
                    await self._crawl_links(page, self.target, 0)

                    # Detect technologies from headers
                    self._detect_technologies()

                    await browser.close()

        except Exception as e:
            logger.error(f"Web crawler error: {e}", exc_info=True)

        # Generate findings from crawl analysis
        findings.extend(self._analyze_crawl_result())
        return findings

    async def _crawl_links(self, page, base_url: str, depth: int):
        """Recursively crawl links up to max_depth."""
        if depth >= self.max_depth:
            return

        base_parsed = urlparse(base_url)
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
        """)
        links = [urljoin(base_url, link) for link in (links or [])]

        for link in links:
            if link in self.visited:
                continue
            self.visited.add(link)

            link_parsed = urlparse(link)
            if link_parsed.netloc != base_parsed.netloc:
                continue

            # Validate scope for this URL
            try:
                validate_scope(link, self.scope)
            except Exception:
                continue

            self.crawl_result.urls.append(link)

            async with self.rate_limiter.limit():
                try:
                    new_page = await page.context.new_page()
                    await new_page.goto(link, wait_until="domcontentloaded", timeout=15000)
                    await self._crawl_links(new_page, link, depth + 1)
                    await new_page.close()
                except Exception:
                    continue

    def _detect_technologies(self):
        """Detect technologies from response headers."""
        headers = self.crawl_result.headers
        server = headers.get("server", "").lower()
        powered_by = headers.get("x-powered-by", "").lower()

        if "nginx" in server:
            self.crawl_result.technologies.append("nginx")
        if "apache" in server:
            self.crawl_result.technologies.append("apache")
        if "cloudflare" in server:
            self.crawl_result.technologies.append("cloudflare")
        if "express" in powered_by:
            self.crawl_result.technologies.append("express")
        if "php" in powered_by or "php" in server:
            self.crawl_result.technologies.append("php")
        if "asp.net" in powered_by or "iis" in server:
            self.crawl_result.technologies.append("asp.net")
        if "python" in powered_by or "python" in server:
            self.crawl_result.technologies.append("python")

    def _analyze_crawl_result(self) -> List[RawFinding]:
        """Analyze the crawl result and generate findings."""
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

        # Check for forms with password fields but no HTTPS
        for form in self.crawl_result.forms:
            for inp in form.get("inputs", []):
                if inp.get("type") == "password" and not form.get("action", "").startswith("https"):
                    findings.append(RawFinding(
                        title="Password Field Over Unencrypted Connection",
                        description="A password input field exists on a page submitted over HTTP.",
                        severity="high",
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