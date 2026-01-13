# Research: Employee-Level Impact Views

**Feature**: 006-employee-level-impact
**Date**: 2026-01-13

## Research Tasks

### 1. §415(c) Limit Calculation Integration

**Question**: How to compute and display §415(c) limits and available room for each participant?

**Decision**: Use the existing `get_415c_limit(plan_year)` function from `src/core/constants.py` to retrieve the annual additions limit. Calculate available room as:

```
available_room = 415c_limit - (deferral_amount + match_amount + after_tax_amount + mega_backdoor_amount)
```

**Rationale**:
- The `get_415c_limit` function already exists and loads limits from `plan_constants.yaml`
- Participant contribution data is available from the `Participant` model
- Deferral amount can be derived from `deferral_rate × compensation`
- This approach is consistent with how limits are handled elsewhere in the codebase

**Alternatives Considered**:
- Store pre-computed limits per participant: Rejected because limits are plan-year-based, not participant-specific
- Compute limits client-side: Rejected to maintain single source of truth in backend

### 2. On-Demand Employee Impact Computation

**Question**: How to compute employee-level impact without requiring debug_details from scenario execution?

**Decision**: Create a dedicated `EmployeeImpactService` that:
1. Takes ScenarioResult parameters (adoption_rate, contribution_rate, seed_used, census_id)
2. Fetches participant data from census via `ParticipantRepository`
3. Reproduces the HCE selection using the same seed
4. Computes individual contributions and constraint status
5. Returns structured `EmployeeImpactView` containing all participant details

**Rationale**:
- Decouples employee impact view from debug mode flag
- Ensures employee details are always available for any scenario
- Leverages existing `ParticipantRepository.get_as_calculation_dicts()` pattern
- Seed reproducibility is already proven in scenario analysis

**Alternatives Considered**:
- Always run scenarios with debug_details=true: Rejected because it increases storage/memory for all scenarios
- Cache debug_details in database: Rejected due to storage overhead and complexity

### 3. Constraint Status Classification

**Question**: How to classify and explain constraint status for each HCE?

**Decision**: Define four constraint states with deterministic classification logic:

| Status | Condition | Display |
|--------|-----------|---------|
| Not Selected | HCE not in selected_hce_ids | "N/A - Not Selected" |
| Unconstrained | Mega-backdoor = requested amount | Full amount shown |
| Reduced | 0 < Mega-backdoor < requested | Shows actual vs requested |
| At §415(c) Limit | Available room ≤ 0 after contributions | Shows limit hit message |

Classification algorithm:
```python
if employee_id not in selected_hce_ids:
    return "Not Selected"
requested = compensation * contribution_rate
available = 415c_limit - existing_contributions
actual = min(requested, max(0, available))
if actual == 0:
    return "At §415(c) Limit"
elif actual < requested:
    return "Reduced"
else:
    return "Unconstrained"
```

**Rationale**:
- Provides clear, actionable explanation for each state
- Matches the spec's FR-008 requirements
- Enables tooltip generation with specific dollar amounts

**Alternatives Considered**:
- Binary constrained/unconstrained: Rejected as less informative
- Additional states (e.g., "Partially Constrained"): Rejected as redundant with "Reduced"

### 4. Streamlit Table Implementation with Sorting/Filtering

**Question**: Best approach for sortable/filterable tables in Streamlit?

**Decision**: Use pandas DataFrame with Streamlit's native `st.dataframe()` plus custom filter controls:
- Convert `EmployeeImpact` list to pandas DataFrame
- Apply filters to DataFrame before display
- Use `st.dataframe(df, use_container_width=True)` for responsive display
- Streamlit 1.28+ provides built-in column sorting in dataframes

For filtering:
- Use `st.selectbox` for Constraint Status dropdown
- Use `st.number_input` for compensation/ACP range filters
- Apply filters via pandas `.query()` or boolean indexing

**Rationale**:
- pandas provides fast sorting/filtering even for 10,000 rows
- Native Streamlit dataframe supports column sorting out-of-box
- Consistent with existing UI patterns in the codebase
- No additional dependencies required

**Alternatives Considered**:
- st-aggrid: Rejected due to additional dependency and complexity
- Custom HTML table: Rejected as harder to maintain and less accessible

### 5. CSV Export Implementation

**Question**: How to implement CSV export with filter/sort state preservation?

**Decision**: Use pandas `to_csv()` with Streamlit's `st.download_button()`:
1. Capture current DataFrame state (post-filter, post-sort)
2. Convert to CSV string via `df.to_csv(index=False)`
3. Generate filename with scenario params and timestamp
4. Render download button with `st.download_button(data=csv_string, file_name=filename, mime='text/csv')`

For "Export All":
1. Concatenate HCE and NHCE DataFrames
2. Add "Group" column as first column
3. Export combined DataFrame

**Rationale**:
- Simple, no external dependencies
- Preserves exact display state (filters, sort order)
- Standard CSV format compatible with Excel/Google Sheets
- Filename includes context for traceability

**Alternatives Considered**:
- Server-side export via API: Rejected as unnecessary complexity for client-side data
- Excel format (.xlsx): Rejected to avoid openpyxl dependency

### 6. Integration with Heatmap Detail Panel

**Question**: How to add "View Employee Details" action to existing heatmap detail panel?

**Decision**: Extend `src/ui/components/heatmap_detail.py`:
1. Add "View Employee Details" button below existing content
2. Store selected scenario in `st.session_state` on click
3. Create new employee impact view that reads from session state
4. Use Streamlit's page navigation or modal pattern for transition

Navigation flow:
```
Heatmap → Click cell → Detail panel → "View Employee Details" → Employee Impact View
                                                              ↓
                                                        "Back to Heatmap" ←
```

**Rationale**:
- Minimal changes to existing heatmap component
- Session state preserves context across view transitions
- Consistent with existing Streamlit patterns in codebase

**Alternatives Considered**:
- Inline employee details in detail panel: Rejected due to space constraints
- Modal overlay: Rejected as Streamlit modal support is limited

### 7. Performance Optimization for Large Censuses

**Question**: How to ensure <2 second load time for 10,000 participants?

**Decision**: Implement these optimizations:
1. Fetch only required participant fields from database
2. Use pandas vectorized operations for calculations
3. Apply pagination (default 100 rows per page) for display
4. Cache computed impact data in session state to avoid recomputation

Performance profile (estimated):
- Database query: ~50ms for 10,000 participants
- Impact computation: ~100ms (vectorized pandas)
- DataFrame preparation: ~50ms
- Streamlit render: ~200ms
- Total: ~400ms (well under 2 second target)

**Rationale**:
- pandas vectorization is highly efficient for tabular data
- Pagination reduces DOM rendering overhead
- Session state caching prevents redundant computation on tab switches

**Alternatives Considered**:
- Pre-compute and store impact data: Rejected as adds storage complexity
- Lazy loading with virtual scroll: Rejected as overkill for 10K rows

## Summary

All technical questions have been resolved. The implementation will:
1. Use existing `get_415c_limit()` for limits
2. Create new `EmployeeImpactService` for on-demand computation
3. Classify constraints with 4 clear states
4. Use pandas DataFrames with native Streamlit sorting
5. Export via pandas `to_csv()` with download button
6. Integrate via button in heatmap detail panel
7. Optimize with vectorized operations and pagination
