/**
 * Run API service functions for grid analysis.
 */

import api from './api'
import type { Run, RunCreate, RunListResponse, GridResult } from '../types'

const BASE_PATH = '/api/workspaces'

export interface RunDetail extends Run {
  results?: GridResult
}

export async function listRuns(workspaceId: string): Promise<RunListResponse> {
  return api.get<RunListResponse>(`${BASE_PATH}/${workspaceId}/runs`)
}

export async function createRun(workspaceId: string, data: RunCreate): Promise<Run> {
  return api.post<Run>(`${BASE_PATH}/${workspaceId}/runs`, data)
}

export async function getRun(workspaceId: string, runId: string): Promise<RunDetail> {
  return api.get<RunDetail>(`${BASE_PATH}/${workspaceId}/runs/${runId}`)
}

export async function deleteRun(workspaceId: string, runId: string): Promise<void> {
  return api.delete(`${BASE_PATH}/${workspaceId}/runs/${runId}`)
}

export const runService = {
  list: listRuns,
  create: createRun,
  get: getRun,
  delete: deleteRun,
}

export default runService
