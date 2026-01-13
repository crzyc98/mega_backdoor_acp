/**
 * Grid layout for displaying workspace cards.
 */

import type { Workspace } from '../types'
import WorkspaceCard from './WorkspaceCard'

interface WorkspaceGridProps {
  workspaces: Workspace[]
  onSelect: (workspace: Workspace) => void
  onEdit: (workspace: Workspace) => void
  onDelete: (workspace: Workspace) => void
}

export default function WorkspaceGrid({
  workspaces,
  onSelect,
  onEdit,
  onDelete,
}: WorkspaceGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {workspaces.map((workspace) => (
        <WorkspaceCard
          key={workspace.id}
          workspace={workspace}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}
