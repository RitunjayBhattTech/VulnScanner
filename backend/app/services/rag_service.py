import json
import os
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class RagService:
    """
    RAG service for retrieving CVE context relevant to scan findings.
    
    Currently uses a local CVE knowledge base stored in ChromaDB.
    Falls back gracefully if ChromaDB is not available.
    """

    # Inline mini CVE knowledge base (common services with known vulnerabilities)
    CVE_KNOWLEDGE: List[Dict[str, Any]] = [
        {"service": "ssh", "port": 22, "cve": "CVE-2024-6387", "description": "OpenSSH regreSSHion - unauthenticated remote code execution in glibc-based systems", "cvss": 8.1, "product": "OpenSSH"},
        {"service": "http", "port": 80, "cve": "CVE-2024-27198", "description": "JetBrains TeamCity authentication bypass allowing unauthenticated RCE", "cvss": 9.8, "product": "Apache HTTP Server"},
        {"service": "https", "port": 443, "cve": "CVE-2023-44487", "description": "HTTP/2 Rapid Reset Attack - DDoS via HTTP/2 stream cancellation", "cvss": 7.5, "product": "HTTP/2 enabled servers"},
        {"service": "mysql", "port": 3306, "cve": "CVE-2023-21971", "description": "Oracle MySQL unspecified vulnerability allowing remote code execution", "cvss": 8.0, "product": "MySQL"},
        {"service": "postgresql", "port": 5432, "cve": "CVE-2024-0985", "description": "PostgreSQL arbitrary code execution via unprivileged user", "cvss": 7.8, "product": "PostgreSQL"},
        {"service": "redis", "port": 6379, "cve": "CVE-2023-41056", "description": "Redis integer overflow in hash table expansion", "cvss": 6.5, "product": "Redis"},
        {"service": "nginx", "port": 80, "cve": "CVE-2024-24989", "description": "Nginx HTTP/2 memory disclosure vulnerability", "cvss": 7.5, "product": "Nginx"},
        {"service": "apache", "port": 80, "cve": "CVE-2024-24795", "description": "Apache HTTP Server HTTP/2 request header confusion", "cvss": 7.5, "product": "Apache HTTP Server"},
        {"service": "tomcat", "port": 8080, "cve": "CVE-2024-21733", "description": "Apache Tomcat response smuggling vulnerability", "cvss": 6.5, "product": "Apache Tomcat"},
        {"service": "docker", "port": 2375, "cve": "CVE-2024-21626", "description": "Docker containerd escape via runc process.cwd", "cvss": 8.6, "product": "Docker"},
        {"service": "kubernetes", "port": 6443, "cve": "CVE-2024-1024", "description": "Kubernetes kubelet authentication bypass", "cvss": 9.0, "product": "Kubernetes"},
        {"service": "elasticsearch", "port": 9200, "cve": "CVE-2023-46673", "description": "Elasticsearch arbitrary file read via snapshot API", "cvss": 7.5, "product": "Elasticsearch"},
        {"service": "mongodb", "port": 27017, "cve": "CVE-2024-1356", "description": "MongoDB arbitrary code execution via crafted queries", "cvss": 8.5, "product": "MongoDB"},
        {"service": "smb", "port": 445, "cve": "CVE-2024-38077", "description": "Windows SMB remote code execution (Zerologon variant)", "cvss": 9.0, "product": "Samba/Windows"},
        {"service": "rdp", "port": 3389, "cve": "CVE-2024-38076", "description": "Windows RDP remote code execution vulnerability", "cvss": 8.8, "product": "Microsoft RDP"},
        {"service": "ftp", "port": 21, "cve": "CVE-2023-39615", "description": "ProFTPD arbitrary file copy vulnerability", "cvss": 7.5, "product": "ProFTPD"},
        {"service": "dns", "port": 53, "cve": "CVE-2023-50387", "description": "DNS KeyTrap - DNSSEC validation DoS via crafted signatures", "cvss": 7.5, "product": "DNS servers"},
    ]

    def __init__(self, index_path: str = ".chromadb"):
        self.index_path = index_path
        self._client = None

    def _get_client(self):
        """Lazy-init ChromaDB client."""
        if self._client is None and HAS_CHROMADB:
            try:
                self._client = chromadb.PersistentClient(
                    path=self.index_path,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                # Seed the collection if it doesn't exist
                collection = self._client.get_or_create_collection("cve_knowledge")
                if collection.count() == 0:
                    self._seed_collection(collection)
            except Exception as e:
                # ChromaDB might fail in some environments
                self._client = None
        return self._client

    def _seed_collection(self, collection) -> None:
        """Seed ChromaDB with initial CVE knowledge base."""
        documents = []
        metadatas = []
        ids = []
        for i, cve in enumerate(self.CVE_KNOWLEDGE):
            documents.append(
                f"Service: {cve['service']} (port {cve['port']}). "
                f"CVE: {cve['cve']}. {cve['description']}. "
                f"CVSS Score: {cve['cvss']}. Product: {cve['product']}."
            )
            metadatas.append(cve)
            ids.append(f"cve_{i}")
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def index_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve CVE context for each finding.
        
        Uses ChromaDB semantic search if available, otherwise falls back to
        keyword matching against the built-in CVE knowledge base.
        """
        client = self._get_client()

        if client:
            try:
                collection = client.get_collection("cve_knowledge")
                return self._chroma_search(collection, findings)
            except Exception:
                pass

        return self._keyword_search(findings)

    def _chroma_search(self, collection, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use ChromaDB for semantic CVE retrieval."""
        results = []
        for finding in findings:
            query = f"{finding.get('service', '')} {finding.get('host', '')} port {finding.get('port', '')}"
            try:
                search_results = collection.query(query_texts=[query], n_results=3)
                contexts = []
                if search_results and search_results.get("metadatas") and search_results["metadatas"][0]:
                    for meta in search_results["metadatas"][0]:
                        contexts.append({
                            "cve": meta.get("cve", ""),
                            "description": meta.get("description", ""),
                            "cvss": meta.get("cvss", 0),
                            "relevance": "high",
                        })
                results.append({
                    "host": finding["host"],
                    "port": finding.get("port"),
                    "service": finding.get("service"),
                    "cve_contexts": contexts,
                })
            except Exception:
                results.append({
                    "host": finding["host"],
                    "port": finding.get("port"),
                    "service": finding.get("service"),
                    "cve_contexts": [],
                })
        return results

    def _keyword_search(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback: match findings against inline CVE knowledge base by service name."""
        results = []
        for finding in findings:
            service = (finding.get("service") or "").lower()
            port = finding.get("port")
            matched_cves = []

            for cve in self.CVE_KNOWLEDGE:
                # Match by service name and/or port
                if cve["service"] == service or cve["port"] == port:
                    matched_cves.append({
                        "cve": cve["cve"],
                        "description": cve["description"],
                        "cvss": cve["cvss"],
                        "product": cve["product"],
                        "relevance": "high" if cve["service"] == service else "medium",
                    })

            results.append({
                "host": finding["host"],
                "port": finding.get("port"),
                "service": finding.get("service"),
                "cve_contexts": matched_cves[:3],  # Top 3
            })

        return results