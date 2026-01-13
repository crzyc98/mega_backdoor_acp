"""
Theme Module.

Provides centralized styling constants and utilities for the ACP Sensitivity Analyzer UI.
"""

from src.ui.theme.colors import COLORS, ColorPalette
from src.ui.theme.typography import TYPOGRAPHY, Typography
from src.ui.theme.spacing import SPACING, BORDER_RADIUS, Spacing, BorderRadius
from src.ui.theme.shadows import SHADOWS, Shadows
from src.ui.theme.status import (
    STATUS_CONFIG,
    CONSTRAINT_CONFIG,
    StatusConfig,
    ConstraintConfig,
    StatusStyle,
    ConstraintStyle,
    get_status_style,
    get_constraint_style,
)
from src.ui.theme.css import (
    get_all_css,
    get_base_css,
    get_card_css,
    get_navigation_css,
    get_button_css,
    get_form_css,
    get_table_css,
    get_status_css,
    get_alert_css,
)
from src.ui.theme.inject import (
    inject_theme_css,
    inject_custom_css,
    inject_html,
)

__all__ = [
    # Colors
    "COLORS",
    "ColorPalette",
    # Typography
    "TYPOGRAPHY",
    "Typography",
    # Spacing
    "SPACING",
    "BORDER_RADIUS",
    "Spacing",
    "BorderRadius",
    # Shadows
    "SHADOWS",
    "Shadows",
    # Status
    "STATUS_CONFIG",
    "CONSTRAINT_CONFIG",
    "StatusConfig",
    "ConstraintConfig",
    "StatusStyle",
    "ConstraintStyle",
    "get_status_style",
    "get_constraint_style",
    # CSS
    "get_all_css",
    "get_base_css",
    "get_card_css",
    "get_navigation_css",
    "get_button_css",
    "get_form_css",
    "get_table_css",
    "get_status_css",
    "get_alert_css",
    # Injection
    "inject_theme_css",
    "inject_custom_css",
    "inject_html",
]
