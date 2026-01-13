"""
Typography Constants.

Defines font families, weights, and letter-spacing for consistent typography.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Typography:
    """Typography configuration for the application theme."""

    # Font family - system font stack
    font_family: str = (
        'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, '
        '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    )

    # Monospace font stack for code/data
    font_mono: str = (
        'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", monospace'
    )

    # Font weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700
    weight_extrabold: int = 800
    weight_black: int = 900

    # Letter spacing (tracking)
    tracking_tighter: str = "-0.05em"
    tracking_tight: str = "-0.025em"
    tracking_normal: str = "0"
    tracking_wide: str = "0.025em"
    tracking_wider: str = "0.05em"
    tracking_widest: str = "0.1em"

    # Line heights
    leading_none: str = "1"
    leading_tight: str = "1.25"
    leading_snug: str = "1.375"
    leading_normal: str = "1.5"
    leading_relaxed: str = "1.625"
    leading_loose: str = "2"


# Singleton instance for easy import
TYPOGRAPHY = Typography()
