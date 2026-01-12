# Feature Specification: CSV Import + Column Mapping Wizard

**Feature Branch**: `003-csv-import-wizard`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Implement a flexible CSV Import + Column Mapping Wizard experience: upload a CSV, preview headers + sample rows, auto-suggest mappings, allow the user to map columns to required census fields, validate the parsed data, and confirm import. Support saving a mapping profile by name for reuse on future uploads. Include duplicate detection, severity-based validation (error/warn/info), and a pre-commit preview that makes it obvious what will be imported and what will be rejected. Define acceptance criteria for the full wizard flow, including usability constraints (fast, minimal steps) and clear user-facing messages for validation issues."

## Clarifications

### Session 2026-01-12

- Q: When duplicates match existing records, what can be updated? → A: Full replace - entire record replaced with new CSV data (except SSN)
- Q: What are the required census fields for import? → A: SSN, DOB, Hire Date, Compensation, Employee Pre Tax Contributions, Employee After Tax Contributions, Employee Roth Contributions, Employer Match Contribution, Employer Non Elective Contribution (9 fields)
- Q: Are contribution fields dollar amounts or percentages? → A: Dollar amounts - all contribution fields are currency values (e.g., 5000.00)
- Q: How long are import logs retained? → A: Indefinite - logs retained permanently until manually deleted
- Q: What date formats should the system accept? → A: Multiple common formats (MM/DD/YYYY, YYYY-MM-DD, M/D/YY) with auto-detection

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload CSV and Auto-Map Columns (Priority: P1)

A plan administrator uploads a census CSV file and the system automatically suggests column mappings based on header names, allowing quick import with minimal manual intervention.

**Why this priority**: This is the core functionality - without file upload and column mapping, no import can occur. Auto-suggestion dramatically reduces user effort and error potential.

**Independent Test**: Can be fully tested by uploading a CSV file with common header names (e.g., "SSN", "First Name", "DOB") and verifying the system correctly suggests mappings to required census fields. Delivers immediate value by enabling data import.

**Acceptance Scenarios**:

1. **Given** a user on the import page, **When** they upload a CSV file, **Then** the system displays the file headers and a preview of the first 5 data rows within 2 seconds.
2. **Given** a CSV with headers matching common patterns (e.g., "SSN", "Social Security", "SS#"), **When** the file is uploaded, **Then** the system auto-suggests the correct census field mapping with 90% accuracy for standard naming conventions.
3. **Given** auto-suggested mappings displayed, **When** the user reviews them, **Then** they can accept all suggestions with a single action or modify individual mappings via dropdown selection.

---

### User Story 2 - Validate Data and Review Issues (Priority: P1)

A plan administrator reviews validation results organized by severity (errors, warnings, info) before committing the import, understanding exactly which records will be imported and which will be rejected.

**Why this priority**: Validation prevents bad data from entering the system. Without clear validation feedback, users cannot trust the import process or fix issues before they become problems.

**Independent Test**: Can be tested by uploading a CSV with intentional data issues (missing required fields, invalid formats, duplicates) and verifying the validation summary clearly categorizes each issue by severity with actionable messages.

**Acceptance Scenarios**:

1. **Given** a CSV has been uploaded and mapped, **When** validation runs, **Then** the system categorizes all issues as Error (blocks import), Warning (allows import with flag), or Info (informational only) within 5 seconds for files up to 10,000 rows.
2. **Given** validation has completed, **When** the user views results, **Then** they see a summary count by severity and can expand to see specific row numbers and field names for each issue.
3. **Given** a row has an Error-level issue, **When** viewing the pre-commit preview, **Then** that row is clearly marked as "Will be rejected" with the specific reason displayed.
4. **Given** a row passes all validations, **When** viewing the pre-commit preview, **Then** that row is clearly marked as "Will be imported" with any warnings displayed.

---

### User Story 3 - Detect and Handle Duplicates (Priority: P1)

A plan administrator is alerted to duplicate records found in the upload (both within the file and against existing data) and can decide how to handle them before import.

**Why this priority**: Duplicate census records cause compliance issues and data integrity problems. Early detection prevents costly cleanup and audit findings.

**Independent Test**: Can be tested by uploading a CSV containing duplicate SSNs (both within the file and matching existing database records) and verifying the system identifies and displays all duplicates with resolution options.

**Acceptance Scenarios**:

1. **Given** a CSV contains rows with identical SSN values, **When** validation runs, **Then** the system identifies these as "In-file duplicates" and flags them as Errors.
2. **Given** a CSV contains SSNs that already exist in the database, **When** validation runs, **Then** the system identifies these as "Existing record duplicates" and flags them as Warnings with the option to fully replace the existing record (all fields except SSN) or skip.
3. **Given** duplicate records are detected, **When** viewing the validation results, **Then** the user sees which specific records are duplicates of which other records.

---

### User Story 4 - Save and Reuse Mapping Profiles (Priority: P2)

A plan administrator saves their column mapping configuration as a named profile and reuses it for future uploads from the same data source.

**Why this priority**: Reusable mapping profiles significantly reduce repetitive work for recurring imports. This is important for efficiency but not required for basic import functionality.

**Independent Test**: Can be tested by saving a mapping profile after completing an import, then uploading a new file and applying the saved profile to verify mappings are correctly restored.

**Acceptance Scenarios**:

1. **Given** a user has configured column mappings, **When** they choose to save the profile, **Then** they can provide a descriptive name and the profile is saved for their account.
2. **Given** a user uploads a new CSV file, **When** they have saved profiles available, **Then** they see a dropdown to select a saved profile alongside the auto-suggest option.
3. **Given** a user selects a saved profile, **When** the CSV headers match the profile's expected columns, **Then** all mappings are applied automatically with a visual indicator of which mappings were applied.
4. **Given** a user selects a saved profile, **When** the CSV headers don't fully match, **Then** the system applies matching mappings and highlights unmatched columns for manual resolution.

---

### User Story 5 - Confirm and Execute Import (Priority: P2)

A plan administrator reviews the final pre-commit summary showing exactly what will happen, confirms the import, and receives a clear success/failure report.

**Why this priority**: Final confirmation prevents accidental imports and the completion report provides audit trail and user confidence. Important for usability but builds on validation functionality.

**Independent Test**: Can be tested by proceeding through the wizard to the confirmation step and verifying the summary accurately reflects row counts, then executing import and verifying the completion report matches expected outcomes.

**Acceptance Scenarios**:

1. **Given** validation is complete, **When** viewing the pre-commit preview, **Then** the user sees: total rows, rows to be imported, rows to be rejected, rows with warnings, and can review each category.
2. **Given** the pre-commit preview is displayed, **When** the user confirms import, **Then** the system imports all valid records and displays a completion summary within 30 seconds for up to 10,000 rows.
3. **Given** import completes, **When** viewing the completion report, **Then** the user sees: records successfully imported, records rejected (with reasons), and can download a detailed log.

---

### Edge Cases

- What happens when the CSV file is empty or contains only headers? System displays a clear message: "File contains no data rows to import."
- What happens when the CSV uses non-standard delimiters or encoding? System auto-detects common delimiters (comma, semicolon, tab) and encodings (UTF-8, Latin-1); displays error if unreadable.
- What happens when a required census field has no column mapped? System prevents proceeding past mapping step until all required fields have mappings, with clear indication of missing mappings.
- What happens when the user's session expires mid-wizard? System preserves wizard state and uploaded file for 24 hours; user can resume from last completed step.
- What happens when a CSV file exceeds the maximum size? System displays clear message with the size limit before upload completes; file is rejected but user can try with smaller file.
- What happens when two users upload files simultaneously? Each user's wizard session is isolated; no cross-contamination of data or state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept CSV file uploads up to 50MB in size.
- **FR-002**: System MUST display CSV headers and a preview of the first 5 data rows after upload.
- **FR-003**: System MUST auto-suggest column mappings based on header name matching against known census field patterns and aliases.
- **FR-004**: System MUST allow users to manually override any auto-suggested mapping via dropdown selection of census fields.
- **FR-005**: System MUST validate that all 9 required census fields (SSN, DOB, Hire Date, Compensation, Employee Pre Tax Contributions, Employee After Tax Contributions, Employee Roth Contributions, Employer Match Contribution, Employer Non Elective Contribution) have column mappings before proceeding to validation step.
- **FR-006**: System MUST perform data validation with three severity levels: Error (blocks record import), Warning (allows import with flag), Info (informational only). Validation rules include: SSN must be 9 digits; DOB and Hire Date must be valid dates in common formats (MM/DD/YYYY, YYYY-MM-DD, M/D/YY) with auto-detection; Compensation and all contribution fields must be non-negative dollar amounts.
- **FR-007**: System MUST detect duplicate records by SSN both within the uploaded file and against existing database records. For existing record matches, the system MUST offer the option to fully replace the existing record (all fields except SSN) or skip the row.
- **FR-008**: System MUST display validation results grouped by severity with expandable details showing row number, field name, and specific issue.
- **FR-009**: System MUST provide a pre-commit preview clearly showing which rows will be imported vs. rejected.
- **FR-010**: System MUST allow users to save column mapping configurations as named profiles.
- **FR-011**: System MUST allow users to load saved mapping profiles when uploading new files.
- **FR-012**: System MUST execute import of all valid records upon user confirmation.
- **FR-013**: System MUST generate a completion report showing import results (success count, rejection count, warnings).
- **FR-014**: System MUST allow users to download a detailed import log containing all validation issues and outcomes. Import logs are retained indefinitely until manually deleted.
- **FR-015**: System MUST complete the full wizard flow in 5 steps or fewer (Upload → Map → Validate → Preview → Confirm).
- **FR-016**: System MUST provide clear, user-friendly messages for all validation issues that explain the problem and suggest resolution.
- **FR-017**: System MUST auto-detect CSV delimiter (comma, semicolon, tab) and character encoding (UTF-8, Latin-1).
- **FR-018**: System MUST preserve wizard state for 24 hours to allow session recovery.

### Key Entities

- **CSV Upload Session**: Represents an in-progress import wizard session. Contains uploaded file reference, mapping state, validation results, and user progress through wizard steps.
- **Mapping Profile**: A saved configuration linking CSV column names to census field identifiers. Has a user-defined name, creation date, and the column-to-field mapping pairs.
- **Validation Issue**: An individual data quality problem found during validation. Has severity level (error/warning/info), row reference, field reference, issue code, and user-friendly message.
- **Import Result**: The outcome of a completed import operation. Contains success count, rejection count, warning count, timestamp, and reference to detailed log.
- **Census Record**: The target entity for imported data. Required fields: SSN (unique identifier), DOB, Hire Date, Compensation, Employee Pre Tax Contributions, Employee After Tax Contributions, Employee Roth Contributions, Employer Match Contribution, Employer Non Elective Contribution. Optional fields (if mapped): First Name, Last Name, Termination Date, Employee Status, Hours Worked, Address.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a standard CSV import (upload through confirmation) in under 3 minutes for files with up to 1,000 rows.
- **SC-002**: Auto-suggested column mappings are correct (require no manual changes) for 90% of columns when using standard header naming conventions.
- **SC-003**: System processes and validates files with 10,000 rows within 10 seconds.
- **SC-004**: Users can identify and understand all validation issues without contacting support in 95% of import attempts.
- **SC-005**: Saved mapping profiles reduce time to complete repeat imports by at least 50% compared to first-time imports.
- **SC-006**: Zero duplicate records are imported when duplicate detection identifies matches (100% duplicate blocking accuracy).
- **SC-007**: 95% of users successfully complete their first import without abandoning the wizard flow.

## Assumptions

- SSN is the unique identifier for census records and the primary field for duplicate detection.
- The system has a defined set of required census fields that must be mapped for import.
- Users have appropriate permissions to import census data before accessing the wizard.
- CSV files use standard row-per-record format with consistent column counts.
- The existing application has a census data structure and database that the import wizard integrates with.
- Mapping profiles are user-specific and not shared across accounts by default.
