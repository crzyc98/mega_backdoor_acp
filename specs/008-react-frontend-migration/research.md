# Research: React Frontend Migration

**Date**: 2026-01-13
**Feature**: 008-react-frontend-migration

## Overview

Research findings for migrating from Streamlit to React 19 + TypeScript + Vite with workspace management.

---

## 1. React 19 State Management Patterns

### Decision: React Context + Local State (no Redux)

### Rationale
- React 19 introduces improved context performance
- Application scope is single-user with moderate complexity
- ui-example demonstrates this pattern successfully with `useMemo` for performance
- Avoids additional dependencies (Redux, Zustand, etc.)

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Redux | Overkill for single-user app; adds boilerplate |
| Zustand | Additional dependency; React Context sufficient |
| Jotai | Atomic model adds complexity without clear benefit |

### Implementation Pattern
```typescript
// WorkspaceContext for active workspace state
const WorkspaceContext = createContext<WorkspaceState | null>(null);

// App-level state lifting for shared data
function App() {
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [censusData, setCensusData] = useState<CensusData | null>(null);
  // ...
}
```

---

## 2. File-Based Workspace Storage

### Decision: JSON files with directory-per-workspace structure

### Rationale
- Matches PlanAlign Engine pattern (proven architecture)
- No external database dependencies
- Human-readable for debugging
- Git-sync friendly if needed
- Simple backup/restore (copy directory)

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| SQLite | Adds database complexity; overkill for single-user |
| IndexedDB (browser) | Data not accessible outside browser; no server-side access |
| DuckDB | Heavy dependency; designed for analytics, not CRUD |

### Storage Structure
```
~/.acp-analyzer/workspaces/
└── {uuid}/
    ├── workspace.json      # Metadata
    ├── data/census.csv     # Census data
    └── runs/{run-uuid}/    # Analysis runs
        ├── run_metadata.json
        └── grid_results.json
```

### Backend Implementation
- Use `pathlib` for cross-platform path handling
- Atomic writes with temp file + rename pattern
- UUID v4 for workspace and run IDs
- JSON serialization via Pydantic `.model_dump_json()`

---

## 3. Vite + React 19 Setup

### Decision: Vite 6.2 with @vitejs/plugin-react

### Rationale
- Fastest dev server startup (ESM-native)
- ui-example already uses this exact stack
- Excellent TypeScript support
- Simple configuration

### Configuration Pattern (from ui-example)
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, host: '0.0.0.0' },
  resolve: {
    alias: { '@': '/src' }
  }
})
```

---

## 4. Tailwind CSS Integration

### Decision: Tailwind via CDN initially, migrate to PostCSS for production

### Rationale
- CDN simplifies initial development (no build step for styles)
- ui-example uses CDN successfully
- PostCSS migration provides tree-shaking for production builds

### Initial Setup (Development)
```html
<!-- index.html -->
<script src="https://cdn.tailwindcss.com"></script>
```

### Production Migration Path
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

## 5. API Client Pattern

### Decision: Fetch-based API client with TypeScript types

### Rationale
- No additional dependencies (axios not needed)
- Native browser API
- Type-safe with generated types from Pydantic schemas

### Implementation Pattern
```typescript
// services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchWorkspaces(): Promise<Workspace[]> {
  const res = await fetch(`${API_BASE}/api/workspaces`);
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}
```

---

## 6. Repository Migration Strategy

### Decision: Move files, then delete Streamlit code

### Rationale
- Preserves git history with `git mv`
- Clean separation before new frontend work
- Reduces confusion during development

### Migration Steps
1. Create backend/ and frontend/ directories
2. `git mv src/api/* backend/app/routers/`
3. `git mv src/core/* backend/app/services/`
4. `git mv src/storage/* backend/app/storage/`
5. `git mv tests/* backend/tests/`
6. Update import paths in Python files
7. Initialize frontend/ with Vite + React
8. Delete src/ui/ (Streamlit) after React is complete

---

## 7. Heatmap Visualization

### Decision: Custom div-based heatmap (no Plotly)

### Rationale
- ui-example demonstrates effective custom implementation
- Tailwind classes for styling
- Better performance than Plotly for simple grid
- Full control over accessibility features (colorblind patterns)

### Pattern from ui-example
```typescript
// Heatmap.tsx (~130 lines)
- Grid of divs with dynamic background colors
- Hover state via onMouseEnter/onMouseLeave
- View modes: PASS_FAIL, MARGIN, RISK_ZONE
- Diagonal stripe pattern for colorblind accessibility
```

---

## 8. Component Structure

### Decision: Feature-based component organization

### Rationale
- Matches ui-example structure
- Clear separation of concerns
- Easy to locate related code

### Structure
```
frontend/src/
├── components/           # Reusable UI components
│   ├── Layout.tsx
│   ├── Heatmap.tsx
│   ├── Modal.tsx
│   └── StatusBadge.tsx
├── pages/               # Route-level components
│   ├── WorkspaceManager.tsx
│   ├── CensusUpload.tsx
│   ├── AnalysisDashboard.tsx
│   ├── EmployeeImpact.tsx
│   └── Export.tsx
├── services/            # API clients
├── hooks/               # Custom hooks (useWorkspace, etc.)
├── types/               # TypeScript interfaces
└── utils/               # Helper functions
```

---

## 9. Testing Strategy

### Decision: Vitest for unit tests, React Testing Library for component tests

### Rationale
- Vitest integrates seamlessly with Vite
- Same config format as Vite
- React Testing Library is standard for React 19
- Fast execution with ESM

### Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

---

## 10. Error Handling Pattern

### Decision: Error boundaries + toast notifications

### Rationale
- Error boundaries prevent full app crashes
- Toast notifications for transient errors (API failures)
- Consistent UX pattern

### Implementation
```typescript
// ErrorBoundary component wraps route components
// useToast hook for API error notifications
// Loading/error/empty states in each data-fetching component
```

---

## Summary

All research items resolved. Key decisions:
- React Context for state (no Redux)
- File-based JSON storage for workspaces
- Custom heatmap (no Plotly)
- Fetch-based API client
- Vitest for testing
- Tailwind via CDN initially
