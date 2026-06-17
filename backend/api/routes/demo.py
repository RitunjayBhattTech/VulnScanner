"""
Demo mode: returns realistic pre-populated scan data for portfolio demonstrations.
No actual scanning is performed.
"""
from fastapi import APIRouter
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_SCAN_ID = "demo-scan-00000000-0000-0000-0000-000000000001"

DEMO_FINDINGS = [
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "SQL Injection in Login Form",
        "description": "The login form parameter 'username' is vulnerable to SQL injection. An attacker can bypass authentication or extract the entire database.",
        "severity": "critical",
        "cvss_score": 9.8,
        "cve_ids": ["CVE-2023-32315"],
        "cwe_ids": ["CWE-89"],
        "affected_component": "http://target.com/login.php?username=",
        "evidence": "Parameter: username\nPayload: ' OR 1=1--\nResponse: 200 OK (Welcome admin!)\nDetected: Authentication bypass successful",
        "ai_triage_notes": "This SQL injection is critical and immediately exploitable. The login form does not use prepared statements, allowing complete authentication bypass. Given this endpoint is internet-facing, exploitation risk is extremely high. A public exploit exists for this vulnerability class.",
        "ai_remediation": "## Immediate Mitigation\nDisable the vulnerable login endpoint or add a WAF rule blocking SQL metacharacters (', --, OR, UNION).\n\n## Permanent Fix\nReplace raw SQL queries with parameterized statements:\n```php\n$stmt = $pdo->prepare('SELECT * FROM users WHERE username = ? AND password = ?');\n$stmt->execute([$username, $password]);\n```\n\n## Verification\nRun: `sqlmap -u 'http://target.com/login.php' --data='username=test&password=test'` — should return 'no injectable parameters found'.",
        "false_positive_probability": 0.02,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nuclei",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Exposed Admin Panel Without Authentication",
        "description": "The admin panel at /admin is accessible without authentication. Full administrative access to the application is available to unauthenticated users.",
        "severity": "critical",
        "cvss_score": 9.1,
        "cve_ids": [],
        "cwe_ids": ["CWE-306"],
        "affected_component": "http://target.com/admin/",
        "evidence": "GET /admin/ HTTP/1.1\nResponse: 200 OK\nContent: <title>Admin Dashboard</title>\nNo authentication challenge received.",
        "ai_triage_notes": "The exposed admin panel represents a critical business risk. An unauthenticated attacker can access all user data, modify application settings, and potentially achieve remote code execution through admin functionality such as file upload or plugin installation.",
        "ai_remediation": "## Immediate Mitigation\nRestrict /admin/ to internal IPs only via web server config:\n```nginx\nlocation /admin/ {\n    allow 10.0.0.0/8;\n    deny all;\n}\n```\n\n## Permanent Fix\nImplement authentication middleware on all admin routes with MFA enforcement.\n\n## Verification\nAttempt to access /admin/ from an external IP — should receive 403 Forbidden.",
        "false_positive_probability": 0.01,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nuclei"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Cross-Site Scripting (XSS) in Search Parameter",
        "description": "The search parameter 'q' reflects user input without sanitization, allowing injection of arbitrary JavaScript.",
        "severity": "high",
        "cvss_score": 7.4,
        "cve_ids": [],
        "cwe_ids": ["CWE-79"],
        "affected_component": "http://target.com/search?q=",
        "evidence": "Payload: <script>alert(document.cookie)</script>\nURL: /search?q=<script>alert(1)</script>\nResponse contains: <script>alert(1)</script> unencoded in page body",
        "ai_triage_notes": "This reflected XSS can be exploited to steal session cookies, perform phishing attacks, or redirect users to malicious sites. Since the application does not use HttpOnly cookies, session hijacking via this XSS is directly possible.",
        "ai_remediation": "## Immediate Mitigation\nAdd Content-Security-Policy header:\n```\nContent-Security-Policy: default-src 'self'; script-src 'self'\n```\n\n## Permanent Fix\nEncode all output:\n```php\necho htmlspecialchars($_GET['q'], ENT_QUOTES, 'UTF-8');\n```\n\n## Verification\nSubmit `<script>alert(1)</script>` — browser should display it as text, not execute it.",
        "false_positive_probability": 0.05,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nuclei"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Missing HTTP Security Headers",
        "description": "Multiple security headers are absent: Strict-Transport-Security, Content-Security-Policy, X-Frame-Options, X-Content-Type-Options.",
        "severity": "medium",
        "cvss_score": 5.3,
        "cve_ids": [],
        "cwe_ids": ["CWE-693"],
        "affected_component": "http://target.com/",
        "evidence": "Response headers:\nServer: Apache/2.4.41\nContent-Type: text/html\n[Missing] Strict-Transport-Security\n[Missing] Content-Security-Policy\n[Missing] X-Frame-Options\n[Missing] X-Content-Type-Options",
        "ai_triage_notes": "Missing security headers increase the attack surface for clickjacking, MIME sniffing, and man-in-the-middle attacks. While not directly exploitable alone, they are commonly required for compliance (PCI-DSS, SOC2) and compound the risk from other findings.",
        "ai_remediation": "## Permanent Fix\nAdd to Apache config or .htaccess:\n```apache\nHeader always set Strict-Transport-Security 'max-age=31536000; includeSubDomains'\nHeader always set X-Frame-Options 'DENY'\nHeader always set X-Content-Type-Options 'nosniff'\nHeader always set Content-Security-Policy \"default-src 'self'\"\n```\n\n## Verification\nRun: `curl -I http://target.com` and verify all four headers are present.",
        "false_positive_probability": 0.01,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "header_analyzer"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "SSL Certificate Expires in 12 Days",
        "description": "The SSL certificate for the target domain expires in 12 days. After expiry, all HTTPS connections will fail and browsers will display security warnings.",
        "severity": "high",
        "cvss_score": 7.0,
        "cve_ids": [],
        "cwe_ids": ["CWE-295"],
        "affected_component": "target.com:443",
        "evidence": "Certificate Subject: CN=target.com\nIssuer: Let's Encrypt\nNot Before: 2024-03-15\nNot After: 2024-06-26\nDays remaining: 12",
        "ai_triage_notes": "Certificate expiry will cause complete service disruption for all HTTPS traffic. Given the 12-day window, this requires immediate action. Let's Encrypt certificates should auto-renew via certbot — the auto-renewal mechanism appears to have failed.",
        "ai_remediation": "## Immediate Action\nRenew the certificate now:\n```bash\ncertbot renew --force-renewal\nsystemctl reload nginx\n```\n\n## Permanent Fix\nEnsure certbot timer is enabled:\n```bash\nsystemctl enable certbot.timer\nsystemctl start certbot.timer\nsystemctl status certbot.timer\n```\n\n## Verification\n```bash\necho | openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -dates\n```",
        "false_positive_probability": 0.0,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "ssl_checker"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Open Port: 3306/tcp (MySQL)",
        "description": "MySQL database port 3306 is exposed to the internet. Database servers should never be directly accessible from public networks.",
        "severity": "high",
        "cvss_score": 7.5,
        "cve_ids": [],
        "cwe_ids": ["CWE-284"],
        "affected_component": "target.com:3306",
        "evidence": "PORT     STATE  SERVICE  VERSION\n3306/tcp open   mysql    MySQL 5.7.39\nMySQL unauthorized greeting received",
        "ai_triage_notes": "An internet-exposed MySQL port is a severe misconfiguration. It exposes the database to brute force attacks, known MySQL CVEs, and direct data exfiltration attempts. MySQL 5.7 is end-of-life and has multiple unpatched CVEs.",
        "ai_remediation": "## Immediate Mitigation\nBlock port 3306 at the firewall immediately:\n```bash\nufw deny 3306\n```\n\n## Permanent Fix\nConfigure MySQL to bind to localhost only in `/etc/mysql/mysql.conf.d/mysqld.cnf`:\n```ini\nbind-address = 127.0.0.1\n```\nThen upgrade MySQL from 5.7 (EOL) to 8.0.\n\n## Verification\n`nmap -p 3306 target.com` should return `filtered` or `closed`.",
        "false_positive_probability": 0.0,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nmap"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Directory Listing Enabled",
        "description": "The web server has directory listing enabled, exposing internal file structure and potentially sensitive files.",
        "severity": "medium",
        "cvss_score": 5.3,
        "cve_ids": [],
        "cwe_ids": ["CWE-548"],
        "affected_component": "http://target.com/uploads/",
        "evidence": "GET /uploads/ HTTP/1.1\nResponse: 200 OK\nContent: Index of /uploads/\nFiles visible: backup_2024.sql, config.bak, users.csv",
        "ai_triage_notes": "Directory listing reveals backup files including what appears to be a database dump (backup_2024.sql) and user data (users.csv). This likely constitutes a data breach scenario requiring immediate attention and possibly regulatory notification.",
        "ai_remediation": "## Immediate Action\nRemove exposed files and disable listing:\n```bash\nrm /var/www/html/uploads/backup_2024.sql\nrm /var/www/html/uploads/users.csv\n```\n\n## Disable Directory Listing (Nginx):\n```nginx\nautoindex off;\n```\n\n## Verification\n`curl http://target.com/uploads/` should return 403 Forbidden.",
        "false_positive_probability": 0.02,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nuclei"
    },
    {
        "id": str(uuid.uuid4()),
        "scan_id": DEMO_SCAN_ID,
        "title": "Sensitive File Exposed: .env",
        "description": "The application's .env file is publicly accessible, exposing database credentials, API keys, and secret keys.",
        "severity": "critical",
        "cvss_score": 9.9,
        "cve_ids": [],
        "cwe_ids": ["CWE-538"],
        "affected_component": "http://target.com/.env",
        "evidence": "GET /.env HTTP/1.1\nResponse: 200 OK\nContent:\nDB_PASSWORD=super_secret_123\nSTRIPE_SECRET_KEY=sk_live_...\nAPP_SECRET=...",
        "ai_triage_notes": "This is the most critical finding. Exposed .env file contains live payment API keys (Stripe), database credentials, and application secrets. This enables complete account takeover, data breach, and financial fraud. Treat all exposed credentials as compromised immediately.",
        "ai_remediation": "## IMMEDIATE — Do These Now\n1. Rotate ALL exposed credentials immediately (DB password, Stripe keys, all secrets)\n2. Check Stripe dashboard for unauthorized transactions\n3. Block access to .env at web server level\n\n## Block in Nginx:\n```nginx\nlocation ~ /\\.env {\n    deny all;\n    return 404;\n}\n```\n\n## Verification\n`curl http://target.com/.env` must return 404.",
        "false_positive_probability": 0.0,
        "is_false_positive": False,
        "delta_status": "new",
        "scanner_source": "nuclei"
    }
]

DEMO_SCAN = {
    "id": DEMO_SCAN_ID,
    "target": "http://demo-target.vulnai.local",
    "scope": ["demo-target.vulnai.local"],
    "status": "completed",
    "scan_types": ["port", "web", "nuclei", "headers", "ssl"],
    "authorisation_confirmed": True,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "summary": "This security assessment identified 8 findings across the target system, including 3 critical vulnerabilities requiring immediate remediation. Most critically, an exposed .env file containing live API credentials and a publicly accessible admin panel were discovered. A SQL injection vulnerability in the login form allows complete authentication bypass. The target system shows signs of security debt — multiple findings suggest fundamental secure development practices are not being followed. Immediate action is required to rotate all exposed credentials, patch the SQL injection, and restrict administrative interfaces. A follow-up scan is recommended within 7 days after remediation.",
    "total_findings": 8,
    "critical_count": 3,
    "high_count": 3,
    "medium_count": 2,
    "low_count": 0,
    "info_count": 0,
    "previous_scan_id": None
}


@router.get("/scan")
async def get_demo_scan():
    """Returns a pre-populated demo scan result."""
    return DEMO_SCAN


@router.get("/findings")
async def get_demo_findings():
    """Returns pre-populated demo findings with AI triage."""
    return DEMO_FINDINGS


@router.get("/summary")
async def get_demo_summary():
    """Returns demo scan statistics for dashboard."""
    return {
        "total_scans": 12,
        "total_findings": 47,
        "critical": 8,
        "high": 14,
        "medium": 18,
        "low": 7,
        "recent_scans": [
            {"target": "http://demo-target.vulnai.local", "status": "completed", "findings": 8, "date": "2024-06-14"},
            {"target": "http://api.demo-target.local", "status": "completed", "findings": 5, "date": "2024-06-12"},
            {"target": "192.168.1.0/24", "status": "completed", "findings": 12, "date": "2024-06-10"},
        ]
    }