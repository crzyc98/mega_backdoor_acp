"""
Repository Layer for Data Access.

Provides CRUD operations for census, participant, and analysis entities.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Generator

from src.core.constants import SYSTEM_VERSION
from src.storage.models import Census, Participant, AnalysisResult, GridAnalysis


class CensusRepository:
    """
    Repository for Census entity operations.

    T034: CensusRepository with save/get/list/delete operations
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, census: Census) -> Census:
        """Save a census to the database."""
        self.conn.execute(
            """
            INSERT INTO census (id, name, plan_year, upload_timestamp,
                              participant_count, hce_count, nhce_count, salt, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                census.id,
                census.name,
                census.plan_year,
                census.upload_timestamp.isoformat(),
                census.participant_count,
                census.hce_count,
                census.nhce_count,
                census.salt,
                census.version,
            ),
        )
        self.conn.commit()
        return census

    def get(self, census_id: str) -> Census | None:
        """Get a census by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM census WHERE id = ?",
            (census_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Census.from_row(dict(row))

    def list(
        self,
        plan_year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Census], int]:
        """
        List censuses with optional filtering.

        Returns tuple of (census list, total count).
        """
        # Build query
        where_clause = ""
        params: list = []

        if plan_year is not None:
            where_clause = "WHERE plan_year = ?"
            params.append(plan_year)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM census {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM census {where_clause}
            ORDER BY upload_timestamp DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        censuses = [Census.from_row(dict(row)) for row in cursor.fetchall()]
        return censuses, total

    def delete(self, census_id: str) -> bool:
        """
        Delete a census and all associated data.

        Returns True if census was deleted, False if not found.
        """
        # Check if exists
        if self.get(census_id) is None:
            return False

        # Delete (cascade handles participants and results)
        self.conn.execute("DELETE FROM census WHERE id = ?", (census_id,))
        self.conn.commit()
        return True


class ParticipantRepository:
    """
    Repository for Participant entity operations.

    T035: ParticipantRepository with bulk insert
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def bulk_insert(self, participants: list[Participant]) -> int:
        """
        Insert multiple participants at once.

        Returns count of inserted records.
        """
        if not participants:
            return 0

        self.conn.executemany(
            """
            INSERT INTO participant (id, census_id, internal_id, is_hce,
                                    compensation_cents, deferral_rate, match_rate, after_tax_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.id,
                    p.census_id,
                    p.internal_id,
                    1 if p.is_hce else 0,
                    p.compensation_cents,
                    p.deferral_rate,
                    p.match_rate,
                    p.after_tax_rate,
                )
                for p in participants
            ],
        )
        self.conn.commit()
        return len(participants)

    def get_by_census(self, census_id: str) -> list[Participant]:
        """Get all participants for a census."""
        cursor = self.conn.execute(
            "SELECT * FROM participant WHERE census_id = ?",
            (census_id,),
        )
        return [Participant.from_row(dict(row)) for row in cursor.fetchall()]

    def get_hces_by_census(self, census_id: str) -> list[Participant]:
        """Get HCE participants for a census."""
        cursor = self.conn.execute(
            "SELECT * FROM participant WHERE census_id = ? AND is_hce = 1",
            (census_id,),
        )
        return [Participant.from_row(dict(row)) for row in cursor.fetchall()]

    def get_nhces_by_census(self, census_id: str) -> list[Participant]:
        """Get NHCE participants for a census."""
        cursor = self.conn.execute(
            "SELECT * FROM participant WHERE census_id = ? AND is_hce = 0",
            (census_id,),
        )
        return [Participant.from_row(dict(row)) for row in cursor.fetchall()]

    def get_as_calculation_dicts(self, census_id: str) -> list[dict]:
        """Get participants as dictionaries ready for ACP calculation."""
        participants = self.get_by_census(census_id)
        return [p.to_calculation_dict() for p in participants]


class AnalysisResultRepository:
    """
    Repository for AnalysisResult entity operations.

    T036: AnalysisResultRepository with save/get operations
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, result: AnalysisResult) -> AnalysisResult:
        """Save an analysis result to the database."""
        self.conn.execute(
            """
            INSERT INTO analysis_result (id, census_id, grid_analysis_id, adoption_rate,
                                        contribution_rate, seed, nhce_acp, hce_acp,
                                        threshold, margin, result, limiting_test,
                                        run_timestamp, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.id,
                result.census_id,
                result.grid_analysis_id,
                result.adoption_rate,
                result.contribution_rate,
                result.seed,
                result.nhce_acp,
                result.hce_acp,
                result.threshold,
                result.margin,
                result.result,
                result.limiting_test,
                result.run_timestamp.isoformat(),
                result.version,
            ),
        )
        self.conn.commit()
        return result

    def get(self, result_id: str) -> AnalysisResult | None:
        """Get an analysis result by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM analysis_result WHERE id = ?",
            (result_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return AnalysisResult.from_row(dict(row))

    def list_by_census(
        self,
        census_id: str,
        grid_id: str | None = None,
    ) -> tuple[list[AnalysisResult], int]:
        """
        List analysis results for a census.

        Args:
            census_id: Census ID to filter by
            grid_id: Optional grid analysis ID to filter by

        Returns tuple of (results list, total count).
        """
        params: list = [census_id]

        if grid_id is not None:
            where_clause = "WHERE census_id = ? AND grid_analysis_id = ?"
            params.append(grid_id)
        else:
            where_clause = "WHERE census_id = ?"

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM analysis_result {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM analysis_result {where_clause}
            ORDER BY run_timestamp DESC
            """,
            params,
        )

        results = [AnalysisResult.from_row(dict(row)) for row in cursor.fetchall()]
        return results, total


class GridAnalysisRepository:
    """
    Repository for GridAnalysis entity operations.

    T056 (Phase 4): GridAnalysisRepository with save/get operations
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, grid: GridAnalysis) -> GridAnalysis:
        """Save a grid analysis to the database."""
        self.conn.execute(
            """
            INSERT INTO grid_analysis (id, census_id, name, created_timestamp,
                                       seed, adoption_rates, contribution_rates, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grid.id,
                grid.census_id,
                grid.name,
                grid.created_timestamp.isoformat(),
                grid.seed,
                json.dumps(grid.adoption_rates),
                json.dumps(grid.contribution_rates),
                grid.version,
            ),
        )
        self.conn.commit()
        return grid

    def get(self, grid_id: str) -> GridAnalysis | None:
        """Get a grid analysis by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM grid_analysis WHERE id = ?",
            (grid_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return GridAnalysis.from_row(dict(row))

    def list_by_census(self, census_id: str) -> list[GridAnalysis]:
        """List all grid analyses for a census."""
        cursor = self.conn.execute(
            "SELECT * FROM grid_analysis WHERE census_id = ? ORDER BY created_timestamp DESC",
            (census_id,),
        )
        return [GridAnalysis.from_row(dict(row)) for row in cursor.fetchall()]


def create_census_from_dataframe(
    df,
    name: str,
    plan_year: int,
    salt: str,
) -> tuple[Census, list[Participant]]:
    """
    Create Census and Participant models from a processed DataFrame.

    Args:
        df: DataFrame with processed census data (with internal_id and compensation_cents)
        name: Census name
        plan_year: Plan year
        salt: Census salt used for ID hashing

    Returns:
        Tuple of (Census, list of Participants)
    """
    census_id = str(uuid.uuid4())

    # Count HCEs and NHCEs
    hce_count = df[df["is_hce"] == True].shape[0]
    nhce_count = df[df["is_hce"] == False].shape[0]

    census = Census(
        id=census_id,
        name=name,
        plan_year=plan_year,
        upload_timestamp=datetime.utcnow(),
        participant_count=len(df),
        hce_count=hce_count,
        nhce_count=nhce_count,
        salt=salt,
        version=SYSTEM_VERSION,
    )

    participants = []
    for _, row in df.iterrows():
        participant = Participant(
            id=str(uuid.uuid4()),
            census_id=census_id,
            internal_id=row["internal_id"],
            is_hce=bool(row["is_hce"]),
            compensation_cents=int(row["compensation_cents"]),
            deferral_rate=float(row["deferral_rate"]),
            match_rate=float(row["match_rate"]),
            after_tax_rate=float(row["after_tax_rate"]),
        )
        participants.append(participant)

    return census, participants
