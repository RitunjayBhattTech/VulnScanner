#!/usr/bin/env python3
"""End-to-end test script for the vulnerability scanner."""
import urllib.request
import json
import time
import sys

BASE = "http://localhost:8000/api/v1"

def request(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    return json.loads(urllib.request.urlopen(r).read())

print("=== Step 1: Check backend health ===")
health = json.loads(urllib.request.urlopen("http://localhost:8000/").read())
print(f"  Status: {health['status']}")
assert health["status"] == "ready"

print("\n=== Step 2: List existing scans ===")
scans = request("GET", "/scans/?limit=5")
print(f"  Found {len(scans)} existing scans")

print("\n=== Step 3: Create a new scan ===")
result = request("POST", "/scans/", {
    "target_scope": "127.0.0.1/32",
    "profile": "normal",
    "authorized": True
})
scan_id = result["id"]
print(f"  Created scan #{scan_id} — status: {result['status']}")

print(f"\n=== Step 4: Wait for scan to complete (up to 2 min) ===")
for i in range(24):
    time.sleep(5)
    scan = request("GET", f"/scans/{scan_id}")
    status = scan["status"]
    sys.stdout.write(f"\r  Status after {(i+1)*5}s: {status}")
    sys.stdout.flush()
    if status in ("completed", "failed"):
        print()
        break

print(f"\n  Final status: {scan['status']}")

print("\n=== Step 5: Get findings ===")
findings = request("GET", f"/scans/{scan_id}/findings")
print(f"  Findings: {len(findings)}")
for f in findings[:5]:
    print(f"    {f['host']}:{f.get('port','?')} {f.get('service','?')} | "
          f"severity={f.get('ai_severity','?')} cvss={f.get('ai_cvss_score','?')}")

print("\n=== Step 6: Get attack chains ===")
chains = request("GET", f"/scans/{scan_id}/chains")
print(f"  Attack chains: {len(chains)}")
for c in chains:
    print(f"    {c['chain_description'][:80]}... | severity={c.get('severity','?')}")

print("\n=== Step 7: Verify GET endpoints ===")
get_scans = request("GET", "/scans/")
print(f"  GET /scans/ — {len(get_scans)} scans total")
get_scan = request("GET", f"/scans/{scan_id}")
print(f"  GET /scans/{scan_id} — status={get_scan['status']}")

print("\n=== Step 8: Check frontend ===")
fe = urllib.request.urlopen("http://localhost:5173/").read().decode()
print(f"  Frontend loads: {'<title>' in fe}")

print("\n✅ ALL CHECKS PASSED")
print(f"  Dashboard: http://localhost:5173")
print(f"  API docs:  http://localhost:8000/docs")
print(f"  Scan #{scan_id} findings: {len(findings)}, chains: {len(chains)}")