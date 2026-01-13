"""
Unit tests for CSS generation utilities.

T055: Validates CSS generation functions produce valid CSS
with proper theme integration.
"""

import pytest

from src.ui.theme.css import (
    get_base_css,
    get_card_css,
    get_navigation_css,
    get_button_css,
    get_form_css,
    get_table_css,
    get_status_css,
    get_alert_css,
    get_all_css,
)
from src.ui.theme.colors import COLORS


class TestBaseCss:
    """Test base CSS generation."""

    def test_returns_string(self):
        """get_base_css should return a string."""
        result = get_base_css()
        assert isinstance(result, str)

    def test_contains_font_family(self):
        """Base CSS should set font-family."""
        result = get_base_css()
        assert "font-family" in result

    def test_contains_heading_styles(self):
        """Base CSS should style headings."""
        result = get_base_css()
        assert "h1" in result
        assert "h2" in result
        assert "h3" in result

    def test_uses_theme_colors(self):
        """Base CSS should use theme color values."""
        result = get_base_css()
        # Should reference the gray-900 color for headings
        assert COLORS.gray_900 in result


class TestCardCss:
    """Test card CSS generation."""

    def test_returns_string(self):
        """get_card_css should return a string."""
        result = get_card_css()
        assert isinstance(result, str)

    def test_defines_card_class(self):
        """Card CSS should define .acp-card class."""
        result = get_card_css()
        assert ".acp-card" in result

    def test_includes_border_radius(self):
        """Card CSS should include border-radius."""
        result = get_card_css()
        assert "border-radius" in result

    def test_includes_box_shadow(self):
        """Card CSS should include box-shadow."""
        result = get_card_css()
        assert "box-shadow" in result


class TestNavigationCss:
    """Test navigation CSS generation."""

    def test_returns_string(self):
        """get_navigation_css should return a string."""
        result = get_navigation_css()
        assert isinstance(result, str)

    def test_styles_sidebar(self):
        """Navigation CSS should style the sidebar."""
        result = get_navigation_css()
        assert "stSidebar" in result

    def test_includes_active_state(self):
        """Navigation CSS should include active state styling."""
        result = get_navigation_css()
        assert "active" in result.lower() or "checked" in result.lower()


class TestButtonCss:
    """Test button CSS generation."""

    def test_returns_string(self):
        """get_button_css should return a string."""
        result = get_button_css()
        assert isinstance(result, str)

    def test_styles_streamlit_buttons(self):
        """Button CSS should target Streamlit button classes."""
        result = get_button_css()
        assert ".stButton" in result

    def test_includes_hover_state(self):
        """Button CSS should include hover state."""
        result = get_button_css()
        assert ":hover" in result

    def test_includes_primary_color(self):
        """Button CSS should use primary theme color."""
        result = get_button_css()
        assert COLORS.primary in result

    def test_includes_transition(self):
        """Button CSS should include smooth transitions."""
        result = get_button_css()
        assert "transition" in result


class TestFormCss:
    """Test form CSS generation."""

    def test_returns_string(self):
        """get_form_css should return a string."""
        result = get_form_css()
        assert isinstance(result, str)

    def test_styles_text_input(self):
        """Form CSS should style text inputs."""
        result = get_form_css()
        assert ".stTextInput" in result

    def test_styles_selectbox(self):
        """Form CSS should style selectboxes."""
        result = get_form_css()
        assert ".stSelectbox" in result

    def test_styles_slider(self):
        """Form CSS should style sliders."""
        result = get_form_css()
        assert ".stSlider" in result

    def test_styles_file_uploader(self):
        """Form CSS should style file uploader."""
        result = get_form_css()
        assert ".stFileUploader" in result

    def test_includes_focus_states(self):
        """Form CSS should include focus states."""
        result = get_form_css()
        assert ":focus" in result

    def test_uses_primary_accent(self):
        """Form CSS should use primary color as accent."""
        result = get_form_css()
        assert COLORS.primary in result


class TestTableCss:
    """Test table CSS generation."""

    def test_returns_string(self):
        """get_table_css should return a string."""
        result = get_table_css()
        assert isinstance(result, str)

    def test_styles_dataframe(self):
        """Table CSS should style Streamlit DataFrames."""
        result = get_table_css()
        assert ".stDataFrame" in result

    def test_includes_header_styling(self):
        """Table CSS should style table headers."""
        result = get_table_css()
        assert "thead" in result or "th" in result

    def test_includes_row_hover(self):
        """Table CSS should include row hover state."""
        result = get_table_css()
        assert "hover" in result


class TestStatusCss:
    """Test status CSS generation."""

    def test_returns_string(self):
        """get_status_css should return a string."""
        result = get_status_css()
        assert isinstance(result, str)

    def test_defines_status_badge_class(self):
        """Status CSS should define .status-badge class."""
        result = get_status_css()
        assert ".status-badge" in result

    def test_includes_pass_status(self):
        """Status CSS should include PASS status styling."""
        result = get_status_css()
        assert "status-pass" in result

    def test_includes_fail_status(self):
        """Status CSS should include FAIL status styling."""
        result = get_status_css()
        assert "status-fail" in result

    def test_includes_risk_status(self):
        """Status CSS should include RISK status styling."""
        result = get_status_css()
        assert "status-risk" in result

    def test_uses_success_color_for_pass(self):
        """Status CSS should use success color for PASS."""
        result = get_status_css()
        assert COLORS.success in result or COLORS.success_light in result

    def test_uses_error_color_for_fail(self):
        """Status CSS should use error color for FAIL."""
        result = get_status_css()
        assert COLORS.error in result or COLORS.error_light in result


class TestAlertCss:
    """Test alert CSS generation."""

    def test_returns_string(self):
        """get_alert_css should return a string."""
        result = get_alert_css()
        assert isinstance(result, str)

    def test_styles_streamlit_alerts(self):
        """Alert CSS should style Streamlit alerts."""
        result = get_alert_css()
        assert ".stAlert" in result

    def test_includes_border_radius(self):
        """Alert CSS should include border-radius."""
        result = get_alert_css()
        assert "border-radius" in result


class TestGetAllCss:
    """Test combined CSS generation."""

    def test_returns_string(self):
        """get_all_css should return a string."""
        result = get_all_css()
        assert isinstance(result, str)

    def test_includes_all_sections(self):
        """Combined CSS should include all section CSS."""
        result = get_all_css()

        # Check for content from each section
        assert "font-family" in result  # base
        assert ".acp-card" in result  # card
        assert "stSidebar" in result  # navigation
        assert ".stButton" in result  # button
        assert ".stTextInput" in result  # form
        assert ".stDataFrame" in result  # table
        assert ".status-badge" in result  # status
        assert ".stAlert" in result  # alert

    def test_includes_theme_header_comment(self):
        """Combined CSS should include header comment."""
        result = get_all_css()
        assert "ACP Theme Styles" in result

    def test_is_valid_css_syntax(self):
        """Combined CSS should have balanced braces."""
        result = get_all_css()

        # Count braces (simple validation)
        open_braces = result.count("{")
        close_braces = result.count("}")

        assert open_braces == close_braces, (
            f"Unbalanced braces: {open_braces} open vs {close_braces} close"
        )

    def test_no_undefined_variables(self):
        """CSS should not contain undefined variable references."""
        result = get_all_css()

        # Check for common template variable patterns that weren't replaced
        assert "{COLORS." not in result
        assert "{TYPOGRAPHY." not in result
        assert "{SPACING." not in result
        assert "{BORDER_RADIUS." not in result
        assert "{SHADOWS." not in result

    def test_css_length_is_reasonable(self):
        """Combined CSS should be a reasonable length (not empty, not huge)."""
        result = get_all_css()

        assert len(result) > 1000, "CSS seems too short"
        assert len(result) < 100000, "CSS seems too long"
