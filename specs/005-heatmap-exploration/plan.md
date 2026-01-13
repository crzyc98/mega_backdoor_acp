# Implementation Plan: Heatmap Exploration

**Branch**: `005-heatmap-exploration` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-heatmap-exploration/spec.md`

## Summary

Enhance the existing heatmap visualization component (`src/ui/components/heatmap.py`) with three view modes (Pass/Fail, Margin, Risk Zone), comprehensive accessibility features (keyboard navigation, non-color status indicators), hover tooltips with scenario details, a slide-out detail panel for drill-down, and a summary statistics panel. This feature builds on the GridResult/ScenarioResult data structures from spec 004 and the existing Plotly-based heatmap rendering.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Streamlit 1.28+, Plotly 5.15+, pandas 2.0+, pydantic 2.0+
**Storage**: N/A (visualization only; reads GridResult from API or session state)
**Testing**: pytest with streamlit-testing-library for UI component tests
**Target Platform**: Web browser (Streamlit application)
**Project Type**: Web application (extending existing Streamlit frontend)
**Performance Goals**: Heatmap render <1s for 25×25 grid; tooltips <200ms; mode switch <500ms
**Constraints**: WCAG 2.1 AA accessibility compliance; keyboard-navigable; colorblind-friendly
**Scale/Scope**: Supports grid dimensions up to 25×25 (625 cells) with full interactivity; larger grids degrade gracefully

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains template placeholders only (not yet customized for this project). No specific gates are defined. Proceeding with standard software engineering best practices:

- [x] **Library-First**: Heatmap visualization is a standalone component in `src/ui/components/`
- [x] **Test-First**: Component tests for each view mode, accessibility features, keyboard navigation
- [x] **Integration Testing**: End-to-end tests for heatmap rendering with real GridResult data
- [x] **Simplicity**: Enhance existing `heatmap.py` rather than create parallel component; reuse existing patterns

## Project Structure

### Documentation (this feature)

```text
specs/005-heatmap-exploration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - frontend only)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── ui/
│   ├── components/
│   │   ├── heatmap.py           # MODIFY: Enhanced with view modes, accessibility
│   │   ├── heatmap_cell.py      # NEW: Cell rendering with icons, focus states
│   │   ├── heatmap_tooltip.py   # NEW: Tooltip content and positioning
│   │   ├── heatmap_detail.py    # NEW: Slide-out detail panel component
│   │   └── heatmap_summary.py   # NEW: Summary statistics panel component
│   │
│   └── pages/
│       └── analysis.py          # MODIFY: Integrate enhanced heatmap components
│
├── core/
│   └── models.py                # EXISTING: Uses ScenarioResult, GridResult from spec 004
│
└── api/                         # NO CHANGES (frontend-only feature)

tests/
├── unit/
│   ├── test_heatmap_view_modes.py    # NEW: View mode switching tests
│   ├── test_heatmap_accessibility.py # NEW: Keyboard nav, focus, contrast tests
│   └── test_heatmap_summary.py       # NEW: Summary statistics calculation tests
├── integration/
│   └── test_heatmap_rendering.py     # NEW: Full component rendering tests
└── contract/                         # N/A (no API changes)
```

**Structure Decision**: Extending existing single-project structure under `src/ui/`. The heatmap enhancement is a pure frontend feature with no API changes. New components are added for separation of concerns (tooltip, detail panel, summary) while the main heatmap.py is enhanced for view mode logic.

## Complexity Tracking

No constitution violations requiring justification. The implementation follows existing patterns.

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Enhance existing heatmap.py vs new component | Maintains backward compatibility, preserves existing integration | New component would require updating all call sites |
| Plotly + custom HTML for accessibility | Plotly handles heatmap rendering; custom overlay for focus/icons | Pure CSS solution lacks Plotly's interactivity |
| Slide-out panel via Streamlit sidebar | Native Streamlit pattern, consistent with app UX | Modal would require custom JS, block interaction |
| Summary computed client-side from GridResult | GridSummary already in GridResult from spec 004 | Server recomputation would add latency |
