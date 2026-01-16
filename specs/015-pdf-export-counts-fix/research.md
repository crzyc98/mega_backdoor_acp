# Research: Fix PDF/CSV Export Counts

**Feature**: 015-pdf-export-counts-fix
**Date**: 2026-01-16

## Research Tasks

### 1. Current Export Route Implementation Analysis

**Decision**: Fix legacy routes to recompute post-exclusion counts on-the-fly

**Rationale**:
- The workspace export routes (commit 7925ea6) already retrieve `included_hce_count`, `included_nhce_count`, and `excluded_count` from the run results summary
- Legacy routes at `/export/{census_id}/pdf` and `/export/{census_id}/csv` don't have access to run results (they operate on census_id, not run_id)
- Per spec clarification, when exclusion data is unavailable, recompute on-the-fly using current eligibility logic

**Alternatives Considered**:
1. Store exclusion counts in census table → Rejected: Census is import-time data, exclusions depend on plan year analysis
2. Require run_id for legacy routes → Rejected: Breaks backward compatibility
3. Fall back to raw counts with warning → Rejected: User prefers consistent accurate data

### 2. ACP Eligibility Filtering Pattern

**Decision**: Reuse existing `determine_acp_inclusion()` from `acp_eligibility.py`

**Rationale**:
- Function already handles all eligibility logic:
  - DOB + 21 years calculation
  - Hire date + 1 year calculation
  - Semi-annual entry dates (Jan 1 / Jul 1)
  - Termination before entry date check
  - Not eligible during year check
- Returns `ACPInclusionResult` with `acp_includable` boolean and `acp_exclusion_reason`
- Used consistently in workspace routes and employee impact service

**Alternatives Considered**:
1. Duplicate eligibility logic in export routes → Rejected: DRY violation, maintenance burden
2. Create new helper function → Rejected: Existing function is sufficient

### 3. Data Flow for Legacy Exports

**Decision**: For legacy routes, load participants, apply eligibility filter, count results

**Rationale**:
- Legacy route flow:
  1. Load census by census_id
  2. Load all participants for census
  3. Load analysis results (grid data) by census_id (and optional grid_id)
  4. **NEW**: Apply `determine_acp_inclusion()` to each participant
  5. **NEW**: Count includable HCEs/NHCEs and excluded participants
  6. Pass accurate counts to `generate_pdf_report()` / `format_csv_export()`

**Implementation Notes**:
- Participants already loaded via `ParticipantRepository.get_by_census_id()`
- Each participant has: `dob`, `hire_date`, `termination_date`, `is_hce`
- Plan year derived from census `plan_year` field

### 4. CSV Metadata Header Format

**Decision**: Update CSV header to show post-exclusion counts

**Rationale**:
- Current CSV header (line 57-62 in export.py service):
  ```
  # ACP Sensitivity Analysis Export
  # Plan Year: {plan_year}
  # Total Participants: {participant_count}
  # HCEs: {hce_count}
  # NHCEs: {nhce_count}
  ```
- Should show post-exclusion counts with exclusion info:
  ```
  # ACP Sensitivity Analysis Export
  # Plan Year: {plan_year}
  # Total Participants: {participant_count}
  # Eligible HCEs: {included_hce_count}
  # Eligible NHCEs: {included_nhce_count}
  # Excluded: {excluded_count}
  ```

**Alternatives Considered**:
1. Keep raw counts and add exclusion counts separately → Rejected: Confusing, doesn't match web display
2. Remove header entirely → Rejected: Loses useful audit metadata

### 5. Testing Strategy

**Decision**: Add unit tests for export routes with exclusion scenarios

**Rationale**:
- Test cases needed:
  1. Census with no exclusions (all participants eligible)
  2. Census with some exclusions (mixed eligibility)
  3. Census with all participants excluded (edge case)
  4. Verify mathematical consistency: HCE + NHCE + Excluded = Total

**Implementation Notes**:
- Use existing test fixtures for census/participant creation
- Mock `determine_acp_inclusion()` for predictable results
- Verify PDF content contains correct counts (parse or check bytes)
- Verify CSV header contains correct counts (string parsing)

## Key Files to Modify

| File | Change |
|------|--------|
| `backend/app/routers/routes/export.py` | Add eligibility filtering to both PDF and CSV routes |
| `backend/app/services/export.py` | Update `format_csv_export()` to accept and display exclusion counts |
| `backend/tests/test_export.py` | Add tests for post-exclusion count accuracy |

## Dependencies

- `backend/app/services/acp_eligibility.py` - `determine_acp_inclusion()`, `plan_year_bounds()`
- `backend/app/storage/repository.py` - `ParticipantRepository.get_by_census_id()`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance regression from on-the-fly calculation | Low | Low | Eligibility check is O(n) simple arithmetic, already used elsewhere |
| Breaking change to CSV format | Low | Medium | Header changes are metadata only, data columns unchanged |
| Incorrect eligibility logic | Low | High | Reusing battle-tested `determine_acp_inclusion()` function |
