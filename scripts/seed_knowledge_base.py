#!/usr/bin/env python3
"""
One-time script to populate the ChromaDB knowledge base with CVE/CWE/OWASP data.
Run: python scripts/seed_knowledge_base.py
"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 60)
    logger.info("VulnAI Scanner - Knowledge Base Seed Script")
    logger.info("=" * 60)

    # Initialize vector store
    logger.info("Initializing ChromaDB vector store...")
    from backend.knowledge.vector_store import VectorStore
    vs = await VectorStore.create()

    if not vs.collections:
        logger.error("ChromaDB not available. Check CHROMA_PERSIST_DIR configuration.")
        sys.exit(1)

    # Count existing documents
    for name in ["cve_knowledge", "owasp_knowledge", "cwe_knowledge"]:
        count = await vs.count(name)
        logger.info(f"  {name}: {count} existing documents")

    # Seed CWE knowledge (MITRE Top 25)
    logger.info("\nSeeding CWE knowledge base...")
    from backend.knowledge.cwe_ingester import CWEIngester
    cwe_ingester = CWEIngester(vs)
    await cwe_ingester.index_top_cwes()
    cwe_count = await vs.count("cwe_knowledge")
    logger.info(f"  CWE documents indexed: {cwe_count}")

    # Seed OWASP knowledge
    logger.info("\nSeeding OWASP knowledge base...")
    from backend.knowledge.owasp_ingester import OWASPIngester
    owasp_ingester = OWASPIngester(vs)
    await owasp_ingester.index_owasp_top10()
    owasp_count = await vs.count("owasp_knowledge")
    logger.info(f"  OWASP documents indexed: {owasp_count}")

    # Seed CVE knowledge (from NVD API)
    logger.info("\nSeeding CVE knowledge base (fetching from NVD API)...")
    from backend.knowledge.cve_ingester import CVEIngester
    cve_ingester = CVEIngester(vs)
    cves = await cve_ingester.fetch_recent_cves(days=120)
    if cves:
        await cve_ingester.index_cves(cves)
    cve_count = await vs.count("cve_knowledge")
    logger.info(f"  CVE documents indexed: {cve_count}")

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("Knowledge Base Seed Complete!")
    logger.info(f"  CVE Knowledge: {cve_count} documents")
    logger.info(f"  CWE Knowledge: {cwe_count} documents")
    logger.info(f"  OWASP Knowledge: {owasp_count} documents")
    logger.info(f"  Total: {cve_count + cwe_count + owasp_count} documents")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())