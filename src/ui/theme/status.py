"""
Status Configuration.

Maps analysis statuses (PASS/RISK/FAIL/ERROR) and constraint statuses
to visual properties (colors, icons, backgrounds).
"""

from dataclasses import dataclass
from typing import NamedTuple

from src.ui.theme.colors import COLORS


class StatusStyle(NamedTuple):
    """Visual properties for a status indicator."""

    color: str
    background: str
    icon: str
    label: str


class ConstraintStyle(NamedTuple):
    """Visual properties for a constraint status indicator."""

    color: str
    icon: str
    label: str
    description: str


@dataclass(frozen=True)
class StatusConfig:
    """Configuration for analysis status indicators."""

    PASS: StatusStyle = StatusStyle(
        color=COLORS.success,
        background=COLORS.success_light,
        icon="✓",
        label="PASS",
    )

    RISK: StatusStyle = StatusStyle(
        color=COLORS.warning,
        background=COLORS.warning_light,
        icon="⚠",
        label="RISK",
    )

    FAIL: StatusStyle = StatusStyle(
        color=COLORS.error,
        background=COLORS.error_light,
        icon="✗",
        label="FAIL",
    )

    ERROR: StatusStyle = StatusStyle(
        color=COLORS.gray_400,
        background=COLORS.gray_100,
        icon="?",
        label="ERROR",
    )

    def get(self, status: str) -> StatusStyle:
        """Get status style by name, with fallback to ERROR."""
        return getattr(self, status.upper(), self.ERROR)


@dataclass(frozen=True)
class ConstraintConfig:
    """Configuration for constraint status indicators."""

    UNCONSTRAINED: ConstraintStyle = ConstraintStyle(
        color=COLORS.success,
        icon="✓",
        label="Unconstrained",
        description="Full contribution feasible",
    )

    REDUCED: ConstraintStyle = ConstraintStyle(
        color=COLORS.warning,
        icon="↓",
        label="Reduced",
        description="Capped by section 415(c)",
    )

    AT_LIMIT: ConstraintStyle = ConstraintStyle(
        color=COLORS.error,
        icon="!",
        label="At §415(c) Limit",
        description="No remaining 415 room",
    )

    NOT_SELECTED: ConstraintStyle = ConstraintStyle(
        color=COLORS.gray_400,
        icon="—",
        label="Not Selected",
        description="Not participating",
    )

    def get(self, status: str) -> ConstraintStyle:
        """Get constraint style by name, with fallback to NOT_SELECTED."""
        # Normalize the status name for lookup
        normalized = status.upper().replace(" ", "_").replace("§", "").replace("(", "").replace(")", "")
        if "AT" in normalized and "LIMIT" in normalized:
            return self.AT_LIMIT
        if "REDUCED" in normalized:
            return self.REDUCED
        if "UNCONSTRAINED" in normalized:
            return self.UNCONSTRAINED
        return self.NOT_SELECTED


# Singleton instances for easy import
STATUS_CONFIG = StatusConfig()
CONSTRAINT_CONFIG = ConstraintConfig()


def get_status_style(status: str) -> StatusStyle:
    """Convenience function to get status style."""
    return STATUS_CONFIG.get(status)


def get_constraint_style(status: str) -> ConstraintStyle:
    """Convenience function to get constraint style."""
    return CONSTRAINT_CONFIG.get(status)
