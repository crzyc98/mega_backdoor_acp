# Implementation Plan: Enhanced Census CSV Upload Wizard

**Branch**: `009-csv-upload-wizard` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-csv-upload-wizard/spec.md`

## Summary

Enhance the census CSV upload experience with an intelligent multi-step wizard featuring auto-detected column mapping with confidence scores, configurable date format parsing with live preview, color-coded row validation feedback (valid/warning/error), and per-workspace saved mapping profiles for repeat imports.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7+ (frontend)
**Primary Dependencies**: FastAPI 0.104+, React 19, React Router 7, Vite 6, pandas 2.0+, pydantic 2.0+
**Storage**: File-based workspace storage (~/.acp-analyzer/workspaces/{uuid}/), SQLite for sessions
**Testing**: pytest (backend), vitest + @testing-library/react (frontend)
**Target Platform**: Web application (Linux server backend, modern browsers frontend)
**Project Type**: web (frontend + backend)
**Performance Goals**: 3-minute import for 1,000 rows, sub-second mapping suggestions, real-time preview updates
**Constraints**: 50MB max file size, 100,000 max rows, 24-hour session TTL
**Scale/Scope**: Single-user workspaces, ~10 concurrent import sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution template has placeholder content - no specific gates defined. Proceeding with standard best practices:

- [x] **Library-First**: Feature extends existing import wizard service layer
- [x] **Test-First**: Will include unit tests for mapping logic, integration tests for API
- [x] **Simplicity**: Building on existing backend infrastructure, minimal new abstractions

**Status**: PASS - No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/009-csv-upload-wizard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── import_session.py    # Extended with date format preferences
│   ├── services/
│   │   ├── field_mappings.py    # Existing - fuzzy matching logic
│   │   ├── import_wizard.py     # Existing - session management
│   │   └── date_parser.py       # NEW - date format detection/parsing
│   ├── routers/
│   │   └── routes/
│   │       └── import_wizard.py # Existing - extend with date format endpoints
│   └── storage/
│       └── models.py            # Extend MappingProfile with workspace_id
└── tests/
    ├── unit/
    │   └── test_date_parser.py  # NEW
    ├── integration/
    │   └── test_import_wizard_api.py  # Extend
    └── contract/
        └── test_import_wizard_contracts.py  # NEW

frontend/
├── src/
│   ├── components/
│   │   ├── ImportWizard/        # NEW - wizard container
│   │   │   ├── index.tsx
│   │   │   ├── StepUpload.tsx
│   │   │   ├── StepMapping.tsx
│   │   │   ├── StepDateFormat.tsx
│   │   │   ├── StepValidation.tsx
│   │   │   └── StepConfirm.tsx
│   │   ├── ColumnMapper.tsx     # NEW - mapping UI with confidence
│   │   ├── DateFormatPicker.tsx # NEW - format selection with preview
│   │   ├── ValidationPreview.tsx # NEW - color-coded row status
│   │   └── MappingProfileSelector.tsx # NEW - saved profiles UI
│   ├── pages/
│   │   └── CensusUpload.tsx     # Existing - integrate wizard
│   ├── services/
│   │   └── importWizardService.ts # NEW - API client for wizard
│   └── types/
│       └── importWizard.ts      # NEW - TypeScript interfaces
└── tests/
    └── components/
        └── ImportWizard.test.tsx # NEW
```

**Structure Decision**: Web application structure using existing backend/frontend split. Extends existing import wizard backend infrastructure while adding comprehensive React frontend components.

## Complexity Tracking

> No violations requiring justification.
