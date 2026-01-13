"""
Heatmap Constants Module.

Defines colors, icons, and configuration for heatmap visualization.
WCAG 2.1 AA compliant color palette with verified contrast ratios.
Uses theme colors for consistency with the rest of the application.
"""

from src.ui.theme.colors import COLORS

# Status colors - using theme colors for consistency
# WCAG 2.1 AA compliant with verified contrast ratios
STATUS_COLORS = {
    "PASS": {"bg": COLORS.success, "text": "#000000"},     # Emerald background, black text
    "RISK": {"bg": COLORS.warning, "text": "#000000"},     # Amber background, black text
    "FAIL": {"bg": COLORS.error, "text": "#FFFFFF"},       # Rose background, white text
    "ERROR": {"bg": COLORS.gray_400, "text": "#000000"},   # Gray background, black text
}

# Status icons (Unicode characters for accessibility)
STATUS_ICONS = {
    "PASS": "✓",    # U+2713 CHECK MARK
    "RISK": "⚠",    # U+26A0 WARNING SIGN
    "FAIL": "✗",    # U+2717 BALLOT X
    "ERROR": "?",   # U+003F QUESTION MARK
}

# Numeric values for categorical heatmap coloring
# T049: -1 is reserved for missing data (gaps in grid)
STATUS_VALUES = {
    "MISSING": -1,  # T049: Special value for grid gaps
    "ERROR": 0,
    "FAIL": 1,
    "RISK": 2,
    "PASS": 3,
}

# T049: Color for missing data cells (light diagonal stripe pattern via lighter gray)
# Using theme gray-200 for consistency
MISSING_DATA_COLOR = COLORS.gray_200

# Custom colorscale for Pass/Fail categorical heatmap
# Uses theme colors for visual consistency
# T049: Extended to handle missing data at -1
# Maps: -1=MISSING(light gray), 0=ERROR(gray), 1=FAIL(red), 2=RISK(amber), 3=PASS(green)
# Normalized for range [-1, 3]: -1→0, 0→0.25, 1→0.5, 2→0.75, 3→1.0
PASS_FAIL_COLORSCALE = [
    [0.0, COLORS.gray_200],     # MISSING - light gray (T049)
    [0.25, COLORS.gray_400],    # ERROR - gray
    [0.5, COLORS.error],        # FAIL - rose
    [0.75, COLORS.warning],     # RISK - amber
    [1.0, COLORS.success],      # PASS - emerald
]

# View mode configurations
VIEW_MODE_CONFIG = {
    "pass_fail": {
        "title": "ACP Test Results",
        "subtitle": "Green=PASS, Yellow=RISK, Red=FAIL, Gray=ERROR",
        "show_icons": True,
        "show_margin_labels": False,
        "colorscale": PASS_FAIL_COLORSCALE,
    },
    "margin": {
        "title": "Margin Distribution",
        "subtitle": "Positive = Safety Buffer (percentage points)",
        "show_icons": False,
        "show_margin_labels": True,
        "colorscale": "RdYlGn",
    },
    "risk_zone": {
        "title": "Risk Zone Analysis",
        "subtitle": "Highlighting scenarios near failure threshold",
        "show_icons": True,
        "show_margin_labels": False,
        "dimmed_opacity": 0.5,
        "colorscale": PASS_FAIL_COLORSCALE,
    },
}

# Focus indicator style for keyboard navigation - using theme primary color
FOCUS_STYLE = {
    "border_width": "2px",
    "border_color": COLORS.primary,
    "border_style": "solid",
}

# Tooltip timing (milliseconds)
TOOLTIP_TIMING = {
    "appear_delay": 200,
    "dismiss_delay": 300,
    "keyboard_delay": 500,
}

# Grid display settings
GRID_SETTINGS = {
    "max_interactive_size": 625,  # 25×25 grid
    "axis_tick_decimation_threshold": 20,  # Show every Nth tick if dimension > threshold
    "cell_min_size": 30,  # Minimum cell size in pixels
}
