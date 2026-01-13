# Feature Specification: Enhanced Census CSV Upload Wizard

**Feature Branch**: `009-csv-upload-wizard`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Improve census CSV upload process with field mapping flow (auto-detection with fuzzy matching), date format handling with live preview, validation feedback with color-coded row status (valid/warning/error), and per-workspace saved mapping profiles"

## Clarifications

### Session 2026-01-13

- Q: What happens when user proceeds with import while error rows exist? → A: Block import entirely until all errors are resolved
- Q: How long before abandoned import sessions expire? → A: 24 hours

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload and Map Census CSV (Priority: P1)

As an administrator, I want to upload a census CSV file and have the system intelligently suggest column mappings so I can quickly import employee data without manual configuration for each field.

**Why this priority**: This is the core functionality - without the ability to upload and map CSV data, no other features can work. It directly enables the primary use case of importing census data for ACP analysis.

**Independent Test**: Can be fully tested by uploading a CSV file, reviewing suggested mappings, adjusting if needed, and confirming the mapping. Delivers value by enabling data import from any CSV format.

**Acceptance Scenarios**:

1. **Given** a user has a workspace selected, **When** they upload a CSV file, **Then** the system displays the file's detected columns and auto-suggests mappings for required fields (employee_id, compensation, deferral_rate, is_hce, match_rate, after_tax_rate) with confidence scores.

2. **Given** the system has suggested column mappings, **When** a suggestion has low confidence (below 60%), **Then** it is visually distinguished and the user is prompted to verify or correct it.

3. **Given** a CSV with non-standard column names (e.g., "Annual Salary" instead of "Compensation"), **When** uploaded, **Then** the system uses fuzzy matching to suggest the correct mapping with an appropriate confidence score.

4. **Given** the user adjusts a column mapping, **When** they change the mapping, **Then** the preview updates immediately to show how the data will be interpreted.

---

### User Story 2 - Date Format Selection with Live Preview (Priority: P2)

As an administrator, I want to select the date format used in my CSV file and see a live preview of how dates will be parsed, so I can ensure dates like hire dates and birth dates are correctly interpreted.

**Why this priority**: Date parsing errors are common with CSV imports. This feature prevents data corruption and reduces support issues, but the system can still function with manual date verification.

**Independent Test**: Can be tested by uploading a CSV with date columns, selecting different date formats, and verifying the preview shows correctly parsed dates.

**Acceptance Scenarios**:

1. **Given** a CSV contains date columns (dob, hire_date), **When** the user views the mapping step, **Then** they can select from common date formats (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, MM-DD-YYYY, DD-MM-YYYY, M/D/YYYY, D/M/YYYY).

2. **Given** a date format is selected, **When** viewing the preview, **Then** the system shows how sample dates from the CSV will be parsed (e.g., "01/15/2020" with MM/DD/YYYY → "January 15, 2020").

3. **Given** a date cannot be parsed with the selected format, **When** viewing the preview, **Then** the row shows an error indicator with the message "Invalid date: [original value]".

---

### User Story 3 - Validation Feedback with Row Status (Priority: P2)

As an administrator, I want to see clear validation feedback for each row in my CSV with color-coded status indicators, so I can identify and fix problems before importing.

**Why this priority**: Validation feedback prevents bad data from entering the system and gives users confidence in their imports. It's essential for data quality but can be deferred after basic upload works.

**Independent Test**: Can be tested by uploading a CSV with intentionally invalid data and verifying the preview shows appropriate color-coded status for each row.

**Acceptance Scenarios**:

1. **Given** a CSV has been uploaded and mapped, **When** viewing the validation preview, **Then** each row displays a status indicator: green (valid), yellow (warning), or red (error).

2. **Given** a row has validation errors, **When** viewing the preview, **Then** the error message is displayed (e.g., "Non-positive compensation value", "Invalid date format", "Missing required field").

3. **Given** a row may be a duplicate of an existing record, **When** viewing the preview, **Then** it shows a yellow warning indicator with the message "Potential duplicate - [employee identifier]".

4. **Given** validation is complete, **When** viewing the summary, **Then** the user sees counts: total rows, valid rows (green), warnings (yellow), errors (red).

---

### User Story 4 - Saved Mapping Profiles per Workspace (Priority: P3)

As an administrator, I want the system to remember my column mappings for each workspace, so future imports from the same data source skip the manual mapping step.

**Why this priority**: This is a convenience feature that improves efficiency for repeat users but isn't required for the core import functionality to work.

**Independent Test**: Can be tested by completing an import, then starting a new import in the same workspace and verifying mappings are pre-applied.

**Acceptance Scenarios**:

1. **Given** a user completes a successful import with custom mappings, **When** they start a new import in the same workspace, **Then** the system offers to apply the previously saved mapping profile.

2. **Given** a saved mapping profile exists but the new CSV has different columns, **When** applying the profile, **Then** the system shows which fields could be mapped and which need manual configuration.

3. **Given** a user has multiple mapping profiles, **When** starting an import, **Then** they can select which profile to apply or start fresh with auto-detection.

4. **Given** a mapping profile is applied, **When** the user modifies mappings, **Then** they can save the changes as a new profile or update the existing one.

---

### Edge Cases

- What happens when a CSV file is empty or contains only headers? System displays "No data rows found" error and prevents import.
- What happens when a required column cannot be mapped? System blocks proceeding to validation and highlights missing required fields.
- What happens when a CSV uses an unexpected delimiter (semicolon, tab)? System auto-detects delimiter and shows it in the preview for user confirmation.
- What happens when encoding is non-UTF8? System attempts to detect encoding and allows user to override if detection fails.
- What happens when a CSV has more rows than the system can preview? System shows a representative sample (first 100 rows) and indicates total row count.
- What happens when a user abandons an import session? Session expires after 24 hours and temporary files are cleaned up.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST auto-detect column mappings using fuzzy string matching with a minimum 60% confidence threshold for suggestions.
- **FR-002**: System MUST allow users to manually override any auto-suggested column mapping.
- **FR-003**: System MUST support configurable date formats for date columns (dob, hire_date) with at least 7 common formats.
- **FR-004**: System MUST provide a live preview showing how selected date formats parse sample values from the CSV.
- **FR-005**: System MUST validate all rows and display per-row status with color-coded indicators (valid/warning/error).
- **FR-006**: System MUST display specific error messages for each validation failure (invalid date, missing required field, out-of-range value, duplicate detection).
- **FR-007**: System MUST persist mapping profiles per workspace for reuse in future imports.
- **FR-008**: System MUST allow users to apply, modify, or delete saved mapping profiles.
- **FR-009**: System MUST detect potential duplicate records and show warnings before import.
- **FR-010**: System MUST show a validation summary with counts of valid, warning, and error rows before allowing import execution.
- **FR-011**: System MUST block import execution entirely when any validation errors exist; all errors must be resolved before import can proceed.
- **FR-012**: System MUST auto-detect CSV delimiter (comma, semicolon, tab) and file encoding.

### Key Entities

- **Import Session**: Temporary state container for an in-progress import, including uploaded file reference, column mappings, validation results, and expiration timestamp (24-hour TTL).
- **Mapping Profile**: Saved configuration associating workspace with column mappings and date format preferences for reuse.
- **Validation Issue**: Individual validation finding with severity (error/warning/info), row number, field name, message, and suggested fix.
- **Preview Row**: Transformed row data showing mapped values and per-row validation status with color coding.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a census import from file upload to execution in under 3 minutes for files with up to 1,000 rows.
- **SC-002**: Auto-detection correctly maps at least 80% of columns from common HR/payroll export formats without manual intervention.
- **SC-003**: 95% of users successfully complete their first import without consulting help documentation.
- **SC-004**: Repeat imports using saved profiles complete in under 1 minute.
- **SC-005**: Zero data corruption incidents from date parsing errors after implementation.
- **SC-006**: Support tickets related to CSV import issues reduce by 50% compared to the current workflow.

## Assumptions

- CSV files will be reasonably well-formed (proper quoting, consistent row lengths).
- Most users import from a small set of HR/payroll systems with predictable column naming conventions.
- Workspaces have a primary data source, making saved profiles useful for repeat imports.
- Date formats within a single CSV are consistent (not mixed formats in the same column).
- Files up to 50MB and 100,000 rows are within acceptable processing limits.
