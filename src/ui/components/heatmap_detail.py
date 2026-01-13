"""
Heatmap Detail Panel Component.

Renders a slide-out detail panel in the sidebar showing complete scenario details.
"""

import streamlit as st

from src.ui.components.heatmap_constants import STATUS_COLORS, STATUS_ICONS


def render_detail_panel(scenario: dict) -> bool:
    """
    Render scenario details in sidebar (slide-out panel).

    Args:
        scenario: Scenario result dict containing all ScenarioResult fields

    Returns:
        True if panel should stay open, False if closed
    """
    with st.sidebar:
        st.header("Scenario Details")

        # Status badge
        status = scenario.get("status") or scenario.get("result", "ERROR")
        # Handle old format
        if status in ("PASS", "FAIL") and "margin" in scenario:
            margin = scenario.get("margin", 1.0)
            if status == "PASS" and margin is not None and margin <= 0.5:
                status = "RISK"

        status_icon = STATUS_ICONS.get(status, "?")
        colors = STATUS_COLORS.get(status, STATUS_COLORS["ERROR"])

        if status == "PASS":
            st.success(f"## {status_icon} {status}")
        elif status == "RISK":
            st.warning(f"## {status_icon} {status}")
        elif status == "FAIL":
            st.error(f"## {status_icon} {status}")
        else:  # ERROR
            st.info(f"## {status_icon} {status}")

        # Grid coordinates
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            adoption_rate = scenario.get("adoption_rate", 0)
            st.metric("Adoption Rate", f"{adoption_rate:.0f}%")
        with col2:
            contribution_rate = scenario.get("contribution_rate", 0)
            st.metric("Contribution Rate", f"{contribution_rate:.1f}%")

        # ERROR-specific display
        if status == "ERROR":
            st.divider()
            error_msg = scenario.get("error_message", "Unknown error occurred")
            st.error(f"**Error:** {error_msg}")
            st.caption("This scenario could not be calculated.")

            # Show close button and return
            if st.button("Close", key="close_detail_panel", use_container_width=True):
                return False
            return True

        # ACP values
        st.divider()
        st.subheader("ACP Values")
        col1, col2 = st.columns(2)

        hce_acp = scenario.get("hce_acp", 0)
        nhce_acp = scenario.get("nhce_acp", 0)

        with col1:
            st.metric("HCE ACP", f"{hce_acp:.2f}%")
        with col2:
            st.metric("NHCE ACP", f"{nhce_acp:.2f}%")

        # Threshold and margin
        st.divider()
        st.subheader("Compliance")
        col1, col2 = st.columns(2)

        threshold = scenario.get("threshold") or scenario.get("max_allowed_acp", 0)
        margin = scenario.get("margin", 0)

        with col1:
            st.metric("Threshold", f"{threshold:.2f}%")
        with col2:
            margin_formatted = f"{margin:+.2f}pp"
            delta_color = "normal" if margin >= 0 else "inverse"
            st.metric("Margin", margin_formatted)

        # Limiting bound
        limiting_bound = scenario.get("limiting_bound") or scenario.get("limiting_test", "N/A")
        if limiting_bound and limiting_bound != "N/A":
            if limiting_bound == "MULTIPLE":
                st.info("**Limiting Test:** 1.25× NHCE ACP (Multiple Test)")
            elif limiting_bound == "ADDITIVE":
                st.info("**Limiting Test:** NHCE ACP + 2.0pp (Additive Test)")
            else:
                st.info(f"**Limiting Test:** {limiting_bound}")

        # Contributor counts
        st.divider()
        st.subheader("Contributors")
        col1, col2 = st.columns(2)

        hce_count = scenario.get("hce_contributor_count", "N/A")
        nhce_count = scenario.get("nhce_contributor_count", "N/A")

        with col1:
            st.metric("HCE Contributors", str(hce_count))
        with col2:
            st.metric("NHCE Contributors", str(nhce_count))

        # Total mega-backdoor amount
        mega_backdoor = scenario.get("total_mega_backdoor_amount")
        if mega_backdoor is not None:
            st.metric("Total Mega-Backdoor", f"${mega_backdoor:,.2f}")

        # Seed
        seed = scenario.get("seed_used") or scenario.get("seed", "N/A")
        st.caption(f"**Seed:** {seed}")

        # Close button
        st.divider()
        if st.button("Close", key="close_detail_panel", use_container_width=True):
            return False

        return True


def get_scenario_at_coordinates(
    grid_result: dict, row: int, col: int
) -> dict | None:
    """
    Get scenario result at specific grid coordinates.

    Args:
        grid_result: Grid analysis result containing adoption_rates, contribution_rates, results
        row: Row index (adoption rate axis)
        col: Column index (contribution rate axis)

    Returns:
        Scenario dict if found, None otherwise
    """
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    results = grid_result.get("results", [])

    if row >= len(adoption_rates) or col >= len(contribution_rates):
        return None

    target_adoption = adoption_rates[row]
    target_contribution = contribution_rates[col]

    for result in results:
        if (
            result.get("adoption_rate") == target_adoption
            and result.get("contribution_rate") == target_contribution
        ):
            return result

    return None
