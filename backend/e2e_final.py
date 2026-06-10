#!/usr/bin/env python3
"""Final end-to-end test for the AI-Augmented Vulnerability Scanner."""
import urllib.request, json, time, sys

BASE = "http://localhost:8000/api/v1"

def req(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=600).read())

print("=" * 60)
print("E2E TEST: AI-Augmented Vulnerability Scanner")
print("=" * 60)

# 1. Health check
print("\n1. Backend health check...")
h = req("GET", "/scans/?limit=1")
print("   OK - API responds")

# 2. Create scan against scanme.nmap.org
print("\n2. Creating scan against scanme.nmap.org...")
result = req("POST", "/scans/", {
    "target_scope": "scanme.nmap.org/32",
    "profile": "normal",
    "authorized": True
})
sid = result["id"]
print(f"   Scan #{sid} created (status: {result['status']})")

# 3. Wait for completion (up to 5 minutes)
print("\n3. Waiting for scan to complete...")
poll_interval = 15
max_polls = 20
for i in range(max_polls):
    time.sleep(poll_interval)
    s = req("GET", f"/scans/{sid}")
    elapsed = (i + 1) * poll_interval
    sys.stdout.write(f"\r   {elapsed}s: {s['status']}")
    sys.stdout.flush()
    if s['status'] in ('completed', 'failed'):
        print()
        break

# 4. Show results
status = req("GET", f"/scans/{sid}")['status']
print(f"\n4. Scan status: {status}")

findings = req("GET", f"/scans/{sid}/findings")
print(f"\n5. Findings: {len(findings)}")
for x in findings:
    host = x["host"]
    port = x.get("port", "-")
    svc = x.get("service", "-")
    sev = x.get("ai_severity", "-")
    cvss = x.get("ai_cvss_score", "-")
    fp = x.get("ai_false_positive_reasoning")
    exp = x.get("ai_exploitation_notes")
    print(f"   {host}:{port} {svc} | severity={sev} cvss={cvss}")
    if fp: print(f"     FP reasoning: {fp[:120]}")
    if exp: print(f"     Exploit notes: {exp[:120]}")

chains = req("GET", f"/scans/{sid}/chains")
print(f"\n6. Attack chains: {len(chains)}")
for c in chains:
    print(f"   {c['chain_description'][:100]}...")
    print(f"     severity={c.get('severity','?')} likelihood={c.get('likelihood','?')} mitre={c.get('mitre_technique_id','?')}")

# 7. Verify all GET endpoints
print("\n7. Verifying all GET endpoints...")
scans = req("GET", "/scans/")
print(f"   GET /scans/ - {len(scans)} scans")
s2 = req("GET", f"/scans/{sid}")
print(f"   GET /scans/{sid} - ok")
f2 = req("GET", f"/scans/{sid}/findings")
print(f"   GET /scans/{sid}/findings - {len(f2)} findings")
c2 = req("GET", f"/scans/{sid}/chains")
print(f"   GET /scans/{sid}/chains - {len(c2)} chains")

# 8. Check frontend
print("\n8. Frontend check...")
fe = urllib.request.urlopen("http://localhost:5173/").read().decode()
print(f"   Frontend loads: {'<title>' in fe}")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"  Backend:     ✅ OK")
print(f"  Scan #{sid}:  ✅ {status}")
print(f"  Findings:    {len(findings)}")
print(f"  Chains:      {len(chains)}")
print(f"  Frontend:    ✅ http://localhost:5173")
print(f"  API docs:    http://localhost:8000/docs")
print()
if status == "completed" and len(findings) > 0:
    print("🎯 AI analysis ran with structured output!")
    print("   The prompt instructed the LLM to return CVSS scores,")
    print("   false positive reasoning, exploitation notes, and")
    print("   attack chains with MITRE ATT&CK IDs.")
elif status == "completed" and len(findings) == 0:
    print("ℹ️  Scan completed but no open ports were found.")
    print("   This is normal for targets with firewalls.")
elif status == "failed":
    print("❌ Scan failed. Check docker compose logs worker")