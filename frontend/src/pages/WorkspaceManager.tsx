/**
 * Workspace manager page - list, create, edit, delete workspaces.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Workspace, WorkspaceCreate, WorkspaceUpdate } from '../types'
import { useWorkspace } from '../hooks/useWorkspace'
import workspaceService from '../services/workspaceService'
import WorkspaceGrid from '../components/WorkspaceGrid'
import EmptyState from '../components/EmptyState'
import CreateWorkspaceModal from '../components/CreateWorkspaceModal'
import EditWorkspaceModal from '../components/EditWorkspaceModal'
import DeleteConfirmModal from '../components/DeleteConfirmModal'
import LoadingSpinner from '../components/LoadingSpinner'

export default function WorkspaceManager() {
  const navigate = useNavigate()
  const { setActiveWorkspace } = useWorkspace()

  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingWorkspace, setEditingWorkspace] = useState<Workspace | null>(null)
  const [deletingWorkspace, setDeletingWorkspace] = useState<Workspace | null>(null)

  const fetchWorkspaces = useCallback(async () => {
    try {
      const response = await workspaceService.list()
      setWorkspaces(response.items)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspaces')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchWorkspaces()
  }, [fetchWorkspaces])

  const handleCreate = async (data: WorkspaceCreate) => {
    const workspace = await workspaceService.create(data)
    setWorkspaces((prev) => [workspace, ...prev])
  }

  const handleUpdate = async (workspaceId: string, data: WorkspaceUpdate) => {
    const updated = await workspaceService.update(workspaceId, data)
    setWorkspaces((prev) =>
      prev.map((w) => (w.id === workspaceId ? updated : w))
    )
  }

  const handleDelete = async () => {
    if (!deletingWorkspace) return
    await workspaceService.delete(deletingWorkspace.id)
    setWorkspaces((prev) => prev.filter((w) => w.id !== deletingWorkspace.id))
    setDeletingWorkspace(null)
  }

  const handleSelect = async (workspace: Workspace) => {
    await setActiveWorkspace(workspace)
    navigate(`/workspace/${workspace.id}`)
  }

  if (loading) {
    return (
      <div className="py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchWorkspaces}
            className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workspaces</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your ACP analysis projects
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Workspace
        </button>
      </div>

      {workspaces.length === 0 ? (
        <EmptyState
          icon={
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          }
          title="No workspaces yet"
          description="Create your first workspace to get started with ACP sensitivity analysis."
          action={
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Workspace
            </button>
          }
        />
      ) : (
        <WorkspaceGrid
          workspaces={workspaces}
          onSelect={handleSelect}
          onEdit={setEditingWorkspace}
          onDelete={setDeletingWorkspace}
        />
      )}

      <CreateWorkspaceModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />

      <EditWorkspaceModal
        workspace={editingWorkspace}
        isOpen={!!editingWorkspace}
        onClose={() => setEditingWorkspace(null)}
        onUpdate={handleUpdate}
      />

      <DeleteConfirmModal
        isOpen={!!deletingWorkspace}
        title="Delete Workspace"
        message={`Are you sure you want to delete "${deletingWorkspace?.name}"? This will permanently remove all census data and analysis runs associated with this workspace.`}
        onClose={() => setDeletingWorkspace(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
