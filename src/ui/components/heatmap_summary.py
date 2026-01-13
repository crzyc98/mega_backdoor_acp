"""
Heatmap Summary Panel Component.

Renders aggregate statistics panel with status counts, margin stats, and derived insights.
"""

import streamlit as st

from src.ui.components.heatmap_models import HeatmapSummaryDisplay


def render_summary_panel(grid_result: dict) -> None:
    """
    Render summary statistics panel above the heatmap.

    Args:
        grid_result: Grid analysis result containing:
            - results: List of scenario results
            - summary: Grid summary statistics
    """
    results = grid_result.get("results", [])
    summary = grid_result.get("summary", {})

    # Build display model
    summary_display = HeatmapSummaryDisplay.from_grid_result(results, summary)

    # Status counts row
    st.subheader("Grid Summary")
    cols = st.columns(5)

    with cols[0]:
        st.metric(
            "Pass",
            summary_display.pass_count,
            help="Scenarios with HCE ACP below threshold with safe margin",
        )
    with cols[1]:
        st.metric(
            "Risk",
            summary_display.risk_count,
            help="Scenarios passing but dangerously close to threshold",
        )
    with cols[2]:
        st.metric(
            "Fail",
            summary_display.fail_count,
            help="Scenarios with HCE ACP exceeding threshold",
        )
    with cols[3]:
        st.metric(
            "Error",
            summary_display.error_count,
            help="Scenarios that could not be calculated",
        )
    with cols[4]:
        st.metric(
            "Total",
            summary_display.total_count,
            help="Total scenarios in grid",
        )

    # Margin statistics in expander
    with st.expander("Margin Statistics", expanded=False):
        _render_margin_details(summary_display)

    # Key insights
    _render_insights(summary_display)


def _render_margin_details(summary: HeatmapSummaryDisplay) -> None:
    """Render detailed margin statistics."""
    # T048: Handle all-ERROR grid scenario
    if summary.error_count == summary.total_count:
        st.warning("⚠️ All scenarios resulted in errors - no margin data available")
        st.caption("This may indicate an issue with the census data or configuration.")
        return

    # Check if we have valid margin data
    if summary.min_margin is None and summary.max_margin is None:
        st.info("No valid margin data available (all scenarios are ERROR)")
        return

    cols = st.columns(3)

    # Minimum margin
    with cols[0]:
        if summary.min_margin:
            st.metric(
                "Min Margin",
                f"{summary.min_margin.value:+.2f}pp",
                help="Smallest margin value in grid",
            )
            st.caption(
                f"at {summary.min_margin.adoption_rate:.0f}% adoption, "
                f"{summary.min_margin.contribution_rate:.1f}% contribution"
            )
        else:
            st.metric("Min Margin", "N/A")

    # Maximum margin
    with cols[1]:
        if summary.max_margin:
            st.metric(
                "Max Margin",
                f"{summary.max_margin.value:+.2f}pp",
                help="Largest margin value in grid",
            )
            st.caption(
                f"at {summary.max_margin.adoption_rate:.0f}% adoption, "
                f"{summary.max_margin.contribution_rate:.1f}% contribution"
            )
        else:
            st.metric("Max Margin", "N/A")

    # Average margin
    with cols[2]:
        if summary.avg_margin is not None:
            st.metric(
                "Avg Margin",
                f"{summary.avg_margin:+.2f}pp",
                help="Average margin across all non-ERROR scenarios",
            )
        else:
            st.metric("Avg Margin", "N/A")


def _render_insights(summary: HeatmapSummaryDisplay) -> None:
    """Render derived insights."""
    insights = []

    # Max safe contribution
    if summary.max_safe_contribution is not None:
        insights.append(
            f"**Max Safe Contribution:** {summary.max_safe_contribution:.1f}% "
            f"(at highest adoption rate tested)"
        )

    # First failure point
    if summary.first_failure_point:
        insights.append(
            f"**First Failure:** at {summary.first_failure_point.adoption_rate:.0f}% adoption, "
            f"{summary.first_failure_point.contribution_rate:.1f}% contribution"
        )
    elif summary.fail_count == 0 and summary.error_count < summary.total_count:
        insights.append("**First Failure:** None (all scenarios pass or are in risk zone)")

    # Pass rate
    valid_count = summary.total_count - summary.error_count
    if valid_count > 0:
        pass_rate = (summary.pass_count / valid_count) * 100
        insights.append(f"**Pass Rate:** {pass_rate:.1f}% of valid scenarios")

    # Risk ratio
    if summary.pass_count + summary.risk_count > 0:
        risk_ratio = summary.risk_count / (summary.pass_count + summary.risk_count) * 100
        if risk_ratio > 20:
            insights.append(f"⚠ **Risk Warning:** {risk_ratio:.0f}% of passing scenarios are in the risk zone")

    # Display insights
    if insights:
        for insight in insights:
            st.markdown(insight)


def calculate_summary_from_results(results: list[dict]) -> dict:
    """
    Calculate summary statistics from a list of scenario results.

    This is useful when the API response doesn't include a pre-computed summary.

    Args:
        results: List of scenario result dicts

    Returns:
        Summary dict compatible with HeatmapSummaryDisplay.from_grid_result()
    """
    pass_count = 0
    risk_count = 0
    fail_count = 0
    error_count = 0

    valid_margins = []
    first_failure = None

    for r in results:
        status = r.get("status") or r.get("result", "ERROR")
        margin = r.get("margin")

        # Handle old format
        if status in ("PASS", "FAIL") and margin is not None:
            if status == "PASS" and margin <= 0.5:
                status = "RISK"

        if status == "PASS":
            pass_count += 1
            if margin is not None:
                valid_margins.append(margin)
        elif status == "RISK":
            risk_count += 1
            if margin is not None:
                valid_margins.append(margin)
        elif status == "FAIL":
            fail_count += 1
            if margin is not None:
                valid_margins.append(margin)
            if first_failure is None:
                first_failure = {
                    "adoption_rate": r.get("adoption_rate", 0),
                    "contribution_rate": r.get("contribution_rate", 0),
                }
        else:  # ERROR
            error_count += 1

    total_count = pass_count + risk_count + fail_count + error_count

    # Calculate max safe contribution at highest adoption
    adoption_rates = sorted(set(r.get("adoption_rate", 0) for r in results))
    max_safe_contribution = None
    if adoption_rates:
        max_adoption = max(adoption_rates)
        passing_at_max = [
            r.get("contribution_rate", 0)
            for r in results
            if r.get("adoption_rate") == max_adoption
            and (_get_status(r) in ("PASS", "RISK"))
        ]
        if passing_at_max:
            max_safe_contribution = max(passing_at_max)

    return {
        "pass_count": pass_count,
        "risk_count": risk_count,
        "fail_count": fail_count,
        "error_count": error_count,
        "total_count": total_count,
        "first_failure_point": first_failure,
        "max_safe_contribution": max_safe_contribution,
        "worst_margin": min(valid_margins) if valid_margins else 0,
    }


def _get_status(result: dict) -> str:
    """Extract status from result, handling old and new formats."""
    status = result.get("status") or result.get("result", "ERROR")
    if status in ("PASS", "FAIL") and "margin" in result:
        margin = result.get("margin", 1.0)
        if status == "PASS" and margin is not None and margin <= 0.5:
            return "RISK"
    return status
