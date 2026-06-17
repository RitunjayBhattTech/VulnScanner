import io
import logging
import re
from datetime import datetime
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String

from backend.models.scan import Scan, Finding, AuditLog

logger = logging.getLogger(__name__)

# Page dimensions
PAGE_W, PAGE_H = letter  # 612 x 792 points
MARGIN = 72  # 1 inch margins

# Severity color palette
SEV_COLORS = {
    "critical": colors.HexColor("#dc2626"),
    "high": colors.HexColor("#ea580c"),
    "medium": colors.HexColor("#ca8a04"),
    "low": colors.HexColor("#2563eb"),
    "informational": colors.HexColor("#6b7280"),
}


class PDFGenerator:
    """Generates professional PDF security assessment reports using ReportLab."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Define a consistent stylesheet for all PDF content."""
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Title'],
            fontSize=24,
            leading=30,
            spaceAfter=6,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=18,
            spaceAfter=4,
            textColor=colors.HexColor('#4a4a6a'),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=22,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#16213e'),
        ))
        self.styles.add(ParagraphStyle(
            name='FindingNumber',
            parent=self.styles['Heading2'],
            fontSize=13,
            leading=16,
            spaceBefore=14,
            spaceAfter=4,
            textColor=colors.HexColor('#0f3460'),
        ))
        self.styles.add(ParagraphStyle(
            name='Body',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=2,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            name='ItalicBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=2,
            spaceAfter=6,
            fontName='Helvetica-Oblique',
        ))
        self.styles.add(ParagraphStyle(
            name='Mono',
            parent=self.styles['Code'],
            fontSize=8,
            leading=10,
            fontName='Courier',
            spaceBefore=4,
            spaceAfter=4,
            leftIndent=8,
        ))
        self.styles.add(ParagraphStyle(
            name='BadgeText',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='FooterText',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='SmallGray',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#aaaaaa'),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.white,
            fontName='Helvetica-Bold',
        ))

    # ---------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ---------------------------------------------------------------
    async def generate(self, scan: Scan, findings: List[Finding], audit_logs: List[AuditLog]) -> bytes:
        """Generate the full PDF report. Wraps everything in try/except for resilience."""
        try:
            return self._build_report(scan, findings, audit_logs)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            return self._build_error_pdf(str(e))

    def _build_report(self, scan: Scan, findings: List[Finding], audit_logs: List[AuditLog]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
        )

        story = []

        # Page 1: Cover page
        self._build_cover(story, scan)
        story.append(PageBreak())

        # Page 2: Executive Summary
        self._build_executive_summary(story, scan)
        story.append(PageBreak())

        # Pages 3+: Detailed Findings (ALL findings)
        self._build_detailed_findings(story, findings)
        story.append(PageBreak())

        # Last Page: Appendix
        self._build_appendix(story, audit_logs)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_error_pdf(self, error_msg: str) -> bytes:
        """Build a minimal 1-page error PDF when generation fails."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
        )
        story = []
        story.append(Spacer(1, 80))
        story.append(Paragraph("VulnAI Security Assessment Report", self.styles['CoverTitle']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("PDF Generation Error", self.styles['SectionHeader']))
        story.append(Paragraph(
            f"The report could not be generated due to an error: {error_msg}",
            self.styles['Body']
        ))
        story.append(Paragraph("Please try again or contact support.", self.styles['Body']))
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # ---------------------------------------------------------------
    # PAGE 1 — COVER PAGE
    # ---------------------------------------------------------------
    def _build_cover(self, story: list, scan: Scan):
        story.append(Spacer(1, 100))

        story.append(Paragraph("VulnAI Security Assessment Report", self.styles['CoverTitle']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Target: {self._safe(scan.target)}", self.styles['CoverSubtitle']))
        story.append(Spacer(1, 6))

        comp_date = scan.completed_at or scan.created_at
        date_str = comp_date.strftime("%B %d, %Y") if comp_date else "Unknown"
        story.append(Paragraph(f"Date: {date_str}", self.styles['CoverSubtitle']))
        story.append(Spacer(1, 4))

        story.append(Paragraph(f"Scan ID: {self._safe(scan.id)}", self.styles['SmallGray']))
        story.append(Spacer(1, 30))

        # Severity breakdown bar
        story.append(self._build_severity_bar(scan))
        story.append(Spacer(1, 60))

        # Footer
        story.append(Paragraph(
            "Generated by VulnAI Scanner \u2014 For Authorised Use Only",
            self.styles['FooterText']
        ))

    def _build_severity_bar(self, scan: Scan) -> Drawing:
        """Build a horizontal colored bar showing severity count breakdown."""
        d = Drawing(468, 50)
        counts = [
            scan.critical_count or 0,
            scan.high_count or 0,
            scan.medium_count or 0,
            scan.low_count or 0,
            scan.info_count or 0,
        ]
        total = sum(counts)
        if total == 0:
            total = 1

        bar_width = 468
        x_pos = 0
        colors_list = [
            colors.HexColor("#dc2626"),
            colors.HexColor("#ea580c"),
            colors.HexColor("#ca8a04"),
            colors.HexColor("#2563eb"),
            colors.HexColor("#6b7280"),
        ]
        labels = ["Critical", "High", "Medium", "Low", "Info"]

        for i, count in enumerate(counts):
            if count == 0:
                continue
            seg_width = max(bar_width * (count / total), 4)
            rect = Rect(x_pos, 0, seg_width, 20, fillColor=colors_list[i], strokeColor=None)
            d.add(rect)
            if seg_width > 30:
                d.add(String(x_pos + seg_width / 2, 10, str(count),
                             textAnchor='middle', fontSize=9, fillColor=colors.white,
                             fontName='Helvetica-Bold'))
            x_pos += seg_width

        legend_x = 0
        for i, label in enumerate(labels):
            if counts[i] == 0:
                continue
            d.add(Rect(legend_x, -18, 10, 10, fillColor=colors_list[i], strokeColor=None))
            d.add(String(legend_x + 14, -13, f"{label} ({counts[i]})",
                         textAnchor='start', fontSize=8, fillColor=colors.HexColor('#555555')))
            legend_x += 90

        return d

    # ---------------------------------------------------------------
    # PAGE 2 — EXECUTIVE SUMMARY
    # ---------------------------------------------------------------
    def _build_executive_summary(self, story: list, scan: Scan):
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        if scan.summary:
            story.append(Paragraph(self._safe(scan.summary), self.styles['Body']))
        else:
            total = scan.total_findings or 0
            story.append(Paragraph(
                f"This automated security assessment identified {total} findings across "
                f"the target system. Manual verification is recommended for all findings "
                f"before remediation.",
                self.styles['Body']
            ))

        story.append(Spacer(1, 12))

        # Summary table
        summary_data = [
            [Paragraph("Severity", self.styles['TableHeader']),
             Paragraph("Count", self.styles['TableHeader'])],
            ["Critical", str(scan.critical_count or 0)],
            ["High", str(scan.high_count or 0)],
            ["Medium", str(scan.medium_count or 0)],
            ["Low", str(scan.low_count or 0)],
            ["Informational", str(scan.info_count or 0)],
            ["TOTAL", str(scan.total_findings or 0)],
        ]

        t = Table(summary_data, colWidths=[200, 100])
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#fee2e2')),
            ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#ffedd5')),
            ('BACKGROUND', (1, 3), (1, 3), colors.HexColor('#fef9c3')),
            ('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#dbeafe')),
            ('BACKGROUND', (1, 5), (1, 5), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]
        t.setStyle(TableStyle(style_cmds))
        story.append(t)

    # ---------------------------------------------------------------
    # PAGES 3+ — DETAILED FINDINGS
    # ---------------------------------------------------------------
    def _build_detailed_findings(self, story: list, findings: List[Finding]):
        if not findings:
            story.append(Paragraph("Detailed Findings", self.styles['SectionHeader']))
            story.append(Paragraph("No findings were discovered during this scan.", self.styles['Body']))
            return

        story.append(Paragraph("Detailed Findings", self.styles['SectionHeader']))
        story.append(Spacer(1, 6))

        for idx, finding in enumerate(findings, start=1):
            story.append(KeepTogether(self._build_finding_block(idx, finding)))
            if idx < len(findings):
                divider_data = [[""]]
                divider = Table(divider_data, colWidths=[468])
                divider.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#cccccc')),
                ]))
                story.append(divider)
                story.append(Spacer(1, 6))

    def _build_finding_block(self, idx: int, finding: Finding) -> list:
        """Build a single finding block."""
        block = []

        # Finding number and title
        block.append(Paragraph(
            f"Finding #{idx}: {self._safe(finding.title)}",
            self.styles['FindingNumber']
        ))

        # Severity badge
        sev = (finding.severity or "informational").lower()
        badge_color = SEV_COLORS.get(sev, SEV_COLORS["informational"])
        badge_data = [[Paragraph(f"  {sev.upper()}  ", self.styles['BadgeText'])]]
        badge_table = Table(badge_data, colWidths=[80])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), badge_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        block.append(badge_table)
        block.append(Spacer(1, 4))

        # Affected Component
        comp = self._safe(finding.affected_component)
        block.append(Paragraph("<b>Affected Component:</b>", self.styles['Body']))
        block.append(Paragraph(comp, self.styles['Mono']))
        block.append(Spacer(1, 4))

        # Description
        desc = self._safe(finding.description)
        block.append(Paragraph("<b>Description:</b>", self.styles['Body']))
        block.append(Paragraph(desc, self.styles['Body']))
        block.append(Spacer(1, 4))

        # Evidence (truncated to 300 chars, monospace, gray background)
        if finding.evidence:
            ev = finding.evidence[:300] + ("..." if len(finding.evidence) > 300 else "")
            ev = self._safe(ev)
            ev_data = [[Paragraph(ev, self.styles['Mono'])]]
            ev_table = Table(ev_data, colWidths=[468])
            ev_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ]))
            block.append(Paragraph("<b>Evidence:</b>", self.styles['Body']))
            block.append(ev_table)
            block.append(Spacer(1, 4))

        # AI Triage Notes (italic)
        notes = self._safe(finding.ai_triage_notes)
        block.append(Paragraph("<b>AI Triage Notes:</b>", self.styles['Body']))
        block.append(Paragraph(notes, self.styles['ItalicBody']))
        block.append(Spacer(1, 4))

        # CVE IDs
        cve_ids = finding.cve_ids
        if cve_ids:
            if isinstance(cve_ids, list):
                cve_str = ", ".join(cve_ids)
            else:
                cve_str = str(cve_ids)
            block.append(Paragraph(f"<b>CVE IDs:</b> {self._safe(cve_str)}", self.styles['Body']))
            block.append(Spacer(1, 4))

        # Remediation
        remediation = self._safe(finding.ai_remediation or "No remediation advice available.")
        block.append(Paragraph("<b>Remediation:</b>", self.styles['Body']))
        remediation_html = self._md_to_html(remediation)
        block.append(Paragraph(remediation_html, self.styles['Body']))
        block.append(Spacer(1, 8))
        return block

    # ---------------------------------------------------------------
    # LAST PAGE — APPENDIX
    # ---------------------------------------------------------------
    def _build_appendix(self, story: list, audit_logs: List[AuditLog]):
        story.append(Paragraph("Appendix", self.styles['SectionHeader']))
        story.append(Spacer(1, 6))

        if audit_logs:
            story.append(Paragraph("<b>Audit Log</b>", self.styles['Body']))
            story.append(Spacer(1, 4))

            log_data = [
                [Paragraph("Timestamp", self.styles['TableHeader']),
                 Paragraph("Action", self.styles['TableHeader']),
                 Paragraph("Actor", self.styles['TableHeader'])]
            ]
            for log in audit_logs[:50]:
                ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-"
                log_data.append([
                    self._safe(ts),
                    self._safe(log.action)[:40],
                    self._safe(log.actor)[:30],
                ])

            t = Table(log_data, colWidths=[140, 180, 140])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("<b>Audit Log:</b> No audit log entries recorded.", self.styles['Body']))
            story.append(Spacer(1, 12))

        # Legal Disclaimer
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Legal Disclaimer</b>", self.styles['Body']))
        story.append(Paragraph(
            "This report was generated for authorised security testing purposes only. "
            "Distribution of this report should be limited to authorised personnel. "
            "The findings contained herein reflect the state of the target system at the "
            "time of testing and may change over time. The authors assume no liability for "
            "any damages arising from the use or misuse of this information.",
            self.styles['ItalicBody']
        ))

    # ---------------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------------
    @staticmethod
    def _safe(value) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _md_to_html(text: str) -> str:
        """Simple markdown to HTML conversion for ReportLab compatibility."""
        AMPERSAND = chr(38)  # &
        LESSTHAN = chr(60)   # <
        GREATERTHAN = chr(62)  # >
        # Must escape HTML entities BEFORE adding any HTML tags
        text = text.replace("&", AMPERSAND + "amp;")
        text = text.replace("<", AMPERSAND + "lt;")
        text = text.replace(">", AMPERSAND + "gt;")
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', LESSTHAN + 'b' + GREATERTHAN + r'\1' + LESSTHAN + '/b' + GREATERTHAN, text)
        # Italic
        text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', LESSTHAN + 'i' + GREATERTHAN + r'\1' + LESSTHAN + '/i' + GREATERTHAN, text)
        # Code blocks
        text = re.sub(r'```(\w*)\n(.*?)```', LESSTHAN + 'font face="Courier" size="8"' + GREATERTHAN + r'\2' + LESSTHAN + '/font' + GREATERTHAN, text, flags=re.DOTALL)
        # Inline code
        text = re.sub(r'`([^`]+)`', LESSTHAN + 'font face="Courier" size="8"' + GREATERTHAN + r'\1' + LESSTHAN + '/font' + GREATERTHAN, text)
        # Line breaks
        text = text.replace("\n", LESSTHAN + "br/" + GREATERTHAN)
        return text
