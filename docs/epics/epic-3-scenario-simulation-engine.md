# Epic 3: Scenario Simulation Engine

**Priority**: High  
**Status**: Pending  
**Estimated Time**: 30 minutes  
**Dependencies**: Epic 2 (Core ACP Calculation Engine)

## Overview

Build a grid-based scenario simulation engine that tests multiple combinations of HCE adoption rates and contribution percentages. This engine will run hundreds of ACP test scenarios to identify pass/fail boundaries and risk zones.

## User Story

As a **plan consultant**, I need **comprehensive scenario analysis** so that I can **identify safe contribution limits and adoption thresholds for mega-backdoor Roth implementations**.

## Acceptance Criteria

### AC1: Scenario Grid Definition
- [ ] Define adoption rate grid: [0.0, 0.25, 0.50, 0.75, 1.0] (0%, 25%, 50%, 75%, 100%)
- [ ] Define contribution rate grid: [2.0, 4.0, 6.0, 8.0, 10.0, 12.0] (2% to 12%)
- [ ] Calculate total scenarios: 5 × 6 = 30 combinations
- [ ] Validate grid parameters are within reasonable bounds

### AC2: Monte Carlo HCE Selection
- [ ] Use numpy.random.choice() for HCE selection
- [ ] Set random seed (42) for reproducible results
- [ ] Calculate n_adopters = int(len(hce_data) × adoption_rate)
- [ ] Handle edge cases (0 adopters, all adopters)
- [ ] Ensure same HCEs selected across contribution rates for consistent comparison

### AC3: Batch Scenario Execution
- [ ] Loop through all adoption rate × contribution rate combinations
- [ ] Call `calculate_acp_for_scenario()` for each combination
- [ ] Collect results in structured list
- [ ] Display real-time progress indicators
- [ ] Track scenario numbers and completion status

### AC4: Progress Reporting
- [ ] Show total scenarios to be run
- [ ] Display current scenario number and parameters
- [ ] Show pass/fail status with visual indicators (✓/✗)
- [ ] Include margin information for each scenario
- [ ] Provide completion summary

### AC5: Results DataFrame Creation
- [ ] Convert results list to pandas DataFrame
- [ ] Ensure all columns are properly typed
- [ ] Sort results by adoption rate, then contribution rate
- [ ] Validate no missing or corrupted data

## Technical Details

### Core Function Signature
```python
def run_scenario_grid(df_census, adoption_rates, contribution_rates):
    """
    Run all scenario combinations and return results
    
    Args:
        df_census: DataFrame with employee data
        adoption_rates: List of adoption rates (0.0-1.0)
        contribution_rates: List of contribution percentages (0.0-25.0)
    
    Returns:
        pd.DataFrame: Results with all scenarios
    """
```

### Grid Configuration
```python
# MVP grid for 2-hour implementation
adoption_rates = [0.0, 0.25, 0.50, 0.75, 1.0]
contribution_rates = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
total_scenarios = len(adoption_rates) * len(contribution_rates)  # 30
```

### Progress Display Format
```
Running 30 scenarios...
──────────────────────────────────────────────────
✓ Scenario 1/30: 0% adoption, 2.0% contribution → PASS (margin: 2.17%)
✓ Scenario 2/30: 0% adoption, 4.0% contribution → PASS (margin: 2.17%)
✗ Scenario 15/30: 50% adoption, 6.0% contribution → FAIL (margin: -1.25%)
```

### Monte Carlo Implementation
```python
np.random.seed(42)  # Reproducible results
hce_data = df[df['is_hce'] == True]
n_adopters = int(len(hce_data) * adoption_rate)
adopters = np.random.choice(hce_data.index, size=n_adopters, replace=False)
```

## Definition of Done

- [ ] `run_scenario_grid()` function executes all parameter combinations
- [ ] Monte Carlo selection works correctly for all adoption rates
- [ ] Progress indicators display clearly during execution
- [ ] Results DataFrame contains all expected columns and data types
- [ ] Function handles edge cases (0% adoption, 100% adoption)
- [ ] Performance acceptable for MVP (30 scenarios in <10 seconds)

## Test Cases

### Test Case 1: Full Grid Execution
- **Input**: Standard 5×6 grid (30 scenarios)
- **Expected**: All scenarios complete successfully
- **Validation**: DataFrame has 30 rows, all columns populated

### Test Case 2: Zero Adoption Scenarios
- **Input**: adoption_rate = 0.0, all contribution rates
- **Expected**: All scenarios PASS (no after-tax contributions)
- **Validation**: pass_fail = 'PASS' for all 0% adoption scenarios

### Test Case 3: High Adoption + High Contribution
- **Input**: adoption_rate = 1.0, contribution_rate = 12.0
- **Expected**: Most likely to FAIL
- **Validation**: Verify failure occurs and margin is negative

### Test Case 4: Edge Case - Single HCE Plan
- **Input**: Census with only 1 HCE
- **Expected**: Function handles fractional adopters correctly
- **Validation**: n_adopters calculation works for small populations

## Performance Requirements

- **Execution Time**: <10 seconds for 30 scenarios
- **Memory Usage**: <100MB for DataFrame operations
- **Scalability**: Support up to 1000 scenarios (future enhancement)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Long execution time | Medium | Profile code, optimize DataFrame operations |
| Memory usage with large grids | Low | Use generators for large scenario sets |
| Random seed inconsistency | Medium | Document seed usage, allow configuration |
| Progress display issues | Low | Test on different terminals/environments |

## Future Enhancements

- **Finer Grid Resolution**: 0.1% increments for adoption and contribution rates
- **Custom Grid Ranges**: Allow user-defined parameter ranges
- **Parallel Processing**: Multi-core execution for large scenario sets
- **Scenario Filtering**: Skip obviously passing/failing scenarios
- **Adaptive Grids**: Focus resolution on boundary regions

## Notes

- Monte Carlo ensures realistic HCE selection patterns
- Grid size optimized for 2-hour MVP timeline
- Progress indicators crucial for user experience
- Results structure enables easy analysis and visualization
- Consider memory usage for larger grids in production