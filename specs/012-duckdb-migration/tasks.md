# Tasks: DuckDB Migration

**Input**: Design documents from `/specs/012-duckdb-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Existing tests will be updated to work with DuckDB. No new test tasks required as this is a backend migration with preserved functionality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Primary database code**: `src/storage/`
- **Backend database code**: `backend/app/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add DuckDB dependency and prepare for migration

- [x] T001 [P] Add `duckdb>=1.0.0` to pyproject.toml dependencies
- [x] T002 [P] Add `duckdb>=1.0.0` to requirements.txt
- [x] T003 Install DuckDB and verify installation with `pip install -e .`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database infrastructure that MUST be complete before user stories can be validated

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create DuckDB schema SQL string in src/storage/database.py with all tables from data-model.md
- [ ] T005 Implement `get_workspace_db_path(workspace_id: str) -> Path` function in src/storage/database.py
- [ ] T006 Implement `create_connection(db_path: Path) -> duckdb.DuckDBPyConnection` function in src/storage/database.py
- [ ] T007 Implement `init_database(conn: duckdb.DuckDBPyConnection) -> None` function in src/storage/database.py
- [ ] T008 Update type hints from `sqlite3.Connection` to `duckdb.DuckDBPyConnection` in src/storage/repository.py

**Checkpoint**: Foundation ready - DuckDB connection and schema infrastructure in place

---

## Phase 3: User Story 1 - Workspace Data Isolation (Priority: P1) 🎯 MVP

**Goal**: Each workspace gets its own isolated DuckDB database file

**Independent Test**: Create two workspaces, import data into each, verify complete isolation

### Implementation for User Story 1

- [ ] T009 [US1] Remove `DATABASE_PATH` constant from src/core/constants.py (no longer a single database file)
- [ ] T010 [US1] Add workspace database path constants to src/core/constants.py: `WORKSPACE_BASE_DIR`, `WORKSPACE_DB_FILENAME`
- [ ] T011 [US1] Implement workspace-aware `get_db(workspace_id: str)` function in src/storage/database.py
- [ ] T012 [US1] Implement workspace-aware `close_db(workspace_id: str)` function in src/storage/database.py
- [ ] T013 [US1] Update `get_connection()` context manager to accept workspace_id parameter in src/storage/database.py
- [ ] T014 [US1] Update FastAPI dependency injection to use workspace_id from request header in src/api/main.py
- [ ] T015 [US1] Add schema_version table creation to init_database() in src/storage/database.py

**Checkpoint**: Workspace isolation is functional - each workspace creates its own database file

---

## Phase 4: User Story 2 - Complete SQLite Replacement (Priority: P1)

**Goal**: Remove all SQLite code and references from the codebase

**Independent Test**: Search codebase for "sqlite" - no functional references should exist

### Implementation for User Story 2

- [ ] T016 [US2] Replace `import sqlite3` with `import duckdb` in src/storage/database.py
- [ ] T017 [US2] Remove all PRAGMA statements (journal_mode, foreign_keys) from src/storage/database.py
- [ ] T018 [US2] Update `datetime('now')` to `current_timestamp` in SCHEMA_SQL in src/storage/database.py
- [ ] T019 [US2] Update `INTEGER CHECK (is_hce IN (0, 1))` to `BOOLEAN` in SCHEMA_SQL in src/storage/database.py
- [ ] T020 [US2] Remove `check_same_thread` parameter from connection creation in src/storage/database.py
- [ ] T021 [US2] Update row factory handling for DuckDB result sets in src/storage/database.py
- [ ] T022 [P] [US2] Replace `import sqlite3` with `import duckdb` in backend/app/database.py
- [ ] T023 [P] [US2] Apply same schema and connection changes to backend/app/database.py
- [ ] T024 [US2] Update repository type hints: `sqlite3.Connection` → `duckdb.DuckDBPyConnection` in src/storage/repository.py
- [ ] T025 [US2] Update any `sqlite3.Row` references to DuckDB equivalent patterns in src/storage/repository.py
- [ ] T026 [US2] Remove `_add_column_if_not_exists` function (use proper schema versioning instead) in src/storage/database.py
- [ ] T027 [US2] Remove `extend_participant_table` function (all columns in base schema) in src/storage/database.py
- [ ] T028 [US2] Verify table creation order respects FK constraints (census first, then dependents) in SCHEMA_SQL

**Checkpoint**: No SQLite code remains - DuckDB is the sole database backend

---

## Phase 5: User Story 3 - Preserved Functionality (Priority: P2)

**Goal**: All existing operations work identically with DuckDB

**Independent Test**: Run existing test suite - all tests should pass

### Implementation for User Story 3

- [ ] T029 [US3] Update test fixtures to use DuckDB in-memory database in tests/unit/
- [ ] T030 [US3] Update test fixtures to use DuckDB in tests/integration/
- [ ] T031 [US3] Update test fixtures to use DuckDB in tests/contract/
- [ ] T032 [US3] Verify CensusRepository CRUD operations work with DuckDB
- [ ] T033 [US3] Verify ParticipantRepository bulk_insert and queries work with DuckDB
- [ ] T034 [US3] Verify GridAnalysisRepository operations work with DuckDB
- [ ] T035 [US3] Verify AnalysisResultRepository operations work with DuckDB
- [ ] T036 [US3] Verify ImportSessionRepository operations work with DuckDB
- [ ] T037 [US3] Verify MappingProfileRepository operations work with DuckDB
- [ ] T038 [US3] Verify ValidationIssueRepository bulk operations work with DuckDB
- [ ] T039 [US3] Verify ImportLogRepository operations work with DuckDB
- [ ] T040 [US3] Verify ImportMetadataRepository operations work with DuckDB
- [ ] T041 [US3] Run full test suite and fix any DuckDB-specific issues

**Checkpoint**: All existing functionality preserved - test suite passes

---

## Phase 6: User Story 4 - Performance Parity (Priority: P3)

**Goal**: Database operations perform at least as well as SQLite

**Independent Test**: Measure response times for typical operations

### Implementation for User Story 4

- [ ] T042 [US4] Verify index creation for all performance-critical queries in SCHEMA_SQL
- [ ] T043 [US4] Test census list performance with 1000+ participants
- [ ] T044 [US4] Test analysis result queries with 100+ scenarios
- [ ] T045 [US4] Optimize any slow queries identified during testing

**Checkpoint**: Performance meets or exceeds SQLite baseline

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T046 [P] Update CLAUDE.md with DuckDB as active database technology
- [ ] T047 [P] Remove any SQLite-related documentation references
- [ ] T048 Add error handling for missing/corrupted database files in src/storage/database.py
- [ ] T049 Add workspace database health check endpoint in src/api/routes/
- [ ] T050 Run quickstart.md validation scenarios
- [ ] T051 Final code review: search for any remaining "sqlite" references

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational, can run parallel to US1
- **User Story 3 (Phase 5)**: Depends on US1 + US2 (needs complete DuckDB setup)
- **User Story 4 (Phase 6)**: Depends on US3 (needs working implementation)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

```
Setup (Phase 1)
    │
    ▼
Foundational (Phase 2)
    │
    ├───────────────────┐
    ▼                   ▼
US1 (Workspace)     US2 (SQLite Removal)
    │                   │
    └─────────┬─────────┘
              ▼
        US3 (Functionality)
              │
              ▼
        US4 (Performance)
              │
              ▼
        Polish (Phase 7)
```

### Parallel Opportunities

**Within Phase 1:**
- T001 and T002 can run in parallel (different files)

**Within Phase 2:**
- All foundational tasks are sequential (building on each other)

**Within Phase 4 (US2):**
- T022 and T023 can run parallel to T016-T021 (different directories)

**Cross-Story Parallelism:**
- US1 and US2 can run in parallel after Foundational
- Both work on different aspects of the same files but address different concerns

---

## Parallel Example: User Story 2

```bash
# Launch src/ and backend/ changes in parallel:
Task: "Replace sqlite3 with duckdb in src/storage/database.py"
Task: "Replace sqlite3 with duckdb in backend/app/database.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (add DuckDB dependency)
2. Complete Phase 2: Foundational (connection infrastructure)
3. Complete Phase 3: User Story 1 (workspace isolation)
4. Complete Phase 4: User Story 2 (SQLite removal)
5. **STOP and VALIDATE**: Verify no SQLite remains, workspaces are isolated

### Full Implementation

1. MVP (above)
2. Add User Story 3: Verify all operations work
3. Add User Story 4: Verify performance
4. Polish: Final cleanup

### Suggested Commit Points

- After T003: "Add DuckDB dependency"
- After T008: "Implement DuckDB connection infrastructure"
- After T015: "Implement workspace-isolated databases"
- After T028: "Complete SQLite to DuckDB migration"
- After T041: "Verify functional parity with DuckDB"
- After T045: "Verify performance parity"
- After T051: "Final cleanup and validation"

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Stories 1 and 2 are both P1 priority and should be completed together for MVP
- Existing test suite serves as the primary validation mechanism
- No new tests needed - update existing tests to use DuckDB fixtures
- Commit after each task or logical group
