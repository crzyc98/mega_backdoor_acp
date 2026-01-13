"""
Streamlit Application Entry Point.

This module provides the main Streamlit application with page navigation
for the ACP Sensitivity Analyzer.
"""

import streamlit as st

from src.core.constants import SYSTEM_VERSION
from src.ui.theme import inject_theme_css, COLORS, TYPOGRAPHY, SPACING, BORDER_RADIUS


# Page configuration
st.set_page_config(
    page_title="ACP Sensitivity Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme CSS
inject_theme_css()

# Header branding with styled HTML
header_html = f"""
<div style="
    display: flex;
    align-items: center;
    gap: {SPACING.md};
    margin-bottom: {SPACING.lg};
    padding-bottom: {SPACING.md};
    border-bottom: 1px solid {COLORS.gray_200};
">
    <span style="font-size: 2rem;">📊</span>
    <div>
        <div style="
            font-size: 1.5rem;
            font-weight: {TYPOGRAPHY.weight_extrabold};
            color: {COLORS.gray_900};
            letter-spacing: {TYPOGRAPHY.tracking_tight};
        ">ACP Sensitivity Analyzer</div>
        <div style="
            display: flex;
            align-items: center;
            gap: {SPACING.sm};
        ">
            <span style="
                display: inline-block;
                padding: 2px 8px;
                background: {COLORS.primary_light};
                color: {COLORS.primary};
                border-radius: {BORDER_RADIUS.full};
                font-size: 0.75rem;
                font-weight: {TYPOGRAPHY.weight_semibold};
                text-transform: uppercase;
                letter-spacing: {TYPOGRAPHY.tracking_wide};
            ">v{SYSTEM_VERSION}</span>
            <span style="
                color: {COLORS.gray_500};
                font-size: 0.875rem;
            ">Mega-Backdoor Roth Compliance Testing</span>
        </div>
    </div>
</div>
"""

# Sidebar navigation with numbered steps
st.sidebar.markdown(
    f"""
    <div style="
        display: flex;
        align-items: center;
        gap: {SPACING.sm};
        margin-bottom: {SPACING.lg};
    ">
        <span style="font-size: 1.5rem;">📊</span>
        <span style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_bold};
            color: {COLORS.primary};
        ">ACP Analyzer</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Navigation options with numbered steps
pages = {
    "1. Upload Census": "upload",
    "2. Import Wizard": "import_wizard",
    "3. Run Analysis": "analysis",
    "4. Export Results": "export",
}

selected_page = st.sidebar.radio(
    "Navigate to",
    list(pages.keys()),
    label_visibility="collapsed",
)


def show_upload_page() -> None:
    """Display the census upload page."""
    st.markdown(header_html, unsafe_allow_html=True)
    from src.ui.pages.upload import render
    render()


def show_analysis_page() -> None:
    """Display the analysis configuration page."""
    st.markdown(header_html, unsafe_allow_html=True)
    from src.ui.pages.analysis import render
    render()


def show_export_page() -> None:
    """Display the export page."""
    st.markdown(header_html, unsafe_allow_html=True)
    from src.ui.pages.export import render
    render()


def show_import_wizard_page() -> None:
    """Display the import wizard page."""
    st.markdown(header_html, unsafe_allow_html=True)
    from src.ui.pages.import_wizard import render
    render()


# Main content based on selected page
if pages[selected_page] == "upload":
    show_upload_page()
elif pages[selected_page] == "import_wizard":
    show_import_wizard_page()
elif pages[selected_page] == "analysis":
    show_analysis_page()
elif pages[selected_page] == "export":
    show_export_page()

# Sidebar footer
st.sidebar.divider()

# Show selected census in sidebar with styled display
if "selected_census_id" in st.session_state:
    st.sidebar.markdown(
        f"""
        <div style="
            background: {COLORS.success_light};
            border: 1px solid {COLORS.success};
            border-radius: {BORDER_RADIUS.lg};
            padding: {SPACING.md};
        ">
            <div style="
                font-size: 0.75rem;
                color: {COLORS.success_text};
                text-transform: uppercase;
                letter-spacing: {TYPOGRAPHY.tracking_wide};
                margin-bottom: {SPACING.xs};
            ">Selected Census</div>
            <div style="
                font-weight: {TYPOGRAPHY.weight_semibold};
                color: {COLORS.gray_900};
            ">{st.session_state.get("selected_census_name", "Unknown")}</div>
            <div style="
                font-size: 0.75rem;
                color: {COLORS.gray_500};
                margin-top: {SPACING.xs};
            ">ID: {st.session_state['selected_census_id'][:8]}...</div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        f"""
        <div style="
            background: {COLORS.gray_50};
            border: 1px dashed {COLORS.gray_300};
            border-radius: {BORDER_RADIUS.lg};
            padding: {SPACING.md};
            text-align: center;
        ">
            <div style="
                font-size: 0.875rem;
                color: {COLORS.gray_500};
            ">No census selected</div>
            <div style="
                font-size: 0.75rem;
                color: {COLORS.gray_400};
                margin-top: {SPACING.xs};
            ">Upload or select a census to begin</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.sidebar.caption(
    f"""
    <div style="
        text-align: center;
        color: {COLORS.gray_400};
        font-size: 0.75rem;
        margin-top: {SPACING.md};
    ">
        ACP Sensitivity Analyzer v{SYSTEM_VERSION}
    </div>
    """,
)
