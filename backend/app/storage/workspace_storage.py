"""File-based workspace storage implementation."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.models.census import CensusSummary
from app.models.run import Run, RunStatus
from app.models.workspace import Workspace, WorkspaceCreate, WorkspaceDetail, WorkspaceUpdate
from app.storage.utils import atomic_write


def get_workspace_base_dir() -> Path:
    """Get the base directory for workspace storage."""
    base_dir = os.environ.get("ACP_WORKSPACE_DIR", "~/.acp-analyzer/workspaces")
    return Path(base_dir).expanduser()


class WorkspaceStorage:
    """File-based storage for workspaces and related data."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize workspace storage.

        Args:
            base_dir: Base directory for workspace files. Defaults to ~/.acp-analyzer/workspaces
        """
        self.base_dir = base_dir or get_workspace_base_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _workspace_dir(self, workspace_id: UUID) -> Path:
        """Get directory path for a workspace."""
        return self.base_dir / str(workspace_id)

    def _workspace_file(self, workspace_id: UUID) -> Path:
        """Get path to workspace.json file."""
        return self._workspace_dir(workspace_id) / "workspace.json"

    def _census_file(self, workspace_id: UUID) -> Path:
        """Get path to census data directory."""
        return self._workspace_dir(workspace_id) / "data" / "census.csv"

    def _census_summary_file(self, workspace_id: UUID) -> Path:
        """Get path to census summary file."""
        return self._workspace_dir(workspace_id) / "data" / "census_summary.json"

    def _runs_dir(self, workspace_id: UUID) -> Path:
        """Get path to runs directory."""
        return self._workspace_dir(workspace_id) / "runs"

    def _run_dir(self, workspace_id: UUID, run_id: UUID) -> Path:
        """Get directory path for a specific run."""
        return self._runs_dir(workspace_id) / str(run_id)

    def _run_metadata_file(self, workspace_id: UUID, run_id: UUID) -> Path:
        """Get path to run metadata file."""
        return self._run_dir(workspace_id, run_id) / "run_metadata.json"

    def _run_results_file(self, workspace_id: UUID, run_id: UUID) -> Path:
        """Get path to run results file."""
        return self._run_dir(workspace_id, run_id) / "grid_results.json"

    # --- Workspace CRUD ---

    def list_workspaces(self) -> list[Workspace]:
        """List all workspaces sorted by updated_at descending."""
        workspaces = []
        if not self.base_dir.exists():
            return workspaces

        for entry in self.base_dir.iterdir():
            if entry.is_dir():
                workspace_file = entry / "workspace.json"
                if workspace_file.exists():
                    try:
                        data = json.loads(workspace_file.read_text())
                        workspaces.append(Workspace(**data))
                    except (json.JSONDecodeError, ValueError):
                        # Skip invalid workspace files
                        continue

        # Sort by updated_at descending
        workspaces.sort(key=lambda w: w.updated_at, reverse=True)
        return workspaces

    def create_workspace(self, data: WorkspaceCreate) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            name=data.name,
            description=data.description,
        )

        # Create workspace directory structure
        workspace_dir = self._workspace_dir(workspace.id)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        (workspace_dir / "data").mkdir(exist_ok=True)
        (workspace_dir / "runs").mkdir(exist_ok=True)

        # Save workspace metadata
        atomic_write(
            self._workspace_file(workspace.id),
            workspace.model_dump_json(indent=2)
        )

        return workspace

    def get_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        """Get a workspace by ID."""
        workspace_file = self._workspace_file(workspace_id)
        if not workspace_file.exists():
            return None

        data = json.loads(workspace_file.read_text())
        return Workspace(**data)

    def get_workspace_detail(self, workspace_id: UUID) -> Optional[WorkspaceDetail]:
        """Get workspace with computed fields (has_census, run_count)."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        has_census = self._census_file(workspace_id).exists()
        run_count = len(self.list_runs(workspace_id))

        return WorkspaceDetail(
            **workspace.model_dump(),
            has_census=has_census,
            run_count=run_count,
        )

    def update_workspace(self, workspace_id: UUID, data: WorkspaceUpdate) -> Optional[Workspace]:
        """Update a workspace."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workspace, field, value)

        workspace.updated_at = datetime.utcnow()

        atomic_write(
            self._workspace_file(workspace_id),
            workspace.model_dump_json(indent=2)
        )

        return workspace

    def delete_workspace(self, workspace_id: UUID) -> bool:
        """Delete a workspace and all its data."""
        workspace_dir = self._workspace_dir(workspace_id)
        if not workspace_dir.exists():
            return False

        shutil.rmtree(workspace_dir)
        return True

    # --- Census operations ---

    def get_census_summary(self, workspace_id: UUID) -> Optional[CensusSummary]:
        """Get census summary for a workspace."""
        summary_file = self._census_summary_file(workspace_id)
        if not summary_file.exists():
            return None

        data = json.loads(summary_file.read_text())
        return CensusSummary(**data)

    def save_census_summary(self, workspace_id: UUID, summary: CensusSummary) -> None:
        """Save census summary."""
        summary_file = self._census_summary_file(workspace_id)
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(summary_file, summary.model_dump_json(indent=2))

    def save_census_data(self, workspace_id: UUID, csv_content: str) -> None:
        """Save census CSV data."""
        census_file = self._census_file(workspace_id)
        census_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(census_file, csv_content)

    def get_census_data_path(self, workspace_id: UUID) -> Optional[Path]:
        """Get path to census CSV file if it exists."""
        census_file = self._census_file(workspace_id)
        if census_file.exists():
            return census_file
        return None

    # --- Run operations ---

    def list_runs(self, workspace_id: UUID) -> list[Run]:
        """List all runs for a workspace."""
        runs_dir = self._runs_dir(workspace_id)
        runs = []

        if not runs_dir.exists():
            return runs

        for entry in runs_dir.iterdir():
            if entry.is_dir():
                metadata_file = entry / "run_metadata.json"
                if metadata_file.exists():
                    try:
                        data = json.loads(metadata_file.read_text())
                        runs.append(Run(**data))
                    except (json.JSONDecodeError, ValueError):
                        continue

        # Sort by created_at descending
        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs

    def create_run(self, workspace_id: UUID, run: Run) -> Run:
        """Create a new run."""
        run_dir = self._run_dir(workspace_id, run.id)
        run_dir.mkdir(parents=True, exist_ok=True)

        atomic_write(
            self._run_metadata_file(workspace_id, run.id),
            run.model_dump_json(indent=2)
        )

        return run

    def get_run(self, workspace_id: UUID, run_id: UUID) -> Optional[Run]:
        """Get a run by ID."""
        metadata_file = self._run_metadata_file(workspace_id, run_id)
        if not metadata_file.exists():
            return None

        data = json.loads(metadata_file.read_text())
        return Run(**data)

    def update_run(self, workspace_id: UUID, run: Run) -> None:
        """Update run metadata."""
        atomic_write(
            self._run_metadata_file(workspace_id, run.id),
            run.model_dump_json(indent=2)
        )

    def delete_run(self, workspace_id: UUID, run_id: UUID) -> bool:
        """Delete a run and its results."""
        run_dir = self._run_dir(workspace_id, run_id)
        if not run_dir.exists():
            return False

        shutil.rmtree(run_dir)
        return True

    def save_run_results(self, workspace_id: UUID, run_id: UUID, results: dict) -> None:
        """Save run results."""
        atomic_write(
            self._run_results_file(workspace_id, run_id),
            json.dumps(results, indent=2)
        )

    def get_run_results(self, workspace_id: UUID, run_id: UUID) -> Optional[dict]:
        """Get run results."""
        results_file = self._run_results_file(workspace_id, run_id)
        if not results_file.exists():
            return None

        return json.loads(results_file.read_text())


# Global instance for convenience
_storage: Optional[WorkspaceStorage] = None


def get_workspace_storage() -> WorkspaceStorage:
    """Get the global workspace storage instance."""
    global _storage
    if _storage is None:
        _storage = WorkspaceStorage()
    return _storage
