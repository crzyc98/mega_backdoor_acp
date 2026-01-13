# Quickstart: Enhanced Census CSV Upload Wizard

## Overview

This feature enhances the census CSV upload experience with a multi-step wizard that includes:
- Auto-detected column mapping with confidence scores
- User-selectable date format with live preview
- Color-coded row validation (valid/warning/error)
- Per-workspace saved mapping profiles

## Prerequisites

- Running backend server (`mega start --api-only`)
- Running frontend dev server (`mega start --ui-only`)
- A workspace created in the application
- Sample CSV file (see `census_example.csv` in repo root)

## User Flow

### 1. Start Import Wizard

Navigate to a workspace and click "Upload Census Data". The wizard opens with Step 1: Upload.

### 2. Upload CSV File

- Drag and drop or click to select a CSV file
- System validates file type and size (max 50MB)
- On success, shows detected delimiter, encoding, and row count

### 3. Map Columns

- System auto-suggests mappings with confidence scores
- Low-confidence (<60%) suggestions highlighted in yellow
- Required fields: employee_id, compensation, deferral_rate
- Optional: is_hce, match_rate, after_tax_rate, ssn, dob, hire_date
- If workspace has saved profiles, option to apply existing profile

### 4. Select Date Format

- System auto-detects likely date format from sample data
- Shows live preview of how dates will be parsed
- Supported formats: MM/DD/YYYY, YYYY-MM-DD, DD/MM/YYYY, etc.
- Invalid dates highlighted in red

### 5. Review Validation

- Full validation runs on all rows
- Color-coded status per row:
  - **Green**: Valid, ready to import
  - **Yellow**: Warning (e.g., duplicate in database)
  - **Red**: Error (blocks import)
- Summary bar shows counts
- Filter to show only errors/warnings
- **Import blocked until all errors resolved**

### 6. Execute Import

- Review final summary
- Option to save mapping as profile for future imports
- Click "Import" to create census records
- Success: Redirected to analysis page

## API Quick Reference

### Create Session
```bash
curl -X POST http://localhost:8000/api/workspaces/{workspace_id}/import/sessions \
  -F "file=@census_example.csv"
```

### Get Mapping Suggestions
```bash
curl http://localhost:8000/api/import/sessions/{session_id}/mapping/suggest
```

### Set Column Mapping
```bash
curl -X PUT http://localhost:8000/api/import/sessions/{session_id}/mapping \
  -H "Content-Type: application/json" \
  -d '{"mapping": {"employee_id": "Employee ID", "compensation": "Annual Compensation"}}'
```

### Preview Date Format
```bash
curl "http://localhost:8000/api/import/sessions/{session_id}/date-format/preview?format=%m/%d/%Y"
```

### Run Validation
```bash
curl -X POST http://localhost:8000/api/import/sessions/{session_id}/validate
```

### Get Preview Rows
```bash
curl "http://localhost:8000/api/import/sessions/{session_id}/preview-rows?status=error&limit=50"
```

### Execute Import
```bash
curl -X POST http://localhost:8000/api/import/sessions/{session_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"save_profile": true, "profile_name": "My HR Export"}'
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/unit/test_date_parser.py -v
pytest tests/integration/test_import_wizard_api.py -v
```

### Frontend Tests
```bash
cd frontend
npm run test -- --filter=ImportWizard
```

## Key Files

### Backend
- `backend/app/services/import_wizard.py` - Core wizard logic
- `backend/app/services/field_mappings.py` - Fuzzy matching
- `backend/app/services/date_parser.py` - Date format handling (NEW)
- `backend/app/routers/routes/import_wizard.py` - API endpoints

### Frontend
- `frontend/src/components/ImportWizard/` - Wizard container and steps
- `frontend/src/components/ColumnMapper.tsx` - Mapping UI
- `frontend/src/components/DateFormatPicker.tsx` - Date format selection
- `frontend/src/components/ValidationPreview.tsx` - Color-coded preview
- `frontend/src/services/importWizardService.ts` - API client

## Troubleshooting

### "Session expired"
Import sessions expire after 24 hours. Start a new import.

### "Missing required field mappings"
Ensure employee_id, compensation, and deferral_rate are mapped before proceeding.

### "Cannot execute - validation errors exist"
All red (error) rows must be fixed in the source CSV before import can proceed.
Warnings (yellow) do not block import.

### Date parsing issues
If dates show as invalid, try different date format selection.
Check that dates in CSV are consistent (same format throughout).
