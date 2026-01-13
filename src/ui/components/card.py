"""
Styled Card Component.

Renders content in a styled card container with optional header and accent.
"""

import streamlit as st
from typing import Literal

from src.ui.theme.colors import COLORS
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.shadows import SHADOWS
from src.ui.theme.typography import TYPOGRAPHY


AccentColor = Literal["primary", "success", "warning", "error", "none"]


def _get_accent_color(accent: AccentColor) -> str:
    """Get the hex color for an accent type."""
    mapping = {
        "primary": COLORS.primary,
        "success": COLORS.success,
        "warning": COLORS.warning,
        "error": COLORS.error,
        "none": "transparent",
    }
    return mapping.get(accent, "transparent")


def render_card(
    title: str | None = None,
    content: str | None = None,
    accent: AccentColor = "none",
    padding: str = SPACING.xl,
) -> None:
    """
    Render a styled card container.

    This function creates an opening card div. Content should be added
    after calling this function, then close_card() should be called.

    Args:
        title: Optional card header text
        content: Optional content to render inside the card
        accent: Color accent for top border (primary, success, warning, error, none)
        padding: Padding inside the card
    """
    accent_color = _get_accent_color(accent)
    accent_style = f"border-top: 3px solid {accent_color};" if accent != "none" else ""

    card_html = f"""
    <div style="
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.xl};
        padding: {padding};
        box-shadow: {SHADOWS.sm};
        margin-bottom: {SPACING.lg};
        {accent_style}
    ">
    """

    if title:
        card_html += f"""
        <div style="
            font-weight: {TYPOGRAPHY.weight_semibold};
            font-size: 1.125rem;
            color: {COLORS.gray_900};
            margin-bottom: {SPACING.md};
            padding-bottom: {SPACING.sm};
            border-bottom: 1px solid {COLORS.gray_100};
        ">{title}</div>
        """

    if content:
        card_html += f"""
        <div style="color: {COLORS.gray_700};">{content}</div>
        """

    card_html += "</div>"

    st.markdown(card_html, unsafe_allow_html=True)


def card_container(
    title: str | None = None,
    accent: AccentColor = "none",
):
    """
    Context manager for card content using Streamlit container.

    Usage:
        with card_container("My Card"):
            st.write("Content goes here")

    Args:
        title: Optional card header text
        accent: Color accent for top border

    Returns:
        Streamlit container for card content
    """
    accent_color = _get_accent_color(accent)
    accent_css = f"border-top: 3px solid {accent_color} !important;" if accent != "none" else ""

    # Inject card-specific CSS
    card_css = f"""
    <style>
    div[data-testid="stVerticalBlock"]:has(> div.card-marker-{id(title)}) {{
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xl};
        box-shadow: {SHADOWS.sm};
        margin-bottom: {SPACING.lg};
        {accent_css}
    }}
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)

    container = st.container()

    with container:
        # Marker for CSS targeting
        st.markdown(f'<div class="card-marker-{id(title)}" style="display:none;"></div>', unsafe_allow_html=True)

        if title:
            st.markdown(
                f"""<div style="
                    font-weight: {TYPOGRAPHY.weight_semibold};
                    font-size: 1.125rem;
                    color: {COLORS.gray_900};
                    margin-bottom: {SPACING.md};
                    padding-bottom: {SPACING.sm};
                    border-bottom: 1px solid {COLORS.gray_100};
                ">{title}</div>""",
                unsafe_allow_html=True
            )

    return container
