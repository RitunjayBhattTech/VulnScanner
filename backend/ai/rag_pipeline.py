import logging
from typing import List

from backend.schemas.finding import RawFinding

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG (Retrieval-Augmented Generation) pipeline for enriching findings with CVE/CWE/OWASP context."""

    def __init__(self):
        self._vector_store = None
        self._encoder = None

    async def _get_vector_store(self):
        """Lazy initialize the vector store."""
        if self._vector_store is None:
            try:
                from backend.knowledge.vector_store import VectorStore
                self._vector_store = await VectorStore.create()
            except Exception as e:
                logger.warning(f"Vector store not available: {e}")
                self._vector_store = None
        return self._vector_store

    async def _get_encoder(self):
        """Lazy initialize the sentence transformer encoder."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Sentence transformer not available: {e}")
                self._encoder = None
        return self._encoder

    async def get_context_for_finding(self, finding: RawFinding) -> str:
        """
        Build a context string from the knowledge base for a given finding.
        Queries CVE, CWE, and OWASP collections for relevant documents.
        """
        try:
            vector_store = await self._get_vector_store()
            if not vector_store:
                return "No knowledge base available."

            # Build query from finding data
            query_parts = [finding.title, finding.description or ""]
            if finding.cve_ids:
                query_parts.extend(finding.cve_ids)
            if finding.affected_component:
                query_parts.append(finding.affected_component)

            query = " ".join([p for p in query_parts if p])

            if not query:
                return ""

            contexts = []

            # Query CVE knowledge
            try:
                cve_results = await vector_store.query("cve_knowledge", query, n_results=5)
                if cve_results:
                    cve_text = "\n\n".join([
                        f"Document {i+1}: {doc['text']}"
                        for i, doc in enumerate(cve_results)
                    ])
                    contexts.append(f"RELEVANT CVEs:\n{cve_text}")
            except Exception as e:
                logger.warning(f"CVE query failed: {e}")

            # Query OWASP knowledge
            try:
                owasp_results = await vector_store.query("owasp_knowledge", query, n_results=3)
                if owasp_results:
                    owasp_text = "\n\n".join([
                        f"Document {i+1}: {doc['text']}"
                        for i, doc in enumerate(owasp_results)
                    ])
                    contexts.append(f"RELEVANT OWASP CONTEXT:\n{owasp_text}")
            except Exception as e:
                logger.warning(f"OWASP query failed: {e}")

            # Query CWE knowledge
            try:
                cwe_results = await vector_store.query("cwe_knowledge", query, n_results=3)
                if cwe_results:
                    cwe_text = "\n\n".join([
                        f"Document {i+1}: {doc['text']}"
                        for i, doc in enumerate(cwe_results)
                    ])
                    contexts.append(f"RELEVANT CWEs:\n{cwe_text}")
            except Exception as e:
                logger.warning(f"CWE query failed: {e}")

            return "\n\n".join(contexts) if contexts else "No relevant knowledge base entries found."

        except Exception as e:
            logger.error(f"RAG pipeline error: {e}", exc_info=True)
            return "Error querying knowledge base."


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()