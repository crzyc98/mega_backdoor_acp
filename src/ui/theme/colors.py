"""
Color Palette Constants.

Tailwind CSS-inspired color palette for consistent styling across the application.
All colors are defined as hex strings.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Centralized color palette for the application theme."""

    # Primary colors (Indigo)
    primary: str = "#4F46E5"
    primary_hover: str = "#4338CA"
    primary_light: str = "#EEF2FF"
    primary_text: str = "#3730A3"

    # Success colors (Emerald) - PASS status
    success: str = "#10B981"
    success_light: str = "#ECFDF5"
    success_text: str = "#065F46"

    # Warning colors (Amber) - RISK status
    warning: str = "#FBBF24"
    warning_light: str = "#FFFBEB"
    warning_text: str = "#92400E"

    # Error colors (Rose) - FAIL status
    error: str = "#F43F5E"
    error_light: str = "#FFF1F2"
    error_text: str = "#9F1239"

    # Gray scale
    gray_50: str = "#F9FAFB"
    gray_100: str = "#F3F4F6"
    gray_200: str = "#E5E7EB"
    gray_300: str = "#D1D5DB"
    gray_400: str = "#9CA3AF"
    gray_500: str = "#6B7280"
    gray_600: str = "#4B5563"
    gray_700: str = "#374151"
    gray_800: str = "#1F2937"
    gray_900: str = "#111827"

    # Slate (for dark backgrounds)
    slate_800: str = "#1E293B"
    slate_900: str = "#0F172A"

    # White and transparent
    white: str = "#FFFFFF"
    transparent: str = "transparent"


# Singleton instance for easy import
COLORS = ColorPalette()
