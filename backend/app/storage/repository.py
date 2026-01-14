"""
Repository Layer for Data Access.

Provides CRUD operations for census, participant, and analysis entities.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Generator

from app.services.constants import SYSTEM_VERSION
from app.storage.models import (
    Census,
    Participant,
    AnalysisResult,
    GridAnalysis,
    ImportMetadata,
    HCEMode,
    ImportSession,
    MappingProfile,
    ValidationIssue,
    ImportLog,
)


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
            INSERT INTO census (id, name, client_name, plan_year, hce_mode, upload_timestamp,
                              participant_count, hce_count, nhce_count,
                              avg_compensation_cents, avg_deferral_rate, salt, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                census.id,
                census.name,
                census.client_name,
                census.plan_year,
                census.hce_mode,
                census.upload_timestamp.isoformat(),
                census.participant_count,
                census.hce_count,
                census.nhce_count,
                census.avg_compensation_cents,
                census.avg_deferral_rate,
                census.salt,
                census.version,
            ),
        )
        self.conn.commit()
        return census

    def update(self, census_id: str, name: str | None = None, client_name: str | None = None) -> Census | None:
        """
        Update census metadata (name, client_name only).

        Args:
            census_id: Census ID to update
            name: New name (if provided)
            client_name: New client name (if provided)

        Returns:
            Updated Census or None if not found
        """
        census = self.get(census_id)
        if census is None:
            return None

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if client_name is not None:
            updates.append("client_name = ?")
            params.append(client_name)

        if not updates:
            return census

        params.append(census_id)
        self.conn.execute(
            f"UPDATE census SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self.conn.commit()

        return self.get(census_id)

    def has_analyses(self, census_id: str) -> bool:
        """Check if a census has associated analyses."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM analysis_result WHERE census_id = ?",
            (census_id,),
        )
        count = cursor.fetchone()[0]
        return count > 0

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
        client_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Census], int]:
        """
        List censuses with optional filtering.

        Args:
            plan_year: Filter by plan year
            client_name: Filter by client name (partial match)
            limit: Maximum results to return
            offset: Pagination offset

        Returns tuple of (census list, total count).
        """
        # Build query
        conditions = []
        params: list = []

        if plan_year is not None:
            conditions.append("plan_year = ?")
            params.append(plan_year)

        if client_name is not None:
            conditions.append("client_name LIKE ?")
            params.append(f"%{client_name}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

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

    def list_participants(
        self,
        census_id: str,
        hce_only: bool = False,
        nhce_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Participant], int]:
        """
        List participants with optional HCE filtering and pagination.

        Args:
            census_id: Census ID to filter by
            hce_only: Return only HCE participants
            nhce_only: Return only NHCE participants
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (participant list, total count)
        """
        conditions = ["census_id = ?"]
        params: list = [census_id]

        if hce_only:
            conditions.append("is_hce = 1")
        elif nhce_only:
            conditions.append("is_hce = 0")

        where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM participant {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM participant {where_clause}
            ORDER BY internal_id
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        participants = [Participant.from_row(dict(row)) for row in cursor.fetchall()]
        return participants, total


class ImportMetadataRepository:
    """
    Repository for ImportMetadata entity operations.

    T007: ImportMetadataRepository with save/get methods
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, metadata: ImportMetadata) -> ImportMetadata:
        """Save import metadata to the database."""
        self.conn.execute(
            """
            INSERT INTO import_metadata (id, census_id, source_filename,
                                        column_mapping, row_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.id,
                metadata.census_id,
                metadata.source_filename,
                json.dumps(metadata.column_mapping),
                metadata.row_count,
                metadata.created_at.isoformat(),
            ),
        )
        self.conn.commit()
        return metadata

    def get_by_census(self, census_id: str) -> ImportMetadata | None:
        """Get import metadata for a census."""
        cursor = self.conn.execute(
            "SELECT * FROM import_metadata WHERE census_id = ?",
            (census_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return ImportMetadata.from_row(dict(row))


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
    client_name: str | None = None,
    hce_mode: HCEMode = "explicit",
) -> tuple[Census, list[Participant]]:
    """
    Create Census and Participant models from a processed DataFrame.

    Args:
        df: DataFrame with processed census data (with internal_id and compensation_cents)
        name: Census name
        plan_year: Plan year
        salt: Census salt used for ID hashing
        client_name: Optional client name
        hce_mode: HCE determination mode used

    Returns:
        Tuple of (Census, list of Participants)
    """
    census_id = str(uuid.uuid4())

    # Count HCEs and NHCEs
    hce_count = int(df[df["is_hce"] == True].shape[0])
    nhce_count = int(df[df["is_hce"] == False].shape[0])

    # Calculate summary statistics
    avg_compensation_cents = None
    avg_deferral_rate = None

    if len(df) > 0:
        if "compensation_cents" in df.columns:
            avg_compensation_cents = int(df["compensation_cents"].mean())
        if "deferral_rate" in df.columns:
            avg_deferral_rate = float(df["deferral_rate"].mean())

    census = Census(
        id=census_id,
        name=name,
        client_name=client_name,
        plan_year=plan_year,
        hce_mode=hce_mode,
        upload_timestamp=datetime.utcnow(),
        participant_count=len(df),
        hce_count=hce_count,
        nhce_count=nhce_count,
        avg_compensation_cents=avg_compensation_cents,
        avg_deferral_rate=avg_deferral_rate,
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


# ============================================================================
# CSV Import Wizard Repositories (Feature 003-csv-import-wizard)
# ============================================================================


class ImportSessionRepository:
    """
    Repository for ImportSession entity operations.

    T008: ImportSessionRepository with CRUD operations
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, session: ImportSession) -> ImportSession:
        """Save a new import session to the database."""
        data = session.to_dict()
        self.conn.execute(
            """
            INSERT INTO import_session (
                id, user_id, created_at, updated_at, expires_at, current_step,
                file_reference, original_filename, file_size_bytes, row_count,
                headers, column_mapping, validation_results, duplicate_resolution,
                import_result_id, workspace_id, date_format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["user_id"],
                data["created_at"],
                data["updated_at"],
                data["expires_at"],
                data["current_step"],
                data["file_reference"],
                data["original_filename"],
                data["file_size_bytes"],
                data["row_count"],
                data["headers"],
                data["column_mapping"],
                data["validation_results"],
                data["duplicate_resolution"],
                data["import_result_id"],
                data.get("workspace_id"),
                data.get("date_format"),
            ),
        )
        self.conn.commit()
        return session

    def update(self, session: ImportSession) -> ImportSession:
        """Update an existing import session."""
        session.updated_at = datetime.utcnow()
        data = session.to_dict()
        self.conn.execute(
            """
            UPDATE import_session SET
                updated_at = ?,
                current_step = ?,
                file_reference = ?,
                original_filename = ?,
                file_size_bytes = ?,
                row_count = ?,
                headers = ?,
                column_mapping = ?,
                validation_results = ?,
                duplicate_resolution = ?,
                import_result_id = ?,
                workspace_id = ?,
                date_format = ?
            WHERE id = ?
            """,
            (
                data["updated_at"],
                data["current_step"],
                data["file_reference"],
                data["original_filename"],
                data["file_size_bytes"],
                data["row_count"],
                data["headers"],
                data["column_mapping"],
                data["validation_results"],
                data["duplicate_resolution"],
                data["import_result_id"],
                data.get("workspace_id"),
                data.get("date_format"),
                data["id"],
            ),
        )
        self.conn.commit()
        return session

    def get(self, session_id: str) -> ImportSession | None:
        """Get an import session by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM import_session WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return ImportSession.from_row(dict(row))

    def list(
        self,
        user_id: str | None = None,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ImportSession], int]:
        """
        List import sessions with optional filtering.

        Args:
            user_id: Filter by user ID
            include_expired: Include expired sessions
            limit: Maximum results to return
            offset: Pagination offset

        Returns tuple of (sessions list, total count).
        """
        conditions = []
        params: list = []

        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)

        if not include_expired:
            conditions.append("expires_at > datetime('now')")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM import_session {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM import_session {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        sessions = [ImportSession.from_row(dict(row)) for row in cursor.fetchall()]
        return sessions, total

    def delete(self, session_id: str) -> bool:
        """
        Delete an import session.

        Returns True if session was deleted, False if not found.
        """
        if self.get(session_id) is None:
            return False

        self.conn.execute("DELETE FROM import_session WHERE id = ?", (session_id,))
        self.conn.commit()
        return True

    def delete_expired(self) -> int:
        """
        Delete all expired sessions.

        Returns count of deleted sessions.
        """
        cursor = self.conn.execute(
            "DELETE FROM import_session WHERE expires_at <= datetime('now')"
        )
        self.conn.commit()
        return cursor.rowcount


class MappingProfileRepository:
    """
    Repository for MappingProfile entity operations.

    T009: MappingProfileRepository with CRUD operations
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, profile: MappingProfile) -> MappingProfile:
        """Save a new mapping profile to the database."""
        data = profile.to_dict()
        self.conn.execute(
            """
            INSERT INTO mapping_profile (
                id, user_id, name, description, created_at, updated_at,
                column_mapping, expected_headers, workspace_id, date_format, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["user_id"],
                data["name"],
                data["description"],
                data["created_at"],
                data["updated_at"],
                data["column_mapping"],
                data["expected_headers"],
                data.get("workspace_id"),
                data.get("date_format"),
                1 if data.get("is_default") else 0,
            ),
        )
        self.conn.commit()
        return profile

    def update(self, profile: MappingProfile) -> MappingProfile:
        """Update an existing mapping profile."""
        profile.updated_at = datetime.utcnow()
        data = profile.to_dict()
        self.conn.execute(
            """
            UPDATE mapping_profile SET
                name = ?,
                description = ?,
                updated_at = ?,
                column_mapping = ?,
                expected_headers = ?,
                date_format = ?,
                is_default = ?
            WHERE id = ?
            """,
            (
                data["name"],
                data["description"],
                data["updated_at"],
                data["column_mapping"],
                data["expected_headers"],
                data.get("date_format"),
                1 if data.get("is_default") else 0,
                data["id"],
            ),
        )
        self.conn.commit()
        return profile

    def get(self, profile_id: str) -> MappingProfile | None:
        """Get a mapping profile by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM mapping_profile WHERE id = ?",
            (profile_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return MappingProfile.from_row(dict(row))

    def get_by_name(
        self,
        name: str,
        user_id: str | None = None,
        workspace_id: str | None = None,
    ) -> MappingProfile | None:
        """
        Get a mapping profile by name.

        Args:
            name: Profile name to look up
            user_id: Optional user ID filter
            workspace_id: Optional workspace ID filter (T037: workspace-scoped profiles)

        Returns:
            MappingProfile if found, None otherwise
        """
        conditions = ["name = ?"]
        params: list = [name]

        if workspace_id is not None:
            conditions.append("workspace_id = ?")
            params.append(workspace_id)
        elif user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        else:
            conditions.append("user_id IS NULL AND workspace_id IS NULL")

        query = f"SELECT * FROM mapping_profile WHERE {' AND '.join(conditions)}"
        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        if row is None:
            return None
        return MappingProfile.from_row(dict(row))

    def list(
        self,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MappingProfile], int]:
        """
        List mapping profiles with optional filtering.

        Args:
            user_id: Filter by user ID
            limit: Maximum results to return
            offset: Pagination offset

        Returns tuple of (profiles list, total count).
        """
        conditions = []
        params: list = []

        if user_id is not None:
            conditions.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM mapping_profile {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM mapping_profile {where_clause}
            ORDER BY name ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        profiles = [MappingProfile.from_row(dict(row)) for row in cursor.fetchall()]
        return profiles, total

    def list_by_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MappingProfile], int]:
        """
        List mapping profiles for a specific workspace.

        T037: Workspace-scoped profile listing.

        Args:
            workspace_id: Workspace ID to filter by
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (profiles list, total count)
        """
        # Get total count
        count_cursor = self.conn.execute(
            "SELECT COUNT(*) FROM mapping_profile WHERE workspace_id = ?",
            (workspace_id,),
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            """
            SELECT * FROM mapping_profile
            WHERE workspace_id = ?
            ORDER BY is_default DESC, name ASC
            LIMIT ? OFFSET ?
            """,
            (workspace_id, limit, offset),
        )

        profiles = [MappingProfile.from_row(dict(row)) for row in cursor.fetchall()]
        return profiles, total

    def delete(self, profile_id: str) -> bool:
        """
        Delete a mapping profile.

        Returns True if profile was deleted, False if not found.
        """
        if self.get(profile_id) is None:
            return False

        self.conn.execute("DELETE FROM mapping_profile WHERE id = ?", (profile_id,))
        self.conn.commit()
        return True


class ValidationIssueRepository:
    """
    Repository for ValidationIssue entity operations.

    T010: ValidationIssueRepository with bulk insert and query by severity
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def bulk_insert(self, issues: list[ValidationIssue]) -> int:
        """
        Insert multiple validation issues at once.

        Returns count of inserted records.
        """
        if not issues:
            return 0

        self.conn.executemany(
            """
            INSERT INTO validation_issue (
                id, session_id, row_number, field_name, source_column,
                severity, issue_code, message, suggestion, raw_value, related_row
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    i.id,
                    i.session_id,
                    i.row_number,
                    i.field_name,
                    i.source_column,
                    i.severity,
                    i.issue_code,
                    i.message,
                    i.suggestion,
                    i.raw_value,
                    i.related_row,
                )
                for i in issues
            ],
        )
        self.conn.commit()
        return len(issues)

    def get_by_session(
        self,
        session_id: str,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ValidationIssue], int]:
        """
        Get validation issues for a session with optional severity filter.

        Args:
            session_id: Session ID to filter by
            severity: Optional severity filter (error, warning, info)
            limit: Maximum results to return
            offset: Pagination offset

        Returns tuple of (issues list, total count).
        """
        conditions = ["session_id = ?"]
        params: list = [session_id]

        if severity is not None:
            conditions.append("severity = ?")
            params.append(severity)

        where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM validation_issue {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM validation_issue {where_clause}
            ORDER BY row_number ASC, severity DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        issues = [ValidationIssue.from_row(dict(row)) for row in cursor.fetchall()]
        return issues, total

    def get_summary(self, session_id: str) -> dict[str, int]:
        """
        Get count of issues by severity for a session.

        Returns dict with error_count, warning_count, info_count.
        """
        cursor = self.conn.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM validation_issue
            WHERE session_id = ?
            GROUP BY severity
            """,
            (session_id,),
        )

        result = {"error": 0, "warning": 0, "info": 0}
        for row in cursor.fetchall():
            result[row["severity"]] = row["count"]

        return result

    def delete_by_session(self, session_id: str) -> int:
        """
        Delete all validation issues for a session.

        Returns count of deleted records.
        """
        cursor = self.conn.execute(
            "DELETE FROM validation_issue WHERE session_id = ?",
            (session_id,),
        )
        self.conn.commit()
        return cursor.rowcount


class ImportLogRepository:
    """
    Repository for ImportLog entity operations.

    T011: ImportLogRepository with CRUD and soft delete
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, log: ImportLog) -> ImportLog:
        """Save a new import log to the database."""
        data = log.to_dict()
        self.conn.execute(
            """
            INSERT INTO import_log (
                id, session_id, census_id, created_at, completed_at,
                original_filename, total_rows, imported_count, rejected_count,
                warning_count, replaced_count, skipped_count,
                column_mapping_used, detailed_results, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["session_id"],
                data["census_id"],
                data["created_at"],
                data["completed_at"],
                data["original_filename"],
                data["total_rows"],
                data["imported_count"],
                data["rejected_count"],
                data["warning_count"],
                data["replaced_count"],
                data["skipped_count"],
                data["column_mapping_used"],
                data["detailed_results"],
                data["deleted_at"],
            ),
        )
        self.conn.commit()
        return log

    def update(self, log: ImportLog) -> ImportLog:
        """Update an existing import log."""
        data = log.to_dict()
        self.conn.execute(
            """
            UPDATE import_log SET
                census_id = ?,
                completed_at = ?,
                imported_count = ?,
                rejected_count = ?,
                warning_count = ?,
                replaced_count = ?,
                skipped_count = ?,
                detailed_results = ?,
                deleted_at = ?
            WHERE id = ?
            """,
            (
                data["census_id"],
                data["completed_at"],
                data["imported_count"],
                data["rejected_count"],
                data["warning_count"],
                data["replaced_count"],
                data["skipped_count"],
                data["detailed_results"],
                data["deleted_at"],
                data["id"],
            ),
        )
        self.conn.commit()
        return log

    def get(self, log_id: str) -> ImportLog | None:
        """Get an import log by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM import_log WHERE id = ? AND deleted_at IS NULL",
            (log_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return ImportLog.from_row(dict(row))

    def list(
        self,
        census_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ImportLog], int]:
        """
        List import logs with optional filtering.

        Args:
            census_id: Filter by census ID
            include_deleted: Include soft-deleted logs
            limit: Maximum results to return
            offset: Pagination offset

        Returns tuple of (logs list, total count).
        """
        conditions = []
        params: list = []

        if census_id is not None:
            conditions.append("census_id = ?")
            params.append(census_id)

        if not include_deleted:
            conditions.append("deleted_at IS NULL")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM import_log {where_clause}",
            params,
        )
        total = count_cursor.fetchone()[0]

        # Get paginated results
        cursor = self.conn.execute(
            f"""
            SELECT * FROM import_log {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        logs = [ImportLog.from_row(dict(row)) for row in cursor.fetchall()]
        return logs, total

    def soft_delete(self, log_id: str) -> bool:
        """
        Soft delete an import log.

        Returns True if log was deleted, False if not found.
        """
        log = self.get(log_id)
        if log is None:
            return False

        log.deleted_at = datetime.utcnow()
        self.update(log)
        return True
