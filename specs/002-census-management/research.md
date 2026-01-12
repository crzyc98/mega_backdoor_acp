# Research: Census Management

**Feature**: 002-census-management
**Date**: 2026-01-12
**Status**: Complete

## Research Tasks

### 1. Existing Census Infrastructure Analysis

**Decision**: Extend existing Census, Participant, and repository classes rather than creating new ones.

**Rationale**:
- The existing `src/storage/models.py` already defines Census and Participant dataclasses with core fields (id, name, plan_year, participant counts, etc.)
- The existing `src/api/routes/census.py` has POST/GET/DELETE endpoints that match most requirements
- The existing `src/core/census_parser.py` handles CSV parsing, PII stripping, and validation
- Adding fields (client_name, hce_mode, column_mapping) is less disruptive than replacing models

**Alternatives Considered**:
- Create separate CensusV2 models: Rejected due to migration complexity and code duplication
- Replace existing models entirely: Rejected to maintain backward compatibility with existing analyses

### 2. Column Mapping Storage Strategy

**Decision**: Store column mapping as JSON in a new `import_metadata` table with foreign key to census.

**Rationale**:
- Column mapping is metadata about the import process, not intrinsic to the census data
- JSON storage allows flexible schema evolution for different source file formats
- Separating metadata from the census table keeps the main table lean and queryable
- SQLite handles JSON storage efficiently as TEXT with json functions available

**Alternatives Considered**:
- Add column_mapping JSON column directly to census table: Rejected due to table width concerns and separation of concerns
- Store in separate file (e.g., JSON sidecar): Rejected due to data integrity risks and query complexity

### 3. HCE Determination Mode Implementation

**Decision**: Add `hce_mode` enum field to Census model with values: "explicit" | "compensation_threshold". Store calculated is_hce on each Participant.

**Rationale**:
- The mode needs to be stored so analyses can be rerun consistently
- Pre-calculating HCE status at import time ensures consistent results across analyses
- When mode is "compensation_threshold", use plan year to look up historical IRS threshold
- Existing `is_hce` field on Participant already stores the classification result

**Alternatives Considered**:
- Calculate HCE dynamically at analysis time: Rejected because threshold could change between analyses, causing inconsistent results
- Store both original HCE flag and calculated status: Rejected as unnecessarily complex for current requirements

### 4. Historical IRS HCE Threshold Data Source

**Decision**: Create `src/core/hce_thresholds.py` module with a dictionary of IRS thresholds by year (2020-2026+), with fallback to most recent year if requested year not found.

**Rationale**:
- IRS publishes HCE thresholds annually; historical data is stable and well-documented
- Hard-coding known values (2020: $130k, 2021: $130k, 2022: $135k, 2023: $150k, 2024: $155k, 2025: $160k) provides immediate functionality
- Fallback behavior handles edge cases gracefully (future years use latest known threshold with warning)
- Module can be easily extended or replaced with external data source later

**Alternatives Considered**:
- External API call for thresholds: Rejected due to network dependency and offline usage requirements
- Database configuration table: Over-engineering for rarely-changing data; can migrate later if needed
- User-provided threshold per census: Rejected as error-prone; system should enforce correct thresholds

### 5. Census Metadata Editability

**Decision**: Add PATCH endpoint to update census name and client_name only. Participant data and plan_year remain immutable.

**Rationale**:
- Spec clarification confirmed: metadata editable, participant data immutable
- Plan year immutability ensures HCE calculations remain valid (changing year would require recalculation)
- PATCH semantics allow partial updates without full resource replacement
- Frontend can implement inline editing for name/client fields

**Alternatives Considered**:
- PUT endpoint for full replacement: Rejected as overly permissive; immutable fields need protection
- Allow plan_year changes with automatic HCE recalculation: Rejected as complex and potentially confusing

### 6. Summary Statistics Calculation

**Decision**: Calculate and store statistics at import time: total_participants, hce_count, nhce_count, avg_compensation, avg_deferral_rate. Add avg_match_rate, avg_after_tax_rate as optional.

**Rationale**:
- Existing Census model already stores participant_count, hce_count, nhce_count
- Adding avg_compensation and avg_deferral_rate provides immediate value per spec (FR-012)
- Pre-calculation ensures fast list/detail views without scanning all participants
- Optional fields handle censuses without match/after-tax data gracefully

**Alternatives Considered**:
- Calculate on-demand: Rejected for performance (scanning 10k rows per list view)
- Separate statistics table: Over-engineering for denormalized counts

### 7. Delete Confirmation and Analysis Warning

**Decision**: Implement soft warning via API response metadata when census has associated analyses. Actual deletion still cascades (existing FK behavior). UI handles confirmation dialog.

**Rationale**:
- Existing database schema already has ON DELETE CASCADE for participants and analysis_results
- Adding a "has_analyses" check before delete provides warning data
- DELETE endpoint returns 204 on success; warning is advisory, not blocking
- This matches spec FR-019: "warn users" not "prevent deletion"

**Alternatives Considered**:
- Prevent deletion if analyses exist: Rejected as too restrictive; spec says warn, not block
- Soft delete with archived status: Over-engineering for current requirements

### 8. Database Schema Migration Strategy

**Decision**: Add new columns with ALTER TABLE statements. Use SQLite's flexible schema approach for backward compatibility.

**Rationale**:
- SQLite allows adding columns with defaults easily
- New columns: `client_name TEXT`, `hce_mode TEXT DEFAULT 'explicit'`, `avg_compensation_cents INTEGER`, `avg_deferral_rate REAL`
- New table: `import_metadata (census_id FK, column_mapping TEXT, source_filename TEXT, created_at TEXT)`
- Existing data continues to work; new fields nullable or have sensible defaults

**Alternatives Considered**:
- Create new database file: Rejected due to data loss risk
- Migration framework (Alembic): Over-engineering for SQLite; direct DDL is simpler

## Summary

All technical decisions align with extending the existing codebase patterns:
- Models: Extend Census with new fields
- API: Add PATCH endpoint and enhance existing endpoints
- Core: New hce_thresholds module, extend census_parser
- Storage: Add import_metadata table, update Census repository
- UI: New census list page with edit capability

No blocking technical unknowns remain. Ready for Phase 1 design.
