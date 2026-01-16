# API Contracts: DuckDB Migration

**Feature**: 012-duckdb-migration

## No New Contracts Required

This feature is a database backend migration that does not change any API contracts.

### Unchanged APIs

All existing endpoints maintain their current request/response schemas:

- `GET/POST/DELETE /api/census/*` - Census management
- `GET/POST /api/analysis/*` - ACP analysis operations
- `GET/POST/DELETE /api/import/*` - Import wizard operations
- `GET/POST/DELETE /api/mapping-profiles/*` - Mapping profile management

### Internal Changes Only

The migration affects only the internal database layer:
- `src/storage/database.py` - Connection management
- `src/storage/repository.py` - Repository implementations
- `backend/app/database.py` - Backend database module

### Workspace Parameter

Existing workspace-aware endpoints continue to work identically:
- Workspace ID passed via header or path parameter
- Database connection resolved to workspace-specific DuckDB file
- No changes to API consumers required
