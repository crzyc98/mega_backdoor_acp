# Feature Specification: UI Style Update

**Feature Branch**: `007-ui-style-update`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Review the files in ui-example/ and develop a plan to update our current UI to this style. The examples are inspiration, not perfect."

## Overview

This feature updates the existing Streamlit-based UI to adopt the modern, professional visual design patterns demonstrated in the `ui-example/` React reference implementation. The goal is to transform the current functional but basic Streamlit interface into a polished, cohesive user experience while maintaining full compatibility with the existing Python/Streamlit architecture.

### Design Inspiration Sources

The `ui-example/` React implementation demonstrates:

1. **Visual Hierarchy**: Bold typography with font-weight extremes (black/extra-bold for headings, light for descriptions)
2. **Card-Based Layout**: Rounded containers (`rounded-2xl`, `rounded-xl`) with subtle borders and shadows
3. **Color System**: Indigo as primary accent, Emerald/Amber/Rose for status indicators, neutral grays for backgrounds
4. **Micro-interactions**: Hover states, transitions, and animated elements
5. **Status Visualization**: Clear PASS/RISK/FAIL/ERROR states with icons and color coding
6. **Dense Data Display**: Professional tables with uppercase tracking-widest headers
7. **Step-Based Navigation**: Numbered workflow tabs (1. Upload -> 2. Analysis -> 3. Impact -> 4. Export)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Professional First Impression (Priority: P1)

A compliance officer opens the ACP Sensitivity Analyzer for the first time and immediately perceives it as a professional, trustworthy enterprise tool based on its polished visual appearance, clear branding, and organized layout.

**Why this priority**: First impressions determine tool adoption. A professional appearance builds confidence that the compliance calculations are reliable.

**Independent Test**: Can be fully tested by viewing the main application layout and navigation without any data loaded, and verifying that visual styling matches professional enterprise application standards.

**Acceptance Scenarios**:

1. **Given** the user launches the application, **When** the main page loads, **Then** they see a clean header with branding (logo icon, app name, version badge) and styled navigation tabs
2. **Given** the user is viewing any page, **When** they observe the layout, **Then** all content appears in properly styled cards with consistent spacing, borders, and shadows
3. **Given** the user views page headings, **When** they read the text, **Then** headings use bold/extra-bold typography with clear hierarchy

---

### User Story 2 - Clear Workflow Navigation (Priority: P1)

A plan administrator needs to follow the census -> analysis -> impact -> export workflow without confusion about their current position or available next steps.

**Why this priority**: The application is workflow-oriented; unclear navigation leads to missed steps and wasted time.

**Independent Test**: Can be fully tested by navigating through each page in sequence and verifying visual indicators show current step and available actions.

**Acceptance Scenarios**:

1. **Given** the user is on any page, **When** they view the navigation, **Then** they see numbered steps (1. Upload Census, 2. Run Analysis, etc.) with the current step visually highlighted
2. **Given** the user views navigation tabs, **When** a tab is active, **Then** it shows a clear visual indicator (underline, color change, or similar)
3. **Given** data is required for a page but not available, **When** the user views that page, **Then** they see a styled empty state card with clear guidance on what to do next

---

### User Story 3 - Status-at-a-Glance Analysis Results (Priority: P1)

An analyst running ACP compliance tests needs to immediately understand the pass/fail status and key metrics without carefully reading detailed numbers.

**Why this priority**: Quick status comprehension enables faster decision-making and reduces user cognitive load during repeated analysis runs.

**Independent Test**: Can be fully tested by running a single scenario analysis and verifying the result display clearly communicates status through size, color, and iconography.

**Acceptance Scenarios**:

1. **Given** a single scenario completes, **When** results display, **Then** the pass/fail status appears prominently with appropriate color (emerald for PASS, rose for FAIL, amber for RISK) and a status icon
2. **Given** analysis results are shown, **When** the user views metrics, **Then** key values (HCE ACP, NHCE ACP, Threshold, Margin) appear in styled metric cards with clear labels
3. **Given** a margin value is displayed, **When** it is positive or negative, **Then** the color indicates the status (emerald for positive/safe, rose for negative/failing)

---

### User Story 4 - Professional Heatmap Visualization (Priority: P2)

An analyst reviewing grid analysis results can quickly scan the heatmap to identify safe operating zones, risk boundaries, and failure regions through color and visual encoding.

**Why this priority**: The heatmap is the primary decision-support visualization; enhanced styling improves data comprehension.

**Independent Test**: Can be fully tested by running a grid analysis and verifying the heatmap displays with improved visual styling while maintaining current functionality.

**Acceptance Scenarios**:

1. **Given** a grid analysis completes, **When** the heatmap displays, **Then** it appears with improved styling (rounded container, proper padding, view mode toggle bar)
2. **Given** the user views pass/fail mode, **When** they scan cells, **Then** PASS (emerald), RISK (amber), FAIL (rose), and ERROR (gray) states are clearly distinguishable with status icons
3. **Given** the user hovers over a cell, **When** the tooltip appears, **Then** it displays in a styled dark panel with organized scenario data

---

### User Story 5 - Enhanced Data Tables (Priority: P2)

A compliance officer reviewing employee-level impact data can scan the table efficiently with clear visual separation between rows, properly formatted values, and intuitive constraint status indicators.

**Why this priority**: Tables are used for audit review; improved readability reduces errors and review time.

**Independent Test**: Can be fully tested by viewing employee impact data and verifying table styling matches professional standards with proper headers, formatting, and status indicators.

**Acceptance Scenarios**:

1. **Given** the user views an employee table, **When** they scan the headers, **Then** headers display in uppercase with tracking (letter-spacing) and subtle background
2. **Given** data rows display, **When** the user views them, **Then** alternating hover states and proper padding create scannable rows
3. **Given** constraint status is shown, **When** the user views it, **Then** status appears with appropriate icon and color (checkmark/emerald for unconstrained, warning/amber for reduced, exclamation/rose for at-limit)

---

### User Story 6 - Styled Export Interface (Priority: P3)

A plan administrator needs to generate audit-ready documentation and can easily distinguish between export format options through visual card-based selection.

**Why this priority**: Export is a key final step but less frequently used than analysis features.

**Independent Test**: Can be fully tested by viewing the export page and verifying export options display as visually distinct cards with clear actions.

**Acceptance Scenarios**:

1. **Given** the user navigates to export, **When** the page displays, **Then** export options (PDF, CSV) appear as separate styled cards with icons and descriptions
2. **Given** export cards display, **When** the user views them, **Then** each card has a colored top accent border indicating its type
3. **Given** the user views action buttons, **When** they look at the export buttons, **Then** buttons are styled with proper padding, border-radius, and hover states

---

### User Story 7 - Form Styling Improvements (Priority: P3)

A user configuring analysis parameters or uploading data interacts with form controls that feel modern and responsive.

**Why this priority**: Form interactions are frequent but current Streamlit defaults are acceptable; this is polish-level improvement.

**Independent Test**: Can be fully tested by interacting with sliders, dropdowns, and buttons throughout the application.

**Acceptance Scenarios**:

1. **Given** the user views slider controls, **When** they are rendered, **Then** sliders display with accent color (indigo) for the active portion
2. **Given** the user views buttons, **When** primary buttons render, **Then** they display with bold styling, shadow, and proper hover transition
3. **Given** input fields display, **When** the user views them, **Then** inputs have consistent border-radius and focus states

---

### Edge Cases

- What happens when content overflows a styled card? Cards should handle overflow gracefully with scrolling or truncation.
- How does the UI behave on narrow viewports? Mobile-responsive considerations should be addressed for essential functionality.
- What happens when Streamlit native components do not support custom styling? Document limitations and use workarounds (custom CSS, components) where critical.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply consistent styling theme across all pages using Streamlit custom CSS injection
- **FR-002**: System MUST render navigation with numbered step labels and active-state indicators
- **FR-003**: System MUST display analysis results with color-coded status indicators (emerald/PASS, amber/RISK, rose/FAIL, gray/ERROR)
- **FR-004**: System MUST render metric values in styled card containers with clear labels
- **FR-005**: System MUST style data tables with uppercase headers, proper spacing, and hover states
- **FR-006**: System MUST render empty states with styled placeholder content and guidance
- **FR-007**: System MUST apply shadow and border-radius styling to container elements
- **FR-008**: System MUST maintain all existing functionality while applying visual updates
- **FR-009**: System MUST use a consistent color palette based on the indigo/emerald/amber/rose scheme
- **FR-010**: System MUST render constraint status with appropriate icons and colors

### Key Entities

- **Theme Configuration**: Centralized styling constants (colors, spacing, typography) for consistent application
- **Status Indicators**: Visual encoding system mapping PASS/RISK/FAIL/ERROR states to colors and icons
- **Constraint Status**: Visual encoding system mapping Unconstrained/Reduced/At-Limit/Not-Selected states

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All pages display with consistent card-based layout containers
- **SC-002**: Navigation shows numbered steps with clear active state indication
- **SC-003**: Analysis results display status with appropriate color coding (PASS=emerald, RISK=amber, FAIL=rose)
- **SC-004**: Data tables render with styled headers (uppercase, tracking) and hover states
- **SC-005**: All existing functionality (upload, analysis, export) continues to work correctly after styling updates
- **SC-006**: Empty states display styled placeholder cards with actionable guidance
- **SC-007**: Form controls (buttons, sliders, inputs) display with accent colors and proper styling

## Assumptions

- Streamlit's `st.markdown(unsafe_allow_html=True)` can be used for CSS injection to achieve custom styling
- Some Streamlit native components have limited customization; workarounds may be needed
- The application remains Streamlit-based; no conversion to React is in scope
- Performance impact of CSS injection is negligible for the application's use case
- Custom styling will be applied via a centralized theme module for maintainability

## Dependencies

- Existing Streamlit UI pages (`app.py`, `pages/*.py`)
- Existing UI components (`components/*.py`)
- Plotly charting library (heatmap styling)
- Current application structure and API integrations remain unchanged

## Out of Scope

- Converting the application from Streamlit to React
- Adding new features or functionality beyond visual styling
- Mobile-first responsive design (basic responsiveness acceptable)
- Dark mode theme (future enhancement)
- Animations and micro-interactions requiring JavaScript injection
