import xml.etree.ElementTree as ET
from subprocess import PIPE, CalledProcessError, run
from typing import Any, Dict, List

from app.core.config import settings


class NmapScanner:
    def scan(self, target_scope: str, profile: str) -> str:
        profile_flags = settings.nmap_profile_map.get(profile, settings.nmap_default_profile)
        args = [
            "nmap",
            "-oX",
            "-",
            "-sV",
            profile_flags,
            target_scope,
        ]

        try:
            result = run(args, stdout=PIPE, stderr=PIPE, text=True, check=True)
            return result.stdout
        except CalledProcessError as exc:
            raise RuntimeError(f"Nmap scan failed: {exc.stderr.strip()}") from exc

    def parse(self, xml_output: str) -> List[Dict[str, Any]]:
        root = ET.fromstring(xml_output)
        findings = []

        for host in root.findall("host"):
            addresses = [addr.get("addr") for addr in host.findall("address") if addr.get("addr")]
            hostname = addresses[0] if addresses else "unknown"
            ports = host.find("ports")
            if ports is None:
                continue

            for port in ports.findall("port"):
                state = port.find("state")
                service = port.find("service")
                if state is None or state.get("state") != "open":
                    continue

                findings.append(
                    {
                        "host": hostname,
                        "port": int(port.get("portid", 0)),
                        "service": service.get("name") if service is not None else None,
                        "service_version": service.get("version") if service is not None else None,
                        "raw": {
                            "protocol": port.get("protocol"),
                            "state": state.get("state"),
                            "product": service.get("product") if service is not None else None,
                        },
                    }
                )

        return findings
