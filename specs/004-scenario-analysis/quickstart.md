# Quickstart: Scenario Analysis

**Feature**: 004-scenario-analysis
**Date**: 2026-01-12

## Overview

This guide shows how to use the enhanced Scenario Analysis API to run ACP test scenarios and interpret results.

---

## Prerequisites

1. A loaded census with HCE/NHCE participant data
2. API server running (see main project README)
3. Census ID from a successful upload

---

## Running a Single Scenario

### Basic Request

```bash
curl -X POST http://localhost:8000/api/v2/analysis/scenario \
  -H "Content-Type: application/json" \
  -d '{
    "census_id": "550e8400-e29b-41d4-a716-446655440000",
    "adoption_rate": 0.5,
    "contribution_rate": 0.06
  }'
```

### Response

```json
{
  "status": "PASS",
  "nhce_acp": 0.035,
  "hce_acp": 0.042,
  "max_allowed_acp": 0.04375,
  "margin": 0.00175,
  "limiting_bound": "MULTIPLE",
  "hce_contributor_count": 25,
  "nhce_contributor_count": 180,
  "total_mega_backdoor_amount": 375000.00,
  "seed_used": 1736640000,
  "adoption_rate": 0.5,
  "contribution_rate": 0.06,
  "error_message": null,
  "debug_details": null
}
```

### Understanding the Response

| Field | Meaning |
|-------|---------|
| `status` | PASS (safe), RISK (passing but close), FAIL (over threshold), ERROR (can't calculate) |
| `nhce_acp` | Average ACP for non-highly compensated employees |
| `hce_acp` | Average ACP for highly compensated employees (includes simulated mega-backdoor) |
| `max_allowed_acp` | The threshold HCE ACP cannot exceed |
| `margin` | How far below (positive) or above (negative) the threshold |
| `limiting_bound` | MULTIPLE (1.25× test) or ADDITIVE (+2.0 test) determined the threshold |
| `total_mega_backdoor_amount` | Total simulated contributions across all adopting HCEs (dollars) |

---

## Running with Reproducibility

To ensure identical results across runs, provide an explicit seed:

```bash
curl -X POST http://localhost:8000/api/v2/analysis/scenario \
  -H "Content-Type: application/json" \
  -d '{
    "census_id": "550e8400-e29b-41d4-a716-446655440000",
    "adoption_rate": 0.5,
    "contribution_rate": 0.06,
    "seed": 42
  }'
```

The `seed_used` field in the response confirms which seed was applied.

---

## Getting Debug Details

For audit purposes or debugging, request detailed calculation breakdown:

```bash
curl -X POST http://localhost:8000/api/v2/analysis/scenario \
  -H "Content-Type: application/json" \
  -d '{
    "census_id": "550e8400-e29b-41d4-a716-446655440000",
    "adoption_rate": 0.5,
    "contribution_rate": 0.06,
    "include_debug": true
  }'
```

Response includes `debug_details`:

```json
{
  "status": "PASS",
  "...": "...",
  "debug_details": {
    "selected_hce_ids": ["P001", "P003", "P007"],
    "hce_contributions": [
      {
        "id": "P001",
        "compensation_cents": 15000000,
        "existing_acp_contributions_cents": 450000,
        "simulated_mega_backdoor_cents": 900000,
        "individual_acp": 0.09
      }
    ],
    "nhce_contributions": [...],
    "intermediate_values": {
      "hce_acp_sum": 2.52,
      "hce_count": 50,
      "nhce_acp_sum": 6.30,
      "nhce_count": 180,
      "threshold_multiple": 0.04375,
      "threshold_additive": 0.055
    }
  }
}
```

---

## Running a Grid Analysis

Explore multiple scenarios at once:

```bash
curl -X POST http://localhost:8000/api/v2/analysis/grid \
  -H "Content-Type: application/json" \
  -d '{
    "census_id": "550e8400-e29b-41d4-a716-446655440000",
    "adoption_rates": [0.25, 0.5, 0.75, 1.0],
    "contribution_rates": [0.04, 0.06, 0.08, 0.10],
    "seed": 12345
  }'
```

### Grid Response

```json
{
  "scenarios": [
    {"status": "PASS", "adoption_rate": 0.25, "contribution_rate": 0.04, "...": "..."},
    {"status": "PASS", "adoption_rate": 0.25, "contribution_rate": 0.06, "...": "..."},
    {"status": "RISK", "adoption_rate": 0.75, "contribution_rate": 0.08, "...": "..."},
    {"status": "FAIL", "adoption_rate": 1.0, "contribution_rate": 0.10, "...": "..."}
  ],
  "summary": {
    "pass_count": 10,
    "risk_count": 4,
    "fail_count": 2,
    "error_count": 0,
    "total_count": 16,
    "first_failure_point": {
      "adoption_rate": 1.0,
      "contribution_rate": 0.08
    },
    "max_safe_contribution": 0.06,
    "worst_margin": -0.0025
  },
  "seed_used": 12345
}
```

### Understanding the Summary

| Field | Meaning |
|-------|---------|
| `pass_count` | Scenarios with comfortable margin (> 0.50 pp) |
| `risk_count` | Scenarios passing but with tight margin (≤ 0.50 pp) |
| `fail_count` | Scenarios that fail the ACP test |
| `first_failure_point` | Lowest contribution rate that fails at highest tested adoption |
| `max_safe_contribution` | Highest contribution rate that passes at 100% adoption |
| `worst_margin` | The tightest margin across all scenarios (most negative = worst failure) |

---

## Status Classification

| Status | Condition | Action |
|--------|-----------|--------|
| **PASS** | Margin > 0.50 pp | Safe to proceed |
| **RISK** | 0 < Margin ≤ 0.50 pp | Caution - small changes could cause failure |
| **FAIL** | Margin ≤ 0 | Would fail ACP test - adjust parameters |
| **ERROR** | Cannot calculate | Check census data (missing HCEs/NHCEs) |

---

## Python Usage Example

```python
import requests

def run_scenario(census_id: str, adoption: float, contribution: float, seed: int = None):
    """Run a single ACP scenario."""
    payload = {
        "census_id": census_id,
        "adoption_rate": adoption,
        "contribution_rate": contribution,
    }
    if seed:
        payload["seed"] = seed

    response = requests.post(
        "http://localhost:8000/api/v2/analysis/scenario",
        json=payload
    )
    return response.json()

def run_grid(census_id: str, adoptions: list, contributions: list, seed: int = None):
    """Run a grid of ACP scenarios."""
    payload = {
        "census_id": census_id,
        "adoption_rates": adoptions,
        "contribution_rates": contributions,
    }
    if seed:
        payload["seed"] = seed

    response = requests.post(
        "http://localhost:8000/api/v2/analysis/grid",
        json=payload
    )
    return response.json()

# Example usage
result = run_scenario(
    census_id="550e8400-e29b-41d4-a716-446655440000",
    adoption=0.5,
    contribution=0.06,
    seed=42
)
print(f"Status: {result['status']}, Margin: {result['margin']:.4f}")

# Grid analysis
grid = run_grid(
    census_id="550e8400-e29b-41d4-a716-446655440000",
    adoptions=[0.25, 0.5, 0.75, 1.0],
    contributions=[0.04, 0.06, 0.08, 0.10],
    seed=12345
)
print(f"Summary: {grid['summary']['pass_count']} pass, {grid['summary']['fail_count']} fail")
print(f"Max safe contribution at full adoption: {grid['summary']['max_safe_contribution']}")
```

---

## Common Error Scenarios

### Census Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "Census with ID 'invalid-id' not found"
}
```

### Invalid Parameters

```json
{
  "error": "VALIDATION_ERROR",
  "message": "adoption_rate must be between 0.0 and 1.0"
}
```

### Edge Case (No HCEs)

```json
{
  "status": "ERROR",
  "error_message": "ACP test not applicable: no HCE participants in census",
  "nhce_acp": null,
  "hce_acp": null,
  "...": "..."
}
```

---

## Performance Notes

- **Single scenario**: Target < 100ms for 10K participants
- **Grid (100 scenarios)**: Target < 5 seconds for 10K participants
- **Debug mode**: Adds overhead; use only when needed for audit/troubleshooting
- Performance may degrade for very large censuses (> 10K participants)
