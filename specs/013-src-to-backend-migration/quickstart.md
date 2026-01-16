# Quickstart: Source Directory Migration

**Feature**: 013-src-to-backend-migration
**Date**: 2026-01-16

## Overview

This migration consolidates all application code from `/src` into `/backend` and removes the legacy `/src` directory.

## Prerequisites

- Git branch: `013-src-to-backend-migration`
- Python 3.11+ environment
- All current tests should pass before starting

## Migration Steps

### Step 1: Verify Current State

```bash
# Ensure we're on the correct branch
git branch --show-current  # Should show: 013-src-to-backend-migration

# Run tests to establish baseline (some UI theme tests will fail - known issue)
cd /workspaces/mega_backdoor_acp/backend
pytest tests/ -v

# Count files to migrate
find src -type f -name "*.py" | wc -l  # Should be ~26 files
```

### Step 2: Update Root Test Imports

Update imports in `/tests/` directory files from `src.*` to `backend.app.*`:

| Old Import | New Import |
|------------|------------|
| `from src.api.main` | `from backend.app.routers.main` |
| `from src.api.schemas` | `from backend.app.routers.schemas` |
| `from src.core.*` | `from backend.app.services.*` |
| `from src.storage.*` | `from backend.app.storage.*` |

Files to update:
- `tests/unit/test_*.py` (7 files)
- `tests/unit/core/test_employee_impact.py`
- `tests/contract/test_*.py` (3 files)
- `tests/integration/test_*.py` (3 files)
- `tests/integration/api/test_employee_impact_api.py`

### Step 3: Update Configuration Files

**`/pyproject.toml`**:
```toml
# Change:
[tool.coverage.run]
source = ["backend/app"]  # was: ["src"]

[tool.ruff.isort]
known-first-party = ["backend", "app"]  # was: ["src"]
```

**`/CLAUDE.md`**:
- Update project structure section to remove `src/`
- Update any command references

### Step 4: Handle UI Theme Tests

The tests in `tests/unit/ui/theme/` reference non-existent modules. Options:
1. Delete the orphaned test files (recommended for this migration)
2. Create placeholder modules (deferred to separate task)

```bash
# Option 1: Remove orphaned tests
rm -rf tests/unit/ui/
```

### Step 5: Delete `/src` Directory

```bash
# Verify no unique files exist
diff -rq src/core backend/app/services 2>/dev/null || echo "Differences found"
diff -rq src/api backend/app/routers 2>/dev/null || echo "Differences found"
diff -rq src/storage backend/app/storage 2>/dev/null || echo "Differences found"

# Remove src directory
rm -rf src/
```

### Step 6: Verify Migration

```bash
# Run full test suite
cd /workspaces/mega_backdoor_acp/backend
pytest tests/ -v

# Run root tests
cd /workspaces/mega_backdoor_acp
pytest tests/ -v

# Verify no src references remain
grep -r "from src\." --include="*.py" . 2>/dev/null && echo "ERROR: src imports still exist"
grep -r "import src\." --include="*.py" . 2>/dev/null && echo "ERROR: src imports still exist"

# Verify src directory is gone
[ -d src ] && echo "ERROR: src directory still exists" || echo "OK: src directory removed"
```

### Step 7: Start Application

```bash
cd /workspaces/mega_backdoor_acp/backend
uvicorn app.routers.main:app --reload

# Test endpoints
curl http://localhost:8000/health
```

## Rollback Procedure

If issues occur:

```bash
# Restore from git
git checkout -- .
git clean -fd

# Or restore specific files
git checkout HEAD -- src/
git checkout HEAD -- tests/
git checkout HEAD -- pyproject.toml
```

## Success Criteria Checklist

- [ ] `/src` directory deleted
- [ ] All tests pass (excluding pre-existing UI theme test failures)
- [ ] Application starts successfully
- [ ] No `src.` imports remain in codebase
- [ ] Configuration files updated
- [ ] CLAUDE.md reflects new structure
