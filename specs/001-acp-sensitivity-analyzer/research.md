# Research: ACP Sensitivity Analyzer

**Feature**: 001-acp-sensitivity-analyzer
**Date**: 2026-01-12

## Overview

This document captures research findings and technology decisions for the ACP Sensitivity Analyzer implementation.

---

## 1. PII Masking Strategy

### Decision
Hash-based masking using SHA-256 with a per-census salt, producing deterministic internal IDs that cannot be reversed to original values.

### Rationale
- **Deterministic**: Same input always produces same hash, enabling audit trail correlation
- **Non-reversible**: SHA-256 is one-way; original Employee ID cannot be recovered
- **Salt per census**: Prevents rainbow table attacks; each census has unique mapping
- **Audit-friendly**: Users can verify their mapping externally if needed

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| UUID generation | Non-deterministic; cannot correlate across re-uploads |
| Simple incrementing IDs | Exposes ordering; potential information leakage |
| Encryption (AES) | Reversible by design; key management complexity |

### Implementation Notes
```python
import hashlib
import secrets

def generate_internal_id(employee_id: str, census_salt: str) -> str:
    """Generate non-reversible internal ID from employee identifier."""
    combined = f"{census_salt}:{employee_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def generate_census_salt() -> str:
    """Generate unique salt for each census upload."""
    return secrets.token_hex(16)
```

---

## 2. Seeded Random Selection for HCE Adoption

### Decision
Use numpy's `Generator` with user-configurable seed (default: timestamp-based) for reproducible HCE selection in partial adoption scenarios.

### Rationale
- **Reproducibility**: Same seed + census + parameters = identical HCE selection
- **Flexibility**: Users can explore different participant mixes by changing seed
- **Modern API**: numpy's `Generator` is preferred over legacy `np.random.seed()`
- **Audit trail**: Seed value stored with results for exact reproduction

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Deterministic selection (top N by ID) | Biased; doesn't model realistic adoption patterns |
| True random (no seed) | Not reproducible; audit failures |
| Global seed (np.random.seed) | Legacy API; state pollution across calls |

### Implementation Notes
```python
import numpy as np
from typing import List

def select_adopting_hces(
    hce_ids: List[str],
    adoption_rate: float,
    seed: int
) -> List[str]:
    """Select HCEs who adopt mega-backdoor based on adoption rate."""
    rng = np.random.default_rng(seed)
    n_adopters = int(len(hce_ids) * adoption_rate)
    return list(rng.choice(hce_ids, size=n_adopters, replace=False))
```

---

## 3. ACP Test Calculation Accuracy

### Decision
Use Python Decimal for intermediate percentage calculations, round to 2 decimal places only at display/export.

### Rationale
- **IRS compliance**: ACP test uses percentage comparisons; precision matters
- **Variance requirement**: SC-003 requires <0.01 percentage point variance from manual calculations
- **Audit reproducibility**: Exact same calculation must be reproducible

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Native float throughout | Floating-point errors accumulate; fails variance requirement |
| Round at each step | Compounds rounding errors; audit trail unclear |
| Integer cents (×10000) | Complex conversion; error-prone |

### Implementation Notes
- Store compensation and contribution amounts as integers (cents)
- Calculate individual ACPs as Decimal with 6 decimal precision
- Calculate group averages as Decimal
- Round final displayed values to 2 decimal places

### Test Formula Verification
```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_acp(contribution_cents: int, compensation_cents: int) -> Decimal:
    """Calculate individual ACP percentage."""
    if compensation_cents == 0:
        return Decimal("0")
    return (Decimal(contribution_cents) / Decimal(compensation_cents) * 100).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )

def acp_test_passes(hce_acp: Decimal, nhce_acp: Decimal) -> bool:
    """Apply IRS dual test: 1.25× OR +2.0 percentage points."""
    limit_125 = nhce_acp * Decimal("1.25")
    limit_plus2 = nhce_acp + Decimal("2.0")
    threshold = max(limit_125, limit_plus2)
    return hce_acp <= threshold
```

---

## 4. SQLite for Persistent Storage

### Decision
Use SQLite with WAL mode for census and results persistence, single-file database at `data/acp_analyzer.db`.

### Rationale
- **No multi-tenancy**: Single-user sessions don't require PostgreSQL
- **Zero config**: No separate database server to manage
- **Portable**: Database file can be backed up/moved easily
- **WAL mode**: Enables concurrent reads during analysis runs

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| PostgreSQL | Operational overhead for MVP; no multi-tenancy requirement |
| DuckDB | Excellent for analytics but less mature for OLTP patterns |
| File-based JSON | No query capability; poor for large datasets |

### Schema Design Principles
- Census data stored without PII (only internal IDs)
- Participant records in separate table with foreign key to census
- Analysis results stored with full reproducibility metadata (seed, version, timestamp)
- Indexes on census_id for efficient filtering

---

## 5. API Rate Limiting

### Decision
Simple in-memory rate limiting using `slowapi` with 60 requests/minute per client IP.

### Rationale
- **Prevents abuse**: Protects against accidental or intentional API hammering
- **Simple implementation**: No external dependencies (Redis)
- **Reasonable limit**: 60 req/min allows burst analysis while preventing overload

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Redis-based limiting | Additional infrastructure for MVP |
| Token bucket | More complex; not needed for current scale |
| No limiting | Risk of resource exhaustion |

### Implementation Notes
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/analysis/{census_id}")
@limiter.limit("60/minute")
async def run_analysis(census_id: str, ...):
    ...
```

---

## 6. CSV Parsing and Validation

### Decision
Use pandas with strict schema validation, explicit column mapping, and early failure on malformed data.

### Rationale
- **Team familiarity**: Existing legacy code uses pandas
- **Performance**: pandas handles large CSVs efficiently
- **Validation**: Easy to implement column presence/type checks

### Required Columns (FR-001)
| CSV Column | Internal Name | Type | Validation |
|------------|---------------|------|------------|
| Employee ID | employee_id | string | Non-empty, unique |
| HCE Status | is_hce | boolean | TRUE/FALSE/1/0 |
| Annual Compensation | compensation | numeric | > 0 |
| Current Deferral Rate | deferral_rate | numeric | >= 0, <= 100 |
| Current Match Rate | match_rate | numeric | >= 0 |
| Current After-Tax Rate | after_tax_rate | numeric | >= 0 |

### PII Detection Heuristics
Columns to strip (not persisted):
- Names: `name`, `first_name`, `last_name`, `full_name`
- SSN: `ssn`, `social_security`, `tax_id`
- Dates: `birth_date`, `dob`, `date_of_birth`
- Contact: `email`, `phone`, `address`, `city`, `state`, `zip`

---

## 7. Export Formats

### Decision
Support CSV (data) and PDF (formatted report) exports with full audit metadata.

### CSV Export Structure
```csv
# ACP Sensitivity Analysis Export
# Census ID: abc123
# Plan Year: 2025
# Generated: 2026-01-12T14:30:00Z
# System Version: 1.0.0
# Seed: 42

adoption_rate,contribution_rate,nhce_acp,hce_acp,threshold,margin,result,limiting_test
0.25,4.0,3.25,4.12,4.06,-0.06,FAIL,1.25x
0.25,6.0,3.25,5.45,4.06,-1.39,FAIL,1.25x
...
```

### PDF Export
- Header with census summary (participant counts, plan year)
- Heatmap visualization
- Summary statistics table
- Full scenario results table
- Footer with audit metadata (timestamp, version, seed)

---

## 8. Streamlit + FastAPI Architecture

### Decision
Run Streamlit and FastAPI as separate processes; Streamlit calls FastAPI internally for consistent business logic.

### Rationale
- **Single source of truth**: All calculations go through FastAPI
- **API-first design**: UI is just another API consumer
- **Testability**: API can be tested independently
- **Future flexibility**: UI could be replaced without affecting API

### Deployment Architecture
```
┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│    FastAPI      │
│   (port 8501)   │     │   (port 8000)   │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │     SQLite      │
                        │   (WAL mode)    │
                        └─────────────────┘
```

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Streamlit only | No clean API for integrations |
| FastAPI + React | Additional frontend complexity |
| Shared library (no API) | Duplicated logic; harder to test |

---

## Summary

All technical decisions have been made. No NEEDS CLARIFICATION items remain. The implementation can proceed to Phase 1 (data model and contracts).

### Key Technologies
- **Backend**: Python 3.11+, FastAPI, pandas, numpy
- **Frontend**: Streamlit 1.28+, Plotly
- **Storage**: SQLite with WAL mode
- **Testing**: pytest

### Key Design Patterns
- PII stripped at import boundary via SHA-256 hashing
- Seeded random selection for reproducibility
- Decimal precision for ACP calculations
- API-first architecture with Streamlit as consumer
