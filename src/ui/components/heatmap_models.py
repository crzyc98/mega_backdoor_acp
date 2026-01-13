"""
Heatmap Models Module.

UI-specific models for heatmap visualization state management.
These models wrap core data structures from spec 004 for display purposes.
"""

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.core.models import LimitingBound, ScenarioResult, ScenarioStatus


class HeatmapViewMode(str, Enum):
    """Available heatmap visualization modes."""

    PASS_FAIL = "pass_fail"  # Categorical status coloring
    MARGIN = "margin"  # Continuous gradient by margin value
    RISK_ZONE = "risk_zone"  # Emphasis on RISK-status cells


class HeatmapFocusState(BaseModel):
    """Tracks keyboard focus position within the heatmap grid."""

    row: int = Field(0, ge=0, description="Focused row index (adoption rate axis)")
    col: int = Field(0, ge=0, description="Focused column index (contribution rate axis)")
    is_focused: bool = Field(False, description="Whether heatmap has keyboard focus")


class HeatmapState(BaseModel):
    """Complete state for heatmap component, stored in Streamlit session_state."""

    view_mode: HeatmapViewMode = Field(
        HeatmapViewMode.PASS_FAIL, description="Current visualization mode"
    )
    focus: HeatmapFocusState = Field(
        default_factory=HeatmapFocusState, description="Keyboard focus state"
    )
    selected_cell: tuple[int, int] | None = Field(
        None, description="(row, col) of cell with open detail panel, or None"
    )
    show_help: bool = Field(
        False, description="Whether keyboard shortcuts overlay is visible"
    )


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
    label: str | None = Field(
        None, description="Optional text label (e.g., margin value)"
    )

    # State
    is_focused: bool = Field(False, description="Whether this cell has keyboard focus")
    is_dimmed: bool = Field(
        False, description="Whether to render with reduced opacity"
    )

    class Config:
        arbitrary_types_allowed = True


class TooltipData(BaseModel):
    """Data displayed in cell hover tooltip."""

    status: str = Field(..., description="Scenario status (PASS/RISK/FAIL/ERROR)")
    status_icon: str = Field(..., description="Status icon character")
    adoption_rate: float = Field(..., description="Y-axis value as percentage")
    contribution_rate: float = Field(..., description="X-axis value as percentage")
    margin: float | None = Field(None, description="Margin in percentage points")
    hce_acp: float | None = Field(None, description="HCE ACP percentage")
    nhce_acp: float | None = Field(None, description="NHCE ACP percentage")
    threshold: float | None = Field(None, description="Max allowed ACP")
    limiting_bound: str | None = Field(
        None, description="Which test determined threshold"
    )
    error_message: str | None = Field(
        None, description="Error description if ERROR status"
    )

    def to_hover_html(self) -> str:
        """Generate HTML-formatted tooltip content for Plotly."""
        if self.status == "ERROR":
            return (
                f"<b>{self.status_icon} {self.status}</b><br>"
                f"Adoption: {self.adoption_rate:.0f}%<br>"
                f"Contribution: {self.contribution_rate:.1f}%<br>"
                f"<i>{self.error_message or 'Unknown error'}</i>"
            )

        # Format values with None handling
        margin_str = f"{self.margin:+.2f}pp" if self.margin is not None else "N/A"
        hce_str = f"{self.hce_acp:.2f}%" if self.hce_acp is not None else "N/A"
        nhce_str = f"{self.nhce_acp:.2f}%" if self.nhce_acp is not None else "N/A"
        threshold_str = f"{self.threshold:.2f}%" if self.threshold is not None else "N/A"

        return (
            f"<b>{self.status_icon} {self.status}</b><br>"
            f"Adoption: {self.adoption_rate:.0f}%<br>"
            f"Contribution: {self.contribution_rate:.1f}%<br>"
            f"Margin: {margin_str}<br>"
            f"HCE ACP: {hce_str}<br>"
            f"NHCE ACP: {nhce_str}<br>"
            f"Threshold: {threshold_str}<br>"
            f"Limiting: {self.limiting_bound or 'N/A'}"
        )


class MarginCoordinate(BaseModel):
    """Margin value with its grid coordinates."""

    value: float = Field(..., description="Margin value in percentage points")
    adoption_rate: float = Field(
        ..., description="Adoption rate where this margin occurs"
    )
    contribution_rate: float = Field(
        ..., description="Contribution rate where this margin occurs"
    )


class FailurePointDisplay(BaseModel):
    """Coordinates of a failure point for display."""

    adoption_rate: float = Field(..., description="Adoption rate where failure occurred")
    contribution_rate: float = Field(
        ..., description="Contribution rate where failure occurred"
    )


class HeatmapSummaryDisplay(BaseModel):
    """Extended summary statistics for display, derived from GridSummary."""

    # Status counts (from GridSummary)
    pass_count: int = Field(0, ge=0)
    risk_count: int = Field(0, ge=0)
    fail_count: int = Field(0, ge=0)
    error_count: int = Field(0, ge=0)
    total_count: int = Field(0, ge=0)

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
    first_failure_point: FailurePointDisplay | None = Field(
        None, description="Coordinates of first failure"
    )

    @classmethod
    def from_grid_result(
        cls, scenarios: list[dict], summary: dict
    ) -> "HeatmapSummaryDisplay":
        """
        Create HeatmapSummaryDisplay from grid result data.

        Args:
            scenarios: List of scenario result dicts
            summary: Grid summary dict from API

        Returns:
            HeatmapSummaryDisplay with computed statistics
        """
        # Get counts from summary
        pass_count = summary.get("pass_count", 0)
        risk_count = summary.get("risk_count", 0)
        fail_count = summary.get("fail_count", 0)
        error_count = summary.get("error_count", 0)
        total_count = summary.get("total_count", len(scenarios))

        # Calculate margin statistics from scenarios
        valid_scenarios = [
            s for s in scenarios if s.get("status") != "ERROR" and s.get("margin") is not None
        ]

        min_margin = None
        max_margin = None
        avg_margin = None

        if valid_scenarios:
            min_scenario = min(valid_scenarios, key=lambda s: s["margin"])
            max_scenario = max(valid_scenarios, key=lambda s: s["margin"])
            avg_margin = sum(s["margin"] for s in valid_scenarios) / len(valid_scenarios)

            min_margin = MarginCoordinate(
                value=min_scenario["margin"],
                adoption_rate=min_scenario["adoption_rate"],
                contribution_rate=min_scenario["contribution_rate"],
            )
            max_margin = MarginCoordinate(
                value=max_scenario["margin"],
                adoption_rate=max_scenario["adoption_rate"],
                contribution_rate=max_scenario["contribution_rate"],
            )

        # Get derived insights from summary
        first_failure = summary.get("first_failure_point")
        first_failure_display = None
        if first_failure:
            first_failure_display = FailurePointDisplay(
                adoption_rate=first_failure.get("adoption_rate", 0),
                contribution_rate=first_failure.get("contribution_rate", 0),
            )

        return cls(
            pass_count=pass_count,
            risk_count=risk_count,
            fail_count=fail_count,
            error_count=error_count,
            total_count=total_count,
            min_margin=min_margin,
            max_margin=max_margin,
            avg_margin=avg_margin,
            max_safe_contribution=summary.get("max_safe_contribution"),
            first_failure_point=first_failure_display,
        )
