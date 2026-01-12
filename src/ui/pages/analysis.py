"""
Analysis Configuration and Results Page.

Handles single scenario and grid analysis configuration and display.
"""

import requests
import streamlit as st

from src.core.constants import DEFAULT_RANDOM_SEED


API_BASE_URL = "http://localhost:8000/api/v1"


def _download_csv(census_id: str, grid_id: str | None = None) -> None:
    """Download CSV export."""
    try:
        url = f"{API_BASE_URL}/export/{census_id}/csv"
        if grid_id:
            url += f"?grid_id={grid_id}"

        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            content_disposition = response.headers.get("Content-Disposition", "")
            filename = "acp_results.csv"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

            st.download_button(
                label="Download CSV",
                data=response.content,
                file_name=filename,
                mime="text/csv",
                key=f"csv_dl_{grid_id or 'single'}",
            )
        else:
            st.error(f"Export failed: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server.")
    except Exception as e:
        st.error(f"Export failed: {str(e)}")


def _download_pdf(census_id: str, grid_id: str | None = None) -> None:
    """Download PDF export."""
    try:
        url = f"{API_BASE_URL}/export/{census_id}/pdf"
        if grid_id:
            url += f"?grid_id={grid_id}"

        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            content_disposition = response.headers.get("Content-Disposition", "")
            filename = "acp_report.pdf"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

            st.download_button(
                label="Download PDF",
                data=response.content,
                file_name=filename,
                mime="application/pdf",
                key=f"pdf_dl_{grid_id or 'single'}",
            )
        else:
            st.error(f"Export failed: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server.")
    except Exception as e:
        st.error(f"Export failed: {str(e)}")


def get_selected_census() -> tuple[str, str] | None:
    """Get the currently selected census ID and name."""
    census_id = st.session_state.get("selected_census_id")
    census_name = st.session_state.get("selected_census_name")

    if census_id:
        return census_id, census_name
    return None


def render_single_scenario_form(census_id: str) -> None:
    """Render single scenario analysis form."""
    st.subheader("Single Scenario Analysis")

    col1, col2 = st.columns(2)

    with col1:
        adoption_rate = st.slider(
            "HCE Adoption Rate (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Percentage of HCEs who adopt mega-backdoor Roth",
        )

    with col2:
        contribution_rate = st.slider(
            "Contribution Rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=6.0,
            step=0.5,
            help="After-tax contribution rate as percentage of compensation",
        )

    # Advanced options
    with st.expander("Advanced Options"):
        use_custom_seed = st.checkbox("Use custom random seed")
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=2**31 - 1,
            value=DEFAULT_RANDOM_SEED,
            disabled=not use_custom_seed,
            help="Seed for reproducible HCE selection",
        )

    if st.button("Run Analysis", type="primary", key="run_single"):
        run_single_analysis(
            census_id=census_id,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            seed=seed if use_custom_seed else None,
        )


def run_single_analysis(
    census_id: str,
    adoption_rate: float,
    contribution_rate: float,
    seed: int | None = None,
) -> None:
    """Run single scenario analysis."""
    try:
        payload = {
            "adoption_rate": adoption_rate,
            "contribution_rate": contribution_rate,
        }
        if seed is not None:
            payload["seed"] = seed

        with st.spinner("Running analysis..."):
            response = requests.post(
                f"{API_BASE_URL}/census/{census_id}/analysis",
                json=payload,
                timeout=60,
            )

        if response.status_code == 200:
            result = response.json()
            display_single_result(result)
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Analysis failed: {error_detail}")

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to API server. "
            "Make sure the API is running on localhost:8000"
        )
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")


def display_single_result(result: dict) -> None:
    """Display single scenario result."""
    st.divider()
    st.subheader("Analysis Result")

    # Pass/Fail indicator
    if result["result"] == "PASS":
        st.success(f"## PASS")
    else:
        st.error(f"## FAIL")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("HCE ACP", f"{result['hce_acp']:.2f}%")

    with col2:
        st.metric("NHCE ACP", f"{result['nhce_acp']:.2f}%")

    with col3:
        st.metric("Threshold", f"{result['threshold']:.2f}%")

    with col4:
        margin_delta = "+" if result["margin"] >= 0 else ""
        st.metric("Margin", f"{margin_delta}{result['margin']:.2f}%")

    # Details
    st.caption(
        f"**Limiting Test:** {result['limiting_test']} | "
        f"**Seed:** {result['seed']} | "
        f"**Adoption:** {result['adoption_rate']}% | "
        f"**Contribution:** {result['contribution_rate']}%"
    )

    # Store result in session for export
    st.session_state["last_result"] = result

    # Export buttons
    st.divider()
    st.subheader("Export Results")
    census_id = st.session_state.get("selected_census_id")
    if census_id:
        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            if st.button("Export to CSV", key="single_csv_export"):
                _download_csv(census_id)
        with col2:
            if st.button("Export to PDF", key="single_pdf_export"):
                _download_pdf(census_id)


def render_grid_analysis_form(census_id: str) -> None:
    """Render grid analysis form."""
    st.subheader("Grid Analysis")

    # Preset options
    preset = st.selectbox(
        "Grid Preset",
        options=["Standard Grid", "Fine Grid", "Custom"],
        help="Choose a preset or customize the grid",
    )

    if preset == "Standard Grid":
        adoption_rates = [0, 25, 50, 75, 100]
        contribution_rates = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    elif preset == "Fine Grid":
        adoption_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        contribution_rates = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    else:
        # Custom
        col1, col2 = st.columns(2)
        with col1:
            adoption_rates = st.multiselect(
                "Adoption Rates (%)",
                options=list(range(0, 101, 5)),
                default=[0, 25, 50, 75, 100],
            )
        with col2:
            contribution_rates = st.multiselect(
                "Contribution Rates (%)",
                options=[float(x) for x in range(1, 16)],
                default=[2.0, 4.0, 6.0, 8.0, 10.0, 12.0],
            )

    st.caption(
        f"Grid size: {len(adoption_rates)} x {len(contribution_rates)} = "
        f"{len(adoption_rates) * len(contribution_rates)} scenarios"
    )

    # Advanced options
    with st.expander("Advanced Options"):
        use_custom_seed = st.checkbox("Use custom random seed", key="grid_seed_check")
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=2**31 - 1,
            value=DEFAULT_RANDOM_SEED,
            disabled=not use_custom_seed,
            help="Seed for reproducible HCE selection",
            key="grid_seed",
        )
        grid_name = st.text_input(
            "Grid Name (optional)",
            placeholder="e.g., Q4 Analysis",
        )

    if st.button("Run Grid Analysis", type="primary", key="run_grid"):
        if len(adoption_rates) < 2 or len(contribution_rates) < 2:
            st.error("Grid requires at least 2 values for each dimension")
        else:
            run_grid_analysis(
                census_id=census_id,
                adoption_rates=sorted(adoption_rates),
                contribution_rates=sorted(contribution_rates),
                seed=seed if use_custom_seed else None,
                name=grid_name if grid_name else None,
            )


def run_grid_analysis(
    census_id: str,
    adoption_rates: list[int],
    contribution_rates: list[float],
    seed: int | None = None,
    name: str | None = None,
) -> None:
    """Run grid scenario analysis."""
    try:
        payload = {
            "adoption_rates": [float(r) for r in adoption_rates],
            "contribution_rates": contribution_rates,
        }
        if seed is not None:
            payload["seed"] = seed
        if name:
            payload["name"] = name

        with st.spinner(f"Running {len(adoption_rates) * len(contribution_rates)} scenarios..."):
            response = requests.post(
                f"{API_BASE_URL}/census/{census_id}/grid",
                json=payload,
                timeout=120,
            )

        if response.status_code == 200:
            result = response.json()
            display_grid_result(result)
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Grid analysis failed: {error_detail}")

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to API server. "
            "Make sure the API is running on localhost:8000"
        )
    except Exception as e:
        st.error(f"Grid analysis failed: {str(e)}")


def display_grid_result(result: dict) -> None:
    """Display grid analysis result with heatmap."""
    st.divider()
    st.subheader("Grid Analysis Results")

    # Summary metrics
    summary = result["summary"]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Scenarios", summary["total_scenarios"])
    with col2:
        st.metric("Passed", summary["pass_count"])
    with col3:
        st.metric("Failed", summary["fail_count"])
    with col4:
        st.metric("Pass Rate", f"{summary['pass_rate']:.1f}%")

    # Heatmap visualization
    from src.ui.components.heatmap import render_heatmap
    render_heatmap(result)

    # Store result in session
    st.session_state["last_grid_result"] = result

    # Export buttons
    st.divider()
    st.subheader("Export Grid Results")
    census_id = st.session_state.get("selected_census_id")
    grid_id = result.get("id")
    if census_id and grid_id:
        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            if st.button("Export to CSV", key="grid_csv_export"):
                _download_csv(census_id, grid_id)
        with col2:
            if st.button("Export to PDF", key="grid_pdf_export"):
                _download_pdf(census_id, grid_id)


def render_results_history(census_id: str) -> None:
    """Render analysis results history."""
    st.subheader("Analysis History")

    try:
        response = requests.get(
            f"{API_BASE_URL}/census/{census_id}/results",
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("items", [])

            if not results:
                st.info("No analysis results yet. Run an analysis above.")
                return

            # Group by grid_analysis_id
            single_results = [r for r in results if r["grid_analysis_id"] is None]
            grid_results = [r for r in results if r["grid_analysis_id"] is not None]

            if single_results:
                st.write("**Single Scenario Results:**")
                for r in single_results[:5]:  # Show last 5
                    result_icon = "" if r["result"] == "PASS" else ""
                    st.caption(
                        f"{result_icon} Adoption: {r['adoption_rate']}%, "
                        f"Contribution: {r['contribution_rate']}% - "
                        f"{r['result']} (margin: {r['margin']:.2f}%)"
                    )

            if grid_results:
                st.write("**Grid Analysis Results:**")
                st.caption(f"Total grid scenarios: {len(grid_results)}")

        else:
            st.warning("Could not load results history")

    except Exception as e:
        st.warning(f"Error loading history: {str(e)}")


def render() -> None:
    """Main render function for analysis page."""
    st.header("Run ACP Analysis")

    # Check for selected census
    selected = get_selected_census()

    if selected is None:
        st.warning(
            "No census selected. Please upload and select a census on the Upload page."
        )
        if st.button("Go to Upload Page"):
            st.switch_page("Upload Census")
        return

    census_id, census_name = selected

    # Show selected census
    st.info(f"**Selected Census:** {census_name} ({census_id[:8]}...)")

    # Analysis tabs
    tab1, tab2, tab3 = st.tabs(["Single Scenario", "Grid Analysis", "History"])

    with tab1:
        render_single_scenario_form(census_id)

    with tab2:
        render_grid_analysis_form(census_id)

    with tab3:
        render_results_history(census_id)
