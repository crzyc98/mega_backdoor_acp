/**
 * Workspace dashboard page with tab navigation.
 */

import { useEffect } from 'react'
import { useParams, Routes, Route, useNavigate } from 'react-router-dom'
import { useWorkspace } from '../hooks/useWorkspace'
import workspaceService from '../services/workspaceService'
import TabNavigation from '../components/TabNavigation'
import LoadingSpinner from '../components/LoadingSpinner'
import CensusUpload from './CensusUpload'
import AnalysisDashboard from './AnalysisDashboard'
import EmployeeImpact from './EmployeeImpact'
import Export from './Export'

const TABS = [
  { id: 'upload', label: 'Upload', path: '' },
  { id: 'analysis', label: 'Analysis', path: '/analysis' },
  { id: 'employees', label: 'Employee Impact', path: '/employees' },
  { id: 'export', label: 'Export', path: '/export' },
]

export default function WorkspaceDashboard() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const navigate = useNavigate()
  const { activeWorkspace, setActiveWorkspace, loading } = useWorkspace()

  useEffect(() => {
    // Load workspace if not already active or if different workspace
    if (workspaceId && activeWorkspace?.id !== workspaceId) {
      workspaceService
        .get(workspaceId)
        .then((workspace) => {
          setActiveWorkspace(workspace)
        })
        .catch((err) => {
          console.error('Failed to load workspace:', err)
          navigate('/')
        })
    }
  }, [workspaceId, activeWorkspace?.id, setActiveWorkspace, navigate])

  if (loading || !activeWorkspace) {
    return (
      <div className="py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const baseUrl = `/workspace/${workspaceId}`

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{activeWorkspace.name}</h1>
        {activeWorkspace.description && (
          <p className="mt-1 text-sm text-gray-500">{activeWorkspace.description}</p>
        )}

        <div className="mt-4 flex items-center gap-4 text-sm">
          <span
            className={`px-2 py-1 rounded-full ${
              activeWorkspace.has_census
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {activeWorkspace.has_census ? 'Census uploaded' : 'No census'}
          </span>
          <span className="text-gray-500">
            {activeWorkspace.run_count} analysis run{activeWorkspace.run_count !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <TabNavigation tabs={TABS} baseUrl={baseUrl} />

      <div className="mt-6">
        <Routes>
          <Route path="/" element={<CensusUpload />} />
          <Route path="/analysis" element={<AnalysisDashboard />} />
          <Route path="/employees" element={<EmployeeImpact />} />
          <Route path="/export" element={<Export />} />
        </Routes>
      </div>
    </div>
  )
}
