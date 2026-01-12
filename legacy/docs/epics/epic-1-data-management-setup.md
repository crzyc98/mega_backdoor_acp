# Epic 1: Data Management & Setup

**Priority**: High  
**Status**: Pending  
**Estimated Time**: 10 minutes  
**Dependencies**: None

## Overview

Set up the foundational data structures and environment needed for the ACP sensitivity analyzer MVP. This epic focuses on creating test data, installing dependencies, and establishing the basic project structure.

## User Story

As a **plan analyst**, I need **test census data and a configured environment** so that I can **run ACP sensitivity scenarios on realistic employee data**.

## Acceptance Criteria

### AC1: Test Census Data Creation
- [ ] Create `census.csv` with 12 employee records
- [ ] Include 4 HCEs (highly compensated employees)
- [ ] Include 8 NHCEs (non-highly compensated employees)
- [ ] Required columns: `employee_id`, `is_hce`, `compensation`, `match_dollars`
- [ ] Realistic compensation ranges ($55K-$250K)
- [ ] Match contributions follow standard employer formulas

### AC2: Environment Setup
- [ ] Virtual environment activated
- [ ] Install pandas for data manipulation
- [ ] Install numpy for numerical calculations
- [ ] Verify Python 3.x compatibility

### AC3: Project Constants
- [ ] Define ACP_MULTIPLIER = 1.25 (IRS regulation)
- [ ] Define ACP_ADDER = 2.00 (IRS regulation)
- [ ] Set output file name: 'acp_results.csv'

## Technical Details

### Sample Census Data Structure
```csv
employee_id,is_hce,compensation,match_dollars
1,TRUE,250000,7500
2,TRUE,200000,7500
3,TRUE,180000,7500
4,TRUE,175000,7500
5,FALSE,90000,4500
6,FALSE,85000,4250
7,FALSE,80000,4000
8,FALSE,75000,3750
9,FALSE,70000,3500
10,FALSE,65000,3250
11,FALSE,60000,3000
12,FALSE,55000,2750
```

### Required Dependencies
```bash
pip install pandas numpy
```

## Definition of Done

- [ ] `census.csv` file created with valid test data
- [ ] All required Python packages installed
- [ ] Constants defined and accessible
- [ ] Environment can successfully import pandas and numpy
- [ ] Test data validates against business rules (HCE thresholds, compensation ranges)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Invalid test data | High | Validate HCE status matches compensation thresholds |
| Missing dependencies | Medium | Use requirements.txt for reproducible installs |
| Data format issues | Medium | Test CSV parsing before full implementation |

## Notes

- HCE threshold typically $150K+ for 2025
- Match contributions should reflect realistic employer formulas
- Test data should represent diverse scenarios for thorough testing
- Keep data simple but realistic for MVP validation