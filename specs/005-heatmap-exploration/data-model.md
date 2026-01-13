# Data Model: Heatmap Exploration

**Feature**: 005-heatmap-exploration
**Date**: 2026-01-13

## Overview

This feature is primarily a visualization layer. It consumes existing data structures from spec 004 (Scenario Analysis) and adds UI-specific models for heatmap display state management. No new database entities are required.

## Existing Models (from spec 004)

These models are already implemented in `src/core/models.py` and are consumed by this feature:

### ScenarioResult
```python
class ScenarioResult(BaseModel):
    status: ScenarioStatus          # PASS | RISK | FAIL | ERROR
    nhce_acp: float | None          # NHCE Actual Contribution Percentage
    hce_acp: float | None           # HCE Actual Contribution Percentage
    max_allowed_acp: float | None   # Threshold value
    margin: float | None            # Distance from threshold (percentage points)
    limiting_bound: LimitingBound | None  # MULTIPLE | ADDITIVE
    hce_contributor_count: int | None
    nhce_contributor_count: int | None
    total_mega_backdoor_amount: float | None  # Dollar amount
    seed_used: int
    adoption_rate: float
    contribution_rate: float
    error_message: str | None
```

### GridResult
```python
class GridResult(BaseModel):
    scenarios: list[ScenarioResult]  # All scenario results
    summary: GridSummary             # Aggregate metrics
    seed_used: int
```

### GridSummary
```python
class GridSummary(BaseModel):
    pass_count: int
    risk_count: int
    fail_count: int
    error_count: int
    total_count: int
    first_failure_point: FailurePoint | None
    max_safe_contribution: float | None
    worst_margin: float
```

## New Models (UI-specific)

These models are added to support heatmap visualization state management. They belong in `src/ui/components/heatmap_models.py`.

### HeatmapViewMode

```python
from enum import Enum

class HeatmapViewMode(str, Enum):
    """Available heatmap visualization modes."""
    PASS_FAIL = "pass_fail"    # Categorical status coloring
    MARGIN = "margin"          # Continuous gradient by margin value
    RISK_ZONE = "risk_zone"    # Emphasis on RISK-status cells
```

### HeatmapFocusState

```python
from pydantic import BaseModel, Field

class HeatmapFocusState(BaseModel):
    """Tracks keyboard focus position within the heatmap grid."""
    row: int = Field(0, ge=0, description="Focused row index (adoption rate axis)")
    col: int = Field(0, ge=0, description="Focused column index (contribution rate axis)")
    is_focused: bool = Field(False, description="Whether heatmap has keyboard focus")
```

### HeatmapCellDisplay

```python
from pydantic import BaseModel, Field

class HeatmapCellDisplay(BaseModel):
    """Display properties for a single heatmap cell."""
    row_index: int = Field(..., ge=0, description="Row position in grid")
    col_index: int = Field(..., ge=0, description="Column position in grid")
    adoption_rate: float = Field(..., description="Y-axis value (percentage)")
    contribution_rate: float = Field(..., description="X-axis value (percentage)")

    # Visual properties (computed based on view mode)
    background_color: str = Field(..., description="Hex color code for cell background")
    text_color: str = Field(..., description="Hex color code for text/icon")
    icon: str = Field(..., description="Status icon character (✓, ⚠, ✗, ?)")
    label: str | None = Field(None, description="Optional text label (e.g., margin value)")

    # State
    is_focused: bool = Field(False, description="Whether this cell has keyboard focus")
    is_dimmed: bool = Field(False, description="Whether to render with reduced opacity")

    # Reference to source data
    scenario_result: "ScenarioResult" = Field(..., description="Underlying scenario data")
```

### TooltipData

```python
from pydantic import BaseModel, Field
from src.core.models import ScenarioStatus, LimitingBound

class TooltipData(BaseModel):
    """Data displayed in cell hover tooltip."""
    status: ScenarioStatus = Field(..., description="Scenario status with icon")
    status_icon: str = Field(..., description="Status icon character")
    adoption_rate: float = Field(..., description="Y-axis value as percentage")
    contribution_rate: float = Field(..., description="X-axis value as percentage")
    margin: float | None = Field(None, description="Margin in percentage points")
    hce_acp: float | None = Field(None, description="HCE ACP percentage")
    nhce_acp: float | None = Field(None, description="NHCE ACP percentage")
    threshold: float | None = Field(None, description="Max allowed ACP")
    limiting_bound: LimitingBound | None = Field(None, description="Which test determined threshold")
    error_message: str | None = Field(None, description="Error description if ERROR status")

    def to_hover_html(self) -> str:
        """Generate HTML-formatted tooltip content for Plotly."""
        if self.status == ScenarioStatus.ERROR:
            return (
                f"<b>{self.status_icon} {self.status.value}</b><br>"
                f"Adoption: {self.adoption_rate:.0f}%<br>"
                f"Contribution: {self.contribution_rate:.1f}%<br>"
                f"<i>{self.error_message}</i>"
            )
        return (
            f"<b>{self.status_icon} {self.status.value}</b><br>"
            f"Adoption: {self.adoption_rate:.0f}%<br>"
            f"Contribution: {self.contribution_rate:.1f}%<br>"
            f"Margin: {self.margin:+.2f}pp<br>"
            f"HCE ACP: {self.hce_acp:.2f}%<br>"
            f"NHCE ACP: {self.nhce_acp:.2f}%<br>"
            f"Threshold: {self.threshold:.2f}%<br>"
            f"Limiting: {self.limiting_bound.value if self.limiting_bound else 'N/A'}"
        )
```

### HeatmapSummaryDisplay

```python
from pydantic import BaseModel, Field

class MarginCoordinate(BaseModel):
    """Margin value with its grid coordinates."""
    value: float = Field(..., description="Margin value in percentage points")
    adoption_rate: float = Field(..., description="Adoption rate where this margin occurs")
    contribution_rate: float = Field(..., description="Contribution rate where this margin occurs")

class HeatmapSummaryDisplay(BaseModel):
    """Extended summary statistics for display, derived from GridSummary."""
    # Status counts (from GridSummary)
    pass_count: int
    risk_count: int
    fail_count: int
    error_count: int
    total_count: int

    # Margin statistics (requires computation from scenarios)
    min_margin: MarginCoordinate | None = Field(
        None, description="Smallest margin with coordinates"
    )
    max_margin: MarginCoordinate | None = Field(
        None, description="Largest margin with coordinates"
    )
    avg_margin: float | None = Field(
        None, description="Average margin excluding ERROR scenarios"
    )

    # Derived insights (from GridSummary)
    max_safe_contribution: float | None = Field(
        None, description="Highest passing contribution at max adoption"
    )
    first_failure_point: "FailurePoint | None" = Field(
        None, description="Coordinates of first failure"
    )
```

### HeatmapState

```python
from pydantic import BaseModel, Field

class HeatmapState(BaseModel):
    """Complete state for heatmap component, stored in Streamlit session_state."""
    view_mode: HeatmapViewMode = Field(
        HeatmapViewMode.PASS_FAIL,
        description="Current visualization mode"
    )
    focus: HeatmapFocusState = Field(
        default_factory=HeatmapFocusState,
        description="Keyboard focus state"
    )
    selected_cell: tuple[int, int] | None = Field(
        None,
        description="(row, col) of cell with open detail panel, or None"
    )
    show_help: bool = Field(
        False,
        description="Whether keyboard shortcuts overlay is visible"
    )
```

## Entity Relationships

```
┌─────────────────┐
│   GridResult    │ (from spec 004)
│   - scenarios   │──────────────┐
│   - summary     │              │
└─────────────────┘              │
        │                        │
        │ contains               │ references
        ▼                        ▼
┌─────────────────┐      ┌──────────────────┐
│  GridSummary    │      │  ScenarioResult  │
│  - pass_count   │      │  - status        │
│  - risk_count   │      │  - margin        │
│  - fail_count   │      │  - hce_acp       │
│  - worst_margin │      │  - ...           │
└─────────────────┘      └──────────────────┘
        │                        │
        │ derived                │ wrapped by
        ▼                        ▼
┌─────────────────────┐  ┌──────────────────┐
│HeatmapSummaryDisplay│  │ HeatmapCellDisplay│
│  - min_margin       │  │  - background    │
│  - max_margin       │  │  - icon          │
│  - avg_margin       │  │  - is_focused    │
└─────────────────────┘  └──────────────────┘
                                 │
                                 │ generates
                                 ▼
                         ┌──────────────────┐
                         │   TooltipData    │
                         │  - to_hover_html │
                         └──────────────────┘
```

## Constants

```python
# src/ui/components/heatmap_constants.py

# Status colors (WCAG 2.1 AA compliant)
STATUS_COLORS = {
    "PASS": {"bg": "#22C55E", "text": "#000000"},
    "RISK": {"bg": "#F59E0B", "text": "#000000"},
    "FAIL": {"bg": "#EF4444", "text": "#FFFFFF"},
    "ERROR": {"bg": "#9CA3AF", "text": "#000000"},
}

# Status icons (Unicode)
STATUS_ICONS = {
    "PASS": "✓",   # U+2713
    "RISK": "⚠",   # U+26A0
    "FAIL": "✗",   # U+2717
    "ERROR": "?",  # U+003F
}

# View mode configurations
VIEW_MODE_CONFIG = {
    "pass_fail": {
        "title": "ACP Test Results",
        "subtitle": "Green=PASS, Yellow=RISK, Red=FAIL, Gray=ERROR",
        "show_icons": True,
        "show_margin_labels": False,
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
    },
}

# Focus indicator style
FOCUS_STYLE = {
    "border_width": "2px",
    "border_color": "#1E40AF",  # Blue-800
    "border_style": "solid",
}
```

## Validation Rules

1. **HeatmapCellDisplay**:
   - `row_index` and `col_index` must be within grid bounds
   - `background_color` and `text_color` must be valid hex codes
   - `icon` must be one of the defined STATUS_ICONS values

2. **HeatmapFocusState**:
   - `row` and `col` must be ≥ 0
   - When `is_focused` is False, `row` and `col` should reset to 0

3. **TooltipData**:
   - If `status` is ERROR, `error_message` must be non-None
   - If `status` is not ERROR, `margin`, `hce_acp`, `nhce_acp`, `threshold` must be non-None

4. **HeatmapSummaryDisplay**:
   - `total_count` must equal `pass_count + risk_count + fail_count + error_count`
   - `avg_margin` must be None if `error_count == total_count` (all ERROR)
