# Research: Fix Export Filenames

**Feature**: 016-fix-export-filenames
**Date**: 2026-01-16

## Research Questions

### Q1: Why are export files named "export.csv" instead of descriptive names?

**Decision**: The root cause is missing CORS `expose_headers` configuration preventing browser JavaScript from accessing the `Content-Disposition` header.

**Rationale**:
- Backend correctly generates descriptive filenames in `Content-Disposition` header
- Frontend correctly parses the header when available
- Browser blocks header access due to CORS security policy
- Adding `expose_headers=["Content-Disposition"]` allows the browser to expose this header to JavaScript

**Alternatives considered**:
1. **Generate filename in frontend**: Rejected - would require additional API call to get workspace/census metadata, duplicates logic
2. **Use URL query parameter for filename**: Rejected - non-standard, breaks RESTful pattern
3. **Embed filename in response body**: Rejected - changes API contract, breaks binary streaming

### Q2: Is the backend generating filenames correctly?

**Decision**: Yes, the backend is correctly generating descriptive filenames.

**Evidence**:
- CSV export (`workspaces.py:1053-1063`): Generates `{SafeName}_{PlanYear}_Run{Seed}_{MonthYear}.csv`
- PDF export (`workspaces.py:1182-1191`): Generates `{SafeName}_{PlanYear}_Run{Seed}_{MonthYear}.pdf`
- Both sanitize workspace names (remove special chars, replace spaces with underscores)
- Header format: `Content-Disposition: attachment; filename={filename}`

### Q3: Is the frontend parsing the header correctly?

**Decision**: Yes, the frontend regex pattern is compatible with the backend header format.

**Evidence** (`exportService.ts:25-33`):
```typescript
const match = contentDisposition.match(/filename=([^;]+)/)
if (match) {
  filename = match[1].replace(/"/g, '')
}
```

The regex `/filename=([^;]+)/` correctly captures:
- `filename=test.csv` → `test.csv`
- `filename="test.csv"` → `"test.csv"` → removes quotes → `test.csv`

### Q4: What CORS configuration is needed?

**Decision**: Add `expose_headers=["Content-Disposition"]` to CORSMiddleware.

**Rationale**:
- CORS `allow_headers` controls which headers the client can SEND
- CORS `expose_headers` controls which headers the client can READ from responses
- By default, browsers only expose "simple" headers: `Cache-Control`, `Content-Language`, `Content-Type`, `Expires`, `Last-Modified`, `Pragma`
- `Content-Disposition` is NOT a simple header and must be explicitly exposed

**Location**: `backend/app/routers/main.py` lines 42-54

## Summary

| Question | Answer | Confidence |
|----------|--------|------------|
| Why generic filenames? | CORS missing expose_headers | High |
| Backend filename generation | Correct | High |
| Frontend header parsing | Correct | High |
| Fix required | Add `expose_headers=["Content-Disposition"]` | High |

## Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/routers/main.py` | 42-54 | CORS middleware configuration |
| `backend/app/routers/workspaces.py` | 1053-1063 | CSV export with filename |
| `backend/app/routers/workspaces.py` | 1182-1191 | PDF export with filename |
| `frontend/src/services/exportService.ts` | 25-33 | Header parsing logic |
