# Implementation Plan: CSV Import + Column Mapping Wizard

**Branch**: `003-csv-import-wizard` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-csv-import-wizard/spec.md`

## Summary

Implement a multi-step CSV Import Wizard that guides users through uploading census data with intelligent column auto-mapping, three-tier severity validation (error/warning/info), duplicate detection, pre-commit preview, and reusable mapping profiles. The wizard integrates with the existing Streamlit UI and FastAPI backend, extending the current census import functionality with a comprehensive wizard flow.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.100+, Streamlit 1.28+, pandas 2.0+, pydantic 2.0+
**Storage**: SQLite (via sqlite3) with WAL mode (existing)
**Testing**: pytest with existing test structure
**Target Platform**: Linux server (web application)
**Project Type**: Web application (Streamlit frontend + FastAPI backend)
**Performance Goals**: Validate 10,000 rows within 10 seconds; complete wizard in under 3 minutes for 1,000 rows
**Constraints**: 50MB max file size; 24-hour session state preservation
**Scale/Scope**: Single-user concurrent imports (session isolated); indefinite log retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is a template without specific constraints defined. No violations detected. Proceeding with standard best practices:
- [x] Code will be testable and independently testable per user story
- [x] No unnecessary abstractions - direct implementation following existing patterns
- [x] Observability through structured logging for import operations

## Project Structure

### Documentation (this feature)

```text
specs/003-csv-import-wizard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   ├── census.py         # Extend with wizard endpoints
│   │   └── import_wizard.py  # NEW: Wizard-specific API routes
│   └── schemas.py            # Extend with wizard schemas
├── core/
│   ├── census_parser.py      # Extend validation logic
│   ├── import_wizard.py      # NEW: Wizard business logic
│   └── field_mappings.py     # NEW: Auto-mapping patterns for 9 required fields
├── storage/
│   ├── models.py             # Extend with new entities
│   ├── database.py           # Extend schema
│   └── repository.py         # Extend with wizard queries
└── ui/
    └── pages/
        └── import_wizard.py  # NEW: Multi-step wizard UI

tests/
├── unit/
│   ├── test_import_wizard.py      # NEW: Wizard logic tests
│   ├── test_field_mappings.py     # NEW: Auto-mapping tests
│   └── test_validation_rules.py   # NEW: Validation tests
├── integration/
│   └── test_wizard_api.py         # NEW: Wizard API tests
└── contract/
    └── test_wizard_schemas.py     # NEW: Schema validation tests
```

**Structure Decision**: Extends existing single-project structure. New wizard components are added as separate modules to maintain separation of concerns while integrating with existing census infrastructure.

## Complexity Tracking

No constitution violations requiring justification. The design follows existing patterns with minimal new abstractions.

## Design Decisions

### Wizard State Management

The wizard will use a session-based state model stored in SQLite, allowing:
- 24-hour session persistence (FR-018)
- Resume from any completed step
- Isolated per-user sessions

### Required Fields Mapping

The 9 required census fields per clarification:
1. SSN (unique identifier, 9 digits)
2. DOB (date, multiple formats)
3. Hire Date (date, multiple formats)
4. Compensation (dollar amount)
5. Employee Pre Tax Contributions (dollar amount)
6. Employee After Tax Contributions (dollar amount)
7. Employee Roth Contributions (dollar amount)
8. Employer Match Contribution (dollar amount)
9. Employer Non Elective Contribution (dollar amount)

### Validation Severity Levels

- **Error**: Blocks record import (invalid SSN, missing required field, in-file duplicate SSN)
- **Warning**: Allows import with flag (existing record duplicate - user chooses replace/skip)
- **Info**: Informational only (date format auto-converted, optional field missing)

### Duplicate Handling

- In-file duplicates (same SSN appears twice in CSV): Error - blocks import
- Existing record duplicates (SSN exists in database): Warning - offer full replace or skip

### Date Format Auto-Detection

Accepted formats: MM/DD/YYYY, YYYY-MM-DD, M/D/YY with auto-detection per column.
