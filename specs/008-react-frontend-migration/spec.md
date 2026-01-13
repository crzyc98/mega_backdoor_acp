# Feature Specification: React Frontend Migration

**Feature Branch**: `008-react-frontend-migration`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Switch frontend to React 19.2.3, TypeScript 5.x, Vite 6.2.0, and Tailwind CSS, using ui-example for inspiration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Workspaces (Priority: P1)

A user creates and manages workspaces to organize their ACP analysis projects. Each workspace contains census data, analysis scenarios, and run history.

**Why this priority**: Workspaces are the foundational organizational unit - all other functionality (upload, analysis, export) operates within the context of an active workspace.

**Independent Test**: Can be fully tested by creating a workspace, viewing it in the workspace manager grid, editing its name/description, and deleting it.

**Acceptance Scenarios**:

1. **Given** a user opens the application, **When** the page loads, **Then** they see the Workspace Manager showing all existing workspaces in a grid view
2. **Given** a user clicks "Create Workspace", **When** they enter a name and description, **Then** a new workspace is created and appears in the grid
3. **Given** a user selects a workspace, **When** they click to open it, **Then** the workspace becomes active and they see the workspace dashboard with Upload, Analysis, Employee Impact, and Export tabs
4. **Given** a user is viewing the workspace grid, **When** they delete a workspace, **Then** the workspace and all its data (census, scenarios, runs) are removed

---

### User Story 2 - Access Application via React Interface (Priority: P2)

A user opens the application in their web browser and sees a modern, responsive React-based interface that provides the same functionality as the existing Streamlit application.

**Why this priority**: This is the foundational UI requirement - without a working React application that can be accessed and navigated, no other functionality can be delivered.

**Independent Test**: Can be fully tested by launching the development server, navigating to the application URL, and verifying the main layout renders with navigation tabs and responsive behavior across screen sizes.

**Acceptance Scenarios**:

1. **Given** a user opens the application URL, **When** the page loads, **Then** they see the main application layout with header, navigation tabs, and footer
2. **Given** a user is viewing the application on a mobile device, **When** the viewport is resized, **Then** the layout adapts responsively without horizontal scrolling
3. **Given** a user clicks on different navigation tabs, **When** the tab changes, **Then** the corresponding view content is displayed without page reload

---

### User Story 3 - Upload and Configure Census Data (Priority: P3)

A plan administrator uploads a CSV file containing employee census data and maps the columns to the required fields for ACP analysis.

**Why this priority**: Census data upload is the entry point for all analysis functionality - without data, no analysis can occur.

**Independent Test**: Can be fully tested by selecting a CSV file, mapping columns, configuring HCE determination, and verifying the data is parsed and displayed correctly.

**Acceptance Scenarios**:

1. **Given** a user is on the Census Upload view, **When** they drag and drop a CSV file, **Then** the file is accepted and column headers are displayed for mapping
2. **Given** a user has uploaded a CSV file, **When** they map columns to required fields, **Then** the system validates the mapping and shows census statistics (total count, HCE/NHCE counts, averages)
3. **Given** a user completes census configuration, **When** they confirm the upload, **Then** the application automatically navigates to the Analysis view

---

### User Story 4 - Run Grid Analysis with Heatmap Visualization (Priority: P4)

An analyst runs a grid analysis across multiple adoption and contribution rate combinations and views the results as an interactive heatmap.

**Why this priority**: Grid analysis with heatmap visualization is the core analytical feature that provides compliance insights across parameter combinations.

**Independent Test**: Can be fully tested by configuring grid parameters, running the analysis, and interacting with the resulting heatmap visualization.

**Acceptance Scenarios**:

1. **Given** census data has been loaded, **When** the user configures adoption rate and contribution rate ranges on the Analysis view, **Then** the ranges are accepted and reflected in the UI
2. **Given** the user has configured grid parameters, **When** they run the grid analysis, **Then** results are displayed as a color-coded heatmap showing PASS/RISK/FAIL status for each combination
3. **Given** a heatmap is displayed, **When** the user hovers over a cell, **Then** a tooltip shows detailed scenario information (rates, HCE ACP, NHCE ACP, threshold, margin)
4. **Given** a heatmap is displayed, **When** the user switches between view modes (Pass/Fail, Margin, Risk Zone), **Then** the visualization updates to reflect the selected mode

---

### User Story 5 - View Employee-Level Impact Details (Priority: P5)

An analyst drills down from a scenario result to view employee-level impact details, including individual mega contribution amounts and constraint statuses.

**Why this priority**: Employee-level details are essential for understanding how a scenario affects individual employees, but depend on scenario analysis being complete first.

**Independent Test**: Can be fully tested by selecting a scenario, navigating to the Employee Impact view, and verifying individual employee data is displayed with filtering capabilities.

**Acceptance Scenarios**:

1. **Given** a scenario has been analyzed, **When** the user clicks to view employee impact, **Then** they are navigated to the Employee Impact view with that scenario's data
2. **Given** the user is on the Employee Impact view, **When** they filter by employee ID, compensation range, or constraint type, **Then** the table updates to show only matching employees
3. **Given** the user is viewing employee data, **When** they toggle between HCE and NHCE views, **Then** the table shows only the selected employee type with relevant columns

---

### User Story 6 - Export Analysis Results (Priority: P6)

A user exports analysis results to PDF or CSV format for reporting or further analysis.

**Why this priority**: Export is a convenience feature that depends on having analysis results to export.

**Independent Test**: Can be fully tested by running an analysis, navigating to Export, and verifying PDF and CSV downloads complete successfully.

**Acceptance Scenarios**:

1. **Given** analysis results exist, **When** the user navigates to the Export view, **Then** they see options for PDF and CSV export
2. **Given** the user selects PDF export, **When** the export completes, **Then** a PDF file is downloaded containing formatted analysis results
3. **Given** the user selects CSV export, **When** the export completes, **Then** a CSV file is downloaded containing tabular analysis data

---

### Edge Cases

- What happens when no workspaces exist? The Workspace Manager shows an empty state with a prominent "Create Workspace" call-to-action.
- What happens if the workspace storage directory is inaccessible? System displays an error with guidance to check file permissions or configure an alternative path.
- What happens when the user uploads an empty or malformed CSV file? System displays a clear error message explaining the issue.
- How does the system handle a CSV with missing required columns? Column mapping interface highlights missing required fields and prevents proceeding until resolved.
- What happens when the analysis API is unavailable? The UI shows a user-friendly error state with retry option.
- How does the heatmap handle very large grids (e.g., 50x50)? The heatmap container provides horizontal and vertical scrolling while maintaining cell interactivity.

## Requirements *(mandatory)*

### Functional Requirements

#### Workspace Management
- **FR-001**: System MUST provide a Workspace Manager view displaying all workspaces in a grid layout
- **FR-002**: System MUST allow users to create, edit, rename, and delete workspaces
- **FR-003**: System MUST maintain an active workspace context accessible throughout the application
- **FR-004**: System MUST persist workspace data to local file storage (no external database required)
- **FR-005**: System MUST store each workspace in a UUID-named directory under a configurable base path

#### Application Shell
- **FR-006**: System MUST render a single-page application using React with client-side routing between views
- **FR-007**: System MUST provide navigation between Upload, Analysis, Employee Impact, and Export views via tabs (within active workspace)

#### Census Upload
- **FR-008**: System MUST support drag-and-drop CSV file upload with column mapping interface
- **FR-009**: System MUST display census statistics (total employees, HCE count, NHCE count, average compensation) after successful upload
- **FR-010**: System MUST store uploaded census data within the active workspace

#### Analysis
- **FR-011**: System MUST provide range sliders for configuring adoption rate and contribution rate parameters
- **FR-012**: System MUST display analysis results as an interactive heatmap with color-coded cells
- **FR-013**: System MUST support three heatmap view modes: Pass/Fail, Margin, and Risk Zone
- **FR-014**: System MUST show tooltip details when hovering over heatmap cells
- **FR-015**: System MUST provide modal dialogs for detailed scenario information
- **FR-016**: System MUST save analysis runs with timestamps to the active workspace

#### Employee Impact
- **FR-017**: System MUST display employee-level data in a filterable, sortable table
- **FR-018**: System MUST support filtering employees by ID, compensation range, constraint type, and employee type (HCE/NHCE)

#### Export & General
- **FR-019**: System MUST provide PDF and CSV export functionality for analysis results
- **FR-020**: System MUST display appropriate empty states with guidance when no data is available
- **FR-021**: System MUST include accessibility patterns (colorblind-friendly visualization modes, keyboard navigation)
- **FR-022**: System MUST communicate with the FastAPI backend for data operations and calculations

### Repository Structure

The migration includes reorganizing the repository to clearly separate backend and frontend concerns:

```
├── backend/          # FastAPI + Python backend
│   ├── app/
│   │   ├── models/   # Pydantic models
│   │   ├── services/ # Business logic
│   │   └── routers/  # API endpoints
│   └── tests/
├── frontend/         # React + TypeScript frontend
│   ├── components/
│   └── src/services/
└── specs/            # Feature specifications
```

- Current `src/api/` and `src/core/` move to `backend/app/`
- Current `src/storage/` moves to `backend/app/`
- Current `src/ui/` (Streamlit) is removed after React implementation
- New React application created in `frontend/` following ui-example patterns
- `tests/` moves to `backend/tests/`

### Workspace Storage Structure

Workspaces are stored in a file-based structure (no external database required):

```
~/.acp-analyzer/workspaces/
└── {workspace_id}/                    # UUID directory
    ├── workspace.json                 # Metadata (name, description, timestamps)
    ├── data/                          # Census data files
    │   └── census.csv
    └── runs/                          # Analysis run history
        └── {run_id}/
            ├── run_metadata.json      # Parameters, timestamp, status
            ├── grid_results.json      # Grid analysis results
            └── exports/               # Generated export files
```

### Workspace API Endpoints

| Endpoint                  | Purpose               |
| ------------------------- | --------------------- |
| GET /api/workspaces       | List all workspaces   |
| POST /api/workspaces      | Create workspace      |
| GET /api/workspaces/{id}  | Get workspace details |
| PUT /api/workspaces/{id}  | Update workspace      |
| DELETE /api/workspaces/{id} | Delete workspace    |

### Key Entities

- **Workspace**: Top-level organizational container with unique ID, name, description, creation/modification timestamps, and associated census data and runs
- **Run**: Analysis execution record containing parameters (adoption/contribution ranges), timestamp, status, and results
- **CensusData**: Collection of employee records with compensation, contribution, and HCE status information (stored per workspace)
- **ScenarioResult**: Analysis result containing adoption rate, contribution rate, HCE ACP, NHCE ACP, threshold, margin, and compliance status
- **GridResult**: Collection of ScenarioResults organized by adoption and contribution rate parameters
- **EmployeeImpact**: Individual employee data with calculated mega contribution amount and constraint status
- **ColumnMapping**: Configuration mapping CSV column headers to required employee data fields

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Workspaces persist across browser sessions and application restarts without data loss
- **SC-002**: Users can navigate between all application views within 1 second of clicking a navigation tab
- **SC-003**: Census file uploads of up to 10,000 employee records complete parsing within 5 seconds
- **SC-004**: Heatmap visualization renders and responds to interactions (hover, click) within 200 milliseconds
- **SC-005**: Application maintains responsive behavior on screens from 320px to 2560px width
- **SC-006**: All existing Streamlit application functionality is accessible through the new React interface
- **SC-007**: 95% of users can complete the primary workflow (upload data, run analysis, view results) without assistance
- **SC-008**: Application achieves a Lighthouse accessibility score of 90 or higher

## Clarifications

### Session 2026-01-13

- Q: What is the Streamlit replacement strategy? → A: Full replacement (remove Streamlit code after React implementation)
- Q: Where should the React frontend live in the repository? → A: Top-level `frontend/` directory with full repo restructure (backend/, frontend/, specs/)
- Q: Should state persist between browser sessions? → A: Yes, with full workspace architecture (file-based storage, scenarios, run history) inspired by PlanAlign Engine

## Assumptions

- The existing Streamlit UI code will be removed after React implementation is complete (full replacement, not parallel operation)
- The existing FastAPI backend API endpoints remain unchanged and continue to provide data operations
- The ui-example directory provides authoritative patterns for component structure, styling approach, and visual design
- Tailwind CSS will be used for styling via CDN initially, with potential migration to npm package for production builds
- No additional UI component libraries will be introduced; all components will be custom-built following ui-example patterns
- The application will be built as a single-page application without server-side rendering requirements
- Browser support targets modern evergreen browsers (Chrome, Firefox, Safari, Edge - latest 2 versions)
