# ACP Sensitivity Analyzer

A web-based compliance tool for retirement-plan analysts to evaluate how "mega backdoor Roth" after-tax contributions affect ACP (Actual Contribution Percentage) nondiscrimination test outcomes under IRC Section 401(m).

## Overview

The ACP Sensitivity Analyzer helps benefits professionals and plan compliance analysts:

- **Validate mega-backdoor Roth programs** against IRS compliance testing
- **Quantify risk thresholds** by transforming compliance uncertainty into actionable data
- **Run sensitivity analysis** across multiple adoption and contribution rate scenarios
- **Visualize results** through interactive heatmaps showing pass/fail/risk zones
- **Drill down to employee-level details** to understand which participants constrain outcomes

## Features

### Workspace Management
- Create and manage multiple analysis workspaces
- Each workspace maintains its own census data and analysis runs
- File-based storage in `~/.acp-analyzer/workspaces/{uuid}/`

### Census Management
- Import participant census data via CSV with drag-and-drop upload
- Automatic PII masking (SSN, names stripped on import)
- Support for explicit HCE flags or compensation-threshold determination
- Summary statistics: participant counts, HCE/NHCE breakdown, average compensation

### Scenario Analysis
- **Grid Analysis**: Run multiple scenarios across adoption × contribution rate combinations
- Reproducible calculations with seeded random HCE selection
- Real-time progress tracking during analysis

### Heatmap Exploration
- Interactive visualization over adoption × contribution parameter space
- Multiple view modes: Pass/Fail, Margin gradient, Risk Zone
- Hover tooltips with detailed scenario metrics
- Click-to-drill-down for employee-level details

### Employee-Level Impact Views
- Individual employee detail drill-down for any scenario
- Filter by HCE/NHCE type and constraint status
- Shows: compensation, contributions, §415(c) limit, available room, constraint status
- Sortable and paginated data table

### Export & Reporting
- CSV export with full calculation details and audit metadata
- PDF report with census summary, results table, and compliance info
- Audit-ready documentation for regulatory compliance

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend API | FastAPI 0.100+, Python 3.11+ |
| Frontend UI | React 19, TypeScript 5.8, Vite 6 |
| Styling | Tailwind CSS |
| Data Processing | Pandas 2.0+, NumPy |
| Data Validation | Pydantic 2.0+ |
| Storage | File-based JSON (workspaces) |
| PDF Export | ReportLab 4.0+ |

## Project Structure

```
mega_backdoor_acp/
├── backend/                    # Python/FastAPI backend
│   ├── app/
│   │   ├── models/            # Pydantic models
│   │   │   ├── workspace.py   # Workspace, WorkspaceDetail
│   │   │   ├── run.py         # Run, RunCreate
│   │   │   ├── census.py      # CensusSummary
│   │   │   └── analysis.py    # GridResult, ScenarioResult
│   │   ├── routers/
│   │   │   └── workspaces.py  # All API endpoints
│   │   ├── services/
│   │   │   ├── acp_calculator.py
│   │   │   ├── scenario_runner.py
│   │   │   ├── census_parser.py
│   │   │   └── export.py
│   │   └── storage/
│   │       └── workspace_storage.py
│   └── tests/
├── frontend/                   # React/TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   │   ├── Layout.tsx
│   │   │   ├── Heatmap.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── ...
│   │   ├── pages/             # Page components
│   │   │   ├── WorkspaceManager.tsx
│   │   │   ├── CensusUpload.tsx
│   │   │   ├── AnalysisDashboard.tsx
│   │   │   ├── EmployeeImpact.tsx
│   │   │   └── Export.tsx
│   │   ├── services/          # API client functions
│   │   ├── hooks/             # React hooks (useWorkspace)
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Utility functions
│   ├── package.json
│   └── vite.config.ts
└── specs/                      # Feature specifications
```

## Installation

### Backend Setup

```bash
# Clone the repository
git clone <repository-url>
cd mega_backdoor_acp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Or install from backend directory
cd backend && pip install -e .
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Quick Start

### Using the CLI (Recommended)

```bash
# Add CLI to PATH (optional)
export PATH="$PWD/bin:$PATH"

# Start both backend and React frontend
mega start

# Or run directly without PATH setup
./bin/mega start
```

This launches:
- **API Server** at http://localhost:8000 (docs at http://localhost:8000/docs)
- **React UI** at http://localhost:5173

Press `Ctrl+C` to stop all services.

### CLI Options

```bash
# Start both API and React frontend
mega start

# Custom ports
mega start --api-port 8080 --ui-port 3000

# Start only API server
mega start --api-only

# Start only frontend
mega start --ui-only

# Headless mode (no browser)
mega start --no-browser
```

### Manual Start (Alternative)

If you prefer to start services manually:

```bash
# Terminal 1: Backend API
cd backend && uvicorn app.routers.main:app --reload --port 8000

# Terminal 2: React Frontend
cd frontend && npm run dev
```

## API Endpoints

### Workspaces

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces` | List all workspaces |
| POST | `/api/workspaces` | Create workspace |
| GET | `/api/workspaces/{id}` | Get workspace details |
| PUT | `/api/workspaces/{id}` | Update workspace |
| DELETE | `/api/workspaces/{id}` | Delete workspace |

### Census

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workspaces/{id}/census` | Upload census CSV |
| GET | `/api/workspaces/{id}/census` | Get census summary |

### Analysis Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/runs` | List runs |
| POST | `/api/workspaces/{id}/runs` | Create and execute run |
| GET | `/api/workspaces/{id}/runs/{run_id}` | Get run with results |
| DELETE | `/api/workspaces/{id}/runs/{run_id}` | Delete run |

### Employee Impact

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/runs/{run_id}/employees` | Get employee impact details |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/runs/{run_id}/export/csv` | Export to CSV |
| GET | `/api/workspaces/{id}/runs/{run_id}/export/pdf` | Export to PDF |

## Regulatory Background

This tool implements ACP testing per **IRC Section 401(m)**:

- **Dual test formula**: `max(NHCE_ACP × 1.25, min(NHCE_ACP + 2.0%, 2 × NHCE_ACP))`
- **HCE determination**: Per IRS compensation thresholds by plan year
- **§415(c) limits**: Annual additions cap per participant
- **§401(a)(17)**: Compensation limit enforcement

The response includes `binding_rule` to show whether the effective limit came from the 1.25x test or the capped 2%/2x test.

Rounding: calculations are kept in decimal precision internally, while UI/CSV/PDF display ACP values in percentage points with two decimals (basis points).

### Status Classifications

| Status | Description |
|--------|-------------|
| **PASS** | Margin > 0.50 percentage points above threshold |
| **RISK** | Passing but margin ≤ 0.50 percentage points |
| **FAIL** | HCE ACP exceeds calculated threshold |
| **ERROR** | Calculation error (e.g., no HCEs/NHCEs) |

## Configuration

IRS annual limits are configured in `backend/app/services/plan_constants.yaml`:

```yaml
annual_limits:
  2025:
    hce_threshold: 160000
    elective_deferral_limit_402g: 23500
    catch_up_limit_414v: 7500
    annual_additions_limit_415c: 70000
    compensation_limit_401a17: 350000
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app

# Frontend type checking
cd frontend
npm run typecheck
```

### Code Quality

```bash
# Backend linting
ruff check backend/

# Frontend linting
cd frontend
npm run lint
```

See [CLAUDE.md](CLAUDE.md) for development guidelines and active technology decisions.

## License

[Add license information here]
