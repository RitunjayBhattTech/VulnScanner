import logging
from typing import List

logger = logging.getLogger(__name__)


class CWEIngester:
    """Indexes MITRE CWE (Common Weakness Enumeration) data into the vector store."""

    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    async def _get_vector_store(self):
        if self.vector_store is None:
            from backend.knowledge.vector_store import VectorStore
            self.vector_store = await VectorStore.create()
        return self.vector_store

    async def index_top_cwes(self):
        """Index the MITRE Top 25 CWEs as static documents."""
        vs = await self._get_vector_store()
        if not vs.collections:
            logger.warning("Vector store not available, skipping CWE indexing")
            return

        top_cwes = [
            {
                "id": "CWE-787",
                "name": "Out-of-bounds Write",
                "description": "The software writes data past the end, or before the beginning, of the intended buffer. This can result in corruption of data, crash, or code execution."
            },
            {
                "id": "CWE-79",
                "name": "Cross-site Scripting (XSS)",
                "description": "The software does not neutralize or incorrectly neutralizes user-controllable input before it is placed in output used as a web page. This allows attackers to inject scripts."
            },
            {
                "id": "CWE-89",
                "name": "SQL Injection",
                "description": "The software constructs SQL commands from user-supplied input without proper neutralization. Attackers can modify SQL statements to access or modify database contents."
            },
            {
                "id": "CWE-416",
                "name": "Use After Free",
                "description": "The software continues to use memory after it has been freed. This can cause crashes or enable code execution by manipulating freed memory."
            },
            {
                "id": "CWE-78",
                "name": "OS Command Injection",
                "description": "The software constructs OS commands from user input without proper neutralization, allowing attackers to execute arbitrary commands."
            },
            {
                "id": "CWE-20",
                "name": "Improper Input Validation",
                "description": "The software does not validate or incorrectly validates input, which can lead to various injection attacks or unexpected behavior."
            },
            {
                "id": "CWE-125",
                "name": "Out-of-bounds Read",
                "description": "The software reads data past the end or before the beginning of the intended buffer, leading to information disclosure or crashes."
            },
            {
                "id": "CWE-22",
                "name": "Path Traversal",
                "description": "The software uses external input to construct a pathname without proper sanitization, allowing access to restricted files."
            },
            {
                "id": "CWE-352",
                "name": "Cross-Site Request Forgery (CSRF)",
                "description": "The web application does not verify that requests are intentional, allowing attackers to trick users into performing actions without consent."
            },
            {
                "id": "CWE-434",
                "name": "Unrestricted File Upload",
                "description": "The software allows file uploads without sufficient restrictions on type or content, potentially allowing attackers to upload malicious files."
            },
            {
                "id": "CWE-862",
                "name": "Missing Authorization",
                "description": "The software does not enforce authorization checks for sensitive operations, allowing unauthorized access."
            },
            {
                "id": "CWE-476",
                "name": "NULL Pointer Dereference",
                "description": "The software dereferences a pointer that is NULL, causing a crash or denial of service."
            },
            {
                "id": "CWE-287",
                "name": "Improper Authentication",
                "description": "The software does not properly verify identity before granting access, allowing unauthorized users to gain privileges."
            },
            {
                "id": "CWE-190",
                "name": "Integer Overflow or Wraparound",
                "description": "The software performs arithmetic operations that can overflow or wrap around, leading to unexpected behavior or security vulnerabilities."
            },
            {
                "id": "CWE-502",
                "name": "Deserialization of Untrusted Data",
                "description": "The software deserializes data without verification, potentially allowing attackers to execute arbitrary code."
            },
            {
                "id": "CWE-77",
                "name": "Improper Neutralization of Command Elements",
                "description": "The software fails to properly sanitize command inputs, enabling command injection attacks."
            },
            {
                "id": "CWE-119",
                "name": "Buffer Overflow",
                "description": "The software writes to a buffer without proper bounds checking, allowing overwriting of adjacent memory."
            },
            {
                "id": "CWE-798",
                "name": "Use of Hard-coded Credentials",
                "description": "The software contains hard-coded passwords or cryptographic keys, which can be extracted and used by attackers."
            },
            {
                "id": "CWE-918",
                "name": "Server-Side Request Forgery (SSRF)",
                "description": "The software makes requests to URLs supplied by users without validation, allowing attacks on internal systems."
            },
            {
                "id": "CWE-306",
                "name": "Missing Authentication for Critical Function",
                "description": "The software does not require authentication for functions that should require it, allowing unauthorized access."
            },
            {
                "id": "CWE-362",
                "name": "Race Condition",
                "description": "The software performs operations in an unsafe order, allowing attackers to exploit timing windows."
            },
            {
                "id": "CWE-269",
                "name": "Improper Privilege Management",
                "description": "The software does not properly manage privileges, potentially allowing privilege escalation."
            },
            {
                "id": "CWE-295",
                "name": "Improper Certificate Validation",
                "description": "The software does not properly validate certificates, enabling man-in-the-middle attacks."
            },
            {
                "id": "CWE-200",
                "name": "Information Exposure",
                "description": "The software exposes sensitive information to unauthorized actors through error messages, timing differences, or other side channels."
            },
            {
                "id": "CWE-522",
                "name": "Insufficiently Protected Credentials",
                "description": "The software transmits or stores credentials insecurely, allowing unauthorized access to authentication data."
            },
        ]

        ids = []
        texts = []
        metadatas = []

        for cwe in top_cwes:
            text = f"{cwe['id']}: {cwe['name']}. {cwe['description']}"
            ids.append(cwe["id"])
            texts.append(text)
            metadatas.append({
                "name": cwe["name"],
                "source": "mitre",
            })

        if ids:
            await vs.add_documents_batch("cwe_knowledge", ids, texts, metadatas)
            logger.info(f"Indexed {len(ids)} CWEs into ChromaDB")