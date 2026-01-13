/**
 * Run type definitions for analysis execution.
 */

export type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface Run {
  id: string
  workspace_id: string
  name?: string
  adoption_rates: number[]
  contribution_rates: number[]
  seed: number
  status: RunStatus
  created_at: string
  completed_at?: string
}

export interface RunCreate {
  name?: string
  adoption_rates: number[]
  contribution_rates: number[]
  seed?: number
}

export interface RunListResponse {
  items: Run[]
  total: number
}
