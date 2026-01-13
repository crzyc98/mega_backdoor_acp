# Quickstart: UI Style Update

**Feature**: 007-ui-style-update
**Date**: 2026-01-13

## Prerequisites

- Python 3.11+
- Existing project dependencies installed (`pip install -r requirements.txt`)
- Streamlit 1.28+ (already in project dependencies)

## Development Setup

```bash
# Navigate to project root
cd /workspaces/mega_backdoor_acp

# Ensure dependencies are installed
pip install -r requirements.txt

# Run the Streamlit app to verify current state
streamlit run src/ui/app.py
```

## Theme Module Structure

The new theme module will be created at:

```text
src/ui/theme/
├── __init__.py       # Public exports
├── colors.py         # ColorPalette constants
├── typography.py     # Typography constants
├── spacing.py        # Spacing and BorderRadius constants
├── shadows.py        # Shadow constants
├── status.py         # StatusConfig and ConstraintStatusConfig
├── css.py            # CSS generation utilities
└── inject.py         # Streamlit CSS injection helper
```

## Usage Patterns

### 1. Injecting Theme CSS (in app.py)

```python
from src.ui.theme import inject_theme_css

# At the top of app.py, after st.set_page_config()
inject_theme_css()
```

### 2. Using Color Constants

```python
from src.ui.theme.colors import COLORS

# Access colors
primary = COLORS.primary          # "#4F46E5"
success = COLORS.success          # "#10B981"
```

### 3. Using Status Configuration

```python
from src.ui.theme.status import get_status_style

style = get_status_style("PASS")
# Returns: {"color": "#10B981", "icon": "✓", "background": "#ECFDF5"}
```

### 4. Creating Styled Cards

```python
from src.ui.components.card import render_card

render_card(
    title="Analysis Results",
    content="Your content here",
    accent_color="primary"  # or "success", "warning", "error"
)
```

### 5. Rendering Status Badges

```python
from src.ui.components.status_badge import render_status_badge

render_status_badge("PASS")  # Renders styled badge with icon
render_status_badge("FAIL")
render_status_badge("RISK")
```

### 6. Rendering Metric Cards

```python
from src.ui.components.metric_card import render_metric_card

render_metric_card(
    label="HCE ACP",
    value="4.52%",
    delta="+0.25%",
    delta_color="success"
)
```

### 7. Rendering Empty States

```python
from src.ui.components.empty_state import render_empty_state

render_empty_state(
    icon="upload",  # or "chart", "users", "file"
    title="No Census Data Found",
    description="Upload your employee data to begin compliance testing.",
    action_label="Go to Upload",
    on_action=lambda: st.session_state.update({"page": "upload"})
)
```

## Testing

```bash
# Run all tests
pytest

# Run theme-specific tests
pytest tests/unit/ui/theme/

# Run with coverage
pytest --cov=src/ui/theme tests/unit/ui/theme/
```

## Visual Verification Checklist

After implementing changes, manually verify:

1. [ ] Header shows branding with styled navigation
2. [ ] All pages use card-based layouts
3. [ ] PASS/RISK/FAIL statuses show correct colors
4. [ ] Metric cards display with proper styling
5. [ ] Tables have uppercase headers with proper spacing
6. [ ] Empty states show styled placeholders
7. [ ] Buttons have proper hover effects
8. [ ] Sliders use indigo accent color

## Common Issues

### CSS Not Applying

- Ensure `inject_theme_css()` is called after `st.set_page_config()`
- Check browser dev tools for CSS conflicts
- Streamlit caches aggressively; try `streamlit run --server.runOnSave true`

### Colors Not Matching

- Verify using exact hex values from `colors.py`
- Check color contrast for accessibility

### Component Styling Inconsistent

- Always use theme components (`render_card`, `render_status_badge`)
- Avoid inline styles; use theme constants

## Files to Modify

| File | Changes |
|------|---------|
| `src/ui/app.py` | Add theme injection, update navigation labels |
| `src/ui/pages/upload.py` | Apply card layouts, styled forms |
| `src/ui/pages/analysis.py` | Status badges, metric cards |
| `src/ui/pages/export.py` | Export option cards |
| `src/ui/components/heatmap.py` | Theme colors in Plotly |
| `src/ui/components/heatmap_constants.py` | Status color values |
| `src/ui/components/employee_impact.py` | Table styling, constraint icons |

## New Files to Create

| File | Purpose |
|------|---------|
| `src/ui/theme/__init__.py` | Theme exports |
| `src/ui/theme/colors.py` | Color palette |
| `src/ui/theme/typography.py` | Font settings |
| `src/ui/theme/spacing.py` | Spacing scale |
| `src/ui/theme/shadows.py` | Shadow values |
| `src/ui/theme/status.py` | Status configurations |
| `src/ui/theme/css.py` | CSS generation |
| `src/ui/theme/inject.py` | CSS injection |
| `src/ui/components/card.py` | Card component |
| `src/ui/components/status_badge.py` | Status badge |
| `src/ui/components/metric_card.py` | Metric display |
| `src/ui/components/empty_state.py` | Empty state |
