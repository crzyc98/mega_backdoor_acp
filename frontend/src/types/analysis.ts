/**
 * Analysis result type definitions.
 */

import type { ExclusionInfo } from './employee'

export type AnalysisStatus = 'PASS' | 'RISK' | 'FAIL' | 'ERROR'
export type ViewMode = 'PASS_FAIL' | 'MARGIN' | 'RISK_ZONE'

/**
 * Rate value as a decimal fraction (0.0 to 1.0).
 * Backend API expects and returns rates in this format.
 * Example: 0.06 represents 6%, 0.75 represents 75%.
 */
export type DecimalRate = number

export interface ScenarioResult {
  status: AnalysisStatus
  nhce_acp: number | null
  hce_acp: number | null
  limit_125?: number | null
  limit_2pct_uncapped?: number | null
  cap_2x?: number | null
  limit_2pct_capped?: number | null
  effective_limit?: number | null
  max_allowed_acp: number | null
  margin: number | null
  binding_rule?: '1.25x' | '2pct/2x' | null
  /** Adoption rate as decimal (0.0-1.0) */
  adoption_rate: DecimalRate
  /** Contribution rate as decimal (0.0-1.0) */
  contribution_rate: DecimalRate
  seed_used: number
  excluded_count?: number | null
  exclusion_breakdown?: ExclusionInfo | null
}

export interface GridSummary {
  pass_count: number
  risk_count: number
  fail_count: number
  error_count: number
  total_count: number
  first_failure_point?: {
    /** Adoption rate as decimal (0.0-1.0) */
    adoption_rate: DecimalRate
    /** Contribution rate as decimal (0.0-1.0) */
    contribution_rate: DecimalRate
  }
  /** Max safe contribution rate as decimal (0.0-1.0) */
  max_safe_contribution?: DecimalRate
  worst_margin?: number
  excluded_count?: number
  exclusion_breakdown?: ExclusionInfo | null
}

export interface GridResult {
  scenarios: ScenarioResult[]
  summary: GridSummary
  seed_used: number
}

// RunDetail is defined in runService.ts to avoid circular dependency
