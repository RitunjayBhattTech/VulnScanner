import io
import logging
from datetime import datetime
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

from backend.models.scan import Scan, Finding, AuditLog

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generates PDF reports for scan results using ReportLab."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Title'],
            fontSize=28,
            leading=34,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a2e'),
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=18,
            spaceAfter=10,
            textColor=colors.HexColor('#4a4a6a'),
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=22,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#16213e'),
        ))
        self.styles.add(ParagraphStyle(
            name='FindingTitle',
            parent=self.styles['Heading2'],
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#0f3460'),
        ))
        self.styles.add(ParagraphStyle(
            name='Mono',
            parent=self.styles['Code'],
            fontSize=8,
            leading=10,
            fontName='Courier',
            spaceBefore=4,
            spaceAfter=4,
        ))

    async def generate(self, scan: Scan, findings: List[Finding], audit_logs: List[AuditLog]) -> bytes:
        """Generate PDF report bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20*mm,
            bottomMargin=20*mm,
            leftMargin=15*mm,
            rightMargin=15*mm,
        )

        story = []

        # Cover page
        self._build_cover(story, scan)

        # Executive Summary
        self._build_executive_summary(story, scan)

        # Findings Overview
        self._build_findings_overview(story, scan, findings)

        # Critical & High Findings (detailed)
        self._build_critical_high_findings(story, findings)

        # Medium & Low Findings (summary table)
        self._build_medium_low_findings(story, findings)

        # Appendix: Audit Log
        self._build_audit_log(story, audit_logs)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_cover(self, story: list, scan: Scan):
        """Build the cover page."""
        story.append(Spacer(1, 80*mm))
        story.append(Paragraph("VulnAI Scanner", self.styles['CoverTitle']))
        story.append(Paragraph("Security Assessment Report", self.styles['CoverSubtitle']))
        story.append(Spacer(1, 20*mm))

        cover_data = [
            ["Target:", scan.target],
            ["Scan ID:", scan.id[:8] + "..."],
            ["Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
            ["Status:", scan.status.upper()],
            ["Scanners:", ", ".join(scan.scan_types) if scan.scan_types else "N/A"],
        ]

        t = Table(cover_data, colWidths=[100, 300])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 30*mm))

        # Disclaimer
        story.append(Paragraph(
            "<b>CONFIDENTIAL</b> — This report contains security assessment findings "
            "for authorised recipients only. Unauthorised distribution is prohibited.",
            ParagraphStyle('Disclaimer', parent=self.styles['Normal'],
                          fontSize=8, textColor=colors.grey,
                          alignment=1)  # Center
        ))
        story.append(PageBreak())

    def _build_executive_summary(self, story: list, scan: Scan):
        """Build the executive summary section."""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 5*mm))

        if scan.summary:
            story.append(Paragraph(scan.summary, self.styles['Normal']))
        else:
            story.append(Paragraph(
                f"Scan of {scan.target} completed with {scan.total_findings} total findings. "
                f"Critical: {scan.critical_count}, High: {scan.high_count}, "
                f"Medium: {scan.medium_count}, Low: {scan.low_count}.",
                self.styles['Normal']
            ))

        # Severity summary table
        summary_data = [
            ["Severity", "Count"],
            ["Critical", str(scan.critical_count)],
            ["High", str(scan.high_count)],
            ["Medium", str(scan.medium_count)],
            ["Low", str(scan.low_count)],
            ["Informational", str(scan.info_count)],
            ["Total", str(scan.total_findings)],
        ]

        t = Table(summary_data, colWidths=[100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#ffdddd')),
            ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#fff3cd')),
            ('BACKGROUND', (1, 5), (1, 5), colors.HexColor('#e8e8e8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(Spacer(1, 5*mm))
        story.append(t)
        story.append(PageBreak())

    def _build_findings_overview(self, story: list, scan: Scan, findings: List[Finding]):
        """Build findings overview with counts by scanner."""
        story.append(Paragraph("Findings Overview", self.styles['SectionHeader']))
        story.append(Spacer(1, 5*mm))

        # Count by scanner
        scanner_counts = {}
        for f in findings:
            src = f.scanner_source or "unknown"
            scanner_counts[src] = scanner_counts.get(src, 0) + 1

        scanner_data = [["Scanner", "Findings"]]
        for scanner, count in scanner_counts.items():
            scanner_data.append([scanner, str(count)])

        t = Table(scanner_data, colWidths=[150, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 10*mm))

        # Delta summary
        new_count = len([f for f in findings if f.delta_status == "new"])
        fixed_count = len([f for f in findings if f.delta_status == "fixed"])
        regressed_count = len([f for f in findings if f.delta_status == "regressed"])
        existing_count = len([f for f in findings if f.delta_status == "existing"])

        delta_data = [
            ["Delta Status", "Count"],
            ["New", str(new_count)],
            ["Fixed", str(fixed_count)],
            ["Regressed", str(regressed_count)],
            ["Existing", str(existing_count)],
        ]

        t = Table(delta_data, colWidths=[150, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(Paragraph("Delta Analysis", self.styles['Heading2']))
        story.append(t)
        story.append(PageBreak())

    def _build_critical_high_findings(self, story: list, findings: List[Finding]):
        """Build detailed section for critical and high findings."""
        critical_high = [f for f in findings if f.severity in ("critical", "high") and not f.is_false_positive]
        if not critical_high:
            return

        story.append(Paragraph("Critical & High Findings", self.styles['SectionHeader']))
        story.append(Spacer(1, 5*mm))

        for finding in critical_high:
            # Severity badge
            badge_color = colors.HexColor('#dc3545') if finding.severity == "critical" else colors.HexColor('#fd7e14')
            story.append(Paragraph(
                f'<font color="{badge_color.hexval()}">■</font> '
                f'<b>{finding.title}</b>',
                self.styles['FindingTitle']
            ))

            # Finding details table
            detail_data = [
                ["Severity", finding.severity.upper()],
                ["Component", finding.affected_component or "N/A"],
                ["Scanner", finding.scanner_source or "N/A"],
            ]
            if finding.cvss_score:
                detail_data.append(["CVSS Score", str(finding.cvss_score)])
            if finding.cve_ids:
                detail_data.append(["CVE IDs", ", ".join(finding.cve_ids) if isinstance(finding.cve_ids, list) else str(finding.cve_ids)])
            if finding.delta_status:
                detail_data.append(["Delta", finding.delta_status.upper()])

            t = Table(detail_data, colWidths=[80, 270])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(t)

            # Description
            if finding.description:
                story.append(Paragraph(
                    f"<b>Description:</b> {finding.description}",
                    self.styles['Normal']
                ))

            # Evidence (truncated at 500 chars)
            if finding.evidence:
                evidence = finding.evidence[:500] + ("..." if len(finding.evidence) > 500 else "")
                story.append(Paragraph(
                    f"<b>Evidence:</b><br/><font face='Courier' size='8'>{evidence}</font>",
                    self.styles['Normal']
                ))

            # AI Triage Notes
            if finding.ai_triage_notes:
                story.append(Paragraph(
                    f"<b>AI Triage:</b> {finding.ai_triage_notes}",
                    self.styles['Normal']
                ))

            # Remediation
            if finding.ai_remediation:
                story.append(Paragraph(
                    f"<b>Remediation:</b><br/>{finding.ai_remediation}",
                    self.styles['Normal']
                ))

            story.append(Spacer(1, 8*mm))

    def _build_medium_low_findings(self, story: list, findings: List[Finding]):
        """Build summary table for medium and low findings."""
        medium_low = [f for f in findings if f.severity in ("medium", "low")]
        if not medium_low:
            return

        story.append(Paragraph("Medium & Low Findings", self.styles['SectionHeader']))
        story.append(Spacer(1, 5*mm))

        data = [["Title", "Severity", "Component", "Scanner"]]
        for f in medium_low[:50]:  # Limit to 50 entries
            data.append([
                f.title[:60],
                f.severity.upper(),
                (f.affected_component or "-")[:30],
                f.scanner_source or "-",
            ])

        t = Table(data, colWidths=[160, 60, 100, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t)

        if len(medium_low) > 50:
            story.append(Paragraph(
                f"<i>... and {len(medium_low) - 50} more medium/low findings</i>",
                self.styles['Normal']
            ))

    def _build_audit_log(self, story: list, audit_logs: List[AuditLog]):
        """Build the audit log appendix."""
        if not audit_logs:
            return

        story.append(PageBreak())
        story.append(Paragraph("Appendix: Audit Log", self.styles['SectionHeader']))
        story.append(Spacer(1, 5*mm))

        data = [["Timestamp", "Action", "Actor", "Details"]]
        for log in audit_logs[:100]:
            details_str = str(log.details or "")[:40]
            data.append([
                log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-",
                log.action[:30],
                log.actor[:20],
                details_str,
            ])

        t = Table(data, colWidths=[80, 100, 60, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t)