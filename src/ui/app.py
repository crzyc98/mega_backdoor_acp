"""
Streamlit Application Entry Point.

This module provides the main Streamlit application with page navigation
for the ACP Sensitivity Analyzer.
"""

import streamlit as st

from src.core.constants import SYSTEM_VERSION


# Page configuration
st.set_page_config(
    page_title="ACP Sensitivity Analyzer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("ACP Sensitivity Analyzer")
st.sidebar.caption(f"Version {SYSTEM_VERSION}")

# Navigation options
pages = {
    "Upload Census": "upload",
    "Run Analysis": "analysis",
    "Export Results": "export",
}

selected_page = st.sidebar.radio("Navigate to", list(pages.keys()))


def show_upload_page() -> None:
    """Display the census upload page."""
    from src.ui.pages.upload import render
    render()


def show_analysis_page() -> None:
    """Display the analysis configuration page."""
    from src.ui.pages.analysis import render
    render()


def show_export_page() -> None:
    """Display the export page."""
    from src.ui.pages.export import render
    render()


# Main content based on selected page
if pages[selected_page] == "upload":
    show_upload_page()
elif pages[selected_page] == "analysis":
    show_analysis_page()
elif pages[selected_page] == "export":
    show_export_page()

# Footer
st.sidebar.divider()
st.sidebar.caption("ACP Sensitivity Analyzer")
st.sidebar.caption("Mega-Backdoor Roth Compliance Testing")

# Show selected census in sidebar
if "selected_census_id" in st.session_state:
    st.sidebar.divider()
    st.sidebar.success(f"**Selected Census:**")
    st.sidebar.write(st.session_state.get("selected_census_name", "Unknown"))
    st.sidebar.caption(f"ID: {st.session_state['selected_census_id'][:8]}...")
