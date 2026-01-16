# Tasks: Fix Export Filenames

**Input**: Design documents from `/specs/016-fix-export-filenames/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: No automated tests requested. Manual browser testing per quickstart.md.

**Organization**: This is a minimal bug fix - both user stories are resolved by a single configuration change.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This fix affects only `backend/app/routers/main.py`

---

## Phase 1: Setup

**Purpose**: No setup needed - this is a bug fix to an existing project

- [x] T001 Verify current branch is `016-fix-export-filenames`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational work needed - existing infrastructure is correct

**Research confirmed**:
- Backend filename generation: CORRECT (`workspaces.py:1053-1063`, `workspaces.py:1182-1191`)
- Frontend header parsing: CORRECT (`exportService.ts:25-33`)
- Only missing: CORS `expose_headers` configuration

---

## Phase 3: User Stories 1 & 2 - Descriptive Export Filenames (Priority: P1) 🎯 MVP

**Goal**: Enable browser JavaScript to read the `Content-Disposition` header so descriptive filenames are used for both CSV and PDF downloads.

**Independent Test**: Download any CSV or PDF export and verify the filename contains workspace name, plan year, run number, and date instead of generic `export.csv` or `export.pdf`.

### Implementation

- [x] T002 [US1] [US2] Add `expose_headers=["Content-Disposition"]` to CORSMiddleware in backend/app/routers/main.py

**Details for T002**:
Locate the CORSMiddleware configuration (lines 42-54) and add the `expose_headers` parameter:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # ADD THIS LINE
)
```

**Checkpoint**: Both User Story 1 (CSV) and User Story 2 (PDF) should now work with descriptive filenames

---

## Phase 4: Verification

**Purpose**: Confirm the fix works for both CSV and PDF exports

- [ ] T003 [US1] Manual test: Download CSV export and verify filename format `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.csv` *(requires manual browser testing)*
- [ ] T004 [US2] Manual test: Download PDF export and verify filename format `{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.pdf` *(requires manual browser testing)*
- [ ] T005 Browser DevTools: Verify `Access-Control-Expose-Headers: Content-Disposition` is present in response headers *(requires manual browser testing)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Verify branch
- **Foundational (Phase 2)**: No work needed (skipped)
- **User Stories (Phase 3)**: Single task resolves both stories
- **Verification (Phase 4)**: Depends on Phase 3 completion

### User Story Dependencies

- **User Story 1 (CSV)**: Resolved by T002
- **User Story 2 (PDF)**: Resolved by T002 (same change)

Both user stories share the same root cause and fix.

### Parallel Opportunities

- T003, T004, T005 can all run in parallel after T002 completes

---

## Implementation Strategy

### MVP (Immediate)

1. Complete T001: Verify branch
2. Complete T002: Add CORS expose_headers configuration
3. Complete T003-T005: Manual verification
4. **DONE**: Both user stories are complete

### Expected Changes

| File | Change |
|------|--------|
| `backend/app/routers/main.py` | Add `expose_headers=["Content-Disposition"]` to CORSMiddleware |

Total: **1 file, 1 line added**

---

## Notes

- This is a minimal bug fix requiring only 1 code change
- Both user stories (CSV and PDF) are fixed by the same change
- No automated tests needed - manual browser testing confirms the fix
- The backend and frontend code are already correct; only CORS config was missing
- After fix: files download as `Acme_Corp_2024_Run42_Jan2026.csv` instead of `export.csv`
