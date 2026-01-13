/**
 * Workspace context for active workspace state management.
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { Workspace, WorkspaceDetail } from '../types'
import { getWorkspace } from '../services/workspaceService'

interface WorkspaceContextType {
  activeWorkspace: WorkspaceDetail | null
  setActiveWorkspace: (workspace: Workspace | null) => void
  refreshActiveWorkspace: () => Promise<void>
  loading: boolean
}

const WorkspaceContext = createContext<WorkspaceContextType | null>(null)

interface WorkspaceProviderProps {
  children: ReactNode
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const [activeWorkspace, setActiveWorkspaceState] = useState<WorkspaceDetail | null>(null)
  const [loading, setLoading] = useState(false)

  const setActiveWorkspace = useCallback(async (workspace: Workspace | null) => {
    if (!workspace) {
      setActiveWorkspaceState(null)
      return
    }

    setLoading(true)
    try {
      const detail = await getWorkspace(workspace.id)
      setActiveWorkspaceState(detail)
    } catch (error) {
      console.error('Failed to fetch workspace details:', error)
      // Still set basic workspace info
      setActiveWorkspaceState({
        ...workspace,
        has_census: false,
        run_count: 0,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  const refreshActiveWorkspace = useCallback(async () => {
    if (!activeWorkspace) return

    setLoading(true)
    try {
      const detail = await getWorkspace(activeWorkspace.id)
      setActiveWorkspaceState(detail)
    } catch (error) {
      console.error('Failed to refresh workspace:', error)
    } finally {
      setLoading(false)
    }
  }, [activeWorkspace])

  return (
    <WorkspaceContext.Provider
      value={{
        activeWorkspace,
        setActiveWorkspace,
        refreshActiveWorkspace,
        loading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return context
}
