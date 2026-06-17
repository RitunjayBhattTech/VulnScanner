import asyncio
import logging
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.models.scan import Scan, Finding, ScanStatus
from backend.core.security import require_authorisation, write_audit_log
from backend.core.rate_limiter import global_rate_limiter
from backend.core.exceptions import ScopeViolationError, AuthorisationRequiredError
from backend.schemas.finding import RawFinding
from backend.ai.claude_client import llm_client
from backend.ai.rag_pipeline import rag_pipeline
from backend.ai.false_positive_filter import false_positive_filter
from backend.ai.triage_agent import triage_agent
from backend.ai.remediation_advisor import remediation_advisor
from backend.pipeline.delta_engine import DeltaEngine

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    """
    Main pipeline orchestration DAG:
    Pre-flight → Discovery → Enumeration → Detection → AI Processing → Delta → Summary → Finalise
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.delta_engine = DeltaEngine()
        self.tech_stack: List[str] = []
        self.scan_start_time: datetime = None

    async def run_scan(self, scan: Scan) -> None:
        """Execute the full scan pipeline."""
        self.scan_start_time = datetime.utcnow()

        try:
            # Step 0: Pre-flight checks
            await self._preflight(scan)

            # Step 1: Discovery - Port Scanner
            await self._discovery(scan)

            # Step 2: Web Surface Enumeration
            await self._enumeration(scan)

            # Step 3: Vulnerability Detection (parallel)
            raw_findings = await self._detection(scan)

            # Step 4: AI Processing
            processed_findings = await self._ai_processing(scan, raw_findings)

            # Step 5: Delta Analysis
            await self._delta_analysis(scan, processed_findings)

            # Step 6: Count findings by severity and update scan record
            await self._update_scan_counts(scan)

            # Step 7: Executive Summary
            await self._generate_summary(scan)

            # Step 8: Finalise
            await self._finalise(scan, None)

        except AuthorisationRequiredError as e:
            await self._finalise(scan, str(e))
            raise
        except Exception as e:
            logger.error(f"Scan pipeline failed for {scan.id}: {e}", exc_info=True)
            await self._finalise(scan, f"Pipeline error: {str(e)}")

    async def _update_scan_counts(self, scan: Scan):
        """Count findings by severity and update scan record."""
        logger.info(f"[Scan {scan.id}] Updating severity counts")

        try:
            # Fetch all findings from DB for this scan
            from backend.models.scan import Finding as FindingModel
            result = await self.db.execute(
                select(FindingModel).where(FindingModel.scan_id == scan.id)
            )
            all_findings = list(result.scalars().all())

            severity_counts = {
                'critical': 0, 'high': 0, 'medium': 0,
                'low': 0, 'informational': 0
            }

            for f in all_findings:
                sev = f.severity
                if hasattr(sev, 'value'):
                    sev = sev.value
                sev = str(sev).lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1

            # Update scan with counts
            scan.total_findings = len(all_findings)
            scan.critical_count = severity_counts['critical']
            scan.high_count = severity_counts['high']
            scan.medium_count = severity_counts['medium']
            scan.low_count = severity_counts['low']
            scan.info_count = severity_counts['informational']

            await self.db.commit()
            logger.info(f"[Scan {scan.id}] Counts saved: {len(all_findings)} total findings")

        except Exception as e:
            logger.error(f"[Scan {scan.id}] Failed to update severity counts: {e}")
            # Don't crash the scan on count failure

    async def _preflight(self, scan: Scan) -> None:
        """Pre-flight checks: authorisation and audit log."""
        logger.info(f"[Scan {scan.id}] Starting pre-flight checks")

        # Enforce authorisation gate
        require_authorisation(scan)

        # Write audit log
        await write_audit_log(
            self.db, scan.id, "scan_started", "system",
            {"target": scan.target, "scan_types": scan.scan_types, "scope": scan.scope}
        )

        # Update status to running
        scan.status = ScanStatus.running
        await self.db.commit()

        logger.info(f"[Scan {scan.id}] Pre-flight checks passed")

    async def _discovery(self, scan: Scan) -> None:
        """Discovery phase: port scanning."""
        if "port" not in scan.scan_types:
            logger.info(f"[Scan {scan.id}] Port scanning skipped (not in scan_types)")
            return

        logger.info(f"[Scan {scan.id}] Starting port discovery")
        from backend.scanners.port_scanner import PortScanner

        scanner = PortScanner(scan.id, scan.target, scan.scope, global_rate_limiter)
        findings = await scanner.run()

        if findings:
            await self._save_raw_findings(scan, findings)
            # Extract tech stack from port findings
            for f in findings:
                if f.affected_component:
                    self.tech_stack.append(f.affected_component.split(":")[-1] if ":" in f.affected_component else f.affected_component)

    async def _enumeration(self, scan: Scan) -> None:
        """Enumeration phase: web crawling."""
        if "web" not in scan.scan_types:
            logger.info(f"[Scan {scan.id}] Web crawling skipped (not in scan_types)")
            return

        logger.info(f"[Scan {scan.id}] Starting web enumeration")
        from backend.scanners.web_crawler import WebCrawler

        scanner = WebCrawler(scan.id, scan.target, scan.scope, global_rate_limiter)
        findings = await scanner.run()
        if findings:
            await self._save_raw_findings(scan, findings)
            if hasattr(scanner, 'crawl_result') and hasattr(scanner.crawl_result, 'technologies'):
                self.tech_stack.extend(scanner.crawl_result.technologies)

    async def _detection(self, scan: Scan) -> List[RawFinding]:
        """Detection phase: run vulnerability scanners in parallel."""
        all_findings = []
        tasks = []

        logger.info(f"[Scan {scan.id}] Starting vulnerability detection")

        # Nuclei (if requested)
        if "nuclei" in scan.scan_types:
            from backend.scanners.nuclei_runner import NucleiRunner
            tasks.append(NucleiRunner(scan.id, scan.target, scan.scope, global_rate_limiter).run())

        # Header analyzer
        if "header" in scan.scan_types:
            from backend.scanners.header_analyzer import HeaderAnalyzer
            tasks.append(HeaderAnalyzer(scan.id, scan.target, scan.scope, global_rate_limiter).run())

        # SSL checker
        if "ssl" in scan.scan_types:
            from backend.scanners.ssl_checker import SSLChecker
            tasks.append(SSLChecker(scan.id, scan.target, scan.scope, global_rate_limiter).run())

        # Semgrep
        if "semgrep" in scan.scan_types:
            from backend.scanners.semgrep_runner import SemgrepRunner
            tasks.append(SemgrepRunner(scan.id, scan.target, scan.scope, global_rate_limiter).run())

        # Run all in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scanner error: {result}")
                elif isinstance(result, list):
                    all_findings.extend(result)

        # Normalize: convert dicts to RawFinding if any scanner returned plain dicts
        normalized = []
        for f in all_findings:
            if isinstance(f, dict):
                normalized.append(RawFinding(
                    title=f.get('title', 'Unknown'),
                    description=f.get('description', ''),
                    severity=f.get('severity', 'informational'),
                    cvss_score=f.get('cvss_score'),
                    affected_component=f.get('affected_component', ''),
                    evidence=f.get('evidence', ''),
                    scanner_source=f.get('scanner_source', 'unknown'),
                    cve_ids=f.get('cve_ids', []),
                    cwe_ids=f.get('cwe_ids', []),
                ))
            else:
                normalized.append(f)
        all_findings = normalized

        # Deduplicate by title + affected_component
        seen = set()
        unique_findings = []
        for f in all_findings:
            key = (f.title.lower(), (f.affected_component or "").lower())
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        logger.info(f"[Scan {scan.id}] Detection complete: {len(unique_findings)} raw findings")
        return unique_findings

    async def _ai_processing(self, scan: Scan, raw_findings: List[RawFinding]) -> List[Finding]:
        """AI processing phase: false positive filter, triage, and remediation."""
        logger.info(f"[Scan {scan.id}] Starting AI processing ({len(raw_findings)} findings)")

        processed = []
        semaphore = asyncio.Semaphore(5)

        scan_context = {
            "exposure": "internet-facing" if "http" in scan.target else "unknown",
            "authenticated": False,
            "previous_count": 0,
        }

        async def process_finding(raw: RawFinding):
            async with semaphore:
                try:
                    fp_prob, fp_reasoning = await false_positive_filter.assess(raw)

                    finding = Finding(
                        scan_id=scan.id,
                        title=raw.title,
                        description=raw.description,
                        severity=raw.severity,
                        cvss_score=raw.cvss_score,
                        cve_ids=raw.cve_ids,
                        cwe_ids=raw.cwe_ids,
                        affected_component=raw.affected_component,
                        evidence=raw.evidence,
                        scanner_source=raw.scanner_source,
                        false_positive_probability=fp_prob,
                        is_false_positive=(fp_prob >= 0.8),
                        created_at=datetime.utcnow(),
                    )

                    if fp_prob < 0.8:
                        triaged = await triage_agent.triage_finding(raw, scan_context)
                        if triaged:
                            finding.ai_triage_notes = triaged.ai_triage_notes
                            finding.ai_remediation = await remediation_advisor.generate_remediation(
                                triaged, self.tech_stack
                            )
                            finding.severity = triaged.adjusted_severity

                    return finding

                except Exception as e:
                    logger.error(f"AI processing error for finding '{raw.title}': {e}")
                    return Finding(
                        scan_id=scan.id,
                        title=raw.title,
                        description=raw.description,
                        severity=raw.severity,
                        cvss_score=raw.cvss_score,
                        cve_ids=raw.cve_ids,
                        cwe_ids=raw.cwe_ids,
                        affected_component=raw.affected_component,
                        evidence=raw.evidence,
                        scanner_source=raw.scanner_source,
                        created_at=datetime.utcnow(),
                    )

        tasks = [process_finding(rf) for rf in raw_findings]
        processed = await asyncio.gather(*tasks)

        self.db.add_all(processed)
        await self.db.commit()

        logger.info(f"[Scan {scan.id}] AI processing complete: {len(processed)} findings processed")
        return processed

    async def _delta_analysis(self, scan: Scan, current_findings: List[Finding]):
        """Delta analysis: compare with previous scan if available."""
        if not scan.previous_scan_id:
            logger.info(f"[Scan {scan.id}] No previous scan for delta analysis")
            return

        logger.info(f"[Scan {scan.id}] Running delta analysis against {scan.previous_scan_id}")

        from backend.models.scan import Finding as FindingModel
        from sqlalchemy import select

        result = await self.db.execute(
            select(FindingModel).where(FindingModel.scan_id == scan.previous_scan_id)
        )
        previous_findings = list(result.scalars().all())

        if not previous_findings:
            logger.info(f"[Scan {scan.id}] No previous findings found for delta analysis")
            return

        delta_findings = self.delta_engine.compare(current_findings, previous_findings)

        for df in delta_findings:
            if df.delta_status:
                for cf in current_findings:
                    if (cf.title == df.title and
                        cf.affected_component == df.affected_component):
                        cf.delta_status = df.delta_status

        await self.db.commit()
        logger.info(f"[Scan {scan.id}] Delta analysis complete")

    async def _generate_summary(self, scan: Scan):
        """Generate AI executive summary."""
        try:
            # Count findings by severity using Python (not DB queries that need greenlet)
            critical = [f for f in scan.findings if f.severity == "critical"]
            high = [f for f in scan.findings if f.severity == "high"]
            medium = [f for f in scan.findings if f.severity == "medium"]
            low = [f for f in scan.findings if f.severity == "low"]
            info = [f for f in scan.findings if f.severity == "informational"]

            new_count = len([f for f in scan.findings if f.delta_status == "new"])
            fixed_count = len([f for f in scan.findings if f.delta_status == "fixed"])
            regressed_count = len([f for f in scan.findings if f.delta_status == "regressed"])

            top_findings = critical[:3] if critical else high[:3]
            top_findings_text = "\n".join([
                f"  - [{f.severity.upper()}] {f.title} ({f.affected_component})"
                for f in top_findings
            ]) or "  - None"

            duration_min = 0
            if self.scan_start_time:
                duration = datetime.utcnow() - self.scan_start_time
                duration_min = round(duration.total_seconds() / 60, 1)

            prompt_path = "backend/ai/prompts/report_summary_prompt.txt"
            try:
                with open(prompt_path) as pf:
                    prompt_template = pf.read()
            except FileNotFoundError:
                prompt_template = "Generate a concise executive summary for the scan of {target}."

            prompt = prompt_template.format(
                target=scan.target,
                total_findings=len(scan.findings),
                critical_count=len(critical),
                high_count=len(high),
                medium_count=len(medium),
                low_count=len(low),
                info_count=len(info),
                top_findings=top_findings_text,
                new_count=new_count,
                fixed_count=fixed_count,
                regressed_count=regressed_count,
                duration=f"{duration_min} min",
                scanners=", ".join(scan.scan_types) if scan.scan_types else "standard",
            )

            response = await llm_client.complete(
                system="You are a senior security analyst generating an executive summary.",
                user=prompt,
                max_tokens=1024,
            )

            if response:
                scan.summary = response
                await self.db.commit()

        except Exception as e:
            logger.error(f"Summary generation error: {e}")

    async def _save_raw_findings(self, scan: Scan, findings: List[RawFinding]):
        """Save raw findings as Finding records."""
        for rf in findings:
            finding = Finding(
                scan_id=scan.id,
                title=rf.title,
                description=rf.description,
                severity=rf.severity,
                cvss_score=rf.cvss_score,
                cve_ids=rf.cve_ids,
                cwe_ids=rf.cwe_ids,
                affected_component=rf.affected_component,
                evidence=rf.evidence,
                scanner_source=rf.scanner_source,
                created_at=datetime.utcnow(),
            )
            self.db.add(finding)
        await self.db.commit()

    async def _finalise(self, scan: Scan, error: str = None):
        """Finalise the scan: set status, write audit log."""
        if error:
            scan.status = ScanStatus.failed
            await write_audit_log(
                self.db, scan.id, "scan_failed", "system",
                {"error": error}
            )
        else:
            scan.status = ScanStatus.completed
            scan.completed_at = datetime.utcnow()
            await write_audit_log(
                self.db, scan.id, "scan_completed", "system",
                {
                    "total_findings": scan.total_findings or 0,
                    "critical_count": scan.critical_count or 0,
                    "high_count": scan.high_count or 0,
                }
            )

        await self.db.commit()
        status = "completed" if not error else "failed"
        logger.info(f"[Scan {scan.id}] Scan {status}")