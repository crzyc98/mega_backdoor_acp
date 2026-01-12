# Epic 5: Testing & Validation

**Priority**: Medium  
**Status**: Pending  
**Estimated Time**: 10 minutes  
**Dependencies**: Epic 4 (Output & Visualization)

## Overview

Implement comprehensive testing and validation to ensure the ACP calculation engine produces accurate, IRS-compliant results. This epic focuses on verifying core logic, testing edge cases, and validating against manual calculations.

## User Story

As a **compliance officer**, I need **validated and tested ACP calculations** so that I can **trust the tool's results for regulatory compliance and client recommendations**.

## Acceptance Criteria

### AC1: Core Logic Validation
- [ ] Verify 0% adoption scenarios all return PASS
- [ ] Confirm higher contribution percentages increase failure likelihood
- [ ] Validate NHCE ACP calculation matches manual computation
- [ ] Check HCE ACP calculation includes both match and after-tax contributions
- [ ] Ensure pass/fail determination follows IRS two-part test

### AC2: Edge Case Testing
- [ ] Test scenario with all HCEs contributing maximum
- [ ] Test scenario with no HCEs contributing (0% adoption)
- [ ] Test scenario with single HCE contributing
- [ ] Handle plans with only 1 HCE or 1 NHCE
- [ ] Validate fractional adopter calculations

### AC3: Mathematical Accuracy
- [ ] Compare calculated results to manual Excel calculations
- [ ] Verify floating-point precision (3 decimal places)
- [ ] Check rounding consistency across all calculations
- [ ] Validate percentage calculations (compensation ratios)
- [ ] Ensure margin calculations (max_allowed - hce_acp) are correct

### AC4: Data Integrity Testing
- [ ] Test with missing compensation data
- [ ] Test with zero compensation values
- [ ] Test with negative match_dollars
- [ ] Validate boolean conversion for is_hce field
- [ ] Check for data type consistency

### AC5: Boundary Testing
- [ ] Test with maximum contribution percentages (25%)
- [ ] Test with minimum contribution percentages (0.1%)
- [ ] Test with 100% adoption rate
- [ ] Test with fractional adoption rates
- [ ] Validate extreme compensation values

## Technical Details

### Core Validation Functions
```python
def validate_core_logic():
    """Test fundamental ACP calculation logic"""
    # Test 1: Zero adoption should always pass
    result = calculate_acp_for_scenario(df_census, 0.0, 10.0)
    assert result['pass_fail'] == 'PASS'
    
    # Test 2: NHCE ACP calculation
    expected_nhce_acp = manual_nhce_calculation(df_census)
    assert abs(result['nhce_acp'] - expected_nhce_acp) < 0.001

def test_edge_cases():
    """Test boundary conditions and edge cases"""
    # Test single HCE scenario
    single_hce_census = create_single_hce_census()
    result = calculate_acp_for_scenario(single_hce_census, 1.0, 12.0)
    assert result['n_hce_contributors'] == 1
```

### Manual Calculation Verification
```python
def manual_nhce_calculation(df):
    """Manual NHCE ACP calculation for validation"""
    nhce_data = df[df['is_hce'] == False]
    contribution_rates = nhce_data['match_dollars'] / nhce_data['compensation'] * 100
    return contribution_rates.mean()
```

### Test Data Scenarios
```python
# Test scenarios with known outcomes
test_scenarios = [
    {'adoption': 0.0, 'contribution': 10.0, 'expected': 'PASS'},
    {'adoption': 1.0, 'contribution': 2.0, 'expected': 'PASS'},
    {'adoption': 1.0, 'contribution': 15.0, 'expected': 'FAIL'},
    {'adoption': 0.5, 'contribution': 6.0, 'expected': 'FAIL'}
]
```

## Definition of Done

- [ ] All core logic validation tests pass
- [ ] Edge case testing covers boundary conditions
- [ ] Manual calculation verification confirms accuracy
- [ ] Data integrity tests handle invalid inputs gracefully
- [ ] Boundary testing validates extreme scenarios
- [ ] Test documentation includes expected vs. actual results

## Test Cases

### Test Case 1: Zero Adoption Validation
- **Input**: adoption_rate=0.0, any contribution_percent
- **Expected**: All scenarios return PASS
- **Validation**: No after-tax contributions means HCE ACP = baseline match only

### Test Case 2: Manual Calculation Verification
- **Input**: Test census with known values
- **Expected**: NHCE ACP = (4500+4250+4000+3750+3500+3250+3000+2750)/(90000+85000+80000+75000+70000+65000+60000+55000)*100 = 4.167%
- **Validation**: Calculation matches manual computation

### Test Case 3: IRS Two-Part Test
- **Input**: NHCE ACP = 4.167%
- **Expected**: limit_a = 4.167 × 1.25 = 5.209%, limit_b = 4.167 + 2.0 = 6.167%
- **Validation**: max_allowed_hce_acp = min(5.209, 6.167) = 5.209%

### Test Case 4: Single HCE Plan
- **Input**: Census with 1 HCE, 5 NHCEs
- **Expected**: Function handles single-employee HCE group
- **Validation**: HCE ACP calculation works with n=1

### Test Case 5: Extreme Contribution Rate
- **Input**: 100% adoption, 25% contribution
- **Expected**: Very likely to FAIL
- **Validation**: HCE ACP significantly exceeds limits

## Validation Checklist

### Mathematical Validation
- [ ] NHCE ACP = average of (match_dollars / compensation * 100)
- [ ] HCE ACP = average of ((match_dollars + after_tax_dollars) / compensation * 100)
- [ ] After-tax dollars = compensation × (contribution_percent / 100)
- [ ] Two-part test: min(NHCE_ACP × 1.25, NHCE_ACP + 2.0)
- [ ] Pass condition: HCE_ACP ≤ max_allowed_hce_acp

### Data Validation
- [ ] Boolean conversion: 'TRUE' → True, 'FALSE' → False
- [ ] Numeric precision: 3 decimal places for percentages
- [ ] Error handling: Missing data raises appropriate exceptions
- [ ] Type consistency: All percentages as floats

## Performance Validation

- [ ] Single scenario calculation: <1ms
- [ ] Full 30-scenario grid: <10 seconds
- [ ] Memory usage: <50MB for standard census
- [ ] No memory leaks during repeated runs

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Calculation errors | High | Manual verification against IRS examples |
| Floating-point precision | Medium | Use consistent rounding strategies |
| Edge case failures | Medium | Comprehensive boundary testing |
| Performance degradation | Low | Profile critical calculation paths |

## Regulatory Compliance

- [ ] Calculations match IRS Revenue Procedure 2019-40
- [ ] Two-part test implementation follows IRC §401(m)
- [ ] HCE definition aligns with current thresholds
- [ ] Rounding follows standard actuarial practices

## Documentation Requirements

- [ ] Test cases documented with expected outcomes
- [ ] Manual calculation examples provided
- [ ] Edge case scenarios explained
- [ ] Performance benchmarks recorded
- [ ] Validation results summarized

## Notes

- Focus on accuracy over speed for MVP
- Document any deviations from IRS examples
- Keep test data simple but comprehensive
- Prioritize tests that catch common errors
- Consider automated testing for future iterations