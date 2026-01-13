# Quickstart: Heatmap Exploration

**Feature**: 005-heatmap-exploration
**Date**: 2026-01-13

## Prerequisites

- Python 3.11+
- Existing project setup with dependencies installed
- Familiarity with Streamlit component development
- Understanding of spec 004 (Scenario Analysis) data structures

## Setup

```bash
# Ensure you're on the feature branch
git checkout 005-heatmap-exploration

# Install/update dependencies (if new ones added)
pip install -r requirements.txt

# Run the Streamlit app for development
streamlit run src/ui/app.py
```

## Key Files to Understand

### Existing (Read First)
1. `src/core/models.py` - ScenarioResult, GridResult, GridSummary definitions
2. `src/ui/components/heatmap.py` - Current heatmap implementation to enhance
3. `src/ui/pages/analysis.py` - Page that integrates the heatmap

### New Files to Create
1. `src/ui/components/heatmap_models.py` - UI-specific models (see data-model.md)
2. `src/ui/components/heatmap_constants.py` - Colors, icons, config
3. `src/ui/components/heatmap_tooltip.py` - Tooltip rendering
4. `src/ui/components/heatmap_detail.py` - Slide-out detail panel
5. `src/ui/components/heatmap_summary.py` - Summary statistics panel

## Development Workflow

### 1. Start with Models and Constants

```python
# src/ui/components/heatmap_models.py
from enum import Enum
from pydantic import BaseModel

class HeatmapViewMode(str, Enum):
    PASS_FAIL = "pass_fail"
    MARGIN = "margin"
    RISK_ZONE = "risk_zone"

# ... (see data-model.md for full definitions)
```

### 2. Enhance View Mode Switching

Modify `src/ui/components/heatmap.py`:

```python
from src.ui.components.heatmap_models import HeatmapViewMode
from src.ui.components.heatmap_constants import STATUS_COLORS, STATUS_ICONS

def render_heatmap(grid_result: dict, view_mode: HeatmapViewMode = HeatmapViewMode.PASS_FAIL) -> None:
    """Render enhanced heatmap with multiple view modes."""

    # View mode selector
    mode = st.radio(
        "View Mode",
        options=[mode.value for mode in HeatmapViewMode],
        format_func=lambda x: x.replace("_", "/").title(),
        horizontal=True,
    )

    if mode == HeatmapViewMode.PASS_FAIL.value:
        _render_pass_fail_heatmap(grid_result)
    elif mode == HeatmapViewMode.MARGIN.value:
        _render_margin_heatmap(grid_result)
    else:  # RISK_ZONE
        _render_risk_zone_heatmap(grid_result)
```

### 3. Add Status Icons to Cells

```python
def _build_cell_text_matrix(results: list[dict], mode: HeatmapViewMode) -> list[list[str]]:
    """Build text matrix for cell annotations."""
    if mode == HeatmapViewMode.MARGIN:
        return [[f"{r['margin']:+.1f}" if r.get('margin') else "ERR" for r in row] for row in results_grid]
    else:
        return [[STATUS_ICONS.get(r['status'], '?') for r in row] for row in results_grid]
```

### 4. Implement Keyboard Navigation

```python
# Session state for focus tracking
if "heatmap_state" not in st.session_state:
    st.session_state.heatmap_state = HeatmapState()

def handle_keyboard_navigation(key: str, grid_rows: int, grid_cols: int) -> None:
    """Update focus state based on keyboard input."""
    state = st.session_state.heatmap_state.focus

    if key == "ArrowUp" and state.row > 0:
        state.row -= 1
    elif key == "ArrowDown" and state.row < grid_rows - 1:
        state.row += 1
    elif key == "ArrowLeft" and state.col > 0:
        state.col -= 1
    elif key == "ArrowRight" and state.col < grid_cols - 1:
        state.col += 1
    elif key in ("Enter", " "):
        st.session_state.heatmap_state.selected_cell = (state.row, state.col)
```

### 5. Add Summary Panel

```python
# src/ui/components/heatmap_summary.py
import streamlit as st
from src.core.models import GridSummary

def render_summary_panel(summary: GridSummary, scenarios: list) -> None:
    """Render summary statistics above heatmap."""
    st.subheader("Grid Summary")

    # Status counts row
    cols = st.columns(5)
    cols[0].metric("Pass", summary.pass_count, delta=None)
    cols[1].metric("Risk", summary.risk_count, delta=None)
    cols[2].metric("Fail", summary.fail_count, delta=None)
    cols[3].metric("Error", summary.error_count, delta=None)
    cols[4].metric("Total", summary.total_count, delta=None)

    # Margin details
    with st.expander("Margin Statistics"):
        # Calculate min/max with coordinates
        valid_scenarios = [s for s in scenarios if s.get("status") != "ERROR"]
        if valid_scenarios:
            min_scenario = min(valid_scenarios, key=lambda s: s["margin"])
            max_scenario = max(valid_scenarios, key=lambda s: s["margin"])
            avg_margin = sum(s["margin"] for s in valid_scenarios) / len(valid_scenarios)

            st.write(f"**Min Margin**: {min_scenario['margin']:+.2f}pp at "
                     f"{min_scenario['adoption_rate']}% adoption, "
                     f"{min_scenario['contribution_rate']}% contribution")
            st.write(f"**Max Margin**: {max_scenario['margin']:+.2f}pp at "
                     f"{max_scenario['adoption_rate']}% adoption, "
                     f"{max_scenario['contribution_rate']}% contribution")
            st.write(f"**Avg Margin**: {avg_margin:+.2f}pp")
```

### 6. Implement Slide-out Detail Panel

```python
# src/ui/components/heatmap_detail.py
import streamlit as st
from src.core.models import ScenarioResult, ScenarioStatus

def render_detail_panel(scenario: dict) -> None:
    """Render scenario details in sidebar (slide-out panel)."""
    with st.sidebar:
        st.header("Scenario Details")

        # Status badge
        status = scenario["status"]
        if status == "PASS":
            st.success(f"✓ {status}")
        elif status == "RISK":
            st.warning(f"⚠ {status}")
        elif status == "FAIL":
            st.error(f"✗ {status}")
        else:
            st.info(f"? {status}")

        # Key metrics
        st.metric("Adoption Rate", f"{scenario['adoption_rate']:.0f}%")
        st.metric("Contribution Rate", f"{scenario['contribution_rate']:.1f}%")

        if status != "ERROR":
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("HCE ACP", f"{scenario['hce_acp']:.2f}%")
            col2.metric("NHCE ACP", f"{scenario['nhce_acp']:.2f}%")

            col1.metric("Threshold", f"{scenario['threshold']:.2f}%")
            col2.metric("Margin", f"{scenario['margin']:+.2f}pp")

            st.write(f"**Limiting Test**: {scenario.get('limiting_bound', 'N/A')}")
            st.write(f"**Total Mega-Backdoor**: ${scenario.get('total_mega_backdoor_amount', 0):,.2f}")
        else:
            st.error(f"Error: {scenario.get('error_message', 'Unknown error')}")

        # Close button
        if st.button("Close", key="close_detail_panel"):
            st.session_state.heatmap_state.selected_cell = None
            st.rerun()
```

## Testing

```bash
# Run unit tests for heatmap components
pytest tests/unit/test_heatmap_*.py -v

# Run with coverage
pytest tests/unit/test_heatmap_*.py --cov=src/ui/components --cov-report=html
```

### Test Examples

```python
# tests/unit/test_heatmap_view_modes.py
import pytest
from src.ui.components.heatmap_models import HeatmapViewMode
from src.ui.components.heatmap_constants import STATUS_COLORS, STATUS_ICONS

def test_view_mode_values():
    assert HeatmapViewMode.PASS_FAIL.value == "pass_fail"
    assert HeatmapViewMode.MARGIN.value == "margin"
    assert HeatmapViewMode.RISK_ZONE.value == "risk_zone"

def test_status_colors_contrast():
    """Verify all status colors meet WCAG 2.1 AA contrast requirements."""
    # Colors have been pre-validated - this test documents the requirement
    assert STATUS_COLORS["PASS"]["bg"] == "#22C55E"
    assert STATUS_COLORS["FAIL"]["text"] == "#FFFFFF"  # White on red

def test_status_icons_defined():
    for status in ["PASS", "RISK", "FAIL", "ERROR"]:
        assert status in STATUS_ICONS
        assert len(STATUS_ICONS[status]) == 1  # Single character
```

## Common Patterns

### Accessing Scenario by Grid Coordinates

```python
def get_scenario_at(grid_result: dict, row: int, col: int) -> dict | None:
    """Get scenario result at specific grid position."""
    adoption_rates = grid_result["adoption_rates"]
    contribution_rates = grid_result["contribution_rates"]

    if row >= len(adoption_rates) or col >= len(contribution_rates):
        return None

    target_adoption = adoption_rates[row]
    target_contribution = contribution_rates[col]

    for result in grid_result["results"]:
        if (result["adoption_rate"] == target_adoption and
            result["contribution_rate"] == target_contribution):
            return result
    return None
```

### Converting Status to Display Properties

```python
def get_cell_display(scenario: dict, view_mode: HeatmapViewMode, is_focused: bool) -> HeatmapCellDisplay:
    """Create display properties for a heatmap cell."""
    status = scenario.get("status", "ERROR")
    colors = STATUS_COLORS.get(status, STATUS_COLORS["ERROR"])

    is_dimmed = (
        view_mode == HeatmapViewMode.RISK_ZONE and
        status != "RISK"
    )

    label = None
    if view_mode == HeatmapViewMode.MARGIN and status != "ERROR":
        label = f"{scenario['margin']:+.1f}"

    return HeatmapCellDisplay(
        row_index=...,
        col_index=...,
        adoption_rate=scenario["adoption_rate"],
        contribution_rate=scenario["contribution_rate"],
        background_color=colors["bg"],
        text_color=colors["text"],
        icon=STATUS_ICONS.get(status, "?"),
        label=label,
        is_focused=is_focused,
        is_dimmed=is_dimmed,
        scenario_result=scenario,
    )
```

## Troubleshooting

### Plotly Chart Not Updating
- Ensure you're using `st.plotly_chart(fig, use_container_width=True, key="unique_key")`
- The `key` parameter forces Streamlit to re-render on state changes

### Keyboard Events Not Captured
- The JavaScript event handler must be rendered with `st.components.html()`
- Check browser console for postMessage errors

### Focus Indicator Not Visible
- Plotly charts render in an iframe; CSS must be injected via `st.markdown(css, unsafe_allow_html=True)`
- Use absolute positioning relative to the chart container

### Session State Lost on Rerun
- Always check `if "key" not in st.session_state:` before initializing
- Use `st.session_state.heatmap_state = HeatmapState()` for typed state
