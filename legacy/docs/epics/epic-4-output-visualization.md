# Epic 4: Output & Visualization

**Priority**: Medium  
**Status**: Pending  
**Estimated Time**: 25 minutes  
**Dependencies**: Epic 3 (Scenario Simulation Engine)

## Overview

Create comprehensive output and visualization capabilities for ACP sensitivity analysis results. This includes console summaries, CSV exports, pass/fail matrices, and key insights extraction to help analysts quickly understand risk zones.

## User Story

As a **plan analyst**, I need **clear visual summaries and exportable results** so that I can **quickly identify safe contribution limits and communicate findings to clients**.

## Acceptance Criteria

### AC1: CSV Export Functionality
- [ ] Export detailed results to `acp_results.csv`
- [ ] Include all scenario parameters and calculated metrics
- [ ] Use appropriate column headers and data types
- [ ] Ensure file can be opened in Excel/Google Sheets
- [ ] Display confirmation message with file location

### AC2: Console Summary Matrix
- [ ] Create pass/fail matrix with adoption rates as columns
- [ ] Show contribution percentages as rows
- [ ] Use visual symbols (✓ for PASS, ✗ for FAIL)
- [ ] Include clear column and row headers
- [ ] Format for readability in terminal display

### AC3: Pivot Table Generation
- [ ] Create pivot table with adoption rates as columns
- [ ] Use contribution percentages as rows
- [ ] Support both text (PASS/FAIL) and numeric (1/0) formats
- [ ] Enable easy filtering and analysis
- [ ] Maintain proper data types for calculations

### AC4: Key Insights Extraction
- [ ] Identify first failure scenario (lowest risk threshold)
- [ ] Determine maximum safe contribution percentage
- [ ] Classify scenarios into safe/risk/fail zones
- [ ] Generate actionable recommendations
- [ ] Handle edge cases (all pass, all fail)

### AC5: Formatted Console Output
- [ ] Professional header with run timestamp
- [ ] Progress indicators during execution
- [ ] Section dividers and clear formatting
- [ ] Summary statistics and key metrics
- [ ] Analysis completion confirmation

## Technical Details

### CSV Export Structure
```csv
hce_adoption_rate,hce_contribution_percent,nhce_acp,hce_acp,max_allowed_hce_acp,margin,pass_fail,n_hce_contributors
0.0,2.0,4.167,4.167,6.167,2.000,PASS,0
0.25,6.0,4.167,7.292,6.167,-1.125,FAIL,1
```

### Console Matrix Format
```
SUMMARY MATRIX (PASS = ✓, FAIL = ✗)
==================================================
Contrib %    0% adopt   25% adopt  50% adopt  75% adopt  100% adopt
----------------------------------------------------------------------
     2.0%       ✓         ✓         ✓         ✓         ✓
     4.0%       ✓         ✓         ✓         ✓         ⚠
     6.0%       ✓         ✓         ⚠         ✗         ✗
     8.0%       ✓         ⚠         ✗         ✗         ✗
    10.0%       ✓         ✗         ✗         ✗         ✗
    12.0%       ✓         ✗         ✗         ✗         ✗
```

### Pivot Table Function
```python
def create_summary_pivot(results_df):
    """Create pivot table summary for easy visualization"""
    pivot = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )
    return pivot
```

### Key Insights Logic
```python
# Find first failure
fail_scenarios = results_df[results_df['pass_fail'] == 'FAIL']
if len(fail_scenarios) > 0:
    first_fail = fail_scenarios.iloc[0]
    
# Find maximum safe contribution
max_safe = results_df[results_df['pass_fail'] == 'PASS']['hce_contribution_percent'].max()
```

## Definition of Done

- [ ] `acp_results.csv` file created with all scenario data
- [ ] Console displays formatted pass/fail matrix
- [ ] `create_summary_pivot()` function generates pivot tables
- [ ] Key insights automatically extracted and displayed
- [ ] Professional formatting with headers and sections
- [ ] All output functions handle edge cases gracefully

## Test Cases

### Test Case 1: Full Results Export
- **Input**: Complete 30-scenario results DataFrame
- **Expected**: CSV file with 30 rows, all columns populated
- **Validation**: File opens correctly in Excel

### Test Case 2: Matrix Display
- **Input**: Mixed pass/fail scenarios
- **Expected**: Clear visual matrix with symbols
- **Validation**: Matrix matches underlying data

### Test Case 3: All Pass Scenarios
- **Input**: Conservative parameters (all scenarios pass)
- **Expected**: "All scenarios PASS! Plan has significant headroom."
- **Validation**: No failure analysis displayed

### Test Case 4: All Fail Scenarios
- **Input**: Aggressive parameters (all scenarios fail)
- **Expected**: First failure analysis still works
- **Validation**: Appropriate warning messages

## Visual Examples

### Terminal Header
```
==================================================
ACP SENSITIVITY ANALYZER - MVP
Run time: 2025-07-08 14:30:15
==================================================
```

### Key Insights Section
```
==================================================
KEY INSIGHTS
==================================================
⚠️  First failure at: 25% adoption, 6.0% contribution
✓ Safe zone: Up to 4.0% contribution at any adoption rate
```

## Performance Requirements

- **CSV Export**: <1 second for 30 scenarios
- **Console Display**: Immediate rendering
- **Pivot Tables**: <1 second generation
- **Memory Usage**: <10MB for formatting operations

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CSV formatting issues | Medium | Test with Excel/Google Sheets |
| Console display problems | Low | Test on different terminal sizes |
| Large dataset formatting | Low | Implement pagination for large results |
| Unicode symbol issues | Low | Provide ASCII fallback options |

## Future Enhancements

- **Interactive Visualizations**: Plotly/Matplotlib charts
- **PDF Report Generation**: Professional client reports
- **Excel Integration**: Direct .xlsx export with formatting
- **Dashboard Integration**: Web-based visualization
- **Custom Color Coding**: Risk-based color schemes

## Notes

- Prioritize clarity over complexity for MVP
- Ensure output works in standard terminal environments
- CSV format should be Excel-compatible
- Visual indicators improve quick decision-making
- Keep formatting code separate from calculation logic