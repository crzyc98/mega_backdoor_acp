"""
Export Page.

Handles exporting analysis results to CSV and PDF formats.
"""

import requests
import streamlit as st

from src.ui.components import render_empty_state
from src.ui.theme.colors import COLORS
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.shadows import SHADOWS
from src.ui.theme.typography import TYPOGRAPHY


API_BASE_URL = "http://localhost:8000/api/v1"


def get_selected_census() -> tuple[str, str] | None:
    """Get the currently selected census ID and name."""
    census_id = st.session_state.get("selected_census_id")
    census_name = st.session_state.get("selected_census_name")

    if census_id:
        return census_id, census_name
    return None


def _render_export_card(
    title: str,
    icon: str,
    description: str,
    accent_color: str,
    button_label: str,
    button_key: str,
    on_click_census_id: str,
    download_func,
) -> None:
    """Render a styled export option card."""
    # Card with accent border
    card_html = f"""
    <div style="
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-top: 4px solid {accent_color};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xl};
        box-shadow: {SHADOWS.sm};
        height: 100%;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: {SPACING.md};
            margin-bottom: {SPACING.md};
        ">
            <span style="font-size: 2rem;">{icon}</span>
            <span style="
                font-size: 1.25rem;
                font-weight: {TYPOGRAPHY.weight_semibold};
                color: {COLORS.gray_900};
            ">{title}</span>
        </div>
        <div style="
            color: {COLORS.gray_600};
            font-size: 0.95rem;
            line-height: {TYPOGRAPHY.leading_relaxed};
            margin-bottom: {SPACING.lg};
        ">{description}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Styled button below card
    if st.button(button_label, type="primary", key=button_key, use_container_width=True):
        download_func(on_click_census_id)


def render_export_options(census_id: str) -> None:
    """Render export format options."""
    st.markdown(
        f"""<div style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {COLORS.gray_900};
            margin-bottom: {SPACING.lg};
        ">Export Formats</div>""",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        _render_export_card(
            title="CSV Export",
            icon="📊",
            description="Export results to CSV format with full audit metadata header. Suitable for data analysis and archival.",
            accent_color=COLORS.success,  # Emerald for CSV
            button_label="📥 Download CSV",
            button_key="export_csv",
            on_click_census_id=census_id,
            download_func=download_csv,
        )

    with col2:
        _render_export_card(
            title="PDF Report",
            icon="📄",
            description="Generate a formatted PDF report suitable for compliance documentation and stakeholder review.",
            accent_color=COLORS.primary,  # Indigo for PDF
            button_label="📥 Download PDF",
            button_key="export_pdf",
            on_click_census_id=census_id,
            download_func=download_pdf,
        )


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
    st.markdown(
        f"""<div style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {COLORS.gray_900};
            margin-bottom: {SPACING.lg};
        ">Available Results</div>""",
        unsafe_allow_html=True
    )

    has_results = "last_result" in st.session_state or "last_grid_result" in st.session_state

    if not has_results:
        render_empty_state(
            icon="chart",
            title="No Results Available",
            description="Run an analysis to generate exportable results.",
            action_label="Go to Analysis",
            action_page="analysis",
        )
        return

    col1, col2 = st.columns(2)

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        status_color = COLORS.success if result["result"] == "PASS" else (COLORS.warning if result["result"] == "RISK" else COLORS.error)

        with col1:
            st.markdown(
                f"""<div style="
                    background: {COLORS.gray_50};
                    border: 1px solid {COLORS.gray_200};
                    border-radius: {BORDER_RADIUS.lg};
                    padding: {SPACING.lg};
                ">
                    <div style="
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: {TYPOGRAPHY.tracking_wide};
                        color: {COLORS.gray_500};
                        margin-bottom: {SPACING.xs};
                    ">Last Single Scenario</div>
                    <div style="
                        font-size: 0.95rem;
                        color: {COLORS.gray_700};
                        margin-bottom: {SPACING.sm};
                    ">Adoption: {result['adoption_rate']}%, Contribution: {result['contribution_rate']}%</div>
                    <div style="
                        display: inline-block;
                        padding: 4px 12px;
                        background: {status_color};
                        color: white;
                        border-radius: {BORDER_RADIUS.full};
                        font-weight: {TYPOGRAPHY.weight_semibold};
                        font-size: 0.875rem;
                    ">{result['result']}</div>
                    <span style="
                        color: {COLORS.gray_500};
                        font-size: 0.875rem;
                        margin-left: {SPACING.sm};
                    ">Margin: {result['margin']:.2f}%</span>
                </div>""",
                unsafe_allow_html=True
            )

    if "last_grid_result" in st.session_state:
        grid = st.session_state["last_grid_result"]

        with col2 if "last_result" in st.session_state else col1:
            st.markdown(
                f"""<div style="
                    background: {COLORS.gray_50};
                    border: 1px solid {COLORS.gray_200};
                    border-radius: {BORDER_RADIUS.lg};
                    padding: {SPACING.lg};
                ">
                    <div style="
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: {TYPOGRAPHY.tracking_wide};
                        color: {COLORS.gray_500};
                        margin-bottom: {SPACING.xs};
                    ">Last Grid Analysis</div>
                    <div style="
                        font-size: 1.5rem;
                        font-weight: {TYPOGRAPHY.weight_bold};
                        color: {COLORS.gray_900};
                    ">{grid['summary']['total_scenarios']} <span style="font-size: 0.875rem; font-weight: normal; color: {COLORS.gray_500};">scenarios</span></div>
                    <div style="
                        font-size: 0.95rem;
                        color: {COLORS.gray_600};
                        margin-top: {SPACING.xs};
                    ">Pass Rate: <span style="font-weight: {TYPOGRAPHY.weight_semibold}; color: {COLORS.success};">{grid['summary']['pass_rate']:.1f}%</span></div>
                </div>""",
                unsafe_allow_html=True
            )


def render_audit_info() -> None:
    """Display audit metadata information."""
    st.markdown(
        f"""<div style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {COLORS.gray_900};
            margin-bottom: {SPACING.lg};
        ">Audit Metadata</div>""",
        unsafe_allow_html=True
    )

    # Styled info card with icon
    items = [
        ("Census ID and name", "🏢"),
        ("Plan year", "📅"),
        ("Participant counts (HCE/NHCE)", "👥"),
        ("Generation timestamp", "🕐"),
        ("System version", "🔢"),
        ("Random seed (for reproducibility)", "🎲"),
    ]

    items_html = "".join([
        f"""<div style="
            display: flex;
            align-items: center;
            gap: {SPACING.sm};
            padding: {SPACING.xs} 0;
        ">
            <span style="font-size: 1rem;">{icon}</span>
            <span style="color: {COLORS.gray_700};">{text}</span>
        </div>"""
        for text, icon in items
    ])

    st.markdown(
        f"""<div style="
            background: {COLORS.primary_light};
            border: 1px solid {COLORS.primary};
            border-left: 4px solid {COLORS.primary};
            border-radius: {BORDER_RADIUS.lg};
            padding: {SPACING.lg};
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: {SPACING.sm};
                margin-bottom: {SPACING.md};
            ">
                <span style="font-size: 1.25rem;">ℹ️</span>
                <span style="
                    font-weight: {TYPOGRAPHY.weight_semibold};
                    color: {COLORS.primary};
                ">All exports include audit metadata for compliance documentation:</span>
            </div>
            {items_html}
        </div>""",
        unsafe_allow_html=True
    )


def render() -> None:
    """Main render function for export page."""
    # Page header with styled typography
    st.markdown(
        f"""<div style="
            font-size: 1.75rem;
            font-weight: {TYPOGRAPHY.weight_bold};
            color: {COLORS.gray_900};
            margin-bottom: {SPACING.lg};
        ">Export Results</div>""",
        unsafe_allow_html=True
    )

    # Check for selected census
    selected = get_selected_census()

    if selected is None:
        render_empty_state(
            icon="file",
            title="No Census Selected",
            description="Please upload and select a census, then run an analysis before exporting.",
            action_label="Go to Upload",
            action_page="upload",
        )
        return

    census_id, census_name = selected

    # Selected census badge
    st.markdown(
        f"""<div style="
            display: inline-flex;
            align-items: center;
            gap: {SPACING.sm};
            background: {COLORS.primary_light};
            border: 1px solid {COLORS.primary};
            border-radius: {BORDER_RADIUS.full};
            padding: {SPACING.xs} {SPACING.md};
            margin-bottom: {SPACING.xl};
        ">
            <span style="font-size: 1rem;">📋</span>
            <span style="
                font-weight: {TYPOGRAPHY.weight_medium};
                color: {COLORS.primary};
            ">Selected Census:</span>
            <span style="
                font-weight: {TYPOGRAPHY.weight_semibold};
                color: {COLORS.gray_900};
            ">{census_name}</span>
            <span style="
                font-size: 0.75rem;
                color: {COLORS.gray_500};
            ">({census_id[:8]}...)</span>
        </div>""",
        unsafe_allow_html=True
    )

    # Show available results
    render_last_results_summary()

    st.divider()

    # Export options
    render_export_options(census_id)

    st.divider()

    # Audit info
    render_audit_info()
