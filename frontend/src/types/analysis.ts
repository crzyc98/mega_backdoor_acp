/**
 * Analysis result type definitions.
 */

export type AnalysisStatus = 'PASS' | 'RISK' | 'FAIL' | 'ERROR'
export type ViewMode = 'PASS_FAIL' | 'MARGIN' | 'RISK_ZONE'

export interface ScenarioResult {
  status: AnalysisStatus
  nhce_acp: number | null
  hce_acp: number | null
  max_allowed_acp: number | null
  margin: number | null
  adoption_rate: number
  contribution_rate: number
  seed_used: number
}

export interface GridSummary {
  pass_count: number
  risk_count: number
  fail_count: number
  error_count: number
  total_count: number
  first_failure_point?: {
    adoption_rate: number
    contribution_rate: number
  }
  max_safe_contribution?: number
  worst_margin?: number
}

export interface GridResult {
  scenarios: ScenarioResult[]
  summary: GridSummary
  seed_used: number
}

export interface RunDetail extends Run {
  results?: GridResult
}

// Need to import Run for the RunDetail interface
import type { Run } from './run'
