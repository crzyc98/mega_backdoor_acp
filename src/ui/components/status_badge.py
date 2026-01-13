"""
Status Badge Component.

Renders PASS/RISK/FAIL/ERROR status indicators with consistent styling.
"""

import streamlit as st
from typing import Literal

from src.ui.theme.colors import COLORS
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.typography import TYPOGRAPHY
from src.ui.theme.status import get_status_style


StatusType = Literal["PASS", "RISK", "FAIL", "ERROR"]
BadgeSize = Literal["sm", "md", "lg"]


def render_status_badge(
    status: StatusType,
    size: BadgeSize = "md",
    show_icon: bool = True,
    show_label: bool = True,
) -> None:
    """
    Render a status badge with appropriate color and icon.

    Args:
        status: Status type (PASS, RISK, FAIL, ERROR)
        size: Badge size (sm, md, lg)
        show_icon: Whether to show the status icon
        show_label: Whether to show the status label text
    """
    style = get_status_style(status)

    # Size-based styling
    sizes = {
        "sm": {
            "padding": f"{SPACING.xs} {SPACING.sm}",
            "font_size": "0.75rem",
            "icon_size": "0.875rem",
            "gap": SPACING.xs,
        },
        "md": {
            "padding": f"{SPACING.xs} {SPACING.md}",
            "font_size": "0.875rem",
            "icon_size": "1rem",
            "gap": SPACING.xs,
        },
        "lg": {
            "padding": f"{SPACING.sm} {SPACING.lg}",
            "font_size": "1rem",
            "icon_size": "1.25rem",
            "gap": SPACING.sm,
        },
    }

    size_config = sizes.get(size, sizes["md"])

    badge_html = f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: {size_config["gap"]};
        padding: {size_config["padding"]};
        border-radius: {BORDER_RADIUS.full};
        background: {style.background};
        color: {style.color};
        font-weight: {TYPOGRAPHY.weight_semibold};
        font-size: {size_config["font_size"]};
        white-space: nowrap;
    ">
    """

    if show_icon:
        badge_html += f'<span style="font-size: {size_config["icon_size"]};">{style.icon}</span>'

    if show_label:
        badge_html += f"<span>{style.label}</span>"

    badge_html += "</span>"

    st.markdown(badge_html, unsafe_allow_html=True)


def render_status_large(
    status: StatusType,
    message: str | None = None,
) -> None:
    """
    Render a large, prominent status indicator.

    Args:
        status: Status type (PASS, RISK, FAIL, ERROR)
        message: Optional message to display below the status
    """
    style = get_status_style(status)

    status_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: {SPACING.md};
        padding: {SPACING.xl} {SPACING.xxl};
        border-radius: {BORDER_RADIUS.xl};
        background: {style.background};
        border: 2px solid {style.color};
        text-align: center;
    ">
        <div style="
            font-size: 3rem;
            line-height: 1;
        ">{style.icon}</div>
        <div style="
            font-size: 1.5rem;
            font-weight: {TYPOGRAPHY.weight_bold};
            color: {style.color};
            letter-spacing: {TYPOGRAPHY.tracking_wide};
        ">{style.label}</div>
    """

    if message:
        status_html += f"""
        <div style="
            font-size: 1rem;
            color: {COLORS.gray_600};
            margin-top: {SPACING.xs};
        ">{message}</div>
        """

    status_html += "</div>"

    st.markdown(status_html, unsafe_allow_html=True)


def get_status_color(status: StatusType) -> str:
    """
    Get the primary color for a status type.

    Args:
        status: Status type

    Returns:
        Hex color string
    """
    style = get_status_style(status)
    return style.color
