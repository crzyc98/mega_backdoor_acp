# Quickstart: CSV Import + Column Mapping Wizard

**Feature**: 003-csv-import-wizard
**Date**: 2026-01-12

## Overview

This guide covers implementing the CSV Import Wizard feature, which provides a 5-step guided flow for importing census data with intelligent column mapping, validation, and duplicate detection.

## Prerequisites

- Python 3.11+
- Existing project dependencies (FastAPI, Streamlit, pandas, pydantic)
- SQLite database initialized

## Getting Started

### 1. Database Schema Update

Run the schema migration to add new tables:

```python
# src/storage/database.py - Add to SCHEMA_SQL

WIZARD_SCHEMA_SQL = """
-- Import wizard session state
CREATE TABLE IF NOT EXISTS import_session (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    current_step TEXT NOT NULL DEFAULT 'upload'
        CHECK (current_step IN ('upload', 'map', 'validate', 'preview', 'confirm', 'completed')),
    file_reference TEXT,
    original_filename TEXT,
    file_size_bytes INTEGER,
    row_count INTEGER,
    headers TEXT,
    column_mapping TEXT,
    validation_results TEXT,
    duplicate_resolution TEXT,
    import_result_id TEXT REFERENCES import_log(id)
);

-- Additional tables from data-model.md...
"""
```

### 2. Core Models

Create the wizard dataclasses:

```python
# src/storage/models.py - Add new models

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

WizardStep = Literal["upload", "map", "validate", "preview", "confirm", "completed"]
Severity = Literal["error", "warning", "info"]
Resolution = Literal["replace", "skip"]

@dataclass
class ImportSession:
    id: str
    current_step: WizardStep
    created_at: datetime
    expires_at: datetime
    file_reference: str | None = None
    original_filename: str | None = None
    row_count: int | None = None
    headers: list[str] | None = None
    column_mapping: dict[str, str] | None = None
    # ... additional fields
```

### 3. Field Mapping Configuration

Define the 9 required fields and their aliases:

```python
# src/core/field_mappings.py

REQUIRED_FIELDS = [
    "ssn",
    "dob",
    "hire_date",
    "compensation",
    "employee_pre_tax",
    "employee_after_tax",
    "employee_roth",
    "employer_match",
    "employer_non_elective",
]

FIELD_ALIASES = {
    "ssn": ["ssn", "social security", "ss#", "social_security_number", "tax_id"],
    "dob": ["dob", "date of birth", "birth date", "birthdate"],
    "hire_date": ["hire date", "hire_date", "date hired", "start date"],
    "compensation": ["compensation", "salary", "annual compensation", "wages"],
    "employee_pre_tax": ["pre tax", "pretax", "401k", "deferral", "ee pre tax"],
    "employee_after_tax": ["after tax", "aftertax", "ee after tax"],
    "employee_roth": ["roth", "roth 401k", "ee roth"],
    "employer_match": ["match", "employer match", "er match", "company match"],
    "employer_non_elective": ["non elective", "nonelective", "profit sharing"],
}

def suggest_mapping(headers: list[str]) -> dict[str, str]:
    """Auto-suggest column mappings based on header names."""
    mapping = {}
    normalized_headers = {h.lower().replace("_", " "): h for h in headers}

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized_headers:
                mapping[field] = normalized_headers[alias]
                break

    return mapping
```

### 4. Validation Engine

Implement the validation rules:

```python
# src/core/import_wizard.py

import re
from datetime import datetime
from typing import Generator

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"]

def validate_ssn(value: str) -> tuple[bool, str | None]:
    """Validate SSN is exactly 9 digits."""
    clean = re.sub(r"[^0-9]", "", str(value))
    if len(clean) != 9:
        return False, f"SSN must be 9 digits, got {len(clean)}"
    return True, None

def validate_date(value: str) -> tuple[bool, str | None, datetime | None]:
    """Validate and parse date from multiple formats."""
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(str(value), fmt)
            if parsed > datetime.now():
                return False, "Date cannot be in the future", None
            return True, None, parsed
        except ValueError:
            continue
    return False, f"Unrecognized date format: {value}", None

def validate_amount(value: str) -> tuple[bool, str | None]:
    """Validate non-negative dollar amount."""
    try:
        amount = float(str(value).replace(",", "").replace("$", ""))
        if amount < 0:
            return False, "Amount cannot be negative"
        return True, None
    except ValueError:
        return False, f"Invalid amount: {value}"

def validate_row(row: dict, mapping: dict[str, str]) -> Generator[ValidationIssue, None, None]:
    """Validate a single row, yielding issues found."""
    # SSN validation
    ssn_col = mapping.get("ssn")
    if ssn_col:
        valid, msg = validate_ssn(row.get(ssn_col, ""))
        if not valid:
            yield ValidationIssue(
                field_name="ssn",
                severity="error",
                issue_code="INVALID_SSN",
                message=msg,
            )

    # Date validations
    for date_field in ["dob", "hire_date"]:
        col = mapping.get(date_field)
        if col:
            valid, msg, _ = validate_date(row.get(col, ""))
            if not valid:
                yield ValidationIssue(
                    field_name=date_field,
                    severity="error",
                    issue_code="INVALID_DATE",
                    message=msg,
                )

    # Amount validations
    for amount_field in ["compensation", "employee_pre_tax", "employee_after_tax",
                         "employee_roth", "employer_match", "employer_non_elective"]:
        col = mapping.get(amount_field)
        if col:
            valid, msg = validate_amount(row.get(col, "0"))
            if not valid:
                yield ValidationIssue(
                    field_name=amount_field,
                    severity="error",
                    issue_code="INVALID_AMOUNT",
                    message=msg,
                )
```

### 5. API Routes

Register the wizard API routes:

```python
# src/api/routes/import_wizard.py

from fastapi import APIRouter, File, UploadFile, HTTPException
from src.core.import_wizard import ImportWizardService

router = APIRouter(prefix="/import", tags=["Import Wizard"])

@router.post("/sessions", status_code=201)
async def create_session(file: UploadFile = File(...)):
    """Create a new import session with uploaded file."""
    if file.size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(413, "File exceeds 50MB limit")

    service = ImportWizardService()
    session = await service.create_session(file)
    return session

@router.get("/sessions/{session_id}/preview")
async def get_preview(session_id: str):
    """Get file headers and sample rows."""
    service = ImportWizardService()
    return await service.get_file_preview(session_id)

# Additional endpoints per openapi.yaml...
```

### 6. Streamlit UI

Implement the wizard pages:

```python
# src/ui/pages/import_wizard.py

import streamlit as st

def render_wizard():
    """Render the import wizard based on current step."""
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = "upload"

    step = st.session_state.wizard_step

    # Progress indicator
    steps = ["Upload", "Map", "Validate", "Preview", "Confirm"]
    current_idx = ["upload", "map", "validate", "preview", "confirm"].index(step)
    st.progress((current_idx + 1) / len(steps))
    st.write(f"Step {current_idx + 1} of {len(steps)}: {steps[current_idx]}")

    # Render current step
    if step == "upload":
        render_upload_step()
    elif step == "map":
        render_mapping_step()
    elif step == "validate":
        render_validation_step()
    elif step == "preview":
        render_preview_step()
    elif step == "confirm":
        render_confirm_step()

def render_upload_step():
    """Step 1: File upload."""
    st.header("Upload Census CSV")

    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

    if uploaded_file:
        # Show preview
        st.subheader("File Preview")
        # Display headers and first 5 rows

        if st.button("Continue to Mapping", type="primary"):
            # Create session via API
            st.session_state.wizard_step = "map"
            st.rerun()
```

## Testing

### Unit Tests

```python
# tests/unit/test_field_mappings.py

def test_suggest_mapping_standard_headers():
    headers = ["SSN", "Date of Birth", "Hire Date", "Salary",
               "Pre Tax", "After Tax", "Roth", "Match", "Profit Sharing"]

    mapping = suggest_mapping(headers)

    assert mapping["ssn"] == "SSN"
    assert mapping["dob"] == "Date of Birth"
    assert mapping["compensation"] == "Salary"
    assert len(mapping) == 9  # All required fields mapped

def test_validate_ssn_valid():
    valid, msg = validate_ssn("123456789")
    assert valid is True
    assert msg is None

def test_validate_ssn_invalid():
    valid, msg = validate_ssn("12345")
    assert valid is False
    assert "9 digits" in msg
```

### Integration Tests

```python
# tests/integration/test_wizard_api.py

def test_create_session(client, sample_csv):
    response = client.post(
        "/api/v1/import/sessions",
        files={"file": ("test.csv", sample_csv, "text/csv")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["current_step"] == "upload"
    assert data["original_filename"] == "test.csv"

def test_full_wizard_flow(client, sample_csv):
    # Create session
    session = client.post("/api/v1/import/sessions", ...).json()

    # Set mapping
    client.put(f"/api/v1/import/sessions/{session['id']}/mapping", ...)

    # Run validation
    client.post(f"/api/v1/import/sessions/{session['id']}/validate")

    # Execute import
    result = client.post(f"/api/v1/import/sessions/{session['id']}/execute", ...)

    assert result.json()["summary"]["imported_count"] > 0
```

## Key Implementation Notes

1. **Session Expiration**: Sessions expire 24 hours after creation. Implement a background cleanup job or check expiration on access.

2. **File Storage**: Store uploaded files in a temp directory with session ID. Clean up after import completion or expiration.

3. **Performance**: For 10,000 row validation in <10 seconds:
   - Use pandas vectorized operations where possible
   - Batch database lookups for duplicate detection
   - Stream validation results instead of holding all in memory

4. **Duplicate Detection**: Hash SSN with a consistent algorithm for comparison. Use batch SQL `IN` queries to find existing records.

5. **Error Messages**: Every validation issue must have a clear, actionable message following the pattern: "Problem: [what's wrong]. Suggestion: [how to fix]."

## File Structure

```
src/
├── api/routes/import_wizard.py    # API endpoints
├── core/
│   ├── field_mappings.py          # Mapping aliases and suggestions
│   └── import_wizard.py           # Wizard business logic
├── storage/
│   └── models.py                  # Extended with wizard models
└── ui/pages/import_wizard.py      # Streamlit wizard UI

tests/
├── unit/
│   ├── test_field_mappings.py
│   └── test_import_wizard.py
└── integration/
    └── test_wizard_api.py
```

## Next Steps

1. Run `/speckit.tasks` to generate the detailed task breakdown
2. Implement Phase 1 (P1 user stories) first:
   - Upload CSV and Auto-Map Columns
   - Validate Data and Review Issues
   - Detect and Handle Duplicates
3. Add Phase 2 (P2) features:
   - Save and Reuse Mapping Profiles
   - Confirm and Execute Import
