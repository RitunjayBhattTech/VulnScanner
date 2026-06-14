import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class CVEIngester:
    """Fetches recent CVE data from NVD API v2 and indexes it into the vector store."""

    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = settings.NVD_API_KEY

    async def _get_vector_store(self):
        """Lazy initialize vector store."""
        if self.vector_store is None:
            from backend.knowledge.vector_store import VectorStore
            self.vector_store = await VectorStore.create()
        return self.vector_store

    async def fetch_recent_cves(self, days: int = 120) -> List[dict]:
        """Fetch CVEs from the last N days from NVD API."""
        vs = await self._get_vector_store()
        if not vs.collections:
            logger.warning("Vector store not available, skipping CVE fetch")
            return []

        start_date = datetime.utcnow() - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        all_cves = []
        start_index = 0
        results_per_page = 50
        max_pages = 10  # Safety limit

        for page in range(max_pages):
            params = {
                "pubStartDate": start_str,
                "pubEndDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000"),
                "startIndex": start_index,
                "resultsPerPage": results_per_page,
            }

            headers = {}
            if self.api_key:
                headers["apiKey"] = self.api_key

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.base_url, params=params, headers=headers)
                    if response.status_code == 403:
                        logger.warning("NVD API rate limited. Try setting NVD_API_KEY.")
                        break
                    response.raise_for_status()
                    data = response.json()

                    vulnerabilities = data.get("vulnerabilities", [])
                    if not vulnerabilities:
                        break

                    for vuln in vulnerabilities:
                        cve = vuln.get("cve", {})
                        cve_id = cve.get("id", "")
                        descriptions = cve.get("descriptions", [])
                        description = ""
                        for desc in descriptions:
                            if desc.get("lang") == "en":
                                description = desc.get("value", "")
                                break

                        metrics = cve.get("metrics", {})
                        cvss_score = None
                        severity = None
                        for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                            if metric_type in metrics and metrics[metric_type]:
                                cvss_data = metrics[metric_type][0].get("cvssData", {})
                                cvss_score = cvss_data.get("baseScore")
                                severity = cvss_data.get("baseSeverity", "").lower()
                                break

                        weaknesses = cve.get("weaknesses", [])
                        cwe_ids = []
                        for weakness in weaknesses:
                            for desc in weakness.get("description", []):
                                if desc.get("value", "").startswith("CWE-"):
                                    cwe_ids.append(desc.get("value", ""))

                        all_cves.append({
                            "id": cve_id,
                            "description": description,
                            "cvss_score": cvss_score,
                            "severity": severity or "unknown",
                            "cwe_ids": cwe_ids,
                            "published": cve.get("published", ""),
                        })

                    start_index += results_per_page

                    # Rate limiting: respect NVD limits (5 req/30s without key, 50 req/30s with key)
                    await asyncio.sleep(6 if not self.api_key else 0.6)

            except httpx.HTTPError as e:
                logger.error(f"NVD API error: {e}")
                break

        logger.info(f"Fetched {len(all_cves)} CVEs from NVD")
        return all_cves

    async def index_cves(self, cves: List[dict]):
        """Index CVEs into the vector store."""
        vs = await self._get_vector_store()
        if not vs.collections:
            logger.warning("Vector store not available, skipping CVE indexing")
            return

        ids = []
        texts = []
        metadatas = []

        for cve in cves:
            if not cve.get("id"):
                continue

            text = f"{cve['id']}: {cve['description']}. CVSS: {cve.get('cvss_score', 'N/A')}. Severity: {cve.get('severity', 'unknown')}."
            if cve.get("cwe_ids"):
                text += f" CWE: {', '.join(cve['cwe_ids'])}"

            ids.append(cve["id"])
            texts.append(text)
            metadatas.append({
                "cvss_score": cve.get("cvss_score") or 0.0,
                "severity": cve.get("severity", "unknown"),
                "published_date": cve.get("published", ""),
                "source": "nvd",
            })

        if ids:
            await vs.add_documents_batch("cve_knowledge", ids, texts, metadatas)
            logger.info(f"Indexed {len(ids)} CVEs into ChromaDB")