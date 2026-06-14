import logging
from typing import List, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store for knowledge base embeddings."""

    def __init__(self, client=None, collections: dict = None):
        self.client = client
        self.collections = collections or {}

    @classmethod
    async def create(cls):
        """Create a new VectorStore instance, initializing ChromaDB."""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            collections = {}

            # Create collections if they don't exist
            for name in ["cve_knowledge", "owasp_knowledge", "cwe_knowledge"]:
                try:
                    collections[name] = client.get_collection(name)
                except Exception:
                    collections[name] = client.create_collection(name)

            return cls(client=client, collections=collections)
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}")
            return cls()

    async def add_document(self, collection: str, doc_id: str, text: str, metadata: dict = None):
        """Add a document to a collection."""
        if collection not in self.collections:
            logger.warning(f"Collection '{collection}' not found")
            return

        try:
            # Generate embedding
            import chromadb.utils.embedding_functions as ef
            ef = ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            embedding = ef([text])[0]

            self.collections[collection].add(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                documents=[text],
            )
        except Exception as e:
            logger.error(f"Failed to add document to {collection}: {e}")

    async def add_documents_batch(self, collection: str, ids: List[str], texts: List[str], metadatas: List[dict] = None):
        """Add multiple documents in batch."""
        if collection not in self.collections:
            logger.warning(f"Collection '{collection}' not found")
            return

        try:
            # Batch in groups of 100
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = (metadatas[i:i + batch_size]) if metadatas else [{}] * len(batch_ids)

                self.collections[collection].add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                )
            logger.info(f"Added {len(ids)} documents to {collection}")
        except Exception as e:
            logger.error(f"Failed to batch add documents to {collection}: {e}")

    async def query(self, collection: str, query_text: str, n_results: int = 5) -> List[dict]:
        """Query a collection for similar documents."""
        if collection not in self.collections:
            logger.warning(f"Collection '{collection}' not found")
            return []

        try:
            import chromadb.utils.embedding_functions as ef
            ef = ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            query_embedding = ef([query_text])[0]

            results = self.collections[collection].query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 10),
            )

            documents = []
            if results and results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = {}
                    if results.get("metadatas") and results["metadatas"][0]:
                        metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                    documents.append({
                        "text": doc,
                        "metadata": metadata,
                    })
            return documents
        except Exception as e:
            logger.error(f"Failed to query {collection}: {e}")
            return []

    async def count(self, collection: str) -> int:
        """Count documents in a collection."""
        if collection not in self.collections:
            return 0
        try:
            return self.collections[collection].count()
        except Exception as e:
            logger.error(f"Failed to count {collection}: {e}")
            return 0