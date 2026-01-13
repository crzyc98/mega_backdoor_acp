/**
 * Workspace card component for grid display.
 */

import type { Workspace } from '../types'

interface WorkspaceCardProps {
  workspace: Workspace
  onSelect: (workspace: Workspace) => void
  onEdit: (workspace: Workspace) => void
  onDelete: (workspace: Workspace) => void
}

export default function WorkspaceCard({
  workspace,
  onSelect,
  onEdit,
  onDelete,
}: WorkspaceCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {workspace.name}
            </h3>
            {workspace.description && (
              <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                {workspace.description}
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 flex items-center gap-4 text-xs text-gray-400">
          <span>Created {formatDate(workspace.created_at)}</span>
          <span>Updated {formatDate(workspace.updated_at)}</span>
        </div>
      </div>

      <div className="border-t border-gray-100 px-5 py-3 bg-gray-50 rounded-b-lg flex items-center justify-between">
        <button
          onClick={() => onSelect(workspace)}
          className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
          Open
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onEdit(workspace)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Edit workspace"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          <button
            onClick={() => onDelete(workspace)}
            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
            aria-label="Delete workspace"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
