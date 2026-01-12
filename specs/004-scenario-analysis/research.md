# Research: Scenario Analysis

**Feature**: 004-scenario-analysis
**Date**: 2026-01-12

## Research Summary

This document captures technical decisions and research findings for the Scenario Analysis feature. The feature extends existing calculation infrastructure rather than introducing new technologies, so research focuses on implementation patterns and edge case handling.

---

## 1. RISK Threshold Implementation

### Decision
Use a constant `RISK_THRESHOLD = Decimal("0.50")` in `src/core/constants.py` for the margin threshold that distinguishes PASS from RISK status.

### Rationale
- Centralizes the threshold value for easy adjustment if business requirements change
- Follows existing pattern in codebase (e.g., `ACP_MULTIPLIER`, `ACP_ADDER` in constants.py)
- Using `Decimal` maintains precision consistency with ACP calculations

### Alternatives Considered
1. **Hardcoded in status logic**: Rejected because it would be scattered and hard to change
2. **User-configurable parameter**: Rejected per spec assumption ("fixed and not user-configurable")
3. **Environment variable**: Rejected as unnecessary complexity for a compliance constant

---

## 2. Status Classification Logic

### Decision
Implement status as a derived property calculated from margin value:

```python
def classify_status(margin: Decimal) -> Literal["PASS", "RISK", "FAIL"]:
    if margin <= 0:
        return "FAIL"
    elif margin <= RISK_THRESHOLD:
        return "RISK"
    else:
        return "PASS"
```

ERROR status is set at a higher level when edge cases prevent calculation.

### Rationale
- Single source of truth (margin determines status)
- Testable in isolation
- Matches spec definition exactly

### Alternatives Considered
1. **Dual-check (margin + boolean)**: Rejected as redundant
2. **Status as input**: Rejected as it should be derived, not specified

---

## 3. Limiting Bound Terminology

### Decision
Change `limiting_test` field values from `"1.25x"` / `"+2.0"` to `"MULTIPLE"` / `"ADDITIVE"` per spec.

### Rationale
- Spec explicitly defines these terms
- More descriptive of the test type
- Backward compatibility note: Existing code uses `"1.25x"` / `"+2.0"` - migration needed

### Migration Plan
1. Add new constants `LIMITING_BOUND_MULTIPLE = "MULTIPLE"` and `LIMITING_BOUND_ADDITIVE = "ADDITIVE"`
2. Update `apply_acp_test()` to use new values
3. Update existing API consumers (if any) or provide deprecation notice

---

## 4. Grid Summary Calculation

### Decision
Compute `GridSummary` as a pure function that takes `list[ScenarioResult]` and returns summary statistics.

### Algorithm for `first_failure_point`:
```python
def find_first_failure_point(results: list[ScenarioResult]) -> tuple[float, float] | None:
    failures = [r for r in results if r.status == "FAIL"]
    if not failures:
        return None
    # Sort by adoption rate (desc), then contribution rate (asc)
    # "First failure" = highest adoption where failure occurs, lowest contrib at that adoption
    failures.sort(key=lambda r: (-r.adoption_rate, r.contribution_rate))
    return (failures[0].adoption_rate, failures[0].contribution_rate)
```

### Algorithm for `max_safe_contribution`:
```python
def find_max_safe_contribution(results: list[ScenarioResult], adoption_rates: list[float]) -> float | None:
    max_adoption = max(adoption_rates)
    passing_at_max = [r for r in results if r.adoption_rate == max_adoption and r.status in ("PASS", "RISK")]
    if not passing_at_max:
        return None
    return max(r.contribution_rate for r in passing_at_max)
```

### Rationale
- Pure functions are easily testable
- No caching needed since grid results are computed once per request
- ERROR scenarios excluded from pass/fail counts

---

## 5. Debug Mode Implementation

### Decision
Add optional `debug_details` field to `ScenarioResult` that is populated only when `include_debug=True` in the request.

### Structure
```python
@dataclass
class DebugDetails:
    selected_hce_ids: list[str]
    hce_contributions: list[ParticipantContribution]
    nhce_contributions: list[ParticipantContribution]
    intermediate_values: dict[str, Decimal]

@dataclass
class ParticipantContribution:
    id: str
    compensation: int  # cents
    existing_acp_contributions: int  # cents (match + after_tax)
    simulated_mega_backdoor: int  # cents (0 for non-adopters and NHCEs)
```

### Rationale
- Keeps normal responses lean (no bloat for typical use)
- Provides full audit trail when needed
- `intermediate_values` captures both threshold calculations

### Performance Consideration
Debug mode adds O(n) overhead for participant iteration. Performance targets (100ms single, 5s grid) assume debug mode OFF. Debug mode may exceed these targets and should document this.

---

## 6. Edge Case: Zero Participants

### Decision
Return ERROR status with descriptive message for census edge cases:

| Condition | Error Message |
|-----------|---------------|
| Zero HCEs | "ACP test not applicable: no HCE participants in census" |
| Zero NHCEs | "ACP test cannot be calculated: no NHCE participants (NHCE ACP undefined)" |
| Zero total | "ACP test cannot be calculated: census is empty" |

### Rationale
- Spec requires ERROR status with error_message
- Clear, actionable messages help users understand why calculation failed
- Distinguishes between "test doesn't apply" vs "test cannot compute"

---

## 7. Rounding for Adoption Count

### Decision
Use Python's `round()` (banker's rounding) for calculating number of adopting HCEs:

```python
n_adopters = round(len(hce_ids) * adoption_rate)
```

### Rationale
- Matches spec requirement: "rounds the selected count to nearest integer"
- Banker's rounding minimizes systematic bias
- Existing code uses `int()` which truncates - need to update

### Edge Cases
| HCE Count | Adoption Rate | Result |
|-----------|---------------|--------|
| 5 | 50% | 2 or 3 (2.5 rounds to 2 with banker's rounding) |
| 3 | 33% | 1 (0.99 rounds to 1) |
| 1 | 50% | 0 or 1 (0.5 rounds to 0 with banker's) |

Note: Banker's rounding rounds 0.5 to nearest even. Consider using `round()` with explicit `ndigits=0` and standard rounding if determinism across Python versions is a concern.

---

## 8. Decimal Precision

### Decision
Maintain existing precision strategy:
- Internal calculations: 6 decimal places (`Decimal("0.000001")`)
- Display/API output: 2 decimal places for percentages, full precision for margin
- Use `ROUND_HALF_UP` for final rounding

### Rationale
- Matches spec variance tolerance (< 0.001 percentage points)
- Consistent with existing `acp_calculator.py` implementation
- Extra internal precision prevents accumulation errors in grid scenarios

---

## 9. Total Mega-Backdoor Amount Calculation

### Decision
Calculate as sum of simulated contributions across selected HCEs:

```python
total_mega_backdoor = sum(
    int(Decimal(p["compensation_cents"]) * contribution_rate / 100)
    for p in participants
    if p["internal_id"] in adopting_hce_ids
)
```

Return value in cents (consistent with existing monetary values) or dollars (per spec "dollars").

### Clarification Needed
Spec says "dollars" but existing code uses cents internally. Decision: Store in cents internally, convert to dollars in API response schema.

---

## 10. Backward Compatibility

### Decision
Maintain backward compatibility through:
1. Keep existing `ScenarioResult` dataclass signature (add new fields with defaults)
2. Existing `run_single_scenario()` continues to work; add `run_single_scenario_v2()` for enhanced version
3. API versioning: Add `/v2/analysis/scenario` endpoint; keep existing endpoint unchanged

### Rationale
- Existing UI and tests continue to work
- Gradual migration path for consumers
- Clear separation between legacy and enhanced behavior

---

## Dependencies

No new external dependencies required. Feature uses existing:
- `numpy` for seeded random selection
- `pydantic` for request/response validation
- `fastapi` for API endpoints
- Standard library `dataclasses` and `decimal`
