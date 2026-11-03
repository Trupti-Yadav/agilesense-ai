from io import BytesIO
from datetime import datetime

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def generate_sprint_report(
    sprint_df,
    metrics,
    health_status,
    health_message,
    high_risk_count,
    medium_risk_count,
    unique_stories_at_risk,
    sprint_level_risks,
    risks,
    primary_drivers,
    recommended_actions,
):
    """Generate a downloadable PDF stakeholder report."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=body_style,
        fontSize=8,
        leading=11,
    )

    story = []

    sprint_name = str(sprint_df["sprint_name"].iloc[0])

    # Report title and metadata.
    story.append(Paragraph("AgileSense AI", title_style))
    story.append(
        Paragraph("Sprint Stakeholder Health Report", styles["Heading2"])
    )
    story.append(
        Paragraph(
            f"<b>Sprint:</b> {escape(sprint_name)}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Report generated:</b> "
            f"{datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            body_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 8))

    # Overall sprint health.
    story.append(Paragraph("1. Stakeholder Sprint Health", heading_style))

    health_colors = {
        "AT RISK": colors.HexColor("#FCE4E4"),
        "NEEDS ATTENTION": colors.HexColor("#FFF2CC"),
        "ON TRACK": colors.HexColor("#E2F0D9"),
    }

    health_table = Table(
        [[Paragraph(
            f"<b>Overall Health: {escape(health_status)}</b><br/>"
            f"{escape(health_message)}",
            body_style,
        )]],
        colWidths=[170 * mm],
    )

    health_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                health_colors.get(health_status, colors.white),
            ),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 10),
        ])
    )

    story.append(health_table)

    # Sprint metrics.
    story.append(Paragraph("2. Sprint Delivery Overview", heading_style))

    metric_data = [
        ["Metric", "Value"],
        ["Completion", f"{metrics['completion_percentage']}%"],
        ["Velocity", f"{metrics['velocity']:g} SP"],
        ["Committed Story Points", f"{metrics['committed_points']:g} SP"],
        ["Blocked Stories", str(metrics["blocked_stories"])],
        ["Carry-over", f"{metrics['carry_over_percentage']}%"],
    ]

    metric_table = Table(
        metric_data,
        colWidths=[85 * mm, 85 * mm],
    )

    metric_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(metric_table)

    # Risk summary.
    story.append(Paragraph("3. Sprint Risk Summary", heading_style))

    risk_summary_data = [
        ["Risk Indicator", "Count"],
        ["Unique Stories at Risk", str(unique_stories_at_risk)],
        ["High-risk Stories", str(high_risk_count)],
        ["Medium-risk Stories", str(medium_risk_count)],
        ["Sprint-level Risks", str(len(sprint_level_risks))],
    ]

    risk_summary_table = Table(
        risk_summary_data,
        colWidths=[120 * mm, 50 * mm],
    )

    risk_summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(risk_summary_table)

    # Primary risk drivers.
    story.append(Paragraph("4. Primary Risk Drivers", heading_style))

    if primary_drivers:
        for driver in primary_drivers:
            story.append(
                Paragraph(f"• {escape(str(driver))}", body_style)
            )
    else:
        story.append(
            Paragraph("No significant risk drivers identified.", body_style)
        )

    # Story-level risks.
    story.append(Paragraph("5. Story-level Risk Details", heading_style))

    story_risks = [
        risk for risk in risks
        if risk["story_id"] is not None
    ]

    if story_risks:
        risk_data = [[
            "Story ID",
            "Level",
            "Category",
            "Evidence",
            "Recommended Action",
        ]]

        for risk in story_risks:
            risk_data.append([
                Paragraph(escape(str(risk["story_id"])), small_style),
                Paragraph(escape(str(risk["level"])), small_style),
                Paragraph(escape(str(risk["category"])), small_style),
                Paragraph(escape(str(risk["evidence"])), small_style),
                Paragraph(escape(str(risk["recommendation"])), small_style),
            ])

        risk_table = Table(
            risk_data,
            colWidths=[19 * mm, 17 * mm, 29 * mm, 52 * mm, 53 * mm],
            repeatRows=1,
        )

        risk_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )

        story.append(risk_table)
    else:
        story.append(
            Paragraph("No story-level risks identified.", body_style)
        )

    # Sprint-level risks.
    story.append(Paragraph("6. Sprint-level Risk Details", heading_style))

    if sprint_level_risks:
        for risk in sprint_level_risks:
            story.append(
                Paragraph(
                    f"<b>{escape(str(risk['level']))} · "
                    f"{escape(str(risk['category']))}</b>",
                    body_style,
                )
            )
            story.append(
                Paragraph(
                    f"<b>Evidence:</b> {escape(str(risk['evidence']))}",
                    body_style,
                )
            )
            story.append(
                Paragraph(
                    f"<b>Suggested action:</b> "
                    f"{escape(str(risk['recommendation']))}",
                    body_style,
                )
            )
            story.append(Spacer(1, 5))
    else:
        story.append(
            Paragraph("No sprint-level risks identified.", body_style)
        )

    # Recommended management actions.
    story.append(
        Paragraph("7. Recommended Management Actions", heading_style)
    )

    if recommended_actions:
        for index, action in enumerate(recommended_actions, start=1):
            story.append(
                Paragraph(
                    f"{index}. {escape(str(action))}",
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "Continue monitoring sprint progress.",
                body_style,
            )
        )

    # Important methodology note.
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "<b>About this assessment:</b> Sprint metrics describe the "
            "uploaded dataset. Risk findings are based on configured "
            "thresholds and deterministic, rule-based indicators. "
            "They provide decision support and are not predictions "
            "of sprint failure. Management decisions remain with "
            "the delivery team.",
            small_style,
        )
    )

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes