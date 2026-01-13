"""
Shadow Constants.

Defines box shadow values for depth and elevation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Shadows:
    """Box shadow scale for elevation effects."""

    # No shadow
    none: str = "none"

    # Extra small shadow for minimal elevation
    xs: str = "0 1px 2px 0 rgb(0 0 0 / 0.03)"

    # Subtle shadow for slight elevation
    sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"

    # Default shadow for cards and containers
    default: str = "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)"

    # Medium shadow for elevated elements
    md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"

    # Large shadow for modals and dropdowns
    lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"

    # Extra large shadow for prominent elements
    xl: str = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"

    # Inner shadow for inset effects
    inner: str = "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)"


# Singleton instance for easy import
SHADOWS = Shadows()
