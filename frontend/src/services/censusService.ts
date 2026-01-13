/**
 * Census API service functions.
 */

import type { CensusSummary } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface CensusUploadParams {
  workspaceId: string
  file: File
  planYear: number
  hceMode: 'explicit' | 'compensation_threshold'
}

export async function uploadCensus(params: CensusUploadParams): Promise<CensusSummary> {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('plan_year', params.planYear.toString())
  formData.append('hce_mode', params.hceMode)

  const response = await fetch(
    `${API_BASE}/api/workspaces/${params.workspaceId}/census`,
    {
      method: 'POST',
      body: formData,
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail?.message || 'Failed to upload census')
  }

  return response.json()
}

export async function getCensus(workspaceId: string): Promise<CensusSummary | null> {
  const response = await fetch(
    `${API_BASE}/api/workspaces/${workspaceId}/census`
  )

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail?.message || 'Failed to get census')
  }

  return response.json()
}

export const censusService = {
  upload: uploadCensus,
  get: getCensus,
}

export default censusService
