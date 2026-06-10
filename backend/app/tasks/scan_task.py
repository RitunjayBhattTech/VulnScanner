from typing import Any, Dict
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import sync_session
from app.db.models import Scan, Finding, AttackChain, AuditLog
from app.services.nmap_service import NmapScanner
from app.services.ollama_service import OllamaClient
from app.services.rag_service import RagService

logger = get_task_logger(__name__)


def _update_scan_status(scan_id: int, status: str) -> None:
    """Update scan status in the database."""
    with sync_session() as session:
        scan = session.get(Scan, scan_id)
        if scan:
            scan.status = status
            session.commit()


def _persist_findings_and_chains(
    scan_id: int,
    findings: list,
    analysis: dict,
) -> None:
    """Save findings, AI analysis, and attack chains to database."""
    with sync_session() as session:
        scan = session.get(Scan, scan_id)
        if not scan:
            logger.error("Scan %s not found", scan_id)
            return

        # Track finding IDs for chain references
        finding_id_map: Dict[str, int] = {}

        for finding in analysis.get("findings", findings):
            db_finding = Finding(
                scan_id=scan_id,
                host=finding["host"],
                port=finding.get("port"),
                service=finding.get("service"),
                raw_data=finding,
                ai_severity=finding.get("ai_severity", "medium"),
                ai_cvss_score=finding.get("ai_cvss_score"),
                ai_false_positive_reasoning=finding.get("ai_false_positive_reasoning"),
                ai_exploitation_notes=finding.get("ai_exploitation_notes"),
                false_positive=False,
            )
            session.add(db_finding)
            session.flush()
            key = f"{finding['host']}:{finding.get('port', 0)}"
            finding_id_map[key] = db_finding.id

        # Persist attack chains
        chains = analysis.get("attack_chains", [])
        for chain in chains:
            steps = chain.get("steps", [])
            resolved_steps = []
            for step in steps:
                if isinstance(step, str) and ":" in step:
                    resolved_steps.append(step)
                elif isinstance(step, str):
                    related = [
                        {"finding_id": fid, "host": k.split(":")[0], "port": int(k.split(":")[1]) if ":" in k else None}
                        for k, fid in finding_id_map.items()
                        if k.startswith(step)
                    ]
                    resolved_steps.extend(related if related else [{"host": step}])
                else:
                    resolved_steps.append(step)

            db_chain = AttackChain(
                scan_id=scan_id,
                chain_description=chain.get("chain_description", ""),
                steps=resolved_steps or steps,
                severity=chain.get("severity", "medium"),
                likelihood=chain.get("likelihood", "medium"),
                mitre_technique_id=chain.get("mitre_technique_id"),
            )
            session.add(db_chain)

        session.commit()
        logger.info(
            "Persisted %s findings and %s attack chains for scan %s",
            len(analysis.get("findings", findings)),
            len(chains),
            scan_id,
        )


def _log_audit(scan_id: int, action: str, target_scope: str, status: str) -> None:
    """Log scan action to audit table."""
    with sync_session() as session:
        audit = AuditLog(
            scan_id=scan_id,
            user="system",
            target_scope=target_scope,
            action=action,
            status=status,
        )
        session.add(audit)
        session.commit()
        logger.info("Logged audit: scan %s - %s - %s", scan_id, action, status)


@celery_app.task(bind=True)
def run_scan(self, scan_id: int, target_scope: str, profile: str, authorized: bool) -> dict:
    if not authorized:
        error_msg = "Scan must be authorized before execution."
        logger.error("Scan %s rejected: not authorized", scan_id)
        _log_audit(scan_id, "scan_rejected", target_scope, "unauthorized")
        raise ValueError(error_msg)

    try:
        logger.info("Starting scan job %s for target %s", scan_id, target_scope)
        _update_scan_status(scan_id, "running")
        _log_audit(scan_id, "scan_started", target_scope, "running")

        # Run nmap scan
        nmap = NmapScanner()
        xml_output = nmap.scan(target_scope, profile)
        findings = nmap.parse(xml_output)
        logger.info("Nmap scan completed with %s findings", len(findings))

        if len(findings) == 0:
            # No findings — skip AI analysis, complete immediately
            analysis = {
                "findings": [],
                "attack_chains": [],
            }
            logger.info("No findings — skipping AI analysis")
        else:
            # Get RAG context
            rag = RagService()
            cve_context = rag.index_findings(findings)

            # AI analysis via Ollama
            llm = OllamaClient(base_url=settings.ollama_url)
            analysis = llm.analyze_findings(findings, cve_context=cve_context)
            logger.info(
                "AI analysis completed: %s enriched findings, %s attack chains",
                len(analysis.get("findings", [])),
                len(analysis.get("attack_chains", [])),
            )

        # Persist findings + attack chains to database (sync)
        _persist_findings_and_chains(scan_id, findings, analysis)
        _update_scan_status(scan_id, "completed")
        _log_audit(scan_id, "scan_completed", target_scope, "success")

        logger.info("Scan job %s completed successfully with %s findings", scan_id, len(findings))

        return {
            "scan_id": scan_id,
            "target_scope": target_scope,
            "profile": profile,
            "finding_count": len(findings),
            "chain_count": len(analysis.get("attack_chains", [])),
            "status": "completed",
        }

    except Exception as e:
        logger.error("Scan job %s failed: %s", scan_id, str(e), exc_info=True)
        _update_scan_status(scan_id, "failed")
        _log_audit(scan_id, "scan_failed", target_scope, f"error: {str(e)}")
        raise