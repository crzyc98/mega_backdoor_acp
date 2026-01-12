"""
Heatmap Visualization Component.

Renders ACP test results as an interactive heatmap using Plotly.
"""

import plotly.graph_objects as go
import streamlit as st


def render_heatmap(grid_result: dict) -> None:
    """
    Render a heatmap visualization of grid analysis results.

    Args:
        grid_result: Grid analysis result from API containing:
            - adoption_rates: List of adoption rates (y-axis)
            - contribution_rates: List of contribution rates (x-axis)
            - results: List of analysis results
    """
    adoption_rates = grid_result["adoption_rates"]
    contribution_rates = grid_result["contribution_rates"]
    results = grid_result["results"]

    # Create matrices for heatmap
    n_adoption = len(adoption_rates)
    n_contribution = len(contribution_rates)

    # Initialize matrices
    pass_fail_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    margin_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    hce_acp_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    hover_text_matrix = [[None] * n_contribution for _ in range(n_adoption)]

    # Fill matrices from results
    for result in results:
        # Find indices
        try:
            adoption_idx = adoption_rates.index(result["adoption_rate"])
            contribution_idx = contribution_rates.index(result["contribution_rate"])
        except ValueError:
            continue

        # Store values
        pass_fail_matrix[adoption_idx][contribution_idx] = 1 if result["result"] == "PASS" else 0
        margin_matrix[adoption_idx][contribution_idx] = result["margin"]
        hce_acp_matrix[adoption_idx][contribution_idx] = result["hce_acp"]

        # Build hover text
        hover_text_matrix[adoption_idx][contribution_idx] = (
            f"Adoption: {result['adoption_rate']}%<br>"
            f"Contribution: {result['contribution_rate']}%<br>"
            f"<b>Result: {result['result']}</b><br>"
            f"HCE ACP: {result['hce_acp']:.2f}%<br>"
            f"NHCE ACP: {result['nhce_acp']:.2f}%<br>"
            f"Threshold: {result['threshold']:.2f}%<br>"
            f"Margin: {result['margin']:+.2f}%<br>"
            f"Limiting Test: {result['limiting_test']}"
        )

    # Display mode selector
    display_mode = st.radio(
        "Display Mode",
        options=["Pass/Fail", "Margin", "HCE ACP"],
        horizontal=True,
    )

    # Select data and colorscale based on mode
    if display_mode == "Pass/Fail":
        z_data = pass_fail_matrix
        colorscale = [[0, "#ef4444"], [1, "#22c55e"]]  # Red for fail, green for pass
        title = "ACP Test Results (Green=PASS, Red=FAIL)"
        showscale = False
        # Create text annotations for Pass/Fail
        text_matrix = [
            [
                "PASS" if val == 1 else "FAIL" if val == 0 else ""
                for val in row
            ]
            for row in pass_fail_matrix
        ]
    elif display_mode == "Margin":
        z_data = margin_matrix
        colorscale = "RdYlGn"  # Red-Yellow-Green diverging
        title = "ACP Test Margin (%) - Positive = Safety Buffer"
        showscale = True
        text_matrix = [
            [f"{val:+.1f}" if val is not None else "" for val in row]
            for row in margin_matrix
        ]
    else:  # HCE ACP
        z_data = hce_acp_matrix
        colorscale = "Viridis"
        title = "HCE ACP (%)"
        showscale = True
        text_matrix = [
            [f"{val:.1f}" if val is not None else "" for val in row]
            for row in hce_acp_matrix
        ]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[f"{r}%" for r in contribution_rates],
        y=[f"{r}%" for r in adoption_rates],
        text=text_matrix,
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertext=hover_text_matrix,
        hovertemplate="%{hovertext}<extra></extra>",
        colorscale=colorscale,
        showscale=showscale,
        zmin=-5 if display_mode == "Margin" else None,
        zmax=5 if display_mode == "Margin" else None,
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Contribution Rate",
        yaxis_title="Adoption Rate",
        height=400 + 30 * n_adoption,
        yaxis=dict(autorange="reversed"),  # Higher adoption at top
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add detailed drill-down
    render_drill_down(results, adoption_rates, contribution_rates)


def render_drill_down(
    results: list[dict],
    adoption_rates: list[float],
    contribution_rates: list[float],
) -> None:
    """Render a detailed view of a specific cell."""
    st.subheader("Scenario Details")

    col1, col2 = st.columns(2)

    with col1:
        selected_adoption = st.selectbox(
            "Adoption Rate (%)",
            options=adoption_rates,
            key="drill_adoption",
        )

    with col2:
        selected_contribution = st.selectbox(
            "Contribution Rate (%)",
            options=contribution_rates,
            key="drill_contribution",
        )

    # Find matching result
    matching_result = None
    for r in results:
        if (r["adoption_rate"] == selected_adoption and
            r["contribution_rate"] == selected_contribution):
            matching_result = r
            break

    if matching_result:
        # Display result details
        if matching_result["result"] == "PASS":
            st.success(f"**{matching_result['result']}**")
        else:
            st.error(f"**{matching_result['result']}**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("HCE ACP", f"{matching_result['hce_acp']:.3f}%")
            st.metric("NHCE ACP", f"{matching_result['nhce_acp']:.3f}%")

        with col2:
            st.metric("Threshold", f"{matching_result['threshold']:.3f}%")
            st.metric("Limiting Test", matching_result["limiting_test"])

        with col3:
            margin_delta = "+" if matching_result["margin"] >= 0 else ""
            st.metric("Margin", f"{margin_delta}{matching_result['margin']:.3f}%")
            st.metric("Seed", str(matching_result["seed"]))
    else:
        st.warning("No result found for selected parameters")
