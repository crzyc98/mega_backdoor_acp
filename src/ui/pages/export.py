"""
Export Page.

Handles exporting analysis results to CSV and PDF formats.
"""

import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000/api/v1"


def get_selected_census() -> tuple[str, str] | None:
    """Get the currently selected census ID and name."""
    census_id = st.session_state.get("selected_census_id")
    census_name = st.session_state.get("selected_census_name")

    if census_id:
        return census_id, census_name
    return None


def render_export_options(census_id: str) -> None:
    """Render export format options."""
    st.subheader("Export Format")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### CSV Export")
        st.write(
            "Export results to CSV format with full audit metadata header. "
            "Suitable for data analysis and archival."
        )
        if st.button("Download CSV", type="primary", key="export_csv"):
            download_csv(census_id)

    with col2:
        st.markdown("### PDF Report")
        st.write(
            "Generate a formatted PDF report suitable for compliance documentation "
            "and stakeholder review."
        )
        if st.button("Download PDF", type="primary", key="export_pdf"):
            download_pdf(census_id)


def download_csv(census_id: str, grid_id: str | None = None) -> None:
    """Download CSV export."""
    try:
        url = f"{API_BASE_URL}/export/{census_id}/csv"
        if grid_id:
            url += f"?grid_id={grid_id}"

        with st.spinner("Generating CSV..."):
            response = requests.get(url, timeout=60)

        if response.status_code == 200:
            # Get filename from header
            content_disposition = response.headers.get("Content-Disposition", "")
            filename = "acp_results.csv"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

            st.download_button(
                label="Click to Download CSV",
                data=response.content,
                file_name=filename,
                mime="text/csv",
                key="download_csv_button",
            )
            st.success("CSV generated successfully!")
        elif response.status_code == 404:
            st.error("No analysis results found. Run an analysis first.")
        else:
            st.error(f"Export failed: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server.")
    except Exception as e:
        st.error(f"Export failed: {str(e)}")


def download_pdf(census_id: str, grid_id: str | None = None) -> None:
    """Download PDF export."""
    try:
        url = f"{API_BASE_URL}/export/{census_id}/pdf"
        if grid_id:
            url += f"?grid_id={grid_id}"

        with st.spinner("Generating PDF..."):
            response = requests.get(url, timeout=60)

        if response.status_code == 200:
            # Get filename from header
            content_disposition = response.headers.get("Content-Disposition", "")
            filename = "acp_report.pdf"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

            st.download_button(
                label="Click to Download PDF",
                data=response.content,
                file_name=filename,
                mime="application/pdf",
                key="download_pdf_button",
            )
            st.success("PDF generated successfully!")
        elif response.status_code == 404:
            st.error("No analysis results found. Run an analysis first.")
        else:
            st.error(f"Export failed: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server.")
    except Exception as e:
        st.error(f"Export failed: {str(e)}")


def render_last_results_summary() -> None:
    """Show summary of last results for context."""
    st.subheader("Available Results")

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        st.write("**Last Single Scenario:**")
        st.write(f"- Adoption: {result['adoption_rate']}%, Contribution: {result['contribution_rate']}%")
        st.write(f"- Result: **{result['result']}** (Margin: {result['margin']:.2f}%)")

    if "last_grid_result" in st.session_state:
        grid = st.session_state["last_grid_result"]
        st.write("**Last Grid Analysis:**")
        st.write(f"- {grid['summary']['total_scenarios']} scenarios")
        st.write(f"- Pass Rate: {grid['summary']['pass_rate']:.1f}%")


def render_audit_info() -> None:
    """Display audit metadata information."""
    st.subheader("Audit Metadata")
    st.info(
        "All exports include audit metadata for compliance documentation:\n\n"
        "- Census ID and name\n"
        "- Plan year\n"
        "- Participant counts (HCE/NHCE)\n"
        "- Generation timestamp\n"
        "- System version\n"
        "- Random seed (for reproducibility)"
    )


def render() -> None:
    """Main render function for export page."""
    st.header("Export Results")

    # Check for selected census
    selected = get_selected_census()

    if selected is None:
        st.warning(
            "No census selected. Please upload and select a census, "
            "then run an analysis before exporting."
        )
        return

    census_id, census_name = selected
    st.info(f"**Selected Census:** {census_name} ({census_id[:8]}...)")

    # Show available results
    render_last_results_summary()

    st.divider()

    # Export options
    render_export_options(census_id)

    st.divider()

    # Audit info
    render_audit_info()
