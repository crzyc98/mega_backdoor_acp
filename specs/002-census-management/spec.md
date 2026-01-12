# Feature Specification: Census Management

**Feature Branch**: `002-census-management`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Add Census Management as a first-class capability: users can create, list, view, and delete imported censuses. The system must store a census and its import metadata (e.g., mapping used, row counts, summary stats) so analyses can be rerun consistently. Define what a census contains (required fields vs optional contribution fields), how HCE status is determined (explicit flag vs compensation-threshold mode), and what summary metrics must be available immediately after import. Include clear acceptance criteria and error cases (missing IDs, invalid values, etc.). We should be able to name the client or name the census."

## Clarifications

### Session 2026-01-12

- Q: What is the data isolation model for censuses? → A: Shared - all users see all censuses (small team/single organization)
- Q: Can census metadata (name, client name) be edited after import? → A: Metadata only - name and client name editable; participant data immutable
- Q: Should censuses have an explicit plan year field? → A: Required field - plan year is mandatory when creating a census
- Q: Which HCE compensation threshold should be used in compensation-threshold mode? → A: Plan year threshold - use the IRS threshold in effect for the census's plan year

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import and Create a Census (Priority: P1)

As a benefits administrator, I want to import employee census data from a file so that I can run ACP analyses on the participant population.

**Why this priority**: This is the foundational capability - without the ability to create/import a census, no other census operations or analyses can occur.

**Independent Test**: Can be fully tested by uploading a valid census file, providing a name for it, and verifying the census appears in the system with correct row counts and summary statistics.

**Acceptance Scenarios**:

1. **Given** I have a CSV file with employee census data containing required fields (employee ID, compensation, deferral rate), **When** I upload the file and provide a census name, **Then** the system creates a census record with import metadata showing row count, timestamp, and summary statistics.

2. **Given** I am importing a census, **When** I provide a census name and optionally a client name, **Then** the system stores both names and associates them with the census.

3. **Given** my census file has column headers that don't match expected field names, **When** I upload the file, **Then** the system prompts me to map my columns to the required census fields, and stores this mapping with the census metadata.

4. **Given** I have successfully imported a census, **When** the import completes, **Then** I immediately see summary metrics including: total participant count, total HCE count, total NHCE count, average compensation, and average deferral rate.

---

### User Story 2 - List and View Censuses (Priority: P1)

As a benefits administrator, I want to view a list of all imported censuses and see details of any individual census so that I can select the appropriate census for analysis or review past imports.

**Why this priority**: Essential for users to locate and work with existing census data - tightly coupled with the create capability as part of core CRUD.

**Independent Test**: Can be fully tested by creating multiple censuses and verifying they appear in a list with correct names, dates, and summary information, then selecting one to view its full details.

**Acceptance Scenarios**:

1. **Given** I have imported one or more censuses, **When** I navigate to the census list view, **Then** I see all censuses with their names, plan years, client names (if provided), import dates, and participant counts.

2. **Given** I am viewing the census list, **When** I select a specific census, **Then** I see the full census details including: all import metadata (mapping used, row counts), summary statistics, and the ability to view individual participant records.

3. **Given** I am viewing a census, **When** I examine the import metadata, **Then** I can see the exact column mapping that was used during import so I can understand how the data was interpreted.

---

### User Story 3 - Delete a Census (Priority: P2)

As a benefits administrator, I want to delete a census that is no longer needed so that I can keep my census list organized and remove outdated or erroneous imports.

**Why this priority**: Important for data hygiene but less critical than create/view for core functionality.

**Independent Test**: Can be fully tested by creating a census, then deleting it and verifying it no longer appears in the census list.

**Acceptance Scenarios**:

1. **Given** I have an existing census with no associated analyses, **When** I request to delete it, **Then** the system removes the census and all its metadata, and it no longer appears in my census list.

2. **Given** I have an existing census, **When** I request to delete it, **Then** the system asks me to confirm the deletion before proceeding.

3. **Given** I have a census with associated analyses that have been run against it, **When** I request to delete it, **Then** the system warns me that associated analyses exist and asks for confirmation before proceeding.

---

### User Story 4 - Configure HCE Determination Method (Priority: P2)

As a benefits administrator, I want to specify how Highly Compensated Employee (HCE) status is determined for a census so that the system correctly classifies participants for ACP testing.

**Why this priority**: Critical for accurate ACP analysis, but can be addressed as a configuration step after basic census operations are working.

**Independent Test**: Can be fully tested by importing a census with compensation data, selecting HCE determination method, and verifying the HCE/NHCE classification matches expectations.

**Acceptance Scenarios**:

1. **Given** I am importing or editing a census, **When** I select "compensation threshold mode" for HCE determination, **Then** the system uses the IRS compensation threshold for the census's plan year (e.g., $155,000 for 2024, $160,000 for 2025) to classify employees as HCE or NHCE based on their compensation.

2. **Given** I am importing a census that includes an explicit HCE flag column, **When** I select "explicit flag mode" for HCE determination, **Then** the system uses the provided flag values to classify employees as HCE or NHCE.

3. **Given** I have configured HCE determination method for a census, **When** I view census summary statistics, **Then** I see the HCE count and NHCE count based on the configured method.

---

### User Story 5 - Rerun Analysis with Stored Census (Priority: P3)

As a benefits administrator, I want to rerun an analysis using a previously imported census so that I can compare results over time or with different parameters while using consistent participant data.

**Why this priority**: Advanced capability that depends on basic census management being fully functional.

**Independent Test**: Can be fully tested by importing a census, running an analysis, then initiating a new analysis selecting the same stored census and verifying the participant data is identical.

**Acceptance Scenarios**:

1. **Given** I have a stored census with complete import metadata, **When** I start a new analysis and select this census, **Then** the analysis uses the exact same participant data as originally imported.

2. **Given** I am starting a new analysis, **When** I select a stored census, **Then** I can see the census summary statistics before proceeding to confirm I'm using the correct data.

---

### Edge Cases

- What happens when a census file has duplicate employee IDs? System rejects the import with an error message listing the duplicate IDs.
- What happens when required fields (employee ID, compensation, deferral rate) are missing from the import file? System rejects the import with an error message identifying which required fields are missing.
- What happens when a row has an invalid value (e.g., negative compensation, deferral rate > 100%)? System rejects the import with an error message identifying the row number and invalid value.
- What happens when a census file is empty (headers only, no data rows)? System rejects the import with an error message indicating no participant data was found.
- What happens when the HCE flag column contains invalid values (not true/false or 1/0)? System rejects the import with an error message identifying the invalid values and expected format.
- What happens when compensation is zero or null and compensation-threshold mode is selected? System treats the participant as NHCE (below threshold).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to import census data from CSV files.
- **FR-002**: System MUST require a census name for each imported census.
- **FR-003**: System MUST allow users to optionally specify a client name for each census.
- **FR-024**: System MUST require a plan year for each imported census.
- **FR-004**: System MUST validate that required fields are present: employee ID, compensation, and deferral rate.
- **FR-005**: System MUST allow users to map source file columns to required census fields when column names don't match expected names.
- **FR-006**: System MUST store the column mapping used for each census import as part of the census metadata.
- **FR-007**: System MUST validate that employee IDs are unique within a census.
- **FR-008**: System MUST validate that compensation values are non-negative numbers.
- **FR-009**: System MUST validate that deferral rates are between 0% and 100% inclusive.
- **FR-010**: System MUST reject imports with validation errors and provide clear error messages identifying the specific issues (row numbers, field names, invalid values).
- **FR-011**: System MUST store import metadata including: import timestamp, total row count, column mapping, and source file name.
- **FR-012**: System MUST calculate and store summary statistics immediately upon successful import: total participants, HCE count, NHCE count, average compensation, average deferral rate.
- **FR-013**: System MUST support two HCE determination modes: explicit flag mode (using a boolean column in the census) and compensation-threshold mode (using IRS compensation limits).
- **FR-014**: System MUST use the IRS HCE compensation threshold that was in effect for the census's plan year when in compensation-threshold mode (e.g., $155,000 for 2024, $160,000 for 2025).
- **FR-015**: System MUST allow users to view a list of all imported censuses with their names, client names, import dates, and participant counts.
- **FR-016**: System MUST allow users to view full details of any census including all metadata and summary statistics.
- **FR-017**: System MUST allow users to view individual participant records within a census.
- **FR-018**: System MUST allow users to delete censuses with confirmation.
- **FR-019**: System MUST warn users when deleting a census that has associated analyses.
- **FR-022**: System MUST allow users to edit census metadata (name, client name) after import.
- **FR-023**: System MUST NOT allow modification of participant data after import; participant records are immutable.
- **FR-020**: System MUST allow previously imported censuses to be selected for new analyses.
- **FR-021**: System MUST support optional contribution-related fields in census imports: employer match rate, catch-up contributions, after-tax contributions.

### Key Entities

- **Census**: A named collection of participant data representing a point-in-time snapshot of a plan's population. Contains a name, plan year (required), optional client name, import metadata, HCE determination configuration, and a list of participants.
- **Participant**: An individual employee record within a census. Contains employee ID, compensation, deferral rate, HCE status, and optional contribution fields (employer match rate, catch-up contributions, after-tax contributions).
- **Import Metadata**: Information about how a census was imported. Contains timestamp, source file name, row count, column mapping (source columns to census fields), and validation results.
- **Census Summary Statistics**: Calculated metrics for a census. Contains total participant count, HCE count, NHCE count, average compensation, average deferral rate, and optionally average contribution rates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can import a 10,000-row census file and see summary statistics within 30 seconds of upload completion.
- **SC-002**: Users can locate and select a previously imported census from a list within 10 seconds.
- **SC-003**: 100% of census imports with validation errors display specific, actionable error messages identifying row numbers and field issues.
- **SC-004**: Users can successfully rerun an analysis using a stored census with identical participant data to the original import.
- **SC-005**: HCE classification accuracy is 100% when using either explicit flag mode or compensation-threshold mode.
- **SC-006**: Users can complete the full census import workflow (file upload, column mapping, HCE configuration, review summary) in under 5 minutes for a standard census file.

## Assumptions

- CSV is the primary import format; other formats (Excel, etc.) may be added in future iterations.
- The system requires access to historical IRS HCE compensation thresholds by plan year; maintaining this threshold data is out of scope for this feature (assumed to be configurable or pre-populated).
- A "census" represents a single plan year snapshot; users who need to track multiple plan years will import multiple censuses.
- The system already has or will have an analysis capability that this census management feature integrates with.
- Users have appropriate authorization to manage censuses; authentication and authorization are handled separately.
- Data isolation model is shared: all censuses are visible to all users (assumes small team/single organization context). No per-user or per-client data partitioning is required.
