/**
 * Census upload page with import wizard integration.
 * T007: Integrates the ImportWizard component for enhanced CSV import experience.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkspace } from '../hooks/useWorkspace'
import censusService from '../services/censusService'
import CensusStats from '../components/CensusStats'
import LoadingSpinner from '../components/LoadingSpinner'
import ImportWizard from '../components/ImportWizard'
import type { CensusSummary } from '../types'
import type { ImportResult } from '../types/importWizard'

export default function CensusUpload() {
  const navigate = useNavigate()
  const { activeWorkspace, refreshActiveWorkspace } = useWorkspace()

  const [censusSummary, setCensusSummary] = useState<CensusSummary | null>(null)
  const [loadingSummary, setLoadingSummary] = useState(true)
  const [showWizard, setShowWizard] = useState(false)

  // Load existing census summary
  useEffect(() => {
    if (!activeWorkspace) return

    setLoadingSummary(true)
    censusService
      .get(activeWorkspace.id)
      .then((summary) => {
        setCensusSummary(summary)
      })
      .catch(() => {
        // No census yet - show wizard by default
        setCensusSummary(null)
        setShowWizard(true)
      })
      .finally(() => {
        setLoadingSummary(false)
      })
  }, [activeWorkspace])

  const handleImportComplete = async (_result: ImportResult) => {
    // Show success message briefly, then navigate
    await new Promise((resolve) => setTimeout(resolve, 1500))

    // Refresh census summary after successful import
    if (activeWorkspace) {
      try {
        const summary = await censusService.get(activeWorkspace.id)
        setCensusSummary(summary)
        await refreshActiveWorkspace()
      } catch {
        // If we can't load the summary, navigate to analysis anyway
      }

      // Navigate to analysis page
      navigate(`/workspace/${activeWorkspace.id}/analysis`)
    } else {
      setShowWizard(false)
    }
  }

  const handleImportCancel = () => {
    setShowWizard(false)
  }

  const handleProceedToAnalysis = () => {
    if (activeWorkspace) {
      navigate(`/workspace/${activeWorkspace.id}/analysis`)
    }
  }

  if (loadingSummary) {
    return (
      <div className="py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Show import wizard
  if (showWizard && activeWorkspace) {
    return (
      <ImportWizard
        workspaceId={activeWorkspace.id}
        onComplete={handleImportComplete}
        onCancel={handleImportCancel}
      />
    )
  }

  // Show statistics if census already uploaded
  if (censusSummary) {
    return (
      <div className="space-y-6">
        <CensusStats summary={censusSummary} />

        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowWizard(true)}
            className="text-sm text-gray-600 hover:text-gray-900 underline"
          >
            Upload new census data
          </button>
          <button
            onClick={handleProceedToAnalysis}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Proceed to Analysis
          </button>
        </div>
      </div>
    )
  }

  // Default: show wizard for new uploads
  if (activeWorkspace) {
    return (
      <ImportWizard
        workspaceId={activeWorkspace.id}
        onComplete={handleImportComplete}
        onCancel={handleImportCancel}
      />
    )
  }

  // No workspace selected
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
      <p className="text-gray-500">Please select a workspace to upload census data.</p>
    </div>
  )
}
