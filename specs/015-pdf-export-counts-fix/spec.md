# Feature Specification: Fix PDF/CSV Export to Use Post-Eligibility Filter Counts

**Feature Branch**: `015-pdf-export-counts-fix`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "the pdf export is using the raw import-time census counts and its also being called with excluded_count=0 so nothing ever gets subtracted. the web page is showing post-eligibility filter counts because the employee impact flow uses and builds the includeable_participants vs excluded and then uses those to compute hce_summary.total_count, nhce_summary.total_count, and excluded_count. can't we use those in the export process"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent PDF Export Counts (Priority: P1)

As a plan administrator, I want the PDF export to show the same participant counts as the web application so that my compliance reports are accurate and consistent across all formats.

**Why this priority**: This is the core issue - exported PDFs currently show misleading participant counts that don't match what users see on screen, which could lead to compliance errors or confusion when sharing reports.

**Independent Test**: Can be fully tested by generating a PDF export after running analysis with excluded participants, then comparing the HCE/NHCE/excluded counts in the PDF to those displayed on the Employee Impact page.

**Acceptance Scenarios**:

1. **Given** a census with 100 participants where 10 are excluded due to eligibility rules, **When** I export a PDF report, **Then** the PDF shows 90 total includable participants (not 100 raw census count)
2. **Given** a census with excluded participants, **When** I export a PDF, **Then** the HCE count + NHCE count + excluded count equals the total census count
3. **Given** identical analysis parameters, **When** I compare the PDF export counts to the Employee Impact page counts, **Then** all participant counts match exactly

---

### User Story 2 - Consistent CSV Export Counts (Priority: P2)

As a plan administrator, I want the CSV export metadata to show accurate post-eligibility counts so that data imported into other systems reflects the correct participant breakdown.

**Why this priority**: CSV exports are often used for further analysis or import into other systems, so accurate metadata prevents downstream errors.

**Independent Test**: Can be fully tested by exporting a CSV after analysis with excluded participants and verifying the header metadata shows post-exclusion counts.

**Acceptance Scenarios**:

1. **Given** a census with excluded participants, **When** I export a CSV, **Then** the metadata header shows post-exclusion HCE and NHCE counts
2. **Given** a census with 50 HCEs where 5 are excluded, **When** I export a CSV, **Then** the HCE count in metadata shows 45 (not 50)

---

### User Story 3 - Legacy Export Route Alignment (Priority: P3)

As a system maintaining backwards compatibility, the legacy export endpoints should produce the same accurate counts as the newer workspace-based export endpoints.

**Why this priority**: Ensures any integrations or bookmarks using legacy endpoints don't receive incorrect data.

**Independent Test**: Can be fully tested by calling legacy export endpoint and comparing counts to workspace export endpoint for the same analysis run.

**Acceptance Scenarios**:

1. **Given** the same analysis run, **When** I use the legacy PDF export endpoint, **Then** the counts match those from the workspace PDF export endpoint
2. **Given** an analysis with excluded participants, **When** I use any export endpoint, **Then** the excluded_count parameter is populated correctly (not hardcoded to 0)

---

### Edge Cases

- What happens when all participants are excluded? The export should show 0 HCEs, 0 NHCEs, and display the total excluded count.
- What happens when no participants are excluded? The export should show the full census counts (post-exclusion equals pre-exclusion).
- What happens when exclusion data is missing from older analysis runs? The system should recompute exclusions on-the-fly using current eligibility logic to ensure exports always show accurate post-exclusion counts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use post-eligibility filter counts (includable HCEs, includable NHCEs) in all PDF exports, not raw census counts
- **FR-002**: System MUST use post-eligibility filter counts in all CSV export metadata headers
- **FR-003**: System MUST pass the correct excluded_count value to PDF generation (not hardcode to 0)
- **FR-004**: System MUST ensure mathematical consistency: includable_HCE + includable_NHCE + excluded = total_census_count
- **FR-005**: Legacy export endpoints MUST produce counts consistent with workspace export endpoints for the same analysis run
- **FR-006**: System MUST recompute post-exclusion counts on-the-fly using current eligibility logic when generating exports from legacy routes that lack stored exclusion data

### Key Entities

- **Census**: The imported employee data containing raw participant counts (hce_count, nhce_count, participant_count) - these are pre-filtering totals
- **Analysis Run**: Contains post-exclusion counts (included_hce_count, included_nhce_count, excluded_count) computed when the analysis was executed
- **Exclusion**: A participant removed from analysis due to ACP eligibility rules (terminated before entry, not eligible during year)
- **Export**: A generated document (PDF or CSV) that should reflect post-exclusion counts to match web display

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of PDF exports show HCE/NHCE counts that match the Employee Impact page display for the same analysis
- **SC-002**: 100% of exports satisfy the mathematical identity: displayed_HCE + displayed_NHCE + excluded = census_total
- **SC-003**: Users report zero discrepancies between exported documents and on-screen data
- **SC-004**: All export endpoints (legacy and workspace) produce identical counts for the same underlying analysis run

## Clarifications

### Session 2026-01-16

- Q: When legacy analysis runs lack stored post-exclusion counts, what should the export show? → A: Recompute exclusions on-the-fly using current eligibility logic

## Assumptions

- The workspace PDF export route has already been fixed to use post-exclusion counts (per recent commit 7925ea6)
- Post-exclusion counts (included_hce_count, included_nhce_count) are stored in the run results summary when analysis is executed
- The Employee Impact service correctly computes post-exclusion counts and these should be the source of truth
- Legacy routes can be modified to access the same post-exclusion count data that the workspace routes use
