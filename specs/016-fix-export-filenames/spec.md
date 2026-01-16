# Feature Specification: Fix Export Filenames

**Feature Branch**: `016-fix-export-filenames`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "claude thinks it has fixed this but it isn't, when i click download csv or download pdf buttons it names it a boring export.csv or pdf. i wanted it to make a name that used the workspace census plan year etc, you see it in the code but its not actually doing it"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download CSV with Descriptive Filename (Priority: P1)

As a user, when I click the "Download CSV" button on the export page, the downloaded file should have a descriptive name that includes the workspace name, plan year, run number, and date, so I can easily identify the file later.

**Why this priority**: This is the core bug fix - users cannot identify their exports without meaningful filenames, making file management difficult.

**Independent Test**: Can be fully tested by clicking the Download CSV button and verifying the downloaded file has a descriptive name instead of "export.csv".

**Acceptance Scenarios**:

1. **Given** a workspace named "Acme Corp" with a 2024 plan year and Run #42, **When** I click "Download CSV", **Then** the downloaded file is named something like `Acme_Corp_2024_Run42_Jan2026.csv` (not `export.csv`)
2. **Given** a workspace with special characters in the name like "Smith & Co.", **When** I click "Download CSV", **Then** the filename uses sanitized characters (e.g., `Smith__Co_2024_Run1_Jan2026.csv`)

---

### User Story 2 - Download PDF with Descriptive Filename (Priority: P1)

As a user, when I click the "Download PDF" button on the export page, the downloaded file should have a descriptive name that includes the workspace name, plan year, run number, and date.

**Why this priority**: Same core issue as CSV - PDF exports also need identifiable filenames for user file management.

**Independent Test**: Can be fully tested by clicking the Download PDF button and verifying the downloaded file has a descriptive name instead of "export.pdf".

**Acceptance Scenarios**:

1. **Given** a workspace named "Acme Corp" with a 2024 plan year and Run #42, **When** I click "Download PDF", **Then** the downloaded file is named something like `Acme_Corp_2024_Run42_Jan2026.pdf` (not `export.pdf`)
2. **Given** a workspace with spaces in the name, **When** I click "Download PDF", **Then** spaces are converted to underscores in the filename

---

### Edge Cases

- What happens when the workspace name contains only special characters that get stripped? The filename should still be valid (e.g., fallback to `Export_2024_Run1_Jan2026.csv`)
- What happens when the browser cannot read the Content-Disposition header due to CORS restrictions? The system must ensure the header is properly exposed
- What happens with very long workspace names? Filenames should be truncated to a reasonable length while remaining identifiable

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deliver downloaded CSV files with descriptive filenames containing workspace name, plan year, run number, and export date
- **FR-002**: System MUST deliver downloaded PDF files with descriptive filenames containing workspace name, plan year, run number, and export date
- **FR-003**: System MUST sanitize workspace names in filenames by removing or replacing special characters that are invalid in filenames
- **FR-004**: System MUST ensure the Content-Disposition header is accessible to the frontend (exposed via CORS if applicable)
- **FR-005**: System MUST use underscores to replace spaces in workspace names within filenames
- **FR-006**: Frontend MUST correctly parse the filename from the Content-Disposition header sent by the backend

### Key Entities

- **Workspace**: Contains the name used in the filename
- **Census**: Contains the plan_year used in the filename
- **Run**: Contains the seed/run number used in the filename
- **Export File**: The downloadable CSV or PDF with the descriptive filename

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of CSV downloads result in a file named with the pattern `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.csv`
- **SC-002**: 100% of PDF downloads result in a file named with the pattern `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.pdf`
- **SC-003**: Downloaded files never have generic names like `export.csv` or `export.pdf`
- **SC-004**: Users can identify the source workspace and date of any exported file by looking at its filename alone

## Assumptions

- The backend is already generating correct descriptive filenames in the Content-Disposition header (verified in code at `workspaces.py` lines 1053-1063 for CSV, lines 1182-1191 for PDF)
- The issue is likely in the frontend's ability to read the Content-Disposition header (CORS header exposure) or in the regex pattern matching in `exportService.ts`
- The filename format `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.{ext}` is the desired format
