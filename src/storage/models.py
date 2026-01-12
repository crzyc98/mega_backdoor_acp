"""
Data Models for ACP Sensitivity Analyzer.

Dataclass models representing census, participant, and analysis entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class Census:
    """
    A collection of participant records for a single plan.

    T031: Census dataclass model per data-model.md
    """
    id: str
    name: str
    plan_year: int
    upload_timestamp: datetime
    participant_count: int
    hce_count: int
    nhce_count: int
    salt: str
    version: str

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "plan_year": self.plan_year,
            "upload_timestamp": self.upload_timestamp.isoformat(),
            "participant_count": self.participant_count,
            "hce_count": self.hce_count,
            "nhce_count": self.nhce_count,
            "salt": self.salt,
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Census":
        """Create Census from database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            plan_year=row["plan_year"],
            upload_timestamp=datetime.fromisoformat(row["upload_timestamp"]),
            participant_count=row["participant_count"],
            hce_count=row["hce_count"],
            nhce_count=row["nhce_count"],
            salt=row["salt"],
            version=row["version"],
        )


@dataclass
class Participant:
    """
    An individual plan participant with ACP-relevant attributes.

    T032: Participant dataclass model per data-model.md
    """
    id: str
    census_id: str
    internal_id: str
    is_hce: bool
    compensation_cents: int
    deferral_rate: float
    match_rate: float
    after_tax_rate: float

    @property
    def match_cents(self) -> int:
        """Calculate match contribution in cents."""
        return int(self.compensation_cents * self.match_rate / 100)

    @property
    def after_tax_cents(self) -> int:
        """Calculate after-tax contribution in cents."""
        return int(self.compensation_cents * self.after_tax_rate / 100)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "census_id": self.census_id,
            "internal_id": self.internal_id,
            "is_hce": 1 if self.is_hce else 0,
            "compensation_cents": self.compensation_cents,
            "deferral_rate": self.deferral_rate,
            "match_rate": self.match_rate,
            "after_tax_rate": self.after_tax_rate,
        }

    def to_calculation_dict(self) -> dict:
        """Convert to dictionary for ACP calculations."""
        return {
            "internal_id": self.internal_id,
            "is_hce": self.is_hce,
            "match_cents": self.match_cents,
            "after_tax_cents": self.after_tax_cents,
            "compensation_cents": self.compensation_cents,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Participant":
        """Create Participant from database row."""
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            internal_id=row["internal_id"],
            is_hce=bool(row["is_hce"]),
            compensation_cents=row["compensation_cents"],
            deferral_rate=row["deferral_rate"],
            match_rate=row["match_rate"],
            after_tax_rate=row["after_tax_rate"],
        )


@dataclass
class AnalysisResult:
    """
    The outcome of running one scenario against a census.

    T033: AnalysisResult dataclass model per data-model.md
    """
    id: str
    census_id: str
    grid_analysis_id: str | None
    adoption_rate: float
    contribution_rate: float
    seed: int
    nhce_acp: float
    hce_acp: float
    threshold: float
    margin: float
    result: Literal["PASS", "FAIL"]
    limiting_test: Literal["1.25x", "+2.0"]
    run_timestamp: datetime
    version: str

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "census_id": self.census_id,
            "grid_analysis_id": self.grid_analysis_id,
            "adoption_rate": self.adoption_rate,
            "contribution_rate": self.contribution_rate,
            "seed": self.seed,
            "nhce_acp": self.nhce_acp,
            "hce_acp": self.hce_acp,
            "threshold": self.threshold,
            "margin": self.margin,
            "result": self.result,
            "limiting_test": self.limiting_test,
            "run_timestamp": self.run_timestamp.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "AnalysisResult":
        """Create AnalysisResult from database row."""
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            grid_analysis_id=row["grid_analysis_id"],
            adoption_rate=row["adoption_rate"],
            contribution_rate=row["contribution_rate"],
            seed=row["seed"],
            nhce_acp=row["nhce_acp"],
            hce_acp=row["hce_acp"],
            threshold=row["threshold"],
            margin=row["margin"],
            result=row["result"],
            limiting_test=row["limiting_test"],
            run_timestamp=datetime.fromisoformat(row["run_timestamp"]),
            version=row["version"],
        )


@dataclass
class GridAnalysis:
    """
    A collection of analysis results across multiple scenarios.

    T055 (Phase 4): GridAnalysis dataclass model per data-model.md
    """
    id: str
    census_id: str
    name: str | None
    created_timestamp: datetime
    seed: int
    adoption_rates: list[float]
    contribution_rates: list[float]
    version: str

    @property
    def scenario_count(self) -> int:
        """Calculate total number of scenarios."""
        return len(self.adoption_rates) * len(self.contribution_rates)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        import json
        return {
            "id": self.id,
            "census_id": self.census_id,
            "name": self.name,
            "created_timestamp": self.created_timestamp.isoformat(),
            "seed": self.seed,
            "adoption_rates": json.dumps(self.adoption_rates),
            "contribution_rates": json.dumps(self.contribution_rates),
            "version": self.version,
        }

    @classmethod
    def from_row(cls, row: dict) -> "GridAnalysis":
        """Create GridAnalysis from database row."""
        import json
        return cls(
            id=row["id"],
            census_id=row["census_id"],
            name=row["name"],
            created_timestamp=datetime.fromisoformat(row["created_timestamp"]),
            seed=row["seed"],
            adoption_rates=json.loads(row["adoption_rates"]),
            contribution_rates=json.loads(row["contribution_rates"]),
            version=row["version"],
        )
