"""
Unit tests for theme color constants.

T054: Validates color palette constants are properly defined
and follow the expected Tailwind-inspired color system.
"""

import re

import pytest

from src.ui.theme.colors import COLORS, ColorPalette


class TestColorPalette:
    """Test the ColorPalette dataclass."""

    def test_colors_instance_is_color_palette(self):
        """COLORS should be an instance of ColorPalette."""
        assert isinstance(COLORS, ColorPalette)

    def test_color_palette_is_frozen(self):
        """ColorPalette should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            COLORS.primary = "#000000"

    def test_primary_color_is_indigo(self):
        """Primary color should be indigo (#4F46E5)."""
        assert COLORS.primary == "#4F46E5"

    def test_primary_hover_is_darker_indigo(self):
        """Primary hover should be darker indigo (#4338CA)."""
        assert COLORS.primary_hover == "#4338CA"

    def test_primary_light_is_light_indigo(self):
        """Primary light should be light indigo (#EEF2FF)."""
        assert COLORS.primary_light == "#EEF2FF"


class TestStatusColors:
    """Test status-related colors (PASS/RISK/FAIL/ERROR)."""

    def test_success_color_is_emerald(self):
        """Success color (PASS) should be emerald (#10B981)."""
        assert COLORS.success == "#10B981"

    def test_success_text_is_readable(self):
        """Success text should be dark for contrast."""
        assert COLORS.success_text == "#065F46"

    def test_warning_color_is_amber(self):
        """Warning color (RISK) should be amber (#FBBF24)."""
        assert COLORS.warning == "#FBBF24"

    def test_warning_text_is_readable(self):
        """Warning text should be dark for contrast."""
        assert COLORS.warning_text == "#92400E"

    def test_error_color_is_rose(self):
        """Error color (FAIL) should be rose (#F43F5E)."""
        assert COLORS.error == "#F43F5E"

    def test_error_text_is_readable(self):
        """Error text should be dark for contrast."""
        assert COLORS.error_text == "#9F1239"


class TestGrayScale:
    """Test gray scale colors."""

    def test_gray_50_is_lightest(self):
        """Gray-50 should be the lightest gray."""
        assert COLORS.gray_50 == "#F9FAFB"

    def test_gray_900_is_darkest(self):
        """Gray-900 should be the darkest gray."""
        assert COLORS.gray_900 == "#111827"

    def test_white_is_ffffff(self):
        """White should be #FFFFFF."""
        assert COLORS.white == "#FFFFFF"


class TestColorFormat:
    """Test that all colors follow the expected format."""

    HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
    SPECIAL_VALUES = {"transparent", "inherit", "initial", "unset"}

    def test_all_colors_are_valid_hex_or_special(self):
        """All color values should be valid 6-digit hex colors or special values."""
        color_attrs = [
            attr for attr in dir(COLORS)
            if not attr.startswith("_") and not callable(getattr(COLORS, attr))
        ]

        for attr in color_attrs:
            value = getattr(COLORS, attr)
            is_hex = self.HEX_COLOR_PATTERN.match(value) is not None
            is_special = value in self.SPECIAL_VALUES
            assert is_hex or is_special, (
                f"Color {attr}={value} is not a valid hex color or special value"
            )

    def test_hex_colors_are_uppercase(self):
        """Hex color values should use uppercase hex digits."""
        color_attrs = [
            attr for attr in dir(COLORS)
            if not attr.startswith("_") and not callable(getattr(COLORS, attr))
        ]

        for attr in color_attrs:
            value = getattr(COLORS, attr)
            # Skip special values
            if value in self.SPECIAL_VALUES:
                continue
            # After the # all digits should be uppercase
            hex_part = value[1:]
            assert hex_part == hex_part.upper(), (
                f"Color {attr}={value} should use uppercase hex"
            )


class TestColorRelationships:
    """Test relationships between related colors."""

    def test_success_light_is_lighter_than_success(self):
        """Success light should be lighter than success (higher RGB values)."""
        # Convert hex to RGB and compare brightness
        success_rgb = int(COLORS.success[1:3], 16), int(COLORS.success[3:5], 16), int(COLORS.success[5:7], 16)
        light_rgb = int(COLORS.success_light[1:3], 16), int(COLORS.success_light[3:5], 16), int(COLORS.success_light[5:7], 16)

        success_brightness = sum(success_rgb) / 3
        light_brightness = sum(light_rgb) / 3

        assert light_brightness > success_brightness

    def test_error_light_is_lighter_than_error(self):
        """Error light should be lighter than error."""
        error_rgb = int(COLORS.error[1:3], 16), int(COLORS.error[3:5], 16), int(COLORS.error[5:7], 16)
        light_rgb = int(COLORS.error_light[1:3], 16), int(COLORS.error_light[3:5], 16), int(COLORS.error_light[5:7], 16)

        error_brightness = sum(error_rgb) / 3
        light_brightness = sum(light_rgb) / 3

        assert light_brightness > error_brightness

    def test_warning_light_is_lighter_than_warning(self):
        """Warning light should be lighter than warning."""
        warning_rgb = int(COLORS.warning[1:3], 16), int(COLORS.warning[3:5], 16), int(COLORS.warning[5:7], 16)
        light_rgb = int(COLORS.warning_light[1:3], 16), int(COLORS.warning_light[3:5], 16), int(COLORS.warning_light[5:7], 16)

        warning_brightness = sum(warning_rgb) / 3
        light_brightness = sum(light_rgb) / 3

        assert light_brightness > warning_brightness
