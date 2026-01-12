"""
Export Module for ACP Analysis Results.

Provides CSV and PDF export functionality with full audit metadata.
"""

import io
from datetime import datetime
from typing import Any

from src.core.constants import SYSTEM_VERSION


def format_csv_export(
    census: dict,
    results: list[dict],
    seed: int | None = None,
) -> str:
    """
    Format analysis results as CSV with audit metadata header.

    Args:
        census: Census metadata dictionary
        results: List of analysis result dictionaries
        seed: Optional seed value (for grid analysis)

    Returns:
        CSV string with header and data
    """
    lines = []

    # Audit metadata header
    lines.append(f"# ACP Sensitivity Analysis Export")
    lines.append(f"# Census ID: {census['id']}")
    lines.append(f"# Census Name: {census['name']}")
    lines.append(f"# Plan Year: {census['plan_year']}")
    lines.append(f"# Participants: {census['participant_count']} (HCE: {census['hce_count']}, NHCE: {census['nhce_count']})")
    lines.append(f"# Generated: {datetime.utcnow().isoformat()}Z")
    lines.append(f"# System Version: {SYSTEM_VERSION}")
    if seed is not None:
        lines.append(f"# Seed: {seed}")
    lines.append("#")

    # CSV header
    columns = [
        "adoption_rate",
        "contribution_rate",
        "nhce_acp",
        "hce_acp",
        "threshold",
        "margin",
        "result",
        "limiting_test",
        "seed",
        "run_timestamp",
    ]
    lines.append(",".join(columns))

    # Data rows
    for r in results:
        row = [
            f"{r['adoption_rate']:.1f}",
            f"{r['contribution_rate']:.1f}",
            f"{r['nhce_acp']:.3f}",
            f"{r['hce_acp']:.3f}",
            f"{r['threshold']:.3f}",
            f"{r['margin']:.3f}",
            r["result"],
            r["limiting_test"],
            str(r["seed"]),
            r.get("run_timestamp", ""),
        ]
        lines.append(",".join(row))

    return "\n".join(lines)


def generate_pdf_report(
    census: dict,
    results: list[dict],
    grid_summary: dict | None = None,
) -> bytes:
    """
    Generate PDF report for analysis results.

    Args:
        census: Census metadata dictionary
        results: List of analysis result dictionaries
        grid_summary: Optional grid analysis summary

    Returns:
        PDF file bytes
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    elements = []

    # Title
    elements.append(Paragraph("ACP Sensitivity Analysis Report", title_style))
    elements.append(Spacer(1, 12))

    # Census Summary
    elements.append(Paragraph("Census Summary", heading_style))
    census_data = [
        ["Census Name:", census["name"]],
        ["Plan Year:", str(census["plan_year"])],
        ["Total Participants:", str(census["participant_count"])],
        ["HCEs:", str(census["hce_count"])],
        ["NHCEs:", str(census["nhce_count"])],
    ]
    census_table = Table(census_data, colWidths=[2 * inch, 4 * inch])
    census_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(census_table)
    elements.append(Spacer(1, 12))

    # Grid Summary (if applicable)
    if grid_summary:
        elements.append(Paragraph("Analysis Summary", heading_style))
        summary_data = [
            ["Total Scenarios:", str(grid_summary["total_scenarios"])],
            ["Passed:", str(grid_summary["pass_count"])],
            ["Failed:", str(grid_summary["fail_count"])],
            ["Pass Rate:", f"{grid_summary['pass_rate']:.1f}%"],
        ]
        summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

    # Results Table
    elements.append(Paragraph("Analysis Results", heading_style))

    # Table header
    header = [
        "Adoption\n(%)",
        "Contrib\n(%)",
        "NHCE\nACP",
        "HCE\nACP",
        "Threshold",
        "Margin",
        "Result",
        "Test",
    ]

    # Limit results for PDF (show first 50)
    display_results = results[:50]
    table_data = [header]

    for r in display_results:
        row = [
            f"{r['adoption_rate']:.0f}",
            f"{r['contribution_rate']:.1f}",
            f"{r['nhce_acp']:.2f}",
            f"{r['hce_acp']:.2f}",
            f"{r['threshold']:.2f}",
            f"{r['margin']:+.2f}",
            r["result"],
            r["limiting_test"],
        ]
        table_data.append(row)

    results_table = Table(table_data, repeatRows=1)
    results_table.setStyle(TableStyle([
        # Header style
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Data style
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    elements.append(results_table)

    if len(results) > 50:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"Note: Showing first 50 of {len(results)} results. See CSV export for complete data.",
            normal_style
        ))

    elements.append(Spacer(1, 24))

    # Audit Footer
    elements.append(Paragraph("Audit Information", heading_style))
    audit_data = [
        ["Generated:", f"{datetime.utcnow().isoformat()}Z"],
        ["System Version:", SYSTEM_VERSION],
        ["Census ID:", census["id"]],
    ]
    audit_table = Table(audit_data, colWidths=[2 * inch, 4 * inch])
    audit_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(audit_table)

    # Formula explanation
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Formula Reference", heading_style))
    elements.append(Paragraph(
        "<b>IRS ACP Test (IRC Section 401(m)):</b> HCE ACP must be ≤ max(NHCE ACP × 1.25, NHCE ACP + 2.0%)",
        normal_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def add_formula_strings(result: dict) -> dict:
    """
    Add formula display strings to an analysis result.

    Args:
        result: Analysis result dictionary

    Returns:
        Result with added formula_125x and formula_plus2 fields
    """
    nhce = result["nhce_acp"]
    hce = result["hce_acp"]

    result["formula_125x"] = f"HCE ACP ({hce:.3f}%) ≤ NHCE ACP ({nhce:.3f}%) × 1.25 = {nhce * 1.25:.3f}%"
    result["formula_plus2"] = f"HCE ACP ({hce:.3f}%) ≤ NHCE ACP ({nhce:.3f}%) + 2.0% = {nhce + 2:.3f}%"
    result["formula_result"] = f"HCE ACP ({hce:.3f}%) {'≤' if result['result'] == 'PASS' else '>'} Threshold ({result['threshold']:.3f}%) → {result['result']}"

    return result
