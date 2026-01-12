# ACP Sensitivity Analyzer for Mega-Backdoor Roth Contributions

## Project Overview

This project implements an ACP (Actual Contribution Percentage) sensitivity analyzer to help plan sponsors evaluate nondiscrimination test risks when offering mega-backdoor Roth conversions. The tool models thousands of scenarios across HCE (Highly Compensated Employee) adoption rates and contribution levels.

## Key Components

### MVP Implementation (Phase 1)
- **Purpose**: 2-hour prototype to validate core ACP calculation logic
- **Key Files**: `run_analysis.py`, `census.csv`
- **Capabilities**:
  - Read employee census data
  - Simulate HCE mega-backdoor Roth adoption scenarios
  - Calculate ACP test pass/fail for each scenario
  - Output results to CSV with summary matrix

### Enterprise Implementation (Full PRD)
- **Purpose**: Production-ready system for TEM analytics team
- **Tech Stack**: DuckDB, dbt, Dagster, FastAPI, Evidence.dev
- **Features**:
  - Handle 100K+ employee censuses
  - 1000+ scenario combinations
  - Real-time compliance dashboards
  - QMAC/QNEC optimization
  - Integration with existing PlanWise Navigator

## Development Setup

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install pandas numpy
```

### Running the MVP
```bash
# Run the basic analysis
python run_analysis.py

# Expected outputs:
# - Console: Pass/fail matrix display
# - acp_results.csv: Detailed scenario results
# - acp_heatmap.csv: Visualization data (if enhanced)
```

## Key Business Rules

### ACP Test Logic
- **NHCE ACP**: Average of non-HCE contribution percentages
- **HCE ACP**: Average of HCE contribution percentages (match + after-tax)
- **Pass Criteria**: HCE ACP ≤ min(NHCE ACP × 1.25, NHCE ACP + 2.0)

### Scenario Parameters
- **Adoption Rates**: 0%, 25%, 50%, 75%, 100% of HCEs participate
- **Contribution Rates**: 2%, 4%, 6%, 8%, 10%, 12% of compensation
- **Selection Method**: Monte Carlo with random HCE selection

## Testing Guidelines

### Core Validation
- 0% adoption → All scenarios should PASS
- Higher contribution % → More likely to FAIL
- NHCE ACP calculation matches manual calculations

### Edge Cases
- All HCEs contribute maximum
- No HCEs contribute  
- Single HCE contributes

## Common Commands

### Development
```bash
# Run linting (if configured)
python -m flake8 .

# Run tests (if configured)
python -m pytest

# Install additional packages
pip install <package_name>
pip freeze > requirements.txt
```

### Data Management
```bash
# Validate census data format
head -5 census.csv

# Check results
head -10 acp_results.csv
```

## Project Structure

```
mega_backdoor_acp/
├── docs/
│   ├── ACP-MVP-PRD.md           # 2-hour MVP specification
│   └── ACP-Enterprise-PRD-v1.0.md  # Full production requirements
├── venv/                        # Python virtual environment
├── run_analysis.py              # Main MVP script (when created)
├── census.csv                   # Sample employee data (when created)
├── acp_results.csv              # Output results (generated)
└── README.md                    # Project readme
```

## Regulatory Context

- **IRC §401(m)**: ACP test requirements
- **IRS Revenue Procedure 2019-40**: Current vs. prior year testing
- **SECURE Act 2.0**: Recent changes to testing rules
- **Mega-backdoor Roth**: After-tax 401(k) → Roth conversion strategy

## Success Metrics

- **Speed**: 500+ scenarios in <2 minutes
- **Accuracy**: <0.1% variance from manual calculations
- **Risk Quantification**: Transform uncertainty into actionable thresholds
- **Compliance**: IRS-compliant calculations with full audit trail

## Next Steps

1. **Expand scenarios**: Finer grids (1% increments)
2. **Add match formulas**: Variable match rates
3. **Include QMAC/QNEC**: Corrective contribution modeling
4. **Build UI**: Web interface or Streamlit app
5. **Scale infrastructure**: DuckDB + dbt as specified in full PRD