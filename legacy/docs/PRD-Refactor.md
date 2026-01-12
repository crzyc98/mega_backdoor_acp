# PRD: ACP Sensitivity Analyzer - Full Stack Refactor

## Executive Summary

Refactor the existing ACP Sensitivity Analyzer from a CLI/Streamlit-based Python application to a modern full-stack architecture with a **FastAPI backend** and **React + TypeScript frontend**. This refactor will improve maintainability, enable API integrations, and provide a professional user experience while preserving all existing business logic.

---

## Goals & Objectives

### Primary Goals
1. **Modernize Architecture**: Separate concerns into a clean API backend and SPA frontend
2. **Enable API Access**: Allow programmatic access to ACP calculations for third-party integrations
3. **Improve UX**: Provide a responsive, modern web interface with real-time interactions
4. **Maintain Accuracy**: Preserve 100% of existing ACP calculation logic and regulatory compliance

### Success Metrics
- All existing tests pass against new backend
- API response time <500ms for single scenario, <5s for full grid
- Frontend loads in <2s on standard connection
- Zero regression in calculation accuracy (<0.01% variance)

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115+ | API framework |
| Pydantic | 2.10+ | Data validation & serialization |
| DuckDB | 1.1+ | Embedded analytics database |
| Pandas | 2.0+ | Data manipulation |
| NumPy | 1.26+ | Numerical operations |
| PyYAML | 6.0+ | Configuration parsing |
| Uvicorn | 0.30+ | ASGI server |
| pytest | 8.0+ | Testing framework |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19+ | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 6.x | Build tool |
| Tailwind CSS | 3.x | Styling |
| React Query | 5.x | Server state management |
| Recharts | 2.x | Charting library |
| React Router | 7.x | Client-side routing |
| Zod | 3.x | Schema validation |

### Development & DevOps
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Local development |
| GitHub Actions | CI/CD |
| ESLint + Prettier | Code quality |
| Ruff | Python linting |

---

## Architecture

```
acp-analyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings & configuration
│   │   ├── dependencies.py      # Dependency injection
│   │   │
│   │   ├── models/              # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── census.py        # Employee census models
│   │   │   ├── scenario.py      # Scenario input/output models
│   │   │   ├── results.py       # Analysis results models
│   │   │   ├── configuration.py # Plan configuration models
│   │   │   └── census_import.py # Import mapping & validation models
│   │   │
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── acp_calculator.py    # Core ACP calculations
│   │   │   ├── contribution_limits.py # § 415(c) validation
│   │   │   ├── scenario_runner.py   # Grid execution
│   │   │   ├── employee_analysis.py # Employee-level details
│   │   │   ├── census_import.py     # CSV parsing, mapping, validation
│   │   │   └── export_service.py    # CSV/Excel exports
│   │   │
│   │   ├── routers/             # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py      # /api/analysis/*
│   │   │   ├── census.py        # /api/census/* (CRUD)
│   │   │   ├── census_import.py # /api/census/import/* (import flow)
│   │   │   ├── configuration.py # /api/config/*
│   │   │   ├── heatmap.py       # /api/heatmap/*
│   │   │   └── export.py        # /api/export/*
│   │   │
│   │   └── db/                  # Database layer
│   │       ├── __init__.py
│   │       ├── database.py      # DuckDB connection
│   │       └── repositories.py  # Data access layer
│   │
│   ├── data/
│   │   └── plan_constants.yaml  # IRS limits configuration
│   │
│   ├── tests/
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── test_acp_calculator.py
│   │   ├── test_contribution_limits.py
│   │   ├── test_api_analysis.py
│   │   └── test_api_census.py
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # App entry point
│   │   ├── App.tsx              # Root component
│   │   │
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/              # Base UI primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Select.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   └── StepIndicator.tsx
│   │   │   │
│   │   │   ├── Heatmap.tsx      # Interactive heatmap
│   │   │   ├── ScenarioCard.tsx # Scenario result display
│   │   │   ├── MetricsPanel.tsx # Key metrics display
│   │   │   ├── RiskBadge.tsx    # PASS/RISK/FAIL indicator
│   │   │   │
│   │   │   └── import/          # Census import components
│   │   │       ├── CensusImportWizard.tsx  # Multi-step wizard
│   │   │       ├── FileUploader.tsx        # Drag-drop CSV upload
│   │   │       ├── ColumnMapper.tsx        # Column mapping UI
│   │   │       ├── ImportPreview.tsx       # Validation preview
│   │   │       └── SaveMappingDialog.tsx   # Save mapping modal
│   │   │
│   │   ├── pages/               # Route pages
│   │   │   ├── Dashboard.tsx    # Executive summary
│   │   │   ├── CensusImport.tsx # Import wizard page
│   │   │   ├── Analysis.tsx     # Run scenarios
│   │   │   ├── Heatmaps.tsx     # Visualization page
│   │   │   ├── EmployeeDetail.tsx # Employee-level view
│   │   │   ├── Configuration.tsx # Plan settings
│   │   │   └── Export.tsx       # Export results
│   │   │
│   │   ├── services/            # API client
│   │   │   ├── api.ts           # Base API configuration
│   │   │   ├── analysisApi.ts   # Analysis endpoints
│   │   │   ├── censusApi.ts     # Census CRUD endpoints
│   │   │   ├── censusImportApi.ts # Import flow endpoints
│   │   │   └── configApi.ts     # Configuration endpoints
│   │   │
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAnalysis.ts
│   │   │   ├── useCensus.ts
│   │   │   ├── useCensusImport.ts # Import wizard state
│   │   │   └── useHeatmapData.ts
│   │   │
│   │   ├── types/               # TypeScript types
│   │   │   ├── census.ts
│   │   │   ├── censusImport.ts  # Import mapping types
│   │   │   ├── scenario.ts
│   │   │   └── results.ts
│   │   │
│   │   └── utils/               # Helper functions
│   │       ├── formatters.ts    # Number/date formatting
│   │       └── validators.ts    # Input validation
│   │
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

---

## Backend API Design

### Base URL
```
Development: http://localhost:8000/api
Production:  https://api.acp-analyzer.com/api
```

### Endpoints

#### Census Management & Import

**Overview**: A flexible CSV import system that lets users map columns from any payroll/HRIS export format to the app's census fields, with mappings saved per data source for future imports.

```
GET    /api/census
       Response: { censuses: CensusSummary[] }

GET    /api/census/{census_id}
       Response: { census_id, summary, employees[], mapping_used }

GET    /api/census/{census_id}/summary
       Response: { hce_count, nhce_count, total_compensation, demographics }

DELETE /api/census/{census_id}
       Response: { success: true }
```

**Import Flow Endpoints**:
```
POST   /api/census/import/preview
       Body: multipart/form-data (CSV file)
       Response: {
         file_id: string,
         headers: string[],
         sample_rows: object[],     # First 5 rows as objects
         row_count: int,
         detected_mapping: ColumnMapping | null,
         saved_mappings: SavedMapping[]
       }

POST   /api/census/import/parse
       Body: {
         file_id: string,
         mapping: ColumnMapping
       }
       Response: {
         employees: ParsedEmployee[],
         validation: {
           valid_count: int,
           warning_count: int,
           error_count: int,
           issues: ValidationIssue[]
         },
         summary: CensusSummary
       }

POST   /api/census/import/confirm
       Body: {
         file_id: string,
         mapping: ColumnMapping,
         save_mapping_as?: string   # Optional: save for future use
       }
       Response: {
         census_id: string,
         summary: CensusSummary,
         employees: Employee[],
         mapping_saved: bool
       }

GET    /api/census/mappings
       Response: { mappings: SavedMapping[] }

DELETE /api/census/mappings/{mapping_id}
       Response: { success: true }
```

#### Analysis
```
POST   /api/analysis/scenario
       Body: {
         census_id: string,
         adoption_rate: float,
         contribution_rate: float,
         plan_year: int
       }
       Response: {
         pass_fail: "PASS" | "FAIL",
         nhce_acp: float,
         hce_acp: float,
         max_allowed_acp: float,
         margin: float,
         limit_a: float,
         limit_b: float,
         passed_limit_a: bool,
         passed_limit_b: bool,
         hce_contributors: int,
         nhce_contributors: int,
         total_mega_backdoor: float
       }

POST   /api/analysis/grid
       Body: {
         census_id: string,
         adoption_rates: float[],
         contribution_rates: float[],
         plan_year: int
       }
       Response: {
         scenarios: ScenarioResult[],
         summary: {
           total_scenarios: int,
           pass_count: int,
           fail_count: int,
           risk_count: int,
           first_failure: { adoption, contribution } | null,
           max_safe_contribution: float
         }
       }

GET    /api/analysis/{analysis_id}
       Response: { analysis_id, created_at, scenarios[], summary }
```

#### Heatmap Data
```
GET    /api/heatmap/pass-fail?census_id={id}&plan_year={year}
       Response: {
         rows: string[],          # contribution rates
         columns: string[],       # adoption rates
         data: ("PASS"|"FAIL")[][]
       }

GET    /api/heatmap/margins?census_id={id}&plan_year={year}
       Response: {
         rows: string[],
         columns: string[],
         data: float[][],
         min: float,
         max: float,
         avg: float
       }

GET    /api/heatmap/risk-zones?census_id={id}&plan_year={year}
       Response: {
         rows: string[],
         columns: string[],
         data: ("SAFE"|"RISK"|"FAIL")[][],
         counts: { safe: int, risk: int, fail: int }
       }
```

#### Employee-Level Analysis
```
GET    /api/employees/{census_id}/analysis
       Query: ?adoption_rate={rate}&contribution_rate={rate}&plan_year={year}
       Response: {
         hce_employees: EmployeeDetail[],
         nhce_employees: EmployeeDetail[],
         scenario_summary: ScenarioResult
       }

GET    /api/employees/{census_id}/{employee_id}
       Response: {
         employee_id: string,
         is_hce: bool,
         compensation: float,
         current_contributions: {...},
         section_415_limit: float,
         available_room: float,
         mega_backdoor_contribution: float
       }
```

#### Configuration
```
GET    /api/config/plan-years
       Response: { years: [2024, 2025, 2026], default: 2024 }

GET    /api/config/limits?plan_year={year}
       Response: {
         compensation_limit: float,      # § 401(a)(17)
         elective_deferral_limit: float, # § 402(g)
         annual_additions_limit: float,  # § 415(c)
         catch_up_limit: float,          # § 414(v)
         super_catch_up_limit: float     # SECURE 2.0
       }

GET    /api/config/scenario-defaults
       Response: {
         adoption_rates: float[],
         contribution_rates: float[],
         acp_test: { multiplier: float, adder: float }
       }
```

#### Export
```
POST   /api/export/csv
       Body: { census_id, analysis_id }
       Response: Binary file download

POST   /api/export/excel
       Body: { census_id, analysis_id, include_charts: bool }
       Response: Binary file download

POST   /api/export/pdf-report
       Body: { census_id, analysis_id, include_executive_summary: bool }
       Response: Binary file download
```

---

## Census Import Feature Specification

A flexible CSV import system that lets users map columns from any payroll/HRIS export format to the app's census fields, with mappings saved per data source for future imports.

### Key Features

1. **Auto-detection**: Scans CSV headers and guesses mappings using common patterns from payroll systems
2. **Two HCE identification modes**:
   - Single column: Boolean "is_hce" or "HCE" column (true/false, yes/no, 1/0)
   - Compensation-based: Auto-calculate HCE status from compensation threshold ($155K for 2024)
3. **Flexible contribution columns**: Map various contribution types (pre-tax, Roth, after-tax, match)
4. **Column mapper UI**: Dropdown selectors for each field with sample data preview
5. **Saved mappings**: Store mappings by name (e.g., "ADP Export", "Paylocity Format") for reuse
6. **Pre-import validation**: Shows parsed employees with validation status before committing
7. **Duplicate detection**: Identify duplicate employee IDs within the upload

### Data Flow

```
Upload CSV → Preview (headers + sample rows) → Column Mapper → Parse with mapping → Validate → Preview employees → Confirm import
                                                       ↓
                                              Save mapping (optional)
```

### Auto-Detection Patterns

The system attempts to automatically detect column mappings based on common header names:

| Target Field | Detected Headers (case-insensitive) |
|-------------|-------------------------------------|
| `employee_id` | "employee_id", "emp_id", "ee_id", "ssn", "employee number", "id" |
| `is_hce` | "is_hce", "hce", "hce_status", "highly_compensated" |
| `compensation` | "compensation", "salary", "annual_salary", "pay", "wages", "gross_pay", "ytd_compensation" |
| `er_match_amt` | "er_match", "employer_match", "match", "company_match", "401k_match" |
| `ee_pre_tax_amt` | "ee_pretax", "pretax", "pre_tax", "401k_deferral", "traditional_401k" |
| `ee_roth_amt` | "ee_roth", "roth", "roth_401k", "roth_deferral" |
| `ee_after_tax_amt` | "ee_aftertax", "after_tax", "aftertax", "voluntary_aftertax" |

### Column Mapping Schema

```typescript
interface ColumnMapping {
  // Required mappings
  employee_id: string;        // CSV column name
  compensation: string;       // CSV column name

  // HCE determination (one of these)
  hce_mode: 'column' | 'compensation_threshold';
  is_hce?: string;            // CSV column name (if mode = 'column')
  hce_threshold?: number;     // Compensation threshold (if mode = 'compensation_threshold')

  // Optional contribution mappings
  er_match_amt?: string;      // CSV column name or null
  ee_pre_tax_amt?: string;    // CSV column name or null
  ee_roth_amt?: string;       // CSV column name or null
  ee_after_tax_amt?: string;  // CSV column name or null

  // Data transformation options
  compensation_multiplier?: number;  // e.g., 1000 if CSV shows "150" for $150,000
  trim_whitespace?: boolean;
  skip_rows?: number;         // Skip header rows
}

interface SavedMapping {
  id: string;
  name: string;               // User-friendly name: "ADP Export", "Paylocity"
  mapping: ColumnMapping;
  created_at: string;
  last_used_at: string;
  use_count: number;
}
```

### Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| Missing employee_id | Error | Employee ID is required |
| Duplicate employee_id | Error | Employee ID must be unique within file |
| Missing compensation | Error | Compensation is required |
| Compensation ≤ 0 | Error | Compensation must be positive |
| Compensation > $1M | Warning | Unusually high compensation |
| Contribution > Compensation | Warning | Contributions exceed annual compensation |
| Invalid HCE value | Error | HCE column must be boolean-like |
| Missing contribution columns | Info | No contribution data will be imported |
| Compensation below HCE threshold but marked HCE | Warning | Verify HCE status |

### Parsed Employee Response

```typescript
interface ParsedEmployee {
  row_number: number;
  employee: Employee;
  status: 'valid' | 'warning' | 'error';
  issues: ValidationIssue[];
}

interface ValidationIssue {
  field: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  value?: any;
}
```

### Frontend Components for Import

#### `CensusImportWizard`
Multi-step wizard component managing the import flow:

```tsx
// Steps
enum ImportStep {
  UPLOAD = 'upload',
  MAP_COLUMNS = 'map_columns',
  PREVIEW = 'preview',
  CONFIRM = 'confirm'
}

interface CensusImportWizardProps {
  onComplete: (censusId: string) => void;
  onCancel: () => void;
}
```

#### `ColumnMapper`
Interactive column mapping interface:

```tsx
interface ColumnMapperProps {
  headers: string[];
  sampleRows: object[];
  detectedMapping?: ColumnMapping;
  savedMappings: SavedMapping[];
  onMappingChange: (mapping: ColumnMapping) => void;
  onSelectSavedMapping: (mappingId: string) => void;
}
```

**Features**:
- Dropdown for each target field showing available CSV columns
- Sample data preview for each mapping (shows first 3 values from selected column)
- Visual indicator for auto-detected vs. manual mappings
- Quick-select from saved mappings dropdown
- HCE mode toggle (column vs. threshold)

#### `ImportPreview`
Data validation and preview table:

```tsx
interface ImportPreviewProps {
  employees: ParsedEmployee[];
  validation: ValidationSummary;
  onConfirm: () => void;
  onBack: () => void;
}
```

**Features**:
- Sortable/filterable table of parsed employees
- Color-coded rows: green (valid), yellow (warning), red (error)
- Expandable issue details per employee
- Summary statistics (HCE count, NHCE count, total comp)
- Filter toggle: Show all / Warnings only / Errors only

#### `SaveMappingDialog`
Save mapping for future use:

```tsx
interface SaveMappingDialogProps {
  mapping: ColumnMapping;
  existingMappings: SavedMapping[];
  onSave: (name: string) => void;
  onCancel: () => void;
}
```

### Example Import Flow

1. **User uploads CSV** from ADP payroll export
2. **System detects headers**: `["EmpID", "FullName", "AnnualSalary", "HCE_Flag", "Match_YTD", "PreTax_YTD", "Roth_YTD"]`
3. **Auto-mapping suggests**:
   - `employee_id` → "EmpID"
   - `compensation` → "AnnualSalary"
   - `is_hce` → "HCE_Flag"
   - `er_match_amt` → "Match_YTD"
   - `ee_pre_tax_amt` → "PreTax_YTD"
   - `ee_roth_amt` → "Roth_YTD"
4. **User reviews mapping**, adjusts if needed
5. **System parses and validates**: Shows 150 valid, 3 warnings, 0 errors
6. **User reviews warnings**: 3 employees with compensation > $500K
7. **User confirms import**, optionally saves mapping as "ADP Export Q4 2024"
8. **Census created** with census_id, ready for analysis

---

## Data Models

### Pydantic Models (Backend)

```python
# models/census.py
class Employee(BaseModel):
    employee_id: str
    is_hce: bool
    compensation: float = Field(ge=0)
    er_match_amt: float = Field(ge=0, default=0)
    ee_pre_tax_amt: float = Field(ge=0, default=0)
    ee_after_tax_amt: float = Field(ge=0, default=0)
    ee_roth_amt: float = Field(ge=0, default=0)

class CensusSummary(BaseModel):
    census_id: str
    total_employees: int
    hce_count: int
    nhce_count: int
    total_compensation: float
    hce_avg_compensation: float
    nhce_avg_compensation: float
    nhce_acp: float  # Baseline NHCE ACP

class CensusUploadResponse(BaseModel):
    census_id: str
    summary: CensusSummary
    employees: list[Employee]
    warnings: list[str] = []

# models/census_import.py
class ColumnMapping(BaseModel):
    employee_id: str
    compensation: str
    hce_mode: Literal['column', 'compensation_threshold']
    is_hce: str | None = None
    hce_threshold: float | None = None
    er_match_amt: str | None = None
    ee_pre_tax_amt: str | None = None
    ee_roth_amt: str | None = None
    ee_after_tax_amt: str | None = None
    compensation_multiplier: float = 1.0
    trim_whitespace: bool = True
    skip_rows: int = 0

class SavedMapping(BaseModel):
    id: str
    name: str
    mapping: ColumnMapping
    created_at: datetime
    last_used_at: datetime
    use_count: int = 0

class ImportPreviewResponse(BaseModel):
    file_id: str
    headers: list[str]
    sample_rows: list[dict]
    row_count: int
    detected_mapping: ColumnMapping | None
    saved_mappings: list[SavedMapping]

class ValidationIssue(BaseModel):
    field: str
    severity: Literal['error', 'warning', 'info']
    message: str
    value: Any | None = None

class ParsedEmployee(BaseModel):
    row_number: int
    employee: Employee
    status: Literal['valid', 'warning', 'error']
    issues: list[ValidationIssue]

class ValidationSummary(BaseModel):
    valid_count: int
    warning_count: int
    error_count: int
    issues: list[ValidationIssue]

class ImportParseResponse(BaseModel):
    employees: list[ParsedEmployee]
    validation: ValidationSummary
    summary: CensusSummary

class ImportConfirmRequest(BaseModel):
    file_id: str
    mapping: ColumnMapping
    save_mapping_as: str | None = None

class ImportConfirmResponse(BaseModel):
    census_id: str
    summary: CensusSummary
    employees: list[Employee]
    mapping_saved: bool

# models/scenario.py
class ScenarioInput(BaseModel):
    census_id: str
    adoption_rate: float = Field(ge=0, le=1)
    contribution_rate: float = Field(ge=0, le=100)
    plan_year: int = Field(ge=2024, le=2030)

class GridInput(BaseModel):
    census_id: str
    adoption_rates: list[float]
    contribution_rates: list[float]
    plan_year: int = 2024

# models/results.py
class ScenarioResult(BaseModel):
    adoption_rate: float
    contribution_rate: float
    pass_fail: Literal["PASS", "FAIL"]
    risk_zone: Literal["SAFE", "RISK", "FAIL"]
    nhce_acp: float
    hce_acp: float
    max_allowed_acp: float
    margin: float
    limit_a: float
    limit_b: float
    passed_limit_a: bool
    passed_limit_b: bool
    hce_contributors: int
    nhce_contributors: int
    total_mega_backdoor: float
    hce_total_contributions: float
    nhce_total_contributions: float

class GridSummary(BaseModel):
    total_scenarios: int
    pass_count: int
    fail_count: int
    risk_count: int
    pass_rate: float
    first_failure: dict | None
    max_safe_contribution: float
    worst_margin: float

class GridResult(BaseModel):
    analysis_id: str
    census_id: str
    plan_year: int
    created_at: datetime
    scenarios: list[ScenarioResult]
    summary: GridSummary

# models/configuration.py
class PlanLimits(BaseModel):
    plan_year: int
    compensation_limit: float      # § 401(a)(17)
    elective_deferral_limit: float # § 402(g)
    annual_additions_limit: float  # § 415(c)
    catch_up_limit: float          # § 414(v)
    super_catch_up_limit: float | None  # SECURE 2.0

class ACPTestParams(BaseModel):
    multiplier: float = 1.25
    adder: float = 2.0

class ScenarioDefaults(BaseModel):
    adoption_rates: list[float]
    contribution_rates: list[float]
    acp_test: ACPTestParams
```

### TypeScript Types (Frontend)

```typescript
// types/census.ts
interface Employee {
  employee_id: string;
  is_hce: boolean;
  compensation: number;
  er_match_amt: number;
  ee_pre_tax_amt: number;
  ee_after_tax_amt: number;
  ee_roth_amt: number;
}

interface CensusSummary {
  census_id: string;
  total_employees: number;
  hce_count: number;
  nhce_count: number;
  total_compensation: number;
  hce_avg_compensation: number;
  nhce_avg_compensation: number;
  nhce_acp: number;
}

// types/results.ts
type PassFail = 'PASS' | 'FAIL';
type RiskZone = 'SAFE' | 'RISK' | 'FAIL';

interface ScenarioResult {
  adoption_rate: number;
  contribution_rate: number;
  pass_fail: PassFail;
  risk_zone: RiskZone;
  nhce_acp: number;
  hce_acp: number;
  max_allowed_acp: number;
  margin: number;
  limit_a: number;
  limit_b: number;
  passed_limit_a: boolean;
  passed_limit_b: boolean;
  hce_contributors: number;
  nhce_contributors: number;
  total_mega_backdoor: number;
}

interface GridResult {
  analysis_id: string;
  census_id: string;
  plan_year: number;
  created_at: string;
  scenarios: ScenarioResult[];
  summary: GridSummary;
}

// types/heatmap.ts
interface HeatmapData<T> {
  rows: string[];
  columns: string[];
  data: T[][];
}

type PassFailHeatmap = HeatmapData<PassFail>;
type MarginHeatmap = HeatmapData<number> & { min: number; max: number; avg: number };
type RiskZoneHeatmap = HeatmapData<RiskZone> & { counts: { safe: number; risk: number; fail: number } };
```

---

## Frontend Pages & Components

### Pages

#### 1. Dashboard (`/`)
**Purpose**: Executive summary with key metrics and quick actions

**Components**:
- `MetricsPanel` - Pass rate, risk count, max safe contribution
- `MiniHeatmap` - Condensed pass/fail grid
- `QuickActions` - Upload census, run analysis, export
- `RecentAnalyses` - List of recent analysis runs
- `CensusList` - Available census files with quick stats

#### 2. Census Import (`/import`)
**Purpose**: Multi-step wizard for importing and mapping census data from CSV

**Components**:
- `CensusImportWizard` - Main wizard container managing step flow
- `FileUploader` - Drag-and-drop CSV upload with file validation
- `ColumnMapper` - Interactive mapping interface with:
  - Field dropdowns showing available CSV columns
  - Sample data preview for selected mappings
  - HCE mode toggle (column vs. threshold)
  - Saved mapping quick-select
- `ImportPreview` - Validation results table with:
  - Color-coded rows (valid/warning/error)
  - Expandable issue details
  - Filter controls (All/Warnings/Errors)
  - Summary statistics
- `SaveMappingDialog` - Save mapping for future imports
- `StepIndicator` - Visual progress through wizard steps

**User Flow**:
1. Upload → 2. Map Columns → 3. Preview & Validate → 4. Confirm Import

#### 3. Analysis (`/analysis`)
**Purpose**: Configure and run scenario analysis

**Components**:
- `CensusSelector` - Choose from imported census data
- `ScenarioForm` - Configure adoption/contribution rates
- `PlanYearSelector` - Select plan year
- `RunAnalysisButton` - Execute analysis
- `ResultsTable` - Detailed scenario results
- `ProgressIndicator` - Analysis progress for large grids

#### 4. Heatmaps (`/heatmaps`)
**Purpose**: Visualize results across scenario grid

**Components**:
- `HeatmapTabs` - Toggle Pass/Fail, Margins, Risk Zones
- `InteractiveHeatmap` - Clickable cells with tooltips
- `ColorLegend` - Explain color coding
- `ScenarioDetail` - Side panel with clicked scenario details
- `MarginDistribution` - Histogram of margins

#### 5. Employee Detail (`/employees`)
**Purpose**: View employee-level impact of mega-backdoor

**Components**:
- `EmployeeTable` - Sortable/filterable employee list
- `EmployeeCard` - Individual employee breakdown
- `ContributionBreakdown` - Visual of contribution components
- `Section415Status` - Limit compliance indicator
- `HCEvsNHCEComparison` - Side-by-side group comparison

#### 6. Configuration (`/config`)
**Purpose**: View and manage plan settings

**Components**:
- `PlanYearTabs` - Switch between years
- `LimitsTable` - Display IRS limits
- `ScenarioDefaultsEditor` - Customize grid parameters
- `ACPTestParams` - View/edit test parameters
- `SavedMappingsManager` - View, edit, delete saved column mappings

#### 7. Export (`/export`)
**Purpose**: Generate reports and export data

**Components**:
- `ExportFormatSelector` - CSV, Excel, PDF options
- `ExportOptionsForm` - Include charts, summary, etc.
- `PreviewPanel` - Preview export content
- `DownloadButton` - Trigger export

### Reusable Components

#### `Heatmap`
```tsx
interface HeatmapProps<T> {
  data: HeatmapData<T>;
  renderCell: (value: T, row: string, col: string) => ReactNode;
  onCellClick?: (row: string, col: string, value: T) => void;
  colorScale?: (value: T) => string;
  showLabels?: boolean;
}
```

#### `RiskBadge`
```tsx
interface RiskBadgeProps {
  status: 'PASS' | 'FAIL' | 'SAFE' | 'RISK';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}
```

#### `MetricCard`
```tsx
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
}
```

---

## Implementation Phases

### Phase 1: Backend Foundation (Week 1-2)
**Goal**: Port core logic to FastAPI with full test coverage

**Tasks**:
1. Initialize FastAPI project structure
2. Port `acp_calculator.py` → `services/acp_calculator.py`
3. Port `contribution_limits.py` → `services/contribution_limits.py`
4. Port `constants.py` → `config.py` with Pydantic Settings
5. Create Pydantic models for all data types
6. Implement `/api/analysis/scenario` endpoint
7. Implement `/api/analysis/grid` endpoint
8. Port and adapt existing tests
9. Add API integration tests
10. Set up DuckDB for census storage

**Deliverables**:
- Working API for single scenario and grid analysis
- 100% test pass rate
- OpenAPI documentation

### Phase 2: Full Backend API (Week 2-3)
**Goal**: Complete all API endpoints

**Tasks**:
1. Implement census upload/management endpoints
2. Implement heatmap data endpoints
3. Implement employee-level analysis endpoints
4. Implement configuration endpoints
5. Implement export endpoints (CSV, Excel)
6. Add request validation and error handling
7. Add API rate limiting
8. Add response caching for expensive operations

**Deliverables**:
- Complete REST API
- Export functionality
- Performance optimization

### Phase 3: Frontend Foundation (Week 3-4)
**Goal**: Set up React app with core pages

**Tasks**:
1. Initialize Vite + React + TypeScript project
2. Configure Tailwind CSS
3. Set up React Router
4. Create base UI components (Button, Card, Input, Table)
5. Set up React Query for API integration
6. Create API client services
7. Implement Dashboard page (basic version)
8. Implement Analysis page
9. Add loading states and error handling

**Deliverables**:
- Working frontend with basic analysis flow
- Connected to backend API

### Phase 4: Visualizations (Week 4-5)
**Goal**: Implement interactive heatmaps and charts

**Tasks**:
1. Implement `Heatmap` component with Recharts
2. Create pass/fail heatmap view
3. Create margins heatmap view
4. Create risk zones heatmap view
5. Add cell click interactions
6. Implement scenario detail panel
7. Add margin distribution chart
8. Implement responsive design

**Deliverables**:
- Full heatmap visualization page
- Interactive scenario exploration

### Phase 5: Employee Analysis & Export (Week 5-6)
**Goal**: Complete remaining features

**Tasks**:
1. Implement Employee Detail page
2. Create employee table with sorting/filtering
3. Implement § 415(c) status indicators
4. Create export page
5. Implement CSV/Excel download
6. Add PDF report generation (optional)
7. Polish Dashboard with all metrics

**Deliverables**:
- Complete feature set
- Export functionality

### Phase 6: Polish & Deploy (Week 6-7)
**Goal**: Production-ready deployment

**Tasks**:
1. Add comprehensive error handling
2. Implement loading skeletons
3. Add keyboard navigation
4. Optimize bundle size
5. Create Docker configurations
6. Set up CI/CD pipeline
7. Write deployment documentation
8. Performance testing and optimization

**Deliverables**:
- Production-ready application
- Docker images
- CI/CD pipeline

---

## Testing Strategy

### Backend Testing
```
tests/
├── unit/
│   ├── test_acp_calculator.py    # Core calculation logic
│   ├── test_contribution_limits.py # § 415(c) validation
│   └── test_models.py            # Pydantic model validation
├── integration/
│   ├── test_api_analysis.py      # Analysis endpoints
│   ├── test_api_census.py        # Census management
│   └── test_api_export.py        # Export functionality
└── fixtures/
    ├── census_small.csv          # 12 employees
    ├── census_large.csv          # 1000 employees
    └── expected_results.json     # Known-good outputs
```

**Coverage Target**: 90%+ for services, 80%+ overall

### Frontend Testing
```
src/
├── __tests__/
│   ├── components/
│   │   ├── Heatmap.test.tsx
│   │   └── RiskBadge.test.tsx
│   ├── pages/
│   │   ├── Dashboard.test.tsx
│   │   └── Analysis.test.tsx
│   └── services/
│       └── api.test.ts
└── e2e/
    ├── analysis-flow.spec.ts
    └── export-flow.spec.ts
```

**Tools**: Vitest (unit), Playwright (e2e)

### Regression Testing
- Compare new API outputs against known-good results from existing CLI tool
- Automated comparison script for all 30 default scenarios
- Mathematical accuracy validation (<0.01% variance)

---

## Migration Plan

### Data Migration
1. Existing `census.csv` format fully supported
2. Add migration script for any saved results
3. Support CSV upload via drag-and-drop

### Feature Parity Checklist
- [ ] NHCE ACP calculation
- [ ] HCE ACP calculation with mega-backdoor
- [ ] IRS two-part test (Limit A/B)
- [ ] § 415(c) contribution limits
- [ ] § 401(a)(17) compensation cap
- [ ] Random HCE selection (reproducible)
- [ ] Pass/fail heatmap
- [ ] Margin heatmap
- [ ] Risk zone classification
- [ ] Employee-level breakdown
- [ ] CSV export
- [ ] Excel export with formatting
- [ ] Key insights extraction
- [ ] Multi-year support (2024, 2025, 2026)

### Deprecation Plan
1. **Phase 1**: New system runs in parallel with Streamlit
2. **Phase 2**: Feature parity confirmed, Streamlit deprecated
3. **Phase 3**: Streamlit code archived, new system primary

---

## Non-Functional Requirements

### Performance
- Single scenario analysis: <500ms
- Full grid (30 scenarios): <3s
- Large census (100K employees): <30s
- Frontend initial load: <2s
- API response time P95: <1s

### Security
- CORS configuration for frontend origin
- Input validation on all endpoints
- Rate limiting (100 requests/minute)
- No PII stored beyond session
- HTTPS in production

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatible
- Color-blind friendly palettes

### Browser Support
- Chrome 90+
- Firefox 90+
- Safari 15+
- Edge 90+

---

## Open Questions

1. **Authentication**: Is user authentication required, or is this internal-only?
2. **Multi-tenancy**: Should different plan sponsors have isolated data?
3. **Historical Data**: Should we store analysis history beyond session?
4. **Real-time Updates**: Any need for WebSocket-based live updates?
5. **PDF Reports**: Priority of PDF export vs. Excel-only?

---

## Appendix

### Existing Code to Preserve
- `acp_calculator.py`: Core calculation logic (340 lines)
- `contribution_limits.py`: § 415(c) validation (183 lines)
- `constants.py`: Configuration loading (61 lines)
- `plan_constants.yaml`: IRS limits data

### Existing Code to Deprecate
- `run_analysis.py`: CLI orchestration → API endpoints
- `enhancements.py`: ASCII visualization → React components
- `streamlit_dashboard.py`: Streamlit UI → React app
- `employee_level_analysis.py`: Partial port to API

### Reference Documents
- `docs/ACP-MVP-PRD.md`: Original 2-hour MVP spec
- `docs/ACP-Enterprise-PRD-v1.0.md`: Full production requirements
- `CLAUDE.md`: Project context and business rules


/speckit.specify
Build an “ACP Sensitivity Analyzer” web product that helps retirement-plan analysts quickly understand how after-tax (“mega backdoor”) employee contributions affect ACP test outcomes. Users should be able to upload a participant census, run a single scenario or a grid of scenarios (adoption rate x contribution rate) for a selected plan year, and see PASS/FAIL plus the limiting test result and margin. Prioritize auditability, reproducibility, and domain correctness for HCE/NHCE treatment. The product should support both interactive UI usage and programmatic API usage. Define user personas, core jobs-to-be-done, key user journeys, and clear acceptance criteria. Out of scope: authentication/multi-tenancy unless required for the MVP.

/speckit.specify
Add “Census Management” as a first-class capability: users can create, list, view, and delete imported censuses. The system must store a census and its import metadata (e.g., mapping used, row counts, summary stats) so analyses can be rerun consistently. Define what a census contains (required fields vs optional contribution fields), how HCE status is determined (explicit flag vs compensation-threshold mode), and what summary metrics must be available immediately after import. Include clear acceptance criteria and error cases (missing IDs, invalid values, etc.).  We should be able to name the client or name the census. 

/speckit.specify
Implement a flexible “CSV Import + Column Mapping Wizard” experience: upload a CSV, preview headers + sample rows, auto-suggest mappings, allow the user to map columns to required census fields, validate the parsed data, and confirm import. Support saving a mapping profile by name for reuse on future uploads. Include duplicate detection, severity-based validation (error/warn/info), and a pre-commit preview that makes it obvious what will be imported and what will be rejected. Define acceptance criteria for the full wizard flow, including usability constraints (fast, minimal steps) and clear user-facing messages for validation issues.

/speckit.specify
Provide “Scenario Analysis” features: run a single scenario (one adoption rate + one contribution rate) and return the full ACP outcome details needed for interpretation (PASS/FAIL, NHCE ACP, HCE ACP, max allowed ACP, margin, which limit bound, contributor counts, and total mega-backdoor amount). Also support running a grid of scenarios and returning a structured results set plus a compact summary (pass/fail/risk counts, first failure point, max safe contribution, worst margin). Define what “RISK” means (e.g., near the boundary) and the acceptance criteria for correctness, determinism, and performance expectations.

/speckit.specify
Create “Heatmap Exploration” for scenario grids: users can view Pass/Fail, Margin, and Risk Zone heatmaps over the (adoption x contribution) grid, hover for tooltips, and click a cell to see the underlying scenario detail. Define what each heatmap must display, how the axes are labeled, how missing/invalid scenarios are handled, and what summary stats are shown (min/max/avg margin, safe/risk/fail counts). Include accessibility requirements (keyboard nav + non-color cues) and acceptance criteria.

/speckit.specify
Add “Employee-Level Impact” views: for a selected scenario, the user can see employee-level details separated by HCE and NHCE, including compensation, existing contributions (by type), §415(c) limit, available room, and computed mega-backdoor amount. The experience should support sorting/filtering and make it easy to explain why the ACP result looks the way it does (e.g., how many HCEs are constrained by limits). Define acceptance criteria for transparency, interpretability, and exportability of these details.

/speckit.specify
Provide “Exports & Reporting”: users can export analysis results (and optionally employee-level detail) as CSV and Excel, with consistent structure that downstream users can use in other tooling. Optionally support a PDF report with an executive summary and key charts if it materially improves stakeholder communication. Define export contents, naming conventions, whether exports include the original census/mapping metadata, and acceptance criteria (reproducible outputs, stable schemas, no leaking unnecessary PII).

/speckit.specify
Define “Plan-Year Configuration & Regulatory Limits” behavior: the product supports multiple plan years and surfaces the relevant IRS limits used in calculations (e.g., §401(a)(17), §402(g), §415(c), catch-up rules). Users should be able to see which constants were applied to a given analysis and adjust scenario-default grids (adoption rates and contribution rates) without changing core rules. Specify guardrails so changes are explicit and traceable. Include acceptance criteria for auditability and preventing silent rule drift.

/speckit.specify
Set explicit “Non-Functional + Compliance Requirements” for the MVP: performance targets (single scenario, grid, and large census), privacy constraints (minimize/avoid storing unnecessary PII), reliability (tests + regression checks against known-good outputs), and UX quality (fast initial load, clear error states). Include acceptance criteria and a definition of done that is measurable.