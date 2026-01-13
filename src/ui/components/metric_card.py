"""
Styled Metric Card Component.

Renders metric values with labels in a styled card format.
"""

import streamlit as st
from typing import Literal

from src.ui.theme.colors import COLORS
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.shadows import SHADOWS
from src.ui.theme.typography import TYPOGRAPHY


DeltaColor = Literal["auto", "success", "warning", "error", "neutral"]


def _get_delta_color(delta_color: DeltaColor, delta_value: float | None) -> str:
    """Determine the color for a delta value."""
    if delta_color == "auto" and delta_value is not None:
        if delta_value > 0:
            return COLORS.success
        elif delta_value < 0:
            return COLORS.error
        else:
            return COLORS.gray_500
    elif delta_color == "success":
        return COLORS.success
    elif delta_color == "warning":
        return COLORS.warning
    elif delta_color == "error":
        return COLORS.error
    else:
        return COLORS.gray_500


def render_metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    delta_value: float | None = None,
    delta_color: DeltaColor = "auto",
    help_text: str | None = None,
) -> None:
    """
    Render a styled metric card.

    Args:
        label: Metric label (displayed above value)
        value: Metric value to display
        delta: Optional delta string (e.g., "+2.5%")
        delta_value: Numeric delta value for color determination (if delta_color="auto")
        delta_color: Color for delta (auto, success, warning, error, neutral)
        help_text: Optional help text displayed below
    """
    delta_color_hex = _get_delta_color(delta_color, delta_value)

    metric_html = f"""
    <div style="
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.md} {SPACING.lg};
        box-shadow: {SHADOWS.sm};
    ">
        <div style="
            font-size: 0.75rem;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {COLORS.gray_500};
            text-transform: uppercase;
            letter-spacing: {TYPOGRAPHY.tracking_wide};
            margin-bottom: {SPACING.xs};
        ">{label}</div>
        <div style="
            font-size: 1.5rem;
            font-weight: {TYPOGRAPHY.weight_bold};
            color: {COLORS.gray_900};
            line-height: 1.2;
        ">{value}</div>
    """

    if delta:
        metric_html += f"""
        <div style="
            font-size: 0.875rem;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {delta_color_hex};
            margin-top: {SPACING.xs};
        ">{delta}</div>
        """

    if help_text:
        metric_html += f"""
        <div style="
            font-size: 0.75rem;
            color: {COLORS.gray_400};
            margin-top: {SPACING.xs};
        ">{help_text}</div>
        """

    metric_html += "</div>"

    st.markdown(metric_html, unsafe_allow_html=True)


def render_metric_row(
    metrics: list[dict],
    columns: int = 4,
) -> None:
    """
    Render a row of metric cards.

    Args:
        metrics: List of metric dicts with keys: label, value, delta (optional),
                 delta_value (optional), delta_color (optional), help_text (optional)
        columns: Number of columns for the layout
    """
    cols = st.columns(columns)

    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_value=metric.get("delta_value"),
                delta_color=metric.get("delta_color", "auto"),
                help_text=metric.get("help_text"),
            )


def render_inline_metric(
    label: str,
    value: str,
    color: str = COLORS.gray_900,
) -> None:
    """
    Render a simple inline metric without card styling.

    Args:
        label: Metric label
        value: Metric value
        color: Color for the value text
    """
    metric_html = f"""
    <div style="display: flex; align-items: baseline; gap: {SPACING.sm};">
        <span style="
            font-size: 0.875rem;
            color: {COLORS.gray_500};
        ">{label}:</span>
        <span style="
            font-size: 1rem;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {color};
        ">{value}</span>
    </div>
    """

    st.markdown(metric_html, unsafe_allow_html=True)
