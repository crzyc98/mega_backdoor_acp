"""
Results Table Component.

Displays ACP analysis results in a formatted table.
"""

import streamlit as st


def render_results_table(results: list[dict], show_audit: bool = True) -> None:
    """
    Render a table of analysis results.

    Args:
        results: List of analysis result dictionaries
        show_audit: Whether to show audit metadata columns
    """
    if not results:
        st.info("No results to display")
        return

    # Prepare table data
    table_data = []
    for r in results:
        row = {
            "Result": "PASS" if r["result"] == "PASS" else "FAIL",
            "Adoption %": f"{r['adoption_rate']:.1f}",
            "Contribution %": f"{r['contribution_rate']:.1f}",
            "HCE ACP %": f"{r['hce_acp']:.3f}",
            "NHCE ACP %": f"{r['nhce_acp']:.3f}",
            "Threshold %": f"{r['threshold']:.3f}",
            "Margin %": f"{r['margin']:+.3f}",
            "Limiting Test": r["limiting_test"],
        }
        if show_audit:
            row["Seed"] = str(r["seed"])
            row["Version"] = r["version"]
        table_data.append(row)

    # Display as dataframe
    st.dataframe(
        table_data,
        use_container_width=True,
        column_config={
            "Result": st.column_config.TextColumn(
                "Result",
                help="Pass or fail status",
                width="small",
            ),
            "Margin %": st.column_config.TextColumn(
                "Margin %",
                help="Positive = safety buffer, Negative = exceeded threshold by",
            ),
        },
    )


def render_single_result(result: dict) -> None:
    """
    Render a single analysis result with details.

    Args:
        result: Single analysis result dictionary
    """
    # Pass/Fail indicator with styling
    if result["result"] == "PASS":
        st.success(f"## PASS")
    else:
        st.error(f"## FAIL")

    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "HCE ACP",
            f"{result['hce_acp']:.2f}%",
            help="Highly Compensated Employee group ACP",
        )

    with col2:
        st.metric(
            "NHCE ACP",
            f"{result['nhce_acp']:.2f}%",
            help="Non-Highly Compensated Employee group ACP",
        )

    with col3:
        st.metric(
            "Threshold",
            f"{result['threshold']:.2f}%",
            help="Maximum allowed HCE ACP",
        )

    with col4:
        margin_sign = "+" if result["margin"] >= 0 else ""
        st.metric(
            "Margin",
            f"{margin_sign}{result['margin']:.2f}%",
            help="Distance from threshold",
        )

    # Additional details
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Parameters:**")
        st.write(f"- Adoption Rate: {result['adoption_rate']}%")
        st.write(f"- Contribution Rate: {result['contribution_rate']}%")
        st.write(f"- Limiting Test: {result['limiting_test']}")

    with col2:
        st.write("**Audit Information:**")
        st.write(f"- Seed: {result['seed']}")
        st.write(f"- Version: {result['version']}")
        if "run_timestamp" in result:
            st.write(f"- Run Time: {result['run_timestamp']}")

    # Formula explanation
    with st.expander("Formula Details"):
        st.markdown(f"""
        **IRS ACP Test (IRC Section 401(m)):**

        The test passes if HCE ACP  Threshold, where:

        - **1.25x Test:** NHCE ACP ({result['nhce_acp']:.3f}%) × 1.25 = {result['nhce_acp'] * 1.25:.3f}%
        - **+2.0 Test:** NHCE ACP ({result['nhce_acp']:.3f}%) + 2.0 = {result['nhce_acp'] + 2:.3f}%

        The threshold is the **higher** of these two values.

        **Result:** {result['limiting_test']} test was limiting (threshold = {result['threshold']:.3f}%)

        HCE ACP ({result['hce_acp']:.3f}%) {'≤' if result['result'] == 'PASS' else '>'} Threshold ({result['threshold']:.3f}%)  **{result['result']}**
        """)
