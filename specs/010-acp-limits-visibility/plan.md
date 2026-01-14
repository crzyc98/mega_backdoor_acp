# Implementation Plan: ACP Limits Visibility

**Branch**: `010-acp-limits-visibility` | **Date**: 2026-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-acp-limits-visibility/spec.md`

## Summary

**Finding: The feature is already implemented.** All 9 ACP limit fields (nhce_acp, hce_acp, limit_125, limit_2pct_uncapped, cap_2x, limit_2pct_capped, effective_limit, binding_rule, margin) exist in the backend models, are computed correctly using the capped 2% formula, and are surfaced in the frontend UI (heatmap tooltip, Compliance Card), CSV export, and PDF export. Unit tests cover all required scenarios.

The spec requirements map to existing implementation as follows:

| Requirement | Implementation Status | Location |
|------------|----------------------|----------|
| FR-001 to FR-009 | Complete | `backend/app/services/acp_calculator.py:180-253` |
| FR-010 (backward compat) | Complete | Fields added without renaming existing ones |
| FR-011 (ERROR handling) | Complete | `backend/app/services/models.py:17-29` (ScenarioStatus enum) |
| FR-012, FR-013 (API fields) | Complete | `backend/app/services/models.py:108-162` (ScenarioResult) |
| FR-014 (typing) | Complete | All fields use explicit types, no `Any` |
| FR-015 (Heatmap tooltip) | Complete | `frontend/src/components/Heatmap.tsx:114-158` |
| FR-016 (Compliance Card) | Complete | `frontend/src/pages/EmployeeImpact.tsx:404-456` |
| FR-017 (display format) | Complete | `formatPercentage()` util functions |
| FR-018 (CSV export) | Complete | `backend/app/services/export.py:63-106` |
| FR-019 (PDF export) | Complete | `backend/app/services/export.py:269-313` |
| FR-020 (export format) | Complete | 2 decimal places in export functions |
| FR-021, FR-022 (README) | Complete | `README.md:232-239` |
| FR-023 to FR-027 (tests) | Complete | `backend/tests/unit/test_acp_calculator.py` |

## Technical Context

**Language/Version**: Python 3.11+, TypeScript 5.8+
**Primary Dependencies**: FastAPI 0.100+, React 19, Pydantic 2.0+, pandas 2.0+
**Storage**: File-based JSON workspaces (~/.acp-analyzer/workspaces/{uuid}/)
**Testing**: pytest (backend), TypeScript type checking (frontend)
**Target Platform**: Linux server (backend API), Web browser (React frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Grid analysis completes in seconds for typical 10x10 grids
**Constraints**: Backward-compatible API changes only
**Scale/Scope**: Typical census files with 50-500 participants

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution violations detected. The existing implementation:
- Follows the established project structure (backend/frontend separation)
- Uses explicit typing throughout (no `Any` types)
- Has comprehensive unit test coverage
- Maintains backward compatibility with existing API contracts

## Project Structure

### Documentation (this feature)

```text
specs/010-acp-limits-visibility/
├── plan.md              # This file
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── analysis.py           # ScenarioResult model (v1 API)
│   ├── services/
│   │   ├── acp_calculator.py     # ACP limit calculations ✓
│   │   ├── models.py             # ScenarioResult model (v2) ✓
│   │   ├── scenario_runner.py    # Grid/scenario execution ✓
│   │   └── export.py             # CSV/PDF export ✓
│   └── routers/
│       └── routes/analysis.py    # API endpoints ✓
└── tests/
    └── unit/
        └── test_acp_calculator.py # Unit tests ✓

frontend/
├── src/
│   ├── components/
│   │   └── Heatmap.tsx           # Tooltip with limits ✓
│   ├── pages/
│   │   └── EmployeeImpact.tsx    # Compliance Card ✓
│   ├── services/
│   │   └── exportService.ts      # Export API calls ✓
│   └── types/
│       └── analysis.ts           # TypeScript types ✓
```

**Structure Decision**: Existing web application structure with clear backend/frontend separation. No structural changes needed.

## Complexity Tracking

> **No violations detected - no justification needed**

## Phase 0: Research Summary

No research needed - the feature is already implemented. The existing code correctly implements:

1. **Capped 2% formula** in `calculate_acp_limits()`:
   ```python
   limit_125 = nhce_acp * 1.25
   limit_2pct_uncapped = nhce_acp + 2.0
   cap_2x = nhce_acp * 2.0
   limit_2pct_capped = min(limit_2pct_uncapped, cap_2x)
   effective_limit = max(limit_125, limit_2pct_capped)
   ```

2. **Binding rule determination**:
   ```python
   binding_rule = "1.25x" if limit_125 >= limit_2pct_capped else "2pct/2x"
   ```

3. **ERROR handling** via ScenarioStatus enum with null-safe optional fields

## Phase 1: Design Review

### Existing Data Model

The `ScenarioResult` model (v2) in `backend/app/services/models.py:108-162` already contains all required fields:

| Field | Type | Description |
|-------|------|-------------|
| nhce_acp | float \| None | NHCE group ACP (null if ERROR) |
| hce_acp | float \| None | HCE group ACP (null if ERROR) |
| limit_125 | float \| None | NHCE ACP × 1.25 |
| limit_2pct_uncapped | float \| None | NHCE ACP + 2.0% |
| cap_2x | float \| None | 2.0 × NHCE ACP |
| limit_2pct_capped | float \| None | min(+2.0%, 2×) |
| effective_limit | float \| None | max(1.25×, capped +2.0) |
| binding_rule | Literal["1.25x", "2pct/2x"] \| None | Which formula binds |
| margin | float \| None | effective_limit - hce_acp |
| status | ScenarioStatus | PASS/RISK/FAIL/ERROR |

### Existing API Contracts

All endpoints already return the complete ScenarioResult with limit fields:
- `POST /v2/scenario` - Single scenario analysis
- `POST /v2/grid` - Grid analysis (returns array of ScenarioResult)
- `POST /v2/scenario/{census_id}/employee-impact` - Drilldown view

### Existing Test Coverage

All 5 required test cases are covered in `test_acp_calculator.py`:

| Test Case | Test Method | Line |
|-----------|-------------|------|
| 1.25x formula binds | `test_apply_acp_test_125x_wins` | 167 |
| 2pct/2x formula binds | `test_apply_acp_test_plus2_wins` | 186 |
| 2x cap changes limit | `test_apply_acp_test_cap_at_2x` | 258 |
| Margin sign matches status | `test_margin_sign_matches_result` | 276 |
| Zero HCE/NHCE → ERROR | `TestEdgeCases` class | 376 |

## Recommendation

**No implementation work required.** The feature specification describes functionality that is already fully implemented.

### Verification Steps

To verify the implementation meets the spec:

1. **Run existing unit tests**:
   ```bash
   cd backend && pytest tests/unit/test_acp_calculator.py -v
   ```

2. **Run the application and verify UI**:
   ```bash
   ./bin/mega start
   ```
   - Upload a census file
   - Run grid analysis
   - Hover over heatmap cells → verify tooltip shows NHCE ACP, HCE ACP, Effective Limit, Binding Rule, Margin
   - Click a cell → verify Compliance Card shows all 9 metrics

3. **Verify exports**:
   - Export to CSV → verify columns include all limit fields
   - Export to PDF → verify "Scenario Compliance Metrics" table

4. **Verify README**:
   - Check line 232 documents the correct capped 2% formula
   - Check line 237 explains binding_rule

### Possible Enhancements (Not Required)

If additional work is desired beyond the spec, consider:
- Adding integration tests for the full end-to-end flow
- Adding visual differentiation in heatmap for which binding rule applies
- Adding aggregate statistics showing which rule binds most often across a grid

## Next Steps

1. Close this feature branch without code changes
2. Optionally run verification steps above to confirm implementation
3. Merge branch to main if verification passes
