/**
 * Export API service functions.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const BASE_PATH = '/api/workspaces'

export type ExportFormat = 'csv' | 'pdf'

export async function downloadExport(
  workspaceId: string,
  runId: string,
  format: ExportFormat
): Promise<void> {
  const url = `${BASE_URL}${BASE_PATH}/${workspaceId}/runs/${runId}/export/${format}`

  try {
    const response = await fetch(url)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail?.message || `Export failed: ${response.statusText}`)
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `export.${format}`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=([^;]+)/)
      if (match) {
        filename = match[1].replace(/"/g, '')
      }
    }

    // Download file
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Export failed')
  }
}

export const exportService = {
  download: downloadExport,
}

export default exportService
