# Research: Source Directory Migration to Backend

**Date**: 2026-01-16
**Feature**: 013-src-to-backend-migration

## Executive Summary

The `/src` directory contains 26 Python files that are legacy code. The `/backend` directory contains 36 Python files in `app/` plus 22 test files. Analysis shows that `/backend` already has equivalent (and more complete) implementations for all `/src` functionality.

**Decision**: Delete `/src` entirely and update imports to point to `/backend/app/*`.

## File Mapping Analysis

### Comparison: `/src` vs `/backend`

| `/src` Module | `/backend` Equivalent | Status |
|---------------|----------------------|--------|
| `src/api/main.py` | `backend/app/routers/main.py` | ✅ Equivalent exists |
| `src/api/schemas.py` | `backend/app/routers/schemas.py` | ✅ Equivalent exists |
| `src/api/dependencies.py` | `backend/app/routers/dependencies.py` | ✅ Equivalent exists |
| `src/api/routes/analysis.py` | `backend/app/routers/routes/analysis.py` | ✅ Equivalent exists |
| `src/api/routes/census.py` | `backend/app/routers/routes/census.py` | ✅ Equivalent exists |
| `src/api/routes/export.py` | `backend/app/routers/routes/export.py` | ✅ Equivalent exists |
| `src/api/routes/import_wizard.py` | `backend/app/routers/routes/import_wizard.py` | ✅ Equivalent exists |
| `src/core/acp_calculator.py` | `backend/app/services/acp_calculator.py` | ✅ Equivalent exists |
| `src/core/acp_eligibility.py` | `backend/app/services/acp_eligibility.py` | ✅ Equivalent exists |
| `src/core/census_parser.py` | `backend/app/services/census_parser.py` | ✅ Equivalent exists |
| `src/core/constants.py` | `backend/app/services/constants.py` | ✅ Equivalent exists |
| `src/core/employee_impact.py` | `backend/app/services/employee_impact.py` | ✅ Equivalent exists |
| `src/core/export.py` | `backend/app/services/export.py` | ✅ Equivalent exists |
| `src/core/field_mappings.py` | `backend/app/services/field_mappings.py` | ✅ Equivalent exists |
| `src/core/hce_thresholds.py` | `backend/app/services/hce_thresholds.py` | ✅ Equivalent exists |
| `src/core/import_wizard.py` | `backend/app/services/import_wizard.py` | ✅ Equivalent exists |
| `src/core/models.py` | `backend/app/services/models.py` | ✅ Equivalent exists |
| `src/core/scenario_runner.py` | `backend/app/services/scenario_runner.py` | ✅ Equivalent exists |
| `src/storage/database.py` | `backend/app/storage/database.py` | ✅ Equivalent exists |
| `src/storage/models.py` | `backend/app/storage/models.py` | ✅ Equivalent exists |
| `src/storage/repository.py` | `backend/app/storage/repository.py` | ✅ Equivalent exists |

### Additional Files in `/backend` (not in `/src`)

| File | Purpose |
|------|---------|
| `backend/app/models/analysis.py` | Pydantic models for analysis |
| `backend/app/models/census.py` | Pydantic models for census |
| `backend/app/models/errors.py` | Error response models |
| `backend/app/models/run.py` | Run-related models |
| `backend/app/models/workspace.py` | Workspace models |
| `backend/app/routers/workspaces.py` | Workspace management routes |
| `backend/app/services/date_parser.py` | Date parsing utilities |
| `backend/app/storage/utils.py` | Storage utilities |
| `backend/app/storage/workspace_storage.py` | Workspace storage layer |

### Missing in `/backend` (unique to `/src`)

None. All `/src` functionality exists in `/backend`.

### Pre-existing Issues (Out of Scope)

The tests `tests/unit/ui/theme/test_colors.py` and `tests/unit/ui/theme/test_css.py` reference `src.ui.theme.*` modules that **do not exist**. These tests are currently failing/broken and represent pre-existing technical debt.

**Decision**: These tests are out of scope for this migration. They should be addressed in a separate cleanup task (either create the missing modules or delete the orphaned tests).

## Import Mapping

### Required Import Updates

| Old Import Pattern | New Import Pattern |
|-------------------|-------------------|
| `from src.api.main` | `from backend.app.routers.main` |
| `from src.api.schemas` | `from backend.app.routers.schemas` |
| `from src.api.routes.*` | `from backend.app.routers.routes.*` |
| `from src.core.*` | `from backend.app.services.*` |
| `from src.storage.*` | `from backend.app.storage.*` |
| `from src.storage.database` | `from backend.app.storage.database` |
| `from src.storage.models` | `from backend.app.storage.models` |
| `from src.storage.repository` | `from backend.app.storage.repository` |

### Files Requiring Import Updates (31 total)

**Root `/tests/` directory**:
1. `tests/unit/test_acp_calculator.py`
2. `tests/unit/test_acp_eligibility.py`
3. `tests/unit/test_census_parser.py`
4. `tests/unit/test_debug_mode.py`
5. `tests/unit/test_export.py`
6. `tests/unit/test_grid_summary.py`
7. `tests/unit/test_scenario_runner.py`
8. `tests/unit/core/test_employee_impact.py`
9. `tests/unit/ui/theme/test_colors.py`
10. `tests/unit/ui/theme/test_css.py`
11. `tests/contract/test_api_schemas.py`
12. `tests/contract/test_employee_impact_schema.py`
13. `tests/contract/test_scenario_contracts.py`
14. `tests/integration/test_analysis_api.py`
15. `tests/integration/test_api_routes.py`
16. `tests/integration/test_export_api.py`
17. `tests/integration/api/test_employee_impact_api.py`

## Configuration Updates Required

### `/pyproject.toml` (root)

| Setting | Current Value | New Value |
|---------|---------------|-----------|
| `[tool.coverage.run] source` | `["src"]` | `["backend/app"]` |
| `[tool.ruff.isort] known-first-party` | `["src"]` | `["backend", "app"]` |

### `/CLAUDE.md`

Update project structure section:
- Remove `src/` from structure diagram
- Update commands section if referencing `src/`

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Tests fail after import updates | Run full test suite after each batch of changes |
| Missing functionality in `/backend` | File comparison already done - all covered |
| UI theme files missing | Investigate if `src/ui/` exists, move if needed |
| External tools referencing `/src` | Search for all `src/` references in config files |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Keep both directories | Creates confusion, violates DRY principle |
| Symlink `/src` → `/backend` | Temporary solution, doesn't clean up codebase |
| Merge incrementally over time | Prolongs technical debt |

## Decision Summary

1. **Delete `/src` entirely**: All functionality exists in `/backend`
2. **Update imports**: Change `src.*` → `backend.app.*` in all test files
3. **Update configs**: Modify `pyproject.toml` and `CLAUDE.md`
4. **Verify tests pass**: Run full test suite after migration
5. **Handle UI theme**: Investigate and handle separately if needed
