# Tasks: Source Directory Migration to Backend

**Input**: Design documents from `/specs/013-src-to-backend-migration/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: No new tests required - this migration updates existing tests to use new import paths.

**Organization**: Tasks are grouped by user story to enable independent verification of each migration phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `backend/app/` is the authoritative source
- Root `/tests/` directory contains tests that import from `src.*` (to be updated)
- Configuration at repository root: `pyproject.toml`, `CLAUDE.md`

---

## Phase 1: Setup (Verification)

**Purpose**: Verify current state before making changes

- [X] T001 Verify on correct git branch `013-src-to-backend-migration`
- [X] T002 Run backend tests to establish baseline in `/workspaces/mega_backdoor_acp/backend`
- [X] T003 Document current test results (some failures expected due to broken UI theme tests)

---

## Phase 2: Foundational (Handle Pre-existing Issues)

**Purpose**: Address orphaned tests that would block migration validation

**⚠️ CRITICAL**: These tests reference non-existent `src.ui.theme.*` modules and must be removed before import updates

- [X] T004 Delete orphaned test file `tests/unit/ui/theme/test_colors.py`
- [X] T005 [P] Delete orphaned test file `tests/unit/ui/theme/test_css.py`
- [X] T006 [P] Delete orphaned test file `tests/unit/ui/theme/__init__.py`
- [X] T007 Delete empty directory `tests/unit/ui/theme/`
- [X] T008 Delete empty directory `tests/unit/ui/` if empty

**Checkpoint**: Orphaned tests removed - import updates can now proceed

---

## Phase 3: User Story 3 - Import Path Consistency (Priority: P2)

**Goal**: Update all `src.*` imports to `backend.app.*` throughout the codebase

**Independent Test**: Run `grep -r "from src\." --include="*.py" tests/` - should return no results after completion

**Note**: This phase is done BEFORE US1/US2 because import updates are prerequisites for tests to pass.

### Unit Test Import Updates

- [X] T009 [P] [US3] Update imports in `tests/unit/test_acp_calculator.py`: `src.core.*` → `backend.app.services.*`
- [X] T010 [P] [US3] Update imports in `tests/unit/test_acp_eligibility.py`: `src.core.*` → `backend.app.services.*`
- [X] T011 [P] [US3] Update imports in `tests/unit/test_census_parser.py`: `src.core.*` → `backend.app.services.*`
- [X] T012 [P] [US3] Update imports in `tests/unit/test_debug_mode.py`: `src.core.*` → `backend.app.services.*`
- [X] T013 [P] [US3] Update imports in `tests/unit/test_export.py`: `src.core.*` → `backend.app.services.*`
- [X] T014 [P] [US3] Update imports in `tests/unit/test_grid_summary.py`: `src.core.*` → `backend.app.services.*`
- [X] T015 [P] [US3] Update imports in `tests/unit/test_scenario_runner.py`: `src.core.*` → `backend.app.services.*`
- [X] T016 [P] [US3] Update imports in `tests/unit/core/test_employee_impact.py`: `src.core.*` → `backend.app.services.*`, `src.storage.*` → `backend.app.storage.*`

### Contract Test Import Updates

- [X] T017 [P] [US3] Update imports in `tests/contract/test_api_schemas.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`
- [X] T018 [P] [US3] Update imports in `tests/contract/test_employee_impact_schema.py`: `src.api.*` → `backend.app.routers.*`
- [X] T019 [P] [US3] Update imports in `tests/contract/test_scenario_contracts.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`

### Integration Test Import Updates

- [X] T020 [P] [US3] Update imports in `tests/integration/test_analysis_api.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`
- [X] T021 [P] [US3] Update imports in `tests/integration/test_api_routes.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`
- [X] T022 [P] [US3] Update imports in `tests/integration/test_export_api.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`
- [X] T023 [P] [US3] Update imports in `tests/integration/api/test_employee_impact_api.py`: `src.api.*` → `backend.app.routers.*`, `src.storage.*` → `backend.app.storage.*`

### Configuration File Updates

- [X] T024 [US3] Update `/pyproject.toml`: Change `source = ["src"]` to `source = ["backend/app"]` in `[tool.coverage.run]`
- [X] T025 [US3] Update `/pyproject.toml`: Change `known-first-party = ["src"]` to `known-first-party = ["backend", "app"]` in `[tool.ruff.isort]`

**Checkpoint**: All imports updated - verify with grep that no `src.` imports remain in test files

---

## Phase 4: User Story 2 - Build and Test Execution (Priority: P1)

**Goal**: Verify all tests pass and application runs correctly after import updates

**Independent Test**: Run full test suite and verify application starts

- [X] T026 [US2] Run root tests `pytest tests/ -v` and verify all pass
- [X] T027 [US2] Run backend tests `cd backend && pytest tests/ -v` and verify all pass
- [X] T028 [US2] Start application `cd backend && uvicorn app.routers.main:app` and verify it starts
- [X] T029 [US2] Test health endpoint `curl http://localhost:8000/health` and verify response

**Checkpoint**: All tests pass and application runs - safe to delete `/src`

---

## Phase 5: User Story 1 - Developer Accessing Codebase (Priority: P1)

**Goal**: Remove `/src` directory to establish single source of truth

**Independent Test**: Verify `/src` directory does not exist and no references remain

- [X] T030 [US1] Delete `/src` directory recursively
- [X] T031 [US1] Verify no `src.` import references remain: `grep -r "from src\." --include="*.py" .`
- [X] T032 [US1] Verify no `src.` import references remain: `grep -r "import src\." --include="*.py" .`

**Checkpoint**: `/src` directory removed - codebase has single source of truth

---

## Phase 6: Polish & Documentation

**Purpose**: Update documentation to reflect new structure

- [X] T033 [P] Update `/CLAUDE.md`: Remove `src/` from project structure section
- [X] T034 [P] Update `/CLAUDE.md`: Update commands section to reference `backend/` paths
- [X] T035 Run final verification: all tests pass, app starts, no src references
- [X] T036 Commit all changes with message: "chore: migrate from /src to /backend directory structure"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - removes blocking orphaned tests
- **US3 Import Updates (Phase 3)**: Depends on Foundational - updates all imports
- **US2 Build/Test (Phase 4)**: Depends on US3 - verifies tests pass
- **US1 Delete /src (Phase 5)**: Depends on US2 - safe to delete only after tests pass
- **Polish (Phase 6)**: Depends on US1 - documentation updates

### Critical Path

```
Setup → Foundational → US3 (Imports) → US2 (Verify) → US1 (Delete) → Polish
```

**Note**: This migration has a strict sequential dependency because tests must pass before deleting `/src`.

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T004, T005, T006 can run in parallel (different files)

**Within Phase 3 (US3 Import Updates)**:
- All T009-T023 can run in parallel (different test files)
- T024, T025 must run sequentially (same file: pyproject.toml)

**Within Phase 6 (Polish)**:
- T033, T034 can run in parallel (different sections of CLAUDE.md, but same file - actually sequential)

---

## Parallel Example: Phase 3 Import Updates

```bash
# Launch all unit test import updates together:
Task: "Update imports in tests/unit/test_acp_calculator.py"
Task: "Update imports in tests/unit/test_acp_eligibility.py"
Task: "Update imports in tests/unit/test_census_parser.py"
Task: "Update imports in tests/unit/test_debug_mode.py"
Task: "Update imports in tests/unit/test_export.py"
Task: "Update imports in tests/unit/test_grid_summary.py"
Task: "Update imports in tests/unit/test_scenario_runner.py"
Task: "Update imports in tests/unit/core/test_employee_impact.py"

# Launch all contract test import updates together:
Task: "Update imports in tests/contract/test_api_schemas.py"
Task: "Update imports in tests/contract/test_employee_impact_schema.py"
Task: "Update imports in tests/contract/test_scenario_contracts.py"

# Launch all integration test import updates together:
Task: "Update imports in tests/integration/test_analysis_api.py"
Task: "Update imports in tests/integration/test_api_routes.py"
Task: "Update imports in tests/integration/test_export_api.py"
Task: "Update imports in tests/integration/api/test_employee_impact_api.py"
```

---

## Implementation Strategy

### MVP First (Minimal Viable Migration)

1. Complete Phase 1: Setup (verify state)
2. Complete Phase 2: Foundational (remove broken tests)
3. Complete Phase 3: US3 (update imports)
4. Complete Phase 4: US2 (verify tests pass)
5. **STOP and VALIDATE**: If tests fail, debug before proceeding
6. Complete Phase 5: US1 (delete /src)
7. Complete Phase 6: Polish (update docs)

### Rollback Points

- **After Phase 2**: Can restore orphaned tests from git if needed
- **After Phase 3**: Can revert import changes with `git checkout -- tests/`
- **After Phase 5**: Cannot easily restore `/src` - ensure Phase 4 passes first

### Commit Strategy

1. Commit after Phase 2: "chore: remove orphaned UI theme tests"
2. Commit after Phase 3: "refactor: update test imports from src to backend.app"
3. Commit after Phase 4: (no changes, just verification)
4. Commit after Phase 5: "chore: remove legacy /src directory"
5. Commit after Phase 6: "docs: update documentation for backend-only structure"

Or single commit at end: "chore: migrate from /src to /backend directory structure"

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This migration has strict sequential dependencies between phases
- Always verify tests pass (Phase 4) before deleting /src (Phase 5)
- Pre-existing broken tests (UI theme) are out of scope - just remove them
