#!/usr/bin/env python3
import urllib.request, json

BASE = "http://localhost:8000/api/v1"

sid = 11
s = json.loads(urllib.request.urlopen(f"{BASE}/scans/{sid}").read())
print(f"Scan #{sid}: status={s['status']}")

f = json.loads(urllib.request.urlopen(f"{BASE}/scans/{sid}/findings").read())
print(f"Findings: {len(f)}")
for x in f:
    print(f"  {x['host']}:{x.get('port','?')} {x.get('service','?')}")
    print(f"    severity={x.get('ai_severity','?')} cvss={x.get('ai_cvss_score','?')}")
    fp = x.get('ai_false_positive_reasoning')
    exp = x.get('ai_exploitation_notes')
    if fp: print(f"    FP: {fp[:150]}")
    if exp: print(f"    Exploit: {exp[:150]}")

c = json.loads(urllib.request.urlopen(f"{BASE}/scans/{sid}/chains").read())
print(f"Chains: {len(c)}")
for ch in c:
    print(f"  {ch['chain_description'][:100]}")
    print(f"    severity={ch.get('severity','?')} likelihood={ch.get('likelihood','?')} mitre={ch.get('mitre_technique_id','?')}")