# Implementation Plan: UI Style Update

**Branch**: `007-ui-style-update` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-ui-style-update/spec.md`

## Summary

Update the existing Streamlit-based UI to adopt modern, professional visual design patterns inspired by the `ui-example/` React reference. This involves creating a centralized theme system with CSS injection, updating all pages and components with consistent card-based layouts, professional typography, and status-aware color coding (indigo primary, emerald/amber/rose for PASS/RISK/FAIL). No new features or React conversion - styling improvements only.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Streamlit 1.28+, Plotly 5.15+, pandas 2.0+, pydantic 2.0+
**Storage**: N/A (styling only, no data persistence changes)
**Testing**: pytest (visual testing via manual verification, functional regression tests)
**Target Platform**: Web browser (Streamlit app)
**Project Type**: Single project (existing monorepo structure)
**Performance Goals**: No measurable impact on page load times
**Constraints**: Streamlit CSS injection limitations, no JavaScript injection
**Scale/Scope**: 4 pages, ~10 UI components to style

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is currently a template without concrete principles defined. This feature proceeds with standard best practices:

| Principle | Status | Notes |
|-----------|--------|-------|
| Simplicity | PASS | Pure CSS styling, no new abstractions or patterns |
| Maintainability | PASS | Centralized theme module for all styling constants |
| Testing | PASS | Existing functional tests remain valid; visual verification manual |
| Backward Compatibility | PASS | No API changes, no functionality changes |

**Gate Result**: PASS - No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/007-ui-style-update/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (theme configuration)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── ui/
│   ├── theme/                    # NEW: Theme module
│   │   ├── __init__.py           # Theme exports
│   │   ├── colors.py             # Color palette constants
│   │   ├── typography.py         # Typography constants
│   │   ├── spacing.py            # Spacing/sizing constants
│   │   ├── css.py                # CSS generation utilities
│   │   └── inject.py             # Streamlit CSS injection
│   ├── components/
│   │   ├── __init__.py
│   │   ├── card.py               # NEW: Styled card wrapper
│   │   ├── status_badge.py       # NEW: PASS/RISK/FAIL badges
│   │   ├── metric_card.py        # NEW: Styled metric display
│   │   ├── empty_state.py        # NEW: Styled empty state
│   │   ├── heatmap.py            # MODIFY: Apply theme
│   │   ├── heatmap_constants.py  # MODIFY: Use theme colors
│   │   ├── employee_impact.py    # MODIFY: Apply theme
│   │   └── results_table.py      # MODIFY: Apply theme
│   ├── pages/
│   │   ├── upload.py             # MODIFY: Apply theme
│   │   ├── import_wizard.py      # MODIFY: Apply theme
│   │   ├── analysis.py           # MODIFY: Apply theme
│   │   └── export.py             # MODIFY: Apply theme
│   └── app.py                    # MODIFY: Inject theme CSS, update navigation

tests/
├── unit/
│   └── ui/
│       └── theme/
│           ├── test_colors.py    # Theme color constants tests
│           └── test_css.py       # CSS generation tests
└── integration/
    └── ui/
        └── test_theme_injection.py  # Verify CSS injection works
```

**Structure Decision**: Single project structure maintained. New `theme/` module added under `src/ui/` for centralized styling. Existing components modified in-place rather than replaced.

## Complexity Tracking

No violations requiring justification. The implementation follows simple patterns:
- Pure CSS styling via Streamlit's `st.markdown(unsafe_allow_html=True)`
- Centralized constants module (no complex patterns)
- Component-by-component updates (no architectural changes)
