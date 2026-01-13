"""
Empty State Component.

Renders styled placeholder content when data is not available.
"""

import streamlit as st
from typing import Callable, Literal

from src.ui.theme.colors import COLORS
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.shadows import SHADOWS
from src.ui.theme.typography import TYPOGRAPHY


IconType = Literal["upload", "chart", "users", "file", "search", "error", "info"]


def _get_icon(icon_type: IconType) -> str:
    """Get the emoji/icon for a given type."""
    icons = {
        "upload": "📤",
        "chart": "📊",
        "users": "👥",
        "file": "📄",
        "search": "🔍",
        "error": "⚠️",
        "info": "ℹ️",
    }
    return icons.get(icon_type, "📋")


def render_empty_state(
    icon: IconType = "info",
    title: str = "No Data Available",
    description: str | None = None,
    action_label: str | None = None,
    action_page: str | None = None,
) -> None:
    """
    Render a styled empty state placeholder.

    Args:
        icon: Icon type to display (upload, chart, users, file, search, error, info)
        title: Main message title
        description: Optional descriptive text
        action_label: Optional action button label
        action_page: Page name to navigate to when action is clicked
    """
    icon_emoji = _get_icon(icon)

    empty_html = f"""
    <div style="
        background: {COLORS.gray_50};
        border: 2px dashed {COLORS.gray_300};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xxxl} {SPACING.xl};
        text-align: center;
        margin: {SPACING.xl} 0;
    ">
        <div style="
            font-size: 3rem;
            margin-bottom: {SPACING.lg};
        ">{icon_emoji}</div>
        <div style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {COLORS.gray_700};
            margin-bottom: {SPACING.sm};
        ">{title}</div>
    """

    if description:
        empty_html += f"""
        <div style="
            font-size: 1rem;
            color: {COLORS.gray_500};
            max-width: 400px;
            margin: 0 auto;
            line-height: {TYPOGRAPHY.leading_relaxed};
        ">{description}</div>
        """

    empty_html += "</div>"

    st.markdown(empty_html, unsafe_allow_html=True)

    # Render action button if specified
    if action_label and action_page:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(action_label, type="primary", use_container_width=True):
                st.session_state["page"] = action_page
                st.rerun()


def render_loading_state(
    message: str = "Loading...",
) -> None:
    """
    Render a loading state placeholder.

    Args:
        message: Loading message to display
    """
    loading_html = f"""
    <div style="
        background: {COLORS.gray_50};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xxl} {SPACING.xl};
        text-align: center;
        margin: {SPACING.xl} 0;
    ">
        <div style="
            font-size: 2rem;
            margin-bottom: {SPACING.md};
            animation: pulse 2s infinite;
        ">⏳</div>
        <div style="
            font-size: 1rem;
            color: {COLORS.gray_500};
        ">{message}</div>
    </div>
    <style>
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    </style>
    """

    st.markdown(loading_html, unsafe_allow_html=True)


def render_error_state(
    title: str = "Something went wrong",
    message: str | None = None,
    retry_callback: Callable | None = None,
) -> None:
    """
    Render an error state placeholder.

    Args:
        title: Error title
        message: Optional error details
        retry_callback: Optional callback function for retry button
    """
    error_html = f"""
    <div style="
        background: {COLORS.error_light};
        border: 1px solid {COLORS.error};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xl};
        text-align: center;
        margin: {SPACING.xl} 0;
    ">
        <div style="
            font-size: 2.5rem;
            margin-bottom: {SPACING.md};
        ">⚠️</div>
        <div style="
            font-size: 1.25rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {COLORS.error};
            margin-bottom: {SPACING.sm};
        ">{title}</div>
    """

    if message:
        error_html += f"""
        <div style="
            font-size: 0.875rem;
            color: {COLORS.gray_600};
            max-width: 400px;
            margin: 0 auto;
        ">{message}</div>
        """

    error_html += "</div>"

    st.markdown(error_html, unsafe_allow_html=True)

    if retry_callback:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Try Again", type="primary", use_container_width=True):
                retry_callback()
