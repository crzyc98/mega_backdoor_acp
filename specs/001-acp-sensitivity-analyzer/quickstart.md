# Quickstart: ACP Sensitivity Analyzer

**Feature**: 001-acp-sensitivity-analyzer
**Date**: 2026-01-12

## Prerequisites

- Python 3.11+
- pip (Python package manager)

## Installation

```bash
# Clone the repository (if not already done)
cd /workspaces/mega_backdoor_acp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Setup

```bash
# Create source directories
mkdir -p src/{core,storage,api/routes,ui/pages,ui/components}
mkdir -p tests/{unit,integration,contract}
mkdir -p data

# Initialize Python packages
touch src/__init__.py
touch src/core/__init__.py
touch src/storage/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/ui/__init__.py
touch src/ui/pages/__init__.py
touch src/ui/components/__init__.py
```

## Running the Application

### Start the API Server

```bash
# From repository root
cd src/api
uvicorn main:app --reload --port 8000

# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Start the Streamlit UI

```bash
# From repository root
cd src/ui
streamlit run app.py --server.port 8501

# UI will be available at http://localhost:8501
```

### Run Both (Development)

```bash
# Terminal 1: API
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Streamlit
streamlit run src/ui/app.py --server.port 8501
```

## Quick Test

### Using the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Upload census (replace with your file)
curl -X POST http://localhost:8000/api/v1/census \
  -F "file=@census.csv" \
  -F "plan_year=2025" \
  -F "name=Test Census"

# Run single scenario
curl -X POST http://localhost:8000/api/v1/census/{census_id}/analysis \
  -H "Content-Type: application/json" \
  -d '{"adoption_rate": 50, "contribution_rate": 6}'

# Run grid analysis
curl -X POST http://localhost:8000/api/v1/census/{census_id}/grid \
  -H "Content-Type: application/json" \
  -d '{
    "adoption_rates": [0, 25, 50, 75, 100],
    "contribution_rates": [2, 4, 6, 8, 10, 12]
  }'
```

### Using the UI

1. Open http://localhost:8501
2. Upload a census CSV file
3. Configure scenario parameters
4. Click "Run Analysis"
5. View results and export

## Sample Census CSV Format

```csv
Employee ID,HCE Status,Annual Compensation,Current Deferral Rate,Current Match Rate,Current After-Tax Rate
EMP001,TRUE,250000,6.0,3.0,0.0
EMP002,TRUE,180000,5.0,2.5,0.0
EMP003,FALSE,75000,4.0,2.0,0.0
EMP004,FALSE,65000,3.0,1.5,0.0
EMP005,FALSE,55000,0.0,0.0,0.0
```

**Required Columns**:
- `Employee ID`: Unique identifier (will be hashed for storage)
- `HCE Status`: TRUE/FALSE or 1/0
- `Annual Compensation`: Positive number
- `Current Deferral Rate`: 0-100
- `Current Match Rate`: >= 0
- `Current After-Tax Rate`: >= 0

**PII Handling**: Employee ID is hashed on import. Names, SSN, and other PII columns are automatically stripped.

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_acp_calculator.py -v
```

## Configuration

### Environment Variables

```bash
# Database path (default: data/acp_analyzer.db)
export ACP_DATABASE_PATH=data/acp_analyzer.db

# API rate limit (default: 60/minute)
export ACP_RATE_LIMIT="60/minute"

# Default seed (default: timestamp-based)
export ACP_DEFAULT_SEED=42
```

### Plan Year Limits

IRS limits are configured in `src/core/constants.py` and loaded from `plan_constants.yaml`:

```yaml
annual_limits:
  2025:
    hce_threshold: 160000
    compensation_limit_401a17: 345000
    annual_additions_limit_415c: 70000
```

## Troubleshooting

### Common Issues

**"No module named 'src'"**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/workspaces/mega_backdoor_acp"
```

**"Census upload fails with validation error"**
- Check CSV column names match exactly (case-sensitive)
- Ensure no empty rows
- Verify numeric columns contain valid numbers

**"Analysis returns unexpected PASS/FAIL"**
- Verify HCE Status column (TRUE/FALSE, not Yes/No)
- Check compensation values are in dollars (not cents)
- Review the seed value for reproducibility

### Database Reset

```bash
# Delete and recreate database
rm data/acp_analyzer.db
# Database will be recreated on next API/UI start
```

## Next Steps

1. Review the full [spec.md](./spec.md) for requirements
2. Check [data-model.md](./data-model.md) for entity details
3. See [contracts/openapi.yaml](./contracts/openapi.yaml) for API documentation
4. Run `/speckit.tasks` to generate implementation tasks
