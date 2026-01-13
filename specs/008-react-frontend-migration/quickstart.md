# Quickstart: React Frontend Migration

**Date**: 2026-01-13
**Feature**: 008-react-frontend-migration

## Prerequisites

- Python 3.11+
- Node.js 18+ (LTS) or 20+
- npm 9+

## Repository Setup

After the migration, the repository structure will be:

```
mega_backdoor_acp/
├── backend/           # Python/FastAPI
├── frontend/          # React/TypeScript
└── specs/             # Feature specifications
```

## Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Run backend server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

API docs at `http://localhost:8000/docs`

## Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Development Workflow

### Running Both Services

Terminal 1 (Backend):
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend && npm run dev
```

### Environment Variables

Frontend (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

Backend (`backend/.env`):
```env
ACP_WORKSPACE_DIR=~/.acp-analyzer/workspaces
```

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app  # with coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage  # with coverage
```

## Building for Production

### Backend
```bash
cd backend
pip install build
python -m build
```

### Frontend
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

## Workspace Storage Location

Workspaces are stored at:
- Linux/Mac: `~/.acp-analyzer/workspaces/`
- Windows: `%USERPROFILE%\.acp-analyzer\workspaces\`

To use a custom location, set `ACP_WORKSPACE_DIR` environment variable.

## Key Commands Reference

| Task | Command |
|------|---------|
| Start backend | `cd backend && uvicorn app.main:app --reload` |
| Start frontend | `cd frontend && npm run dev` |
| Run backend tests | `cd backend && pytest` |
| Run frontend tests | `cd frontend && npm test` |
| Build frontend | `cd frontend && npm run build` |
| Lint backend | `cd backend && ruff check .` |
| Lint frontend | `cd frontend && npm run lint` |
| Format backend | `cd backend && ruff format .` |

## Troubleshooting

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### CORS errors
Ensure backend has CORS middleware configured for `http://localhost:3000`

### Workspace permission errors
Check that `~/.acp-analyzer/` directory is writable:
```bash
mkdir -p ~/.acp-analyzer/workspaces
chmod 755 ~/.acp-analyzer
```
