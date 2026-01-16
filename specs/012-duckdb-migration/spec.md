# Feature Specification: DuckDB Migration

**Feature Branch**: `012-duckdb-migration`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "can we switch this to use duckdb for the database? it would be a db in each individual workspace folder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Workspace Data Isolation (Priority: P1)

Users need each workspace to have its own isolated database, ensuring that census data, analysis results, and import history are completely separate between workspaces. When a user opens a workspace, all operations read from and write to that workspace's dedicated database file.

**Why this priority**: Data isolation is fundamental to the multi-workspace architecture. Without per-workspace databases, users cannot safely work with multiple client datasets or maintain data separation between projects.

**Independent Test**: Can be fully tested by creating two workspaces, importing different census files into each, and verifying that data from one workspace never appears in the other.

**Acceptance Scenarios**:

1. **Given** a user creates a new workspace, **When** the workspace is initialized, **Then** a DuckDB database file is created within that workspace folder
2. **Given** a user imports census data into Workspace A, **When** the user switches to Workspace B, **Then** the imported census is not visible in Workspace B
3. **Given** a user has workspaces with existing data, **When** the user deletes a workspace, **Then** only that workspace's database and data are removed

---

### User Story 2 - Complete SQLite Replacement (Priority: P1)

All database operations must use DuckDB instead of SQLite. There must be no legacy SQLite code, configuration, or data paths remaining in the codebase. This is a clean-break migration with no backward compatibility layer.

**Why this priority**: The user has explicitly requested no legacy SQLite support. Maintaining two database backends would add complexity and maintenance burden.

**Independent Test**: Can be verified by searching the codebase for any remaining SQLite imports, references, or code paths, and confirming the application functions entirely with DuckDB.

**Acceptance Scenarios**:

1. **Given** the migration is complete, **When** searching the codebase for "sqlite" or "sqlite3", **Then** no functional references exist (only migration documentation if any)
2. **Given** a fresh installation, **When** the application starts, **Then** only DuckDB databases are created with no SQLite fallback
3. **Given** existing functionality, **When** users perform all CRUD operations, **Then** all operations succeed using DuckDB

---

### User Story 3 - Preserved Functionality (Priority: P2)

All existing database operations continue to work identically after migration. Users can import census files, run ACP analyses, save mapping profiles, and view import history without any behavioral changes to the application.

**Why this priority**: Functional parity ensures users experience no disruption. While critical, it depends on the database infrastructure being in place first.

**Independent Test**: Can be tested by running the existing test suite against the DuckDB implementation and verifying all tests pass.

**Acceptance Scenarios**:

1. **Given** a user uploads a census CSV, **When** the import wizard completes, **Then** all participant records are stored and retrievable
2. **Given** a census with participants, **When** the user runs a grid analysis, **Then** all analysis results are persisted and can be queried
3. **Given** an import session, **When** validation issues are detected, **Then** all issues are stored with correct severity and row references

---

### User Story 4 - Performance Parity or Improvement (Priority: P3)

Database operations perform at least as well as the current SQLite implementation. Users should not notice any slowdown in census imports, analysis queries, or general application responsiveness.

**Why this priority**: While important for user experience, performance can be optimized after functional correctness is achieved.

**Independent Test**: Can be tested by measuring response times for typical operations (census list, analysis results query) and comparing to baseline.

**Acceptance Scenarios**:

1. **Given** a census with 1000 participants, **When** listing all participants, **Then** results return within acceptable response time
2. **Given** a grid analysis with 100 scenarios, **When** querying all results, **Then** query performance meets or exceeds current benchmarks

---

### Edge Cases

- What happens when a workspace database file is corrupted or missing?
  - Application should detect missing database and offer to reinitialize
- How does the system handle concurrent access to the same workspace database?
  - DuckDB handles concurrent reads; concurrent writes from multiple processes should be prevented at the application level
- What happens during schema migrations for existing workspaces?
  - Workspaces should track schema version and apply migrations on first access

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace all SQLite database operations with DuckDB equivalents
- **FR-002**: System MUST create a DuckDB database file (`workspace.duckdb` or similar) within each workspace folder (`~/.acp-analyzer/workspaces/{uuid}/`)
- **FR-003**: System MUST NOT retain any SQLite code, imports, or fallback mechanisms - complete removal required
- **FR-004**: System MUST initialize the database schema automatically when creating a new workspace
- **FR-005**: System MUST support all existing data models: Census, Participant, AnalysisResult, GridAnalysis, ImportMetadata, ImportSession, MappingProfile, ValidationIssue, ImportLog
- **FR-006**: System MUST maintain referential integrity through foreign key constraints
- **FR-007**: System MUST support concurrent read operations within a single workspace
- **FR-008**: System MUST provide a mechanism for schema version tracking and future migrations
- **FR-009**: System MUST gracefully handle missing or inaccessible database files with clear user feedback

### Key Entities

- **Workspace Database**: A DuckDB file located within each workspace folder, containing all tables for that workspace's data
- **Database Connection Manager**: Service responsible for creating, caching, and closing database connections for the active workspace
- **Schema Manager**: Component that initializes tables and handles version tracking for migrations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing automated tests pass with the DuckDB implementation
- **SC-002**: Zero SQLite imports or references remain in the production codebase
- **SC-003**: Each workspace folder contains its own isolated database file
- **SC-004**: Users can perform all existing operations (import, analyze, export) without functional regression
- **SC-005**: Database operations complete within response times comparable to the current implementation
- **SC-006**: New workspaces are created with properly initialized database schemas

## Assumptions

- The existing data model (tables, columns, relationships) is compatible with DuckDB's SQL dialect
- DuckDB's Python API (`duckdb` package) provides equivalent functionality to `sqlite3` for connection management and query execution
- Workspace folders already exist in the file system structure (`~/.acp-analyzer/workspaces/{uuid}/`)
- No data migration from existing SQLite databases is required (fresh start per workspace)
- The application is single-user per workspace (no multi-process write conflicts)

## Out of Scope

- Migration tooling for converting existing SQLite data to DuckDB format
- Multi-user concurrent write access to the same workspace
- Cloud-based or networked database storage
- Backward compatibility with SQLite databases
- Any legacy SQLite support or dual-database mode
