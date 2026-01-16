"""
Export Module for ACP Analysis Results.

Provides CSV and PDF export functionality with full audit metadata.
"""

from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.constants import SYSTEM_VERSION
from app.services.acp_calculator import calculate_acp_limits


def _ensure_limit_fields(result: dict) -> dict:
    nhce = result.get("nhce_acp")
    if nhce is None:
        return result

    limits = calculate_acp_limits(Decimal(str(nhce)))
    result.setdefault("limit_125", float(limits["limit_125"]))
    result.setdefault("limit_2pct_uncapped", float(limits["limit_2pct_uncapped"]))
    result.setdefault("cap_2x", float(limits["cap_2x"]))
    result.setdefault("limit_2pct_capped", float(limits["limit_2pct_capped"]))
    result.setdefault("effective_limit", float(limits["effective_limit"]))
    result.setdefault("binding_rule", "1.25x" if limits["limit_125"] >= limits["limit_2pct_capped"] else "2pct/2x")
    result.setdefault("threshold", result.get("effective_limit"))
    return result


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
        "limit_125",
        "limit_2pct_uncapped",
        "cap_2x",
        "limit_2pct_capped",
        "effective_limit",
        "binding_rule",
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
        _ensure_limit_fields(r)
        row = [
            f"{r['adoption_rate']:.1f}",
            f"{r['contribution_rate']:.1f}",
            f"{r['nhce_acp']:.2f}" if r.get("nhce_acp") is not None else "",
            f"{r['hce_acp']:.2f}" if r.get("hce_acp") is not None else "",
            f"{r['limit_125']:.2f}" if r.get("limit_125") is not None else "",
            f"{r['limit_2pct_uncapped']:.2f}" if r.get("limit_2pct_uncapped") is not None else "",
            f"{r['cap_2x']:.2f}" if r.get("cap_2x") is not None else "",
            f"{r['limit_2pct_capped']:.2f}" if r.get("limit_2pct_capped") is not None else "",
            f"{r['effective_limit']:.2f}" if r.get("effective_limit") is not None else "",
            r.get("binding_rule", ""),
            f"{r['threshold']:.2f}" if r.get("threshold") is not None else "",
            f"{r['margin']:.2f}" if r.get("margin") is not None else "",
            r.get("result", ""),
            r.get("limiting_test", ""),
            str(r.get("seed", "")),
            r.get("run_timestamp", ""),
        ]
        lines.append(",".join(row))

    return "\n".join(lines)


def generate_pdf_report(
    census: dict,
    results: list[dict],
    grid_summary: dict | None = None,
    excluded_count: int = 0,
) -> bytes:
    """
    Generate PDF report for analysis results.

    Args:
        census: Census metadata dictionary
        results: List of analysis result dictionaries
        grid_summary: Optional grid analysis summary
        excluded_count: Number of participants excluded from ACP test

    Returns:
        PDF file bytes
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.colors import HexColor
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

    # Define colors matching frontend theme
    BLUE_PRIMARY = HexColor('#2563eb')      # blue-600
    BLUE_LIGHT = HexColor('#dbeafe')        # blue-100
    BLUE_DARK = HexColor('#1e40af')         # blue-800
    GREEN_PRIMARY = HexColor('#22c55e')     # green-500
    GREEN_LIGHT = HexColor('#dcfce7')       # green-100
    RED_PRIMARY = HexColor('#ef4444')       # red-500
    RED_LIGHT = HexColor('#fee2e2')         # red-100
    PURPLE_LIGHT = HexColor('#f3e8ff')      # purple-100
    PURPLE_TEXT = HexColor('#7e22ce')       # purple-700
    AMBER_LIGHT = HexColor('#fef3c7')       # amber-100
    AMBER_TEXT = HexColor('#b45309')        # amber-700
    GRAY_LIGHT = HexColor('#f9fafb')        # gray-50
    GRAY_MEDIUM = HexColor('#e5e7eb')       # gray-200

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
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        textColor=BLUE_DARK,
        fontSize=20,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        textColor=BLUE_PRIMARY,
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8,
    )
    normal_style = styles["Normal"]

    elements = []

    # Title
    elements.append(Paragraph("ACP Sensitivity Analysis Report", title_style))
    elements.append(Spacer(1, 12))

    # Census Summary - styled like frontend stat boxes
    elements.append(Paragraph("Census Summary", heading_style))

    # Stats row with colored backgrounds
    stats_data = [[
        f"Plan Year\n{census['plan_year']}",
        f"Total Participants\n{census['participant_count']:,}",
        f"HCEs\n{census['hce_count']:,}",
        f"NHCEs\n{census['nhce_count']:,}",
    ]]
    if excluded_count > 0:
        stats_data[0].append(f"Excluded\n{excluded_count:,}")

    col_count = len(stats_data[0])
    col_width = 6.5 * inch / col_count
    stats_table = Table(stats_data, colWidths=[col_width] * col_count, rowHeights=[0.7 * inch])
    stats_table.setStyle(TableStyle([
        # Plan Year - blue
        ("BACKGROUND", (0, 0), (0, 0), BLUE_LIGHT),
        ("TEXTCOLOR", (0, 0), (0, 0), BLUE_PRIMARY),
        # Total Participants - blue
        ("BACKGROUND", (1, 0), (1, 0), BLUE_LIGHT),
        ("TEXTCOLOR", (1, 0), (1, 0), BLUE_PRIMARY),
        # HCEs - purple
        ("BACKGROUND", (2, 0), (2, 0), PURPLE_LIGHT),
        ("TEXTCOLOR", (2, 0), (2, 0), PURPLE_TEXT),
        # NHCEs - green
        ("BACKGROUND", (3, 0), (3, 0), GREEN_LIGHT),
        ("TEXTCOLOR", (3, 0), (3, 0), GREEN_PRIMARY),
        # Excluded - amber (if present)
        ("BACKGROUND", (4, 0), (4, 0), AMBER_LIGHT) if col_count > 4 else ("BACKGROUND", (0, 0), (0, 0), BLUE_LIGHT),
        ("TEXTCOLOR", (4, 0), (4, 0), AMBER_TEXT) if col_count > 4 else ("TEXTCOLOR", (0, 0), (0, 0), BLUE_PRIMARY),
        # Common styling
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(stats_table)

    # Census name as subtitle
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<i>Census: {census['name']}</i>", normal_style))
    elements.append(Spacer(1, 12))

    # Grid Summary (if applicable)
    if grid_summary:
        elements.append(Paragraph("Analysis Summary", heading_style))

        pass_rate = grid_summary['pass_rate']
        pass_color = GREEN_PRIMARY if pass_rate >= 80 else (AMBER_TEXT if pass_rate >= 50 else RED_PRIMARY)
        pass_bg = GREEN_LIGHT if pass_rate >= 80 else (AMBER_LIGHT if pass_rate >= 50 else RED_LIGHT)

        summary_data = [[
            f"Total Scenarios\n{grid_summary['total_scenarios']:,}",
            f"Passed\n{grid_summary['pass_count']:,}",
            f"Failed\n{grid_summary['fail_count']:,}",
            f"Pass Rate\n{pass_rate:.1f}%",
        ]]
        summary_table = Table(summary_data, colWidths=[1.625 * inch] * 4, rowHeights=[0.6 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), GRAY_LIGHT),
            ("BACKGROUND", (1, 0), (1, 0), GREEN_LIGHT),
            ("TEXTCOLOR", (1, 0), (1, 0), GREEN_PRIMARY),
            ("BACKGROUND", (2, 0), (2, 0), RED_LIGHT),
            ("TEXTCOLOR", (2, 0), (2, 0), RED_PRIMARY),
            ("BACKGROUND", (3, 0), (3, 0), pass_bg),
            ("TEXTCOLOR", (3, 0), (3, 0), pass_color),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
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
        "Limit",
        "Margin",
        "Rule",
        "Result",
    ]

    # Limit results for PDF (show first 100)
    display_results = results[:100]
    table_data = [header]

    for r in display_results:
        _ensure_limit_fields(r)
        row = [
            f"{r['adoption_rate']:.0f}",
            f"{r['contribution_rate']:.1f}",
            f"{r['nhce_acp']:.2f}" if r.get("nhce_acp") is not None else "N/A",
            f"{r['hce_acp']:.2f}" if r.get("hce_acp") is not None else "N/A",
            f"{r['effective_limit']:.2f}" if r.get("effective_limit") is not None else "N/A",
            f"{r['margin']:+.2f}" if r.get("margin") is not None else "N/A",
            r.get("binding_rule", ""),
            r.get("result", ""),
        ]
        table_data.append(row)

    results_table = Table(table_data, repeatRows=1)

    # Build style commands for results table
    style_commands = [
        # Header style - blue theme
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Data style
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
        # Alternating row colors
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
    ]

    # Add color coding for PASS/FAIL cells in the Result column (column 7)
    for row_idx, r in enumerate(display_results, start=1):
        result_val = r.get("result", "")
        if result_val == "PASS":
            style_commands.append(("BACKGROUND", (7, row_idx), (7, row_idx), GREEN_LIGHT))
            style_commands.append(("TEXTCOLOR", (7, row_idx), (7, row_idx), GREEN_PRIMARY))
        elif result_val == "FAIL":
            style_commands.append(("BACKGROUND", (7, row_idx), (7, row_idx), RED_LIGHT))
            style_commands.append(("TEXTCOLOR", (7, row_idx), (7, row_idx), RED_PRIMARY))

    results_table.setStyle(TableStyle(style_commands))
    elements.append(results_table)

    if len(results) > 100:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"<i>Note: Showing first 100 of {len(results)} results. See CSV export for complete data.</i>",
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
        ("TEXTCOLOR", (0, 0), (0, -1), BLUE_PRIMARY),
    ]))
    elements.append(audit_table)

    # Scenario compliance table (show all results)
    if results:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Scenario Compliance Metrics", heading_style))
        compliance_header = [
            "Adopt\n(%)",
            "Contrib\n(%)",
            "Limit 1.25x",
            "Limit +2.0",
            "Cap 2x",
            "Capped +2.0",
            "Effective",
            "Rule",
            "Margin",
        ]
        compliance_rows = [compliance_header]
        for r in display_results:
            _ensure_limit_fields(r)
            compliance_rows.append([
                f"{r['adoption_rate']:.0f}",
                f"{r['contribution_rate']:.1f}",
                f"{r['limit_125']:.2f}" if r.get("limit_125") is not None else "N/A",
                f"{r['limit_2pct_uncapped']:.2f}" if r.get("limit_2pct_uncapped") is not None else "N/A",
                f"{r['cap_2x']:.2f}" if r.get("cap_2x") is not None else "N/A",
                f"{r['limit_2pct_capped']:.2f}" if r.get("limit_2pct_capped") is not None else "N/A",
                f"{r['effective_limit']:.2f}" if r.get("effective_limit") is not None else "N/A",
                r.get("binding_rule", ""),
                f"{r['margin']:+.2f}" if r.get("margin") is not None else "N/A",
            ])
        compliance_table = Table(compliance_rows, repeatRows=1)
        compliance_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, GRAY_MEDIUM),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ]))
        elements.append(compliance_table)

    # Formula explanation
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Formula Reference", heading_style))
    elements.append(Paragraph(
        "<b>IRS ACP Test (IRC Section 401(m)):</b> HCE ACP must be ≤ max(NHCE ACP × 1.25, min(NHCE ACP + 2.0%, 2× NHCE ACP))",
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
    _ensure_limit_fields(result)
    nhce = result["nhce_acp"]
    hce = result["hce_acp"]

    result["formula_125x"] = f"HCE ACP ({hce:.2f}%) ≤ NHCE ACP ({nhce:.2f}%) × 1.25 = {result['limit_125']:.2f}%"
    result["formula_plus2"] = (
        f"HCE ACP ({hce:.2f}%) ≤ min(NHCE ACP ({nhce:.2f}%) + 2.0%, 2× NHCE ACP) = "
        f"{result['limit_2pct_capped']:.2f}%"
    )
    result["formula_result"] = (
        f"HCE ACP ({hce:.2f}%) {'≤' if result['result'] == 'PASS' else '>'} "
        f"Effective Limit ({result['effective_limit']:.2f}%) → {result['result']}"
    )

    return result
