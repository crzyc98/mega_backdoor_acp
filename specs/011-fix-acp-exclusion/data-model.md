# Data Model: ACP Exclusion Bug Fix

**Feature**: 011-fix-acp-exclusion
**Date**: 2026-01-15

## Entity Changes

### ACPExclusionReason (Extend)

**File**: `src/core/acp_eligibility.py`

**Current**:
```python
ACPExclusionReason = Literal["TERMINATED_BEFORE_ENTRY", "NOT_ELIGIBLE_DURING_YEAR"]
```

**Updated**:
```python
ACPExclusionReason = Literal[
    "TERMINATED_BEFORE_ENTRY",
    "NOT_ELIGIBLE_DURING_YEAR",
    "MISSING_DOB",
    "MISSING_HIRE_DATE",
]
```

| Value | Description | Trigger Condition |
|-------|-------------|-------------------|
| TERMINATED_BEFORE_ENTRY | Employee left before plan entry | termination_date < entry_date |
| NOT_ELIGIBLE_DURING_YEAR | Entry date after plan year end | entry_date > plan_year_end |
| MISSING_DOB | Date of birth not provided | dob is None or empty |
| MISSING_HIRE_DATE | Hire date not provided | hire_date is None or empty |

---

### ACPInclusionResult (Extend)

**File**: `src/core/acp_eligibility.py`

**Current**:
```python
@dataclass(frozen=True)
class ACPInclusionResult:
    eligibility_date: date
    entry_date: date
    acp_includable: bool
    acp_exclusion_reason: ACPExclusionReason | None
```

**Updated**:
```python
@dataclass(frozen=True)
class ACPInclusionResult:
    eligibility_date: date | None  # None if data error
    entry_date: date | None        # None if data error
    acp_includable: bool           # Always False for error cases
    acp_exclusion_reason: ACPExclusionReason | None
```

**Field Changes**:

| Field | Before | After | Notes |
|-------|--------|-------|-------|
| eligibility_date | `date` | `date \| None` | None when DOB or hire_date missing |
| entry_date | `date` | `date \| None` | None when DOB or hire_date missing |
| acp_includable | `bool` | `bool` | No change (False for errors) |
| acp_exclusion_reason | `ACPExclusionReason \| None` | Same | New values: MISSING_DOB, MISSING_HIRE_DATE |

---

### ExclusionInfo (Extend)

**File**: `src/core/models.py`

**Current**:
```python
class ExclusionInfo(BaseModel):
    total_excluded: int
    terminated_before_entry_count: int
    not_eligible_during_year_count: int
```

**Updated**:
```python
class ExclusionInfo(BaseModel):
    total_excluded: int = Field(..., ge=0, description="Total participants excluded from ACP")
    terminated_before_entry_count: int = Field(
        ..., ge=0, description="Excluded: terminated before entry date"
    )
    not_eligible_during_year_count: int = Field(
        ..., ge=0, description="Excluded: not eligible during plan year"
    )
    missing_dob_count: int = Field(
        0, ge=0, description="Excluded: missing date of birth"
    )
    missing_hire_date_count: int = Field(
        0, ge=0, description="Excluded: missing hire date"
    )
```

**New Fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| missing_dob_count | int | 0 | Count of participants excluded due to missing DOB |
| missing_hire_date_count | int | 0 | Count of participants excluded due to missing hire_date |

**Validation Rules**:
- All counts must be >= 0
- total_excluded = sum of all reason counts

---

### ACPExclusionReason Enum (Pydantic Model)

**File**: `src/core/models.py`

**Current**:
```python
class ACPExclusionReason(str, Enum):
    TERMINATED_BEFORE_ENTRY = "TERMINATED_BEFORE_ENTRY"
    NOT_ELIGIBLE_DURING_YEAR = "NOT_ELIGIBLE_DURING_YEAR"
```

**Updated**:
```python
class ACPExclusionReason(str, Enum):
    TERMINATED_BEFORE_ENTRY = "TERMINATED_BEFORE_ENTRY"
    NOT_ELIGIBLE_DURING_YEAR = "NOT_ELIGIBLE_DURING_YEAR"
    MISSING_DOB = "MISSING_DOB"
    MISSING_HIRE_DATE = "MISSING_HIRE_DATE"
```

---

### ExcludedParticipant (Extend Literal)

**File**: `src/core/models.py`

**Current**:
```python
class ExcludedParticipant(BaseModel):
    exclusion_reason: Literal["TERMINATED_BEFORE_ENTRY", "NOT_ELIGIBLE_DURING_YEAR"]
```

**Updated**:
```python
class ExcludedParticipant(BaseModel):
    exclusion_reason: Literal[
        "TERMINATED_BEFORE_ENTRY",
        "NOT_ELIGIBLE_DURING_YEAR",
        "MISSING_DOB",
        "MISSING_HIRE_DATE",
    ]
```

---

## State Transitions

### Participant Eligibility State Machine

```
┌─────────────────┐
│  Census Import  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Missing DOB?      ┌──────────────────┐
│  Parse Dates    │──────────────────────▶│  MISSING_DOB     │
└────────┬────────┘                       │  (excluded)      │
         │                                └──────────────────┘
         │ Valid DOB
         ▼
┌─────────────────┐     Missing hire?     ┌──────────────────────┐
│  Parse Hire     │──────────────────────▶│  MISSING_HIRE_DATE   │
└────────┬────────┘                       │  (excluded)          │
         │                                └──────────────────────┘
         │ Valid hire
         ▼
┌─────────────────┐
│ Calc Eligibility│
│ eligibility_date│
│ = max(age21,    │
│      yos1)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calc Entry Date │
│ = next Jan1/Jul1│
└────────┬────────┘
         │
         ├──── entry > PY_END ────▶ NOT_ELIGIBLE_DURING_YEAR (excluded)
         │
         ├──── term < entry ──────▶ TERMINATED_BEFORE_ENTRY (excluded)
         │
         └──── otherwise ─────────▶ INCLUDED (acp_includable = True)
```

---

## Relationships

```
Census (1) ────── (*) Participant
                        │
                        │ determine_acp_inclusion()
                        ▼
                  ACPInclusionResult
                        │
                        │ aggregate by reason
                        ▼
                  ExclusionInfo
                        │
                        │ attach to
                        ▼
              ScenarioResult / GridSummary / EmployeeImpactView
```

---

## Backward Compatibility

| Change | Impact | Mitigation |
|--------|--------|------------|
| New enum values | Existing code may not handle | Default handling in switch/match |
| Nullable eligibility_date | API consumers | Document as optional in OpenAPI |
| New ExclusionInfo fields | API response larger | Default to 0, existing consumers ignore |

All changes are **additive** - existing functionality preserved.
