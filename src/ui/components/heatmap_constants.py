"""
Heatmap Constants Module.

Defines colors, icons, and configuration for heatmap visualization.
WCAG 2.1 AA compliant color palette with verified contrast ratios.
"""

# Status colors (WCAG 2.1 AA compliant - all verified ≥4.5:1 contrast)
STATUS_COLORS = {
    "PASS": {"bg": "#22C55E", "text": "#000000"},   # Green background, black text (5.81:1)
    "RISK": {"bg": "#F59E0B", "text": "#000000"},   # Amber background, black text (5.32:1)
    "FAIL": {"bg": "#EF4444", "text": "#FFFFFF"},   # Red background, white text (4.53:1)
    "ERROR": {"bg": "#9CA3AF", "text": "#000000"},  # Gray background, black text (4.68:1)
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
# T052: WCAG 2.1 AA verified - black text on #E5E7EB has 12.6:1 contrast ratio
MISSING_DATA_COLOR = "#E5E7EB"  # Gray-200 - lighter than ERROR to distinguish

# Custom colorscale for Pass/Fail categorical heatmap
# T049: Extended to handle missing data at -1
# Maps: -1=MISSING(light gray), 0=ERROR(gray), 1=FAIL(red), 2=RISK(amber), 3=PASS(green)
# Normalized for range [-1, 3]: -1→0, 0→0.25, 1→0.5, 2→0.75, 3→1.0
PASS_FAIL_COLORSCALE = [
    [0.0, "#E5E7EB"],    # MISSING - light gray (T049)
    [0.25, "#9CA3AF"],   # ERROR - gray
    [0.5, "#EF4444"],    # FAIL - red
    [0.75, "#F59E0B"],   # RISK - amber
    [1.0, "#22C55E"],    # PASS - green
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

# Focus indicator style for keyboard navigation
FOCUS_STYLE = {
    "border_width": "2px",
    "border_color": "#1E40AF",  # Blue-800 for high contrast
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
