/**
 * Employee and census type definitions.
 */

export type ConstraintStatus = 'Unconstrained' | 'At §415(c) Limit' | 'Reduced' | 'Not Selected'

export interface EmployeeImpact {
  employee_id: string
  is_hce: boolean
  compensation: number
  deferral_amount: number
  match_amount: number
  after_tax_amount: number
  section_415c_limit: number
  available_room: number
  mega_backdoor_amount: number
  requested_mega_backdoor: number
  individual_acp: number | null
  constraint_status: ConstraintStatus
  constraint_detail: string
}

export interface EmployeeImpactSummary {
  group: 'HCE' | 'NHCE'
  total_count: number
  at_limit_count: number | null
  reduced_count: number | null
  average_available_room: number | null
  total_mega_backdoor: number | null
  average_individual_acp: number
  total_match: number
  total_after_tax: number
}

export interface EmployeeImpactView {
  census_id: string
  adoption_rate: number
  contribution_rate: number
  seed_used: number
  plan_year: number
  section_415c_limit: number
  hce_employees: EmployeeImpact[]
  nhce_employees: EmployeeImpact[]
  hce_summary: EmployeeImpactSummary
  nhce_summary: EmployeeImpactSummary
}

export interface EmployeeImpactRequest {
  adoption_rate: number
  contribution_rate: number
  seed: number
}

export interface CensusSummary {
  id: string
  plan_year: number
  participant_count: number
  hce_count: number
  nhce_count: number
  avg_compensation?: number
  upload_timestamp: string
}

export interface CensusStats {
  total_employees: number
  hce_count: number
  nhce_count: number
  avg_compensation: number
  total_compensation: number
}
