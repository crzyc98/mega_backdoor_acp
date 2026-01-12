# Research: CSV Import + Column Mapping Wizard

**Feature**: 003-csv-import-wizard
**Date**: 2026-01-12

## Research Tasks

### 1. Wizard State Persistence Strategy

**Decision**: SQLite-based session storage with JSON serialization

**Rationale**:
- The existing application already uses SQLite with WAL mode for concurrent reads
- Session data is structured (wizard step, mappings, validation results) and benefits from queryable storage
- 24-hour persistence requirement (FR-018) is easily achieved with timestamp-based expiration
- SQLite handles the isolation requirement naturally through session IDs

**Alternatives considered**:
- Redis: Would add infrastructure complexity; not justified for single-user scenario
- File-based sessions: Less queryable, harder to clean up expired sessions
- Streamlit session_state only: Lost on browser refresh, doesn't persist across server restarts

### 2. CSV Parsing and Delimiter Detection

**Decision**: Use pandas with Python's csv.Sniffer for delimiter detection

**Rationale**:
- pandas already used extensively in existing `census_parser.py`
- csv.Sniffer reliably detects comma, semicolon, tab delimiters
- chardet library for encoding detection (UTF-8, Latin-1)
- Existing pattern in codebase uses pandas.read_csv

**Alternatives considered**:
- clevercsv: More sophisticated but adds dependency
- Manual detection: Reinventing the wheel

### 3. Auto-Mapping Algorithm for 9 Required Fields

**Decision**: Fuzzy string matching with alias dictionaries

**Rationale**:
- Each required field has common aliases (e.g., "SSN" → "Social Security", "SS#", "Tax ID")
- Normalize headers (lowercase, strip, replace separators) before matching
- Use Levenshtein distance for fuzzy matching as fallback
- Existing `detect_column_mapping()` in census_parser.py provides foundation

**Implementation**:
```python
FIELD_ALIASES = {
    "ssn": ["ssn", "social security", "ss#", "social_security_number", "tax_id", "taxid"],
    "dob": ["dob", "date of birth", "birth date", "birthdate", "birth_date"],
    "hire_date": ["hire date", "hire_date", "hiredate", "date hired", "start date"],
    "compensation": ["compensation", "salary", "annual compensation", "wages", "pay"],
    "employee_pre_tax": ["pre tax", "pretax", "pre-tax", "401k", "deferral", "ee pre tax"],
    "employee_after_tax": ["after tax", "aftertax", "after-tax", "ee after tax"],
    "employee_roth": ["roth", "roth 401k", "ee roth"],
    "employer_match": ["match", "employer match", "er match", "company match"],
    "employer_non_elective": ["non elective", "nonelective", "er non elective", "profit sharing"],
}
```

### 4. Date Format Auto-Detection

**Decision**: pandas.to_datetime with format inference + explicit format list

**Rationale**:
- pandas.to_datetime with `infer_datetime_format=True` handles most cases
- Explicit fallback to try MM/DD/YYYY, YYYY-MM-DD, M/D/YY in order
- Per-column detection: sample first non-null values to determine format
- Convert all dates to ISO format internally for storage consistency

**Implementation approach**:
```python
DATE_FORMATS = [
    "%m/%d/%Y",   # MM/DD/YYYY
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%y",   # M/D/YY
    "%d/%m/%Y",   # DD/MM/YYYY (fallback)
]
```

### 5. Validation Engine Design

**Decision**: Rule-based validator with severity classification

**Rationale**:
- Each field type has specific validation rules
- Rules return (severity, message) tuples
- Validation runs in single pass for performance (10k rows in <10s target)
- Results grouped by severity for display

**Validation rules per field type**:

| Field | Validation | Severity on Fail |
|-------|------------|------------------|
| SSN | 9 digits only | Error |
| DOB | Valid date, not future | Error |
| Hire Date | Valid date | Error |
| Compensation | Non-negative number | Error |
| Contribution fields | Non-negative dollar amount | Error |
| All required | Not null/empty | Error |
| SSN (in-file) | Unique within file | Error |
| SSN (existing) | Not in database | Warning (replace/skip option) |

### 6. Duplicate Detection Strategy

**Decision**: Two-phase detection with batch database lookup

**Rationale**:
- Phase 1: In-file duplicates detected via pandas groupby on SSN column
- Phase 2: Existing duplicates via batch SQL query (IN clause with all SSNs)
- Batch approach avoids N+1 queries, critical for performance
- Results include reference to which row/record is duplicated

**Implementation**:
```python
# Phase 1: In-file duplicates
duplicates = df[df.duplicated(subset=['ssn'], keep=False)]

# Phase 2: Existing records (batch query)
ssn_list = df['ssn'].unique().tolist()
existing = repository.find_participants_by_ssns(ssn_list)
```

### 7. Mapping Profile Storage

**Decision**: New `mapping_profile` table with JSON column mapping

**Rationale**:
- Simple structure: id, user_id (optional), name, mapping JSON, created_at
- User-specific profiles as default (per spec assumption)
- JSON storage for flexible column mapping structure
- Profile can be loaded and applied to new uploads

### 8. Pre-Commit Preview Data Structure

**Decision**: Categorized row list with status and issues

**Rationale**:
- Preview needs: total rows, to-import, to-reject, with-warnings
- Each row has: row_number, status (import/reject/warning), issues list
- Issues include: severity, field, message
- Paginated display for large files

### 9. Import Log Storage

**Decision**: New `import_log` table with indefinite retention

**Rationale**:
- Per clarification: logs retained indefinitely until manually deleted
- Log includes: session_id, timestamp, row outcomes, validation issues
- JSON blob for detailed per-row results
- Downloadable as CSV/JSON

### 10. Streamlit Wizard UI Pattern

**Decision**: Step-based state machine with progress indicator

**Rationale**:
- Streamlit's `st.session_state` for in-memory wizard state
- Steps: Upload → Map → Validate → Preview → Confirm
- Progress bar showing current step
- Back/Next navigation with validation gates
- Existing pattern in upload.py can be extended

**UI Components**:
- Step 1: File uploader + header preview
- Step 2: Column mapping dropdowns with auto-suggestions highlighted
- Step 3: Validation progress + results summary
- Step 4: Categorized preview tables (import/reject/warning)
- Step 5: Confirmation + execution + results report

## Technology Decisions Summary

| Component | Technology | Reason |
|-----------|------------|--------|
| State persistence | SQLite table | Existing infrastructure, 24hr persistence |
| CSV parsing | pandas + csv.Sniffer | Existing pattern, reliable detection |
| Encoding detection | chardet | Standard library for encoding detection |
| Column matching | Fuzzy string + aliases | 90% accuracy target achievable |
| Date parsing | pandas.to_datetime | Flexible format handling |
| Validation | Custom rule engine | Performance + severity classification |
| Duplicate detection | pandas + batch SQL | Performance for 10k rows |
| Profile storage | SQLite JSON column | Simple, flexible |
| UI framework | Streamlit | Existing frontend |

## No Unresolved Clarifications

All technical decisions are resolved. Ready for Phase 1 design.
