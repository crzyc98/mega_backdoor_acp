# Epic 2: Core ACP Calculation Engine

**Priority**: High  
**Status**: Pending  
**Estimated Time**: 40 minutes  
**Dependencies**: Epic 1 (Data Management & Setup)

## Overview

Implement the IRS-compliant ACP (Actual Contribution Percentage) test calculation engine. This is the core business logic that determines whether mega-backdoor Roth adoption scenarios pass or fail nondiscrimination testing.

## User Story

As a **compliance analyst**, I need **accurate ACP test calculations** so that I can **determine if HCE after-tax contributions will cause the plan to fail nondiscrimination tests**.

## Acceptance Criteria

### AC1: Data Loading & Validation
- [ ] Load census data from CSV file
- [ ] Validate required columns exist
- [ ] Convert `is_hce` string to boolean
- [ ] Handle missing or invalid data gracefully
- [ ] Display summary statistics (total employees, HCEs, NHCEs)

### AC2: NHCE ACP Calculation
- [ ] Filter employees where `is_hce = FALSE`
- [ ] Calculate contribution percentage: `match_dollars / compensation * 100`
- [ ] Compute average NHCE ACP across all non-HCEs
- [ ] Round to 3 decimal places for precision

### AC3: HCE ACP Calculation with After-Tax
- [ ] Filter employees where `is_hce = TRUE`
- [ ] Add simulated after-tax contributions based on scenario parameters
- [ ] Calculate total contributions: `match_dollars + after_tax_dollars`
- [ ] Compute contribution percentage: `total_contributions / compensation * 100`
- [ ] Compute average HCE ACP across all HCEs

### AC4: IRS Compliance Test Logic
- [ ] Implement two-part test: min(NHCE_ACP × 1.25, NHCE_ACP + 2.0)
- [ ] Apply limit_a = NHCE_ACP × ACP_MULTIPLIER (1.25)
- [ ] Apply limit_b = NHCE_ACP + ACP_ADDER (2.0)
- [ ] Set max_allowed_hce_acp = min(limit_a, limit_b)
- [ ] Determine pass/fail: HCE_ACP ≤ max_allowed_hce_acp

### AC5: Scenario Result Structure
- [ ] Return structured dictionary with all key metrics
- [ ] Include input parameters (adoption rate, contribution percentage)
- [ ] Include calculated values (NHCE ACP, HCE ACP, limits)
- [ ] Include test result (PASS/FAIL) and margin
- [ ] Include number of contributing HCEs

## Technical Details

### Core Function Signature
```python
def calculate_acp_for_scenario(df_census, hce_adoption_rate, hce_contribution_percent):
    """
    Calculate ACP test results for a single scenario
    
    Args:
        df_census: DataFrame with employee data
        hce_adoption_rate: Float 0.0-1.0 (percentage adopting as decimal)
        hce_contribution_percent: Float 0.0-25.0 (contribution percentage)
    
    Returns:
        dict: Scenario results with all metrics
    """
```

### IRS Regulation Implementation
```python
# Two-part ACP test (IRC §401(m))
limit_a = nhce_acp * ACP_MULTIPLIER  # 1.25 factor
limit_b = nhce_acp + ACP_ADDER       # 2.0 percentage point adder
max_allowed_hce_acp = min(limit_a, limit_b)
passed = hce_acp <= max_allowed_hce_acp
```

### Expected Output Structure
```python
{
    'hce_adoption_rate': 0.50,
    'hce_contribution_percent': 6.0,
    'nhce_acp': 4.167,
    'hce_acp': 8.750,
    'max_allowed_hce_acp': 6.167,
    'margin': -2.583,
    'pass_fail': 'FAIL',
    'n_hce_contributors': 2
}
```

## Definition of Done

- [ ] `load_census()` function validates and loads test data
- [ ] `calculate_acp_for_scenario()` function implements IRS-compliant logic
- [ ] All calculations match manual verification
- [ ] Error handling for edge cases (no HCEs, no NHCEs)
- [ ] Function returns structured results in expected format
- [ ] Code includes appropriate comments and docstrings

## Test Cases

### Test Case 1: Zero Adoption
- **Input**: adoption_rate=0.0, contribution_percent=10.0
- **Expected**: All scenarios should PASS (no after-tax contributions)

### Test Case 2: Full Adoption Low Contribution
- **Input**: adoption_rate=1.0, contribution_percent=2.0
- **Expected**: Likely PASS (low contribution amounts)

### Test Case 3: Full Adoption High Contribution
- **Input**: adoption_rate=1.0, contribution_percent=12.0
- **Expected**: Likely FAIL (high contribution amounts)

### Test Case 4: Edge Case - Single HCE
- **Input**: Census with 1 HCE, adoption_rate=1.0
- **Expected**: Function handles single-employee groups

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Calculation errors | High | Manual verification against IRS examples |
| Division by zero | Medium | Add checks for empty employee groups |
| Floating point precision | Low | Use consistent rounding (3 decimal places) |
| Invalid input parameters | Medium | Add input validation and bounds checking |

## Regulatory References

- **IRC §401(m)**: ACP test requirements
- **IRS Revenue Procedure 2019-40**: Current vs. prior year testing methods
- **ERISA Section 401(a)(4)**: Nondiscrimination requirements

## Notes

- Focus on current-year ACP testing method for MVP
- Prior-year testing can be added in future iterations
- Ensure calculations handle both integer and float inputs
- Random seed (42) used for reproducible HCE selection