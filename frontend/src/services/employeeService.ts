/**
 * Employee impact API service functions.
 */

import api from './api'
import type { EmployeeImpactView } from '../types'

const BASE_PATH = '/api/workspaces'

export async function getEmployeeImpact(
  workspaceId: string,
  runId: string,
  adoptionRate: number,
  contributionRate: number
): Promise<EmployeeImpactView> {
  const params = new URLSearchParams({
    adoption_rate: adoptionRate.toString(),
    contribution_rate: contributionRate.toString(),
  })
  return api.get<EmployeeImpactView>(
    `${BASE_PATH}/${workspaceId}/runs/${runId}/employees?${params}`
  )
}

export const employeeService = {
  getImpact: getEmployeeImpact,
}

export default employeeService
