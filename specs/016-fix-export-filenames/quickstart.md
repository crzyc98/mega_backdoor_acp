# Quickstart: Fix Export Filenames

**Feature**: 016-fix-export-filenames
**Date**: 2026-01-16

## Overview

This bug fix adds CORS `expose_headers` configuration to allow the browser to read the `Content-Disposition` header from export responses, enabling descriptive filenames for CSV and PDF downloads.

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- A workspace with at least one completed analysis run

## Implementation

### Single File Change

**File**: `backend/app/routers/main.py`

Add `expose_headers=["Content-Disposition"]` to the CORSMiddleware configuration:

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

## Testing

### Quick Test

1. Start the backend:
   ```bash
   cd backend && uvicorn app.routers.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend && npm run dev
   ```

3. Open browser to http://localhost:5173

4. Navigate to a workspace with a completed run

5. Click "Download CSV"
   - **Before fix**: File downloads as `export.csv`
   - **After fix**: File downloads as `WorkspaceName_2024_Run42_Jan2026.csv`

6. Click "Download PDF"
   - **Before fix**: File downloads as `export.pdf`
   - **After fix**: File downloads as `WorkspaceName_2024_Run42_Jan2026.pdf`

### DevTools Verification

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click a download button
4. Find the export request
5. Check Response Headers:
   - `Content-Disposition: attachment; filename=...` should be present
   - `Access-Control-Expose-Headers: Content-Disposition` should be present

### Expected Filename Format

```
{WorkspaceName}_{PlanYear}_Run{Seed}_{MonthYear}.{ext}
```

Examples:
- `Acme_Corp_2024_Run42_Jan2026.csv`
- `Test_Workspace_2025_Run1_Jan2026.pdf`

## Troubleshooting

### Still seeing "export.csv"?

1. **Hard refresh**: Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Clear cache**: DevTools → Application → Clear storage
3. **Incognito window**: Test in a private/incognito window
4. **Check backend restart**: Ensure uvicorn reloaded after the change

### Response header not visible in DevTools?

The header may be present but collapsed. Look for:
- `content-disposition` (lowercase)
- Expand "Response Headers" section fully
