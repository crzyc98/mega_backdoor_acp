# Research: Enhanced Census CSV Upload Wizard

**Date**: 2026-01-13
**Feature**: 009-csv-upload-wizard

## Summary

Research phase complete. The existing backend infrastructure provides a solid foundation with import wizard services, session management, and validation logic already implemented. The primary work is building the React frontend components to expose these capabilities with improved UX.

---

## 1. Existing Backend Infrastructure

### Decision: Extend existing import wizard services

**Rationale**: Backend already has comprehensive implementation in `backend/app/services/import_wizard.py` and `backend/app/routers/routes/import_wizard.py` including:
- Session management with 24-hour TTL
- CSV parsing with auto-detection of delimiter and encoding
- Row-level validation with specific error codes
- Duplicate detection (in-file and against existing records)
- Mapping profile CRUD operations

**Alternatives considered**:
- Building new services from scratch: Rejected - would duplicate existing tested code
- Using third-party import library: Rejected - existing code is well-suited to domain needs

### Existing Capabilities Inventory

| Feature | Status | Location |
|---------|--------|----------|
| Session management | Complete | `import_wizard.py:create_session()` |
| CSV delimiter detection | Complete | `import_wizard.py:detect_delimiter()` |
| Encoding detection | Complete | `import_wizard.py:detect_encoding()` |
| Column mapping suggestion | Complete | `field_mappings.py:suggest_mapping()` |
| Fuzzy matching (60% threshold) | Complete | `field_mappings.py:find_best_match()` |
| Date validation | Partial | `import_wizard.py:validate_date()` - needs user-selectable format |
| Row validation | Complete | `import_wizard.py:validate_row()` |
| Duplicate detection | Complete | `import_wizard.py:detect_in_file_duplicates()` |
| Mapping profiles | Complete | `import_wizard.py` routes + storage models |

---

## 2. Date Format Handling

### Decision: User-selectable date format with auto-detection hint

**Rationale**: The current `validate_date()` function tries multiple formats sequentially, which can cause ambiguity (is "01/02/2020" January 2nd or February 1st?). Users need explicit control.

**Implementation approach**:
1. Auto-detect likely format from sample data (heuristic: try all formats, count successes)
2. Present detected format as default but allow user override
3. Show live preview of how selected format parses sample dates
4. Store selected format in session and mapping profile

**Supported formats** (already in backend):
```python
DATE_FORMATS = [
    "%m/%d/%Y",      # MM/DD/YYYY
    "%Y-%m-%d",      # YYYY-MM-DD (ISO)
    "%m/%d/%y",      # MM/DD/YY
    "%m-%d-%Y",      # MM-DD-YYYY
    "%m-%d-%y",      # MM-DD-YY
    "%Y/%m/%d",      # YYYY/MM/DD
    "%d/%m/%Y",      # DD/MM/YYYY
    "%d-%m-%Y",      # DD-MM-YYYY
]
```

**Alternatives considered**:
- Fully automatic format detection: Rejected - ambiguous formats (MM/DD vs DD/MM) require user confirmation
- Free-form format entry: Rejected - error-prone, complex validation needed

---

## 3. Frontend Component Architecture

### Decision: Multi-step wizard with discrete components

**Rationale**: The import process has clear sequential steps with dependencies. A wizard pattern provides:
- Clear progress indication
- Ability to go back and correct earlier decisions
- Isolation of concerns (each step handles one task)

**Wizard steps**:
1. **Upload** - File selection and initial validation
2. **Mapping** - Column mapping with confidence indicators
3. **Date Format** - Date format selection with live preview
4. **Validation** - Full validation with color-coded row status
5. **Confirm** - Summary and import execution

**Component hierarchy**:
```
<ImportWizard>
  ├── <WizardProgress>           # Step indicator
  ├── <StepUpload>               # File dropzone + file info
  ├── <StepMapping>
  │   ├── <MappingProfileSelector>  # Saved profiles dropdown
  │   └── <ColumnMapper>            # Field mapping UI
  ├── <StepDateFormat>
  │   └── <DateFormatPicker>        # Format selection + preview
  ├── <StepValidation>
  │   └── <ValidationPreview>       # Color-coded row table
  └── <StepConfirm>                 # Summary + execute button
```

**Alternatives considered**:
- Single-page form with sections: Rejected - overwhelming, harder to manage state
- Modal-based flow: Rejected - limited space, poor for data tables

---

## 4. Validation Preview UI

### Decision: Color-coded row status with expandable error details

**Rationale**: Users need to quickly scan validation results and drill into specific issues.

**Status indicators**:
- **Green (valid)**: Row passes all validation
- **Yellow (warning)**: Row has non-blocking issues (e.g., duplicate in database)
- **Red (error)**: Row has blocking issues that must be resolved

**UI patterns**:
- Status badge on each row (color + icon)
- Summary bar showing counts (e.g., "150 valid, 3 warnings, 2 errors")
- Expandable row details showing specific issues and suggestions
- Filter controls to show only errors/warnings
- "Jump to next error" navigation

**Alternatives considered**:
- Inline editing: Rejected - users should fix source file, not edit in wizard
- Separate error report page: Rejected - loses context of full data preview

---

## 5. Mapping Profile Storage

### Decision: Per-workspace profiles with workspace_id foreign key

**Rationale**: Users import from consistent sources per workspace. Profiles should be scoped to workspace, not global.

**Schema extension needed**:
```python
# MappingProfile model - add workspace_id
workspace_id: str  # Foreign key to workspace
date_format: str | None  # Store selected date format
```

**API additions**:
- `GET /workspaces/{id}/import/mapping-profiles` - List profiles for workspace
- `POST /workspaces/{id}/import/mapping-profiles` - Create profile for workspace

**Alternatives considered**:
- Global profiles: Rejected - different workspaces may have different data sources
- User-level profiles: Rejected - single-user workspaces make this equivalent to workspace-level

---

## 6. API Contract Extensions

### New endpoints needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/import/sessions/{id}/date-format` | PUT | Set date format for session |
| `/import/sessions/{id}/date-preview` | GET | Preview date parsing results |
| `/import/sessions/{id}/preview-rows` | GET | Get transformed rows with validation status |
| `/workspaces/{id}/import/mapping-profiles` | GET/POST | Workspace-scoped profile management |

### Response enhancements

**PreviewRow schema**:
```typescript
interface PreviewRow {
  row_number: number;
  status: 'valid' | 'warning' | 'error';
  original_values: Record<string, string>;
  mapped_values: Record<string, any>;
  issues: ValidationIssue[];
}
```

---

## 7. Performance Considerations

### Decision: Paginated preview with 100-row pages

**Rationale**: Files can have 100,000 rows. Loading all into browser would be slow and memory-intensive.

**Approach**:
- Preview shows first 100 rows by default
- Pagination available for full dataset
- Validation summary computed server-side
- "Jump to error" fetches specific page containing error row

**Alternatives considered**:
- Virtual scrolling: More complex, harder to implement "jump to error"
- Full dataset load: Not viable for large files

---

## Conclusion

No NEEDS CLARIFICATION items remain. The existing backend provides ~70% of required functionality. Primary development effort is:

1. **Backend** (30%): Date format selection endpoint, preview rows endpoint, workspace-scoped profile queries
2. **Frontend** (70%): Full wizard implementation with all 5 steps and associated components

Proceed to Phase 1: Data Model and API Contracts.
