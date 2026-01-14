/**
 * Color scale utilities for heatmap visualization.
 */

import type { AnalysisStatus, ViewMode } from '../types'

// Status colors
const STATUS_COLORS: Record<AnalysisStatus, string> = {
  PASS: '#22c55e',  // green-500
  RISK: '#f59e0b',  // amber-500
  FAIL: '#ef4444',  // red-500
  ERROR: '#6b7280', // gray-500
}

// Status background colors (lighter)
const STATUS_BG_COLORS: Record<AnalysisStatus, string> = {
  PASS: '#dcfce7',  // green-100
  RISK: '#fef3c7',  // amber-100
  FAIL: '#fee2e2',  // red-100
  ERROR: '#f3f4f6', // gray-100
}

// Margin color scale (green to red via yellow)
function marginToColor(margin: number | null): string {
  if (margin === null) return STATUS_COLORS.ERROR

  // Clamp margin to reasonable range (-2 to 2)
  const clamped = Math.max(-2, Math.min(2, margin))

  // Convert to 0-1 scale (0 = fail, 1 = pass)
  const normalized = (clamped + 2) / 4

  if (normalized <= 0.5) {
    // Red to yellow
    const ratio = normalized * 2
    const r = 239
    const g = Math.round(68 + (158 - 68) * ratio)
    const b = 68
    return `rgb(${r}, ${g}, ${b})`
  } else {
    // Yellow to green
    const ratio = (normalized - 0.5) * 2
    const r = Math.round(245 - (245 - 34) * ratio)
    const g = Math.round(158 + (197 - 158) * ratio)
    const b = Math.round(11 + (94 - 11) * ratio)
    return `rgb(${r}, ${g}, ${b})`
  }
}

export function getCellColor(
  status: AnalysisStatus,
  margin: number | null,
  viewMode: ViewMode
): string {
  switch (viewMode) {
    case 'PASS_FAIL':
      return STATUS_COLORS[status]
    case 'MARGIN':
      return marginToColor(margin)
    case 'RISK_ZONE':
      // Highlight risk zone cells
      if (status === 'RISK') {
        return '#f59e0b' // amber-500 (brighter for emphasis)
      }
      return STATUS_COLORS[status]
    default:
      return STATUS_COLORS[status]
  }
}

export function getCellBackgroundColor(status: AnalysisStatus): string {
  return STATUS_BG_COLORS[status]
}

export function getStatusLabel(status: AnalysisStatus): string {
  const labels: Record<AnalysisStatus, string> = {
    PASS: 'Pass',
    RISK: 'Risk',
    FAIL: 'Fail',
    ERROR: 'Error',
  }
  return labels[status]
}

export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  // Handle both fraction (0.25) and percentage (25) formats
  const pct = value > 1 ? value : value * 100
  return `${pct.toFixed(1)}%`
}

export function formatMargin(margin: number | null | undefined): string {
  if (margin === null || margin === undefined) return 'N/A'
  const sign = margin > 0 ? '+' : ''
  return `${sign}${margin.toFixed(2)}%`
}
