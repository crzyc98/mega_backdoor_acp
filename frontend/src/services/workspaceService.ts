/**
 * Workspace API service functions.
 */

import api from './api'
import type {
  Workspace,
  WorkspaceCreate,
  WorkspaceDetail,
  WorkspaceListResponse,
  WorkspaceUpdate,
} from '../types'

const BASE_PATH = '/api/workspaces'

export async function listWorkspaces(): Promise<WorkspaceListResponse> {
  return api.get<WorkspaceListResponse>(BASE_PATH)
}

export async function createWorkspace(data: WorkspaceCreate): Promise<Workspace> {
  return api.post<Workspace>(BASE_PATH, data)
}

export async function getWorkspace(workspaceId: string): Promise<WorkspaceDetail> {
  return api.get<WorkspaceDetail>(`${BASE_PATH}/${workspaceId}`)
}

export async function updateWorkspace(
  workspaceId: string,
  data: WorkspaceUpdate
): Promise<Workspace> {
  return api.put<Workspace>(`${BASE_PATH}/${workspaceId}`, data)
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  return api.delete(`${BASE_PATH}/${workspaceId}`)
}

export const workspaceService = {
  list: listWorkspaces,
  create: createWorkspace,
  get: getWorkspace,
  update: updateWorkspace,
  delete: deleteWorkspace,
}

export default workspaceService
