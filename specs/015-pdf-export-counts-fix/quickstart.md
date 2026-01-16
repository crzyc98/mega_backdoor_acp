# Quickstart: Fix PDF/CSV Export Counts

**Feature**: 015-pdf-export-counts-fix
**Date**: 2026-01-16

## Overview

This fix ensures legacy export routes (`/export/{census_id}/pdf` and `/export/{census_id}/csv`) display post-eligibility filter counts instead of raw census counts, matching the behavior of the web application's Employee Impact page.

## Prerequisites

- Python 3.11+
- Backend dependencies installed: `cd backend && pip install -r requirements.txt`
- Test data: Census with participants that have mixed eligibility (some excluded)

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/routers/routes/export.py` | Legacy export route handlers |
| `backend/app/services/export.py` | PDF/CSV generation logic |
| `backend/app/services/acp_eligibility.py` | Eligibility filtering (reuse) |
| `backend/tests/test_export.py` | Export tests |

## Implementation Steps

### Step 1: Update Legacy PDF Route

In `backend/app/routers/routes/export.py`, the PDF route currently:
```python
# Current (line ~208)
pdf_bytes = generate_pdf_report(census_dict, results, grid_summary, excluded_count=0)
```

Change to compute post-exclusion counts using `determine_acp_inclusion()`:
```python
# After fix
from ..services.acp_eligibility import determine_acp_inclusion, plan_year_bounds

participants = participant_repo.get_by_census_id(census_id)
plan_start, plan_end = plan_year_bounds(census.plan_year)

included_hce = included_nhce = excluded = 0
for p in participants:
    result = determine_acp_inclusion(p.dob, p.hire_date, p.termination_date, plan_start, plan_end)
    if result.acp_includable:
        if p.is_hce:
            included_hce += 1
        else:
            included_nhce += 1
    else:
        excluded += 1

pdf_bytes = generate_pdf_report(
    census_dict, results, grid_summary,
    excluded_count=excluded,
    hce_count=included_hce,
    nhce_count=included_nhce
)
```

### Step 2: Update Legacy CSV Route

Similar pattern for CSV export - compute counts and pass to `format_csv_export()`.

### Step 3: Update Export Service

Modify `format_csv_export()` in `backend/app/services/export.py` to accept and display exclusion counts in the header.

### Step 4: Add Tests

Add test cases in `backend/tests/test_export.py`:
- Test with no exclusions
- Test with some exclusions
- Test with all participants excluded
- Verify mathematical consistency

## Testing

```bash
# Run export tests
cd backend && pytest tests/test_export.py -v

# Run all backend tests
cd backend && pytest tests/ -v
```

## Verification

After implementation, verify:
1. PDF export shows "Eligible HCEs", "Eligible NHCEs", "Excluded" in census summary
2. CSV header shows same post-exclusion counts
3. HCE + NHCE + Excluded = Total Participants
4. Counts match Employee Impact page for same census
