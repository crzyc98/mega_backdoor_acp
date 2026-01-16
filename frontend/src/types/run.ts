/**
 * Run type definitions for analysis execution.
 */

import type { DecimalRate } from './analysis'

export type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface Run {
  id: string
  workspace_id: string
  name?: string
  /** Adoption rates as decimals (0.0-1.0), e.g., [0.20, 0.40, 0.60] */
  adoption_rates: DecimalRate[]
  /** Contribution rates as decimals (0.0-1.0), e.g., [0.02, 0.04, 0.06] */
  contribution_rates: DecimalRate[]
  seed: number
  status: RunStatus
  created_at: string
  completed_at?: string
}

export interface RunCreate {
  name?: string
  /** Adoption rates as decimals (0.0-1.0), e.g., [0.20, 0.40, 0.60] */
  adoption_rates: DecimalRate[]
  /** Contribution rates as decimals (0.0-1.0), e.g., [0.02, 0.04, 0.06] */
  contribution_rates: DecimalRate[]
  seed?: number
}

export interface RunListResponse {
  items: Run[]
  total: number
}
