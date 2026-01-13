# API Contracts: Heatmap Exploration

**Feature**: 005-heatmap-exploration
**Date**: 2026-01-13

## Overview

This feature is a **frontend-only visualization enhancement**. It does not introduce any new API endpoints or modify existing API contracts.

## Consumed Endpoints

The heatmap component consumes data from existing endpoints defined in spec 004 (Scenario Analysis):

### GET /api/v1/census/{census_id}/grid

**Purpose**: Retrieve grid analysis results for visualization

**Response**: `GridResult` containing:
- `scenarios`: List of `ScenarioResult` objects (one per grid cell)
- `summary`: `GridSummary` with aggregate statistics
- `seed_used`: Base random seed

**Used By**:
- `src/ui/pages/analysis.py` → `display_grid_result()`
- `src/ui/components/heatmap.py` → `render_heatmap()`

### POST /api/v1/census/{census_id}/grid

**Purpose**: Execute grid analysis and return results

**Request Body**: `GridRequest` with adoption_rates, contribution_rates, seed

**Response**: `GridResult` (same as GET)

**Used By**:
- `src/ui/pages/analysis.py` → `run_grid_analysis()`

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Streamlit)                        │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ analysis.py  │───▶│ heatmap.py   │───▶│ Plotly Chart     │  │
│  │              │    │ + new files  │    │ + Summary Panel  │  │
│  │ run_grid_    │    │              │    │ + Detail Panel   │  │
│  │ analysis()   │    │ render_      │    │                  │  │
│  └──────┬───────┘    │ heatmap()    │    └──────────────────┘  │
│         │            └──────────────┘                           │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │ HTTP POST /api/v1/census/{id}/grid
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ analysis.py  │───▶│ scenario_    │───▶│ GridResult       │  │
│  │ (routes)     │    │ runner.py    │    │ + GridSummary    │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## No New Contracts Required

The heatmap enhancement:
1. ✅ Reads existing `GridResult` from API response
2. ✅ Uses `ScenarioResult` fields for cell display (status, margin, acp values)
3. ✅ Uses `GridSummary` for summary panel statistics
4. ✅ Manages UI state (view mode, focus, selection) entirely client-side

All data transformations happen in the frontend:
- `GridResult` → `HeatmapCellDisplay[]` (per-cell visual properties)
- `GridSummary` → `HeatmapSummaryDisplay` (extended summary with min/max coordinates)
- `ScenarioResult` → `TooltipData` (tooltip content)
