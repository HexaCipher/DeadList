"""
DeadList PDF Report Generator
Generates formatted PDF analysis reports using ReportLab.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# DeadList brand colors
BRAND_BG = colors.HexColor("#0A0E13")
BRAND_SURFACE = colors.HexColor("#161B22")
BRAND_RED = colors.HexColor("#F85149")
BRAND_GREEN = colors.HexColor("#3FB950")
BRAND_AMBER = colors.HexColor("#D29922")
BRAND_BLUE = colors.HexColor("#58A6FF")
BRAND_PRIMARY = colors.HexColor("#1F6FEB")
TEXT_PRIMARY = colors.HexColor("#333333")
TEXT_SECONDARY = colors.HexColor("#666666")


def generate_report(analysis_data: Dict[str, Any]) -> bytes:
    """
    Generate a complete PDF analysis report.

    Args:
        analysis_data: Full analysis data including processes, connections, etc.

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="DeadListTitle",
        parent=styles["Title"],
        fontSize=24,
        textColor=TEXT_PRIMARY,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="DeadListTagline",
        parent=styles["Normal"],
        fontSize=10,
        textColor=TEXT_SECONDARY,
        spaceAfter=20,
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=BRAND_PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SubSection",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=TEXT_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyMono",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Courier",
        textColor=TEXT_SECONDARY,
    ))

    elements = []

    # ── Title Page ────────────────────────────────────────────
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("☠ DeadList", styles["DeadListTitle"]))
    elements.append(Paragraph(
        "The process that's dead to the system. Found alive by DeadList.",
        styles["DeadListTagline"],
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_PRIMARY))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Memory Forensics Analysis Report", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    # ── File Metadata ─────────────────────────────────────────
    elements.append(Paragraph("1. File Metadata", styles["SectionTitle"]))

    meta_data = [
        ["Field", "Value"],
        ["Filename", analysis_data.get("filename", "N/A")],
        ["MD5 Hash", analysis_data.get("md5_hash", "N/A")],
        ["SHA256 Hash", analysis_data.get("sha256_hash", "N/A")],
        ["File Size", _format_bytes(analysis_data.get("file_size_bytes", 0))],
        ["Analysis Date", analysis_data.get("created_at", "N/A")],
        ["Status", analysis_data.get("status", "N/A").upper()],
        ["OS Profile", analysis_data.get("os_profile", "Auto-detected")],
    ]

    meta_table = Table(meta_data, colWidths=[120, 380])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)

    # ── Risk Summary ──────────────────────────────────────────
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("2. Risk Summary", styles["SectionTitle"]))

    risk_level = analysis_data.get("risk_level", "unknown").upper()
    hidden_count = analysis_data.get("hidden_process_count", 0)
    total_count = analysis_data.get("total_process_count", 0)
    suspicious_conns = analysis_data.get("suspicious_connection_count", 0)

    risk_color = {
        "CRITICAL": BRAND_RED,
        "HIGH": BRAND_AMBER,
        "MEDIUM": BRAND_AMBER,
        "LOW": BRAND_BLUE,
        "CLEAN": BRAND_GREEN,
    }.get(risk_level, TEXT_SECONDARY)

    risk_data = [
        ["Metric", "Value"],
        ["Overall Risk Level", risk_level],
        ["Hidden Processes (DKOM)", str(hidden_count)],
        ["Total Processes", str(total_count)],
        ["Suspicious Connections", str(suspicious_conns)],
    ]

    risk_table = Table(risk_data, colWidths=[200, 300])
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ("TEXTCOLOR", (1, 1), (1, 1), risk_color),
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(risk_table)

    # ── Process Table ─────────────────────────────────────────
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("3. Process Analysis", styles["SectionTitle"]))

    processes = analysis_data.get("processes", [])
    if processes:
        proc_header = ["PID", "Name", "PPID", "Status", "Score", "Hidden"]
        proc_rows = [proc_header]

        for proc in sorted(processes, key=lambda p: p.get("suspicion_score", 0), reverse=True):
            proc_rows.append([
                str(proc.get("pid", "")),
                str(proc.get("name", ""))[:30],
                str(proc.get("ppid", "")),
                str(proc.get("status", "clean")).upper(),
                str(proc.get("suspicion_score", 0)),
                "YES" if proc.get("is_hidden") else "No",
            ])

        proc_table = Table(proc_rows, colWidths=[50, 140, 50, 90, 50, 50])
        proc_style = [
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        # Highlight hidden/suspicious rows
        for i, proc in enumerate(sorted(processes, key=lambda p: p.get("suspicion_score", 0), reverse=True), 1):
            if proc.get("is_hidden"):
                proc_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEE2E2")))
            elif proc.get("suspicion_score", 0) >= 30:
                proc_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEF3C7")))

        proc_table.setStyle(TableStyle(proc_style))
        elements.append(proc_table)
    else:
        elements.append(Paragraph("No processes found.", styles["Normal"]))

    # ── Network Connections ───────────────────────────────────
    elements.append(PageBreak())
    elements.append(Paragraph("4. Network Connections", styles["SectionTitle"]))

    connections = analysis_data.get("connections", [])
    if connections:
        net_header = ["PID", "Protocol", "Local", "Remote", "State", "Suspicious"]
        net_rows = [net_header]

        for conn in connections:
            local = f"{conn.get('local_addr', '')}:{conn.get('local_port', '')}"
            remote = f"{conn.get('remote_addr', '')}:{conn.get('remote_port', '')}"
            net_rows.append([
                str(conn.get("pid", "")),
                str(conn.get("protocol", "")),
                local[:25],
                remote[:25],
                str(conn.get("state", ""))[:15],
                "⚠ YES" if conn.get("is_suspicious_port") else "No",
            ])

        net_table = Table(net_rows, colWidths=[40, 55, 120, 120, 80, 60])
        net_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(net_table)

    # ── Memory Regions (Malfind) ──────────────────────────────
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("5. Suspicious Memory Regions (Malfind)", styles["SectionTitle"]))

    regions = analysis_data.get("memory_regions", [])
    if regions:
        for region in regions:
            elements.append(Paragraph(
                f"PID {region.get('pid')} — {region.get('process_name', 'Unknown')} @ {region.get('address', 'N/A')}",
                styles["SubSection"],
            ))
            elements.append(Paragraph(
                f"Protection: {region.get('protection', 'N/A')} | Size: {region.get('size', 'N/A')} bytes | Tag: {region.get('tag', 'N/A')}",
                styles["Normal"],
            ))
            if region.get("hex_dump"):
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(
                    region["hex_dump"].replace("\n", "<br/>"),
                    styles["BodyMono"],
                ))
            elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("No suspicious memory regions found.", styles["Normal"]))

    # ── Footer ────────────────────────────────────────────────
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Generated by DeadList v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "The process that's dead to the system. Found alive by DeadList.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=TEXT_SECONDARY, alignment=TA_CENTER),
    ))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")
    return pdf_bytes


def _format_bytes(size: int) -> str:
    """Format byte count to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
