#!/usr/bin/env python3
import urllib.request, json

BASE = "http://localhost:8000/api/v1"

s = json.loads(urllib.request.urlopen(f"{BASE}/scans/9").read())
print(f"Status: {s['status']}")

f = json.loads(urllib.request.urlopen(f"{BASE}/scans/9/findings").read())
print(f"Findings: {len(f)}")
for x in f:
    host = x["host"]
    port = x.get("port", "?")
    svc = x.get("service", "?")
    sev = x.get("ai_severity", "?")
    cvss = x.get("ai_cvss_score", "?")
    fp = x.get("ai_false_positive_reasoning", "")
    exp = x.get("ai_exploitation_notes", "")
    print(f"  {host}:{port} {svc} | severity={sev} cvss={cvss}")
    if fp: print(f"    FP: {fp[:120]}")
    if exp: print(f"    Exploit: {exp[:120]}")

c = json.loads(urllib.request.urlopen(f"{BASE}/scans/9/chains").read())
print(f"Chains: {len(c)}")
for ch in c:
    print(f"  {ch['chain_description'][:100]} | severity={ch.get('severity','?')} likelihood={ch.get('likelihood','?')}")
    if ch.get('mitre_technique_id'):
        print(f"    MITRE: {ch['mitre_technique_id']}")

print(f"\nDashboard: http://localhost:5173")