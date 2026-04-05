"""
pdf_exporter.py — Styled PDF report generation using ReportLab.

Generates a professional MOM (Minutes of Meeting) PDF with:
- Cover header with meeting metadata
- Summary paragraph
- Decisions list
- Action Items table with color-coded priority rows
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.platypus import KeepTogether


# ─────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────

BRAND_PURPLE = colors.HexColor("#6366f1")
BRAND_DARK = colors.HexColor("#1e1b4b")
BRAND_LIGHT = colors.HexColor("#f8f7ff")
PRIORITY_HIGH = colors.HexColor("#fef2f2")
PRIORITY_MED = colors.HexColor("#fff7ed")
PRIORITY_LOW = colors.HexColor("#f0fdf4")
PRIORITY_HIGH_TEXT = colors.HexColor("#ef4444")
PRIORITY_MED_TEXT = colors.HexColor("#f97316")
PRIORITY_LOW_TEXT = colors.HexColor("#22c55e")
GRAY_100 = colors.HexColor("#f1f5f9")
GRAY_300 = colors.HexColor("#cbd5e1")
GRAY_700 = colors.HexColor("#334155")


def _priority_row_color(priority: str):
    mapping = {
        "high": PRIORITY_HIGH,
        "medium": PRIORITY_MED,
        "low": PRIORITY_LOW,
    }
    return mapping.get(priority.lower(), colors.white)


def _priority_text_color(priority: str):
    mapping = {
        "high": PRIORITY_HIGH_TEXT,
        "medium": PRIORITY_MED_TEXT,
        "low": PRIORITY_LOW_TEXT,
    }
    return mapping.get(priority.lower(), GRAY_700)


# ─────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Title"],
            fontSize=22,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#c7d2fe"),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=13,
            textColor=BRAND_PURPLE,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6,
            borderPad=(0, 0, 3, 0),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            textColor=GRAY_700,
            alignment=TA_JUSTIFY,
            leading=15,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            textColor=GRAY_700,
            leftIndent=12,
            bulletIndent=0,
            leading=14,
            spaceAfter=3,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontSize=9,
            textColor=GRAY_700,
            leading=12,
        ),
        "priority_cell": ParagraphStyle(
            "PriorityCell",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            leading=12,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER,
        ),
    }
    return styles


# ─────────────────────────────────────────────
# PDF builder
# ─────────────────────────────────────────────

def export_pdf(
    insights: dict,
    meeting_title: str = "Meeting Minutes",
) -> bytes:
    """
    Build a styled PDF report from parsed meeting insights.

    Parameters
    ----------
    insights : dict
        {"summary": str, "decisions": list, "actions": list}
    meeting_title : str
        Title shown at the top of the PDF.

    Returns
    -------
    bytes
        Raw PDF bytes suitable for st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=meeting_title,
        author="AI Meeting Assistant",
    )

    styles = _build_styles()
    story = []

    # ── Header Banner ───────────────────────────────
    banner_data = [[Paragraph(meeting_title, styles["title"])],
                   [Paragraph(
                       f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')} · AI Meeting Assistant",
                       styles["subtitle"],
                   )]]
    banner_table = Table(banner_data, colWidths=[doc.width])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_DARK, BRAND_DARK]),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 18))

    # ── Summary ─────────────────────────────────────
    story.append(Paragraph("📋 Meeting Summary", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY_300, spaceAfter=8))
    summary_text = insights.get("summary", "No summary available.")
    story.append(Paragraph(summary_text, styles["body"]))
    story.append(Spacer(1, 14))

    # ── Decisions ───────────────────────────────────
    decisions = insights.get("decisions", [])
    if decisions:
        story.append(Paragraph("✅ Key Decisions", styles["section_heading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY_300, spaceAfter=8))
        for i, decision in enumerate(decisions, 1):
            bullet = Paragraph(f"<bullet>&bull;</bullet> {decision}", styles["bullet"])
            story.append(bullet)
        story.append(Spacer(1, 14))

    # ── Action Items Table ──────────────────────────
    actions = insights.get("actions", [])
    if actions:
        story.append(Paragraph("🎯 Action Items", styles["section_heading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY_300, spaceAfter=8))

        # Table header row
        col_widths = [doc.width * 0.40, doc.width * 0.18, doc.width * 0.16, doc.width * 0.26]
        header_row = [
            Paragraph("Task", styles["table_header"]),
            Paragraph("Owner", styles["table_header"]),
            Paragraph("Priority", styles["table_header"]),
            Paragraph("Deadline", styles["table_header"]),
        ]
        table_data = [header_row]

        for action in actions:
            priority = action.get("priority", "Medium")
            priority_color = _priority_text_color(priority)
            priority_para = ParagraphStyle(
                f"Priority_{priority}",
                parent=styles["priority_cell"],
                textColor=priority_color,
            )
            deadline = action.get("deadline") or "—"
            row = [
                Paragraph(action.get("task", ""), styles["table_cell"]),
                Paragraph(action.get("owner", "Unassigned"), styles["table_cell"]),
                Paragraph(priority, priority_para),
                Paragraph(str(deadline), styles["table_cell"]),
            ]
            table_data.append(row)

        action_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Build row-level style commands
        row_commands = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, GRAY_300),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_100]),
        ]
        # Priority color on data rows
        for i, action in enumerate(actions, start=1):
            bg = _priority_row_color(action.get("priority", "Medium"))
            row_commands.append(("BACKGROUND", (2, i), (2, i), bg))

        action_table.setStyle(TableStyle(row_commands))
        story.append(action_table)
        story.append(Spacer(1, 20))


    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_300, spaceAfter=6))
    story.append(Paragraph(
        "Generated by AI Meeting Assistant · Powered by NVIDIA NIM &amp; Whisper",
        styles["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
