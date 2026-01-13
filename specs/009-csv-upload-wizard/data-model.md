# Data Model: Enhanced Census CSV Upload Wizard

**Date**: 2026-01-13
**Feature**: 009-csv-upload-wizard

## Entity Overview

```
┌─────────────────┐      ┌──────────────────┐
│    Workspace    │──1:N─│  MappingProfile  │
└─────────────────┘      └──────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐      ┌──────────────────┐
│  ImportSession  │──1:N─│ ValidationIssue  │
└─────────────────┘      └──────────────────┘
        │
        │ 1:1 (optional)
        ▼
┌─────────────────┐
│   ImportLog     │
└─────────────────┘
```

---

## Entities

### ImportSession (Extended)

Temporary state container for an in-progress import wizard session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, UUID | Unique session identifier |
| workspace_id | string | FK, required | Associated workspace |
| created_at | datetime | required | Session creation timestamp |
| updated_at | datetime | required | Last modification timestamp |
| expires_at | datetime | required | Session expiration (created_at + 24h) |
| current_step | enum | required | `upload` \| `mapping` \| `date_format` \| `validation` \| `preview` \| `completed` |
| original_filename | string | optional | Uploaded file name |
| file_size_bytes | integer | optional | File size in bytes |
| file_reference | string | optional | Path to temp file storage |
| row_count | integer | optional | Total rows in CSV (excluding header) |
| headers | string[] | optional | Detected CSV column headers |
| column_mapping | object | optional | `{target_field: source_column}` |
| date_format | string | optional | Selected date format (e.g., `%m/%d/%Y`) |
| validation_results | object | optional | `{error_count, warning_count, info_count, valid_count}` |
| duplicate_resolution | object | optional | `{ssn_hash: 'skip' \| 'replace'}` |
| import_result_id | string | FK, optional | Link to ImportLog after execution |

**State transitions**:
```
upload → mapping → date_format → validation → preview → completed
           ↑______________|______________|
              (can go back)
```

**Validation rules**:
- expires_at must be > created_at
- file_reference must exist on filesystem while session active
- column_mapping required before advancing past `mapping` step
- validation_results required before advancing to `preview` step

---

### MappingProfile (Extended)

Saved column mapping configuration for reuse across imports.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, UUID | Unique profile identifier |
| workspace_id | string | FK, required | **NEW** - Associated workspace |
| name | string | required, unique per workspace | User-friendly profile name |
| description | string | optional | Profile description |
| column_mapping | object | required | `{target_field: source_column}` |
| date_format | string | optional | **NEW** - Preferred date format |
| expected_headers | string[] | optional | Headers this profile expects |
| created_at | datetime | required | Profile creation timestamp |
| updated_at | datetime | optional | Last modification timestamp |
| is_default | boolean | default: false | **NEW** - Auto-apply on new imports |

**Validation rules**:
- name must be unique within workspace (workspace_id + name is unique)
- column_mapping must include all required fields: `employee_id`, `compensation`, `deferral_rate`
- Only one profile per workspace can have `is_default = true`

---

### ValidationIssue (Existing)

Individual validation finding for a specific row/field.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, UUID | Unique issue identifier |
| session_id | string | FK, required | Associated import session |
| row_number | integer | required, >= 1 | 1-based row number in CSV |
| field_name | string | required | Target field name (e.g., `ssn`, `compensation`) |
| source_column | string | required | Original CSV column name |
| severity | enum | required | `error` \| `warning` \| `info` |
| issue_code | string | required | Machine-readable issue type |
| message | string | required | Human-readable error message |
| suggestion | string | optional | Suggested fix |
| raw_value | string | optional | Original value from CSV |
| related_row | integer | optional | Related row (for duplicates) |

**Issue codes** (exhaustive list):
- `INVALID_SSN` - SSN format validation failed
- `INVALID_DATE` - Date could not be parsed
- `FUTURE_DATE` - Date is in the future
- `INVALID_AMOUNT` - Amount format validation failed
- `NEGATIVE_AMOUNT` - Negative value where positive required
- `MISSING_REQUIRED` - Required field is empty
- `DUPLICATE_IN_FILE` - Same SSN appears elsewhere in file
- `DUPLICATE_EXISTING` - SSN already exists in database

---

### PreviewRow (API Response Only)

Transformed row data for validation preview display. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| row_number | integer | 1-based row number |
| status | enum | `valid` \| `warning` \| `error` (derived from issues) |
| original_values | object | `{column_name: raw_value}` |
| mapped_values | object | `{target_field: transformed_value}` |
| parsed_dates | object | `{date_field: {raw, parsed, formatted, valid}}` |
| issues | ValidationIssue[] | All issues for this row |

**Status derivation**:
- `error` if any issue has severity=error
- `warning` if any issue has severity=warning (and no errors)
- `valid` if no issues

---

### DateFormatPreview (API Response Only)

Preview of date parsing with selected format. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| format | string | Date format string (e.g., `%m/%d/%Y`) |
| format_label | string | Human-readable label (e.g., `MM/DD/YYYY`) |
| samples | DateSample[] | Parsed sample dates |
| success_rate | float | Percentage of samples parsed successfully |
| recommended | boolean | Whether this format is auto-detected recommendation |

**DateSample**:
| Field | Type | Description |
|-------|------|-------------|
| raw_value | string | Original value from CSV |
| parsed_date | string \| null | ISO date if parsed, null if failed |
| display_date | string \| null | Formatted for display (e.g., "January 15, 2020") |
| valid | boolean | Whether parsing succeeded |
| error | string \| null | Error message if parsing failed |

---

## Indexes

### ImportSession
- `idx_session_workspace` on `workspace_id` (filter by workspace)
- `idx_session_expires` on `expires_at` (cleanup expired sessions)

### MappingProfile
- `idx_profile_workspace` on `workspace_id` (filter by workspace)
- `uq_profile_workspace_name` on `(workspace_id, name)` UNIQUE

### ValidationIssue
- `idx_issue_session` on `session_id` (fetch issues for session)
- `idx_issue_session_severity` on `(session_id, severity)` (filter by severity)
- `idx_issue_session_row` on `(session_id, row_number)` (fetch issues for specific row)

---

## Migration Notes

### Schema changes from existing models

1. **ImportSession**: Add `date_format` field (string, nullable)
2. **MappingProfile**:
   - Add `workspace_id` field (string, required) - backfill existing with default workspace
   - Add `date_format` field (string, nullable)
   - Add `is_default` field (boolean, default false)
   - Add unique constraint on `(workspace_id, name)`

### Backward compatibility

- Existing import sessions without `date_format` will use auto-detection
- Existing mapping profiles will be assigned to a default workspace during migration
