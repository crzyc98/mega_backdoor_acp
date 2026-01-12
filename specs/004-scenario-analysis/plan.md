# Implementation Plan: Scenario Analysis

**Branch**: `004-scenario-analysis` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-scenario-analysis/spec.md`

## Summary

Extend the existing scenario runner engine to return comprehensive ACP outcome details with PASS/FAIL/RISK/ERROR status classification, full calculation breakdowns, grid summary statistics, and optional debug mode. This feature enhances `src/core/scenario_runner.py` and `src/core/acp_calculator.py` with new data structures and calculation logic, exposes enhanced functionality via new API endpoints, and maintains full backward compatibility with existing code.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.100+, pandas 2.0+, pydantic 2.0+, numpy
**Storage**: N/A (stateless calculation engine; results not persisted by this feature)
**Testing**: pytest with pytest-benchmark for performance validation
**Target Platform**: Linux server (web application backend)
**Project Type**: Web application (extending existing FastAPI backend)
**Performance Goals**: Single scenario <100ms for 10K participants; Grid (100 scenarios) <5s for 10K participants
**Constraints**: Deterministic results (same seed = same output); backward compatible with existing ScenarioResult consumers
**Scale/Scope**: Supports census files up to 10K participants with target performance; graceful degradation beyond

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders only (not yet customized for this project). No specific gates are defined. Proceeding with standard software engineering best practices:

- [x] **Library-First**: Scenario analysis is a pure calculation module in `src/core/`
- [x] **Test-First**: Comprehensive tests for RISK classification, grid summaries, edge cases
- [x] **Integration Testing**: API contract tests for new/modified endpoints
- [x] **Simplicity**: Extend existing `ScenarioResult` rather than replace; add new fields

## Project Structure

### Documentation (this feature)

```text
specs/004-scenario-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── acp_calculator.py    # MODIFY: Add total_mega_backdoor_amount calculation
│   ├── scenario_runner.py   # MODIFY: Enhanced ScenarioResult, RISK status, GridSummary
│   ├── constants.py         # MODIFY: Add RISK_THRESHOLD constant
│   └── models.py            # NEW: Pydantic models for requests/results
│
├── api/
│   ├── routes/
│   │   └── analysis.py      # MODIFY: New endpoints for enhanced scenario analysis
│   └── schemas.py           # MODIFY: Add new request/response schemas
│
└── ui/                      # OUT OF SCOPE (engine only per spec)

tests/
├── unit/
│   ├── test_scenario_runner.py     # MODIFY: RISK classification, ERROR handling tests
│   ├── test_grid_summary.py        # NEW: Grid summary calculation tests
│   └── test_debug_mode.py          # NEW: Debug output tests
├── integration/
│   └── test_analysis_api.py        # MODIFY: New endpoint tests
└── contract/
    └── test_scenario_contracts.py  # NEW: Contract validation for new schemas
```

**Structure Decision**: Extending existing single-project structure under `src/`. The scenario analysis engine is a pure calculation module with no new storage requirements. All changes extend existing files or add new files within the established `src/core/` and `src/api/` directories.

## Complexity Tracking

No constitution violations requiring justification. The implementation extends existing patterns.

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Extend ScenarioResult vs new class | Backward compatibility, shared base logic | New class would duplicate test infrastructure |
| RISK as status vs separate flag | Single source of truth, simpler API | Separate flag would require dual-checking |
| GridSummary computed on return | Avoids extra storage, always current | Cached summary would require invalidation logic |
