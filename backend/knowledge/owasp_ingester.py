import logging

logger = logging.getLogger(__name__)


class OWASPIngester:
    """Indexes OWASP Top 10 knowledge into the vector store."""

    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    async def _get_vector_store(self):
        if self.vector_store is None:
            from backend.knowledge.vector_store import VectorStore
            self.vector_store = await VectorStore.create()
        return self.vector_store

    async def index_owasp_top10(self):
        """Index OWASP Top 10 2021 descriptions and mitigations as static documents."""
        vs = await self._get_vector_store()
        if not vs.collections:
            logger.warning("Vector store not available, skipping OWASP indexing")
            return

        owasp_entries = [
            {
                "id": "OWASP-01",
                "title": "Broken Access Control",
                "description": "Broken Access Control is the number one web security risk. It occurs when users can act outside of their intended permissions. This includes accessing unauthorized functionality, viewing other users' data, or modifying data without proper authorization. Mitigation includes implementing least privilege principles, validating permissions on every request, and using role-based access control (RBAC).",
            },
            {
                "id": "OWASP-02",
                "title": "Cryptographic Failures",
                "description": "Cryptographic failures (formerly Sensitive Data Exposure) occur when sensitive data is not properly protected in transit or at rest. This includes using weak encryption algorithms, not enforcing HTTPS, storing passwords in plaintext, or exposing credit card numbers. Mitigations include using strong encryption (AES-256, TLS 1.3), properly managing keys, and never storing sensitive data unnecessarily.",
            },
            {
                "id": "OWASP-03",
                "title": "Injection",
                "description": "Injection occurs when untrusted data is sent to an interpreter as part of a command or query. SQL, NoSQL, OS command, and LDAP injection are common types. The attacker's hostile data tricks the interpreter into executing unintended commands. Mitigations include using parameterized queries (prepared statements), input validation, and proper escaping.",
            },
            {
                "id": "OWASP-04",
                "title": "Insecure Design",
                "description": "Insecure Design refers to risks related to design and architecture flaws. These occur when software is built without adequate security consideration from the start. This category emphasizes the need for threat modeling, secure design patterns, and reference architectures. Mitigations include establishing secure design patterns, threat modeling during development, and security reviews.",
            },
            {
                "id": "OWASP-05",
                "title": "Security Misconfiguration",
                "description": "Security misconfiguration is the most common issue. It results from using default configurations, incomplete or ad-hoc configurations, open cloud storage, misconfigured HTTP headers, and unnecessary features enabled. Mitigations include automating configuration management, removing unused features, and regularly auditing configurations against benchmarks.",
            },
            {
                "id": "OWASP-06",
                "title": "Vulnerable and Outdated Components",
                "description": "Using components with known vulnerabilities undermines application security. This includes outdated libraries, frameworks, and software with unpatched vulnerabilities. Attackers exploit known CVEs to compromise the system. Mitigations include maintaining an inventory of components, regularly updating dependencies, and monitoring CVE databases.",
            },
            {
                "id": "OWASP-07",
                "title": "Identification and Authentication Failures",
                "description": "Authentication failures include weak password policies, credential stuffing, session hijacking, and improper session management. Attackers can compromise passwords, keys, or session tokens to assume user identities. Mitigations include implementing MFA, using strong password policies, and secure session management practices.",
            },
            {
                "id": "OWASP-08",
                "title": "Software and Data Integrity Failures",
                "description": "Integrity failures occur when software or data is modified without authorization. This includes using untrusted plugins/libraries, unsigned software updates, and insufficient CI/CD security. The SolarWinds supply chain attack is a prominent example. Mitigations include signing code, verifying software provenance, and securing the CI/CD pipeline.",
            },
            {
                "id": "OWASP-09",
                "title": "Security Logging and Monitoring Failures",
                "description": "Without proper logging and monitoring, breaches can go undetected for extended periods. This includes missing critical events, log tampering, or not monitoring for suspicious activity. Mitigations include logging all authentication attempts, failed access controls, and input validation failures, plus implementing SIEM integration and alerting.",
            },
            {
                "id": "OWASP-10",
                "title": "Server-Side Request Forgery (SSRF)",
                "description": "SSRF occurs when a web application fetches remote resources based on user input without proper validation. Attackers can make the server send requests to internal systems, read cloud metadata, or access internal services. Mitigations include validating and sanitizing URLs, blocking access to internal IP ranges, and using allowlists of permitted destinations.",
            },
        ]

        ids = []
        texts = []
        metadatas = []

        for entry in owasp_entries:
            text = f"{entry['title']}: {entry['description']}"
            ids.append(entry["id"])
            texts.append(text)
            metadatas.append({
                "title": entry["title"],
                "source": "owasp",
            })

        if ids:
            await vs.add_documents_batch("owasp_knowledge", ids, texts, metadatas)
            logger.info(f"Indexed {len(ids)} OWASP entries into ChromaDB")