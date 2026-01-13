/**
 * Workspace type definitions.
 */

export interface Workspace {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface WorkspaceDetail extends Workspace {
  has_census: boolean
  run_count: number
}

export interface WorkspaceCreate {
  name: string
  description?: string
}

export interface WorkspaceUpdate {
  name?: string
  description?: string
}

export interface WorkspaceListResponse {
  items: Workspace[]
  total: number
}
