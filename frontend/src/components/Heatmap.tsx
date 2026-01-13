/**
 * Heatmap component for displaying grid analysis results.
 */

import { useState, useMemo } from 'react'
import type { ScenarioResult, ViewMode } from '../types'
import { getCellColor, getStatusLabel, formatPercentage, formatMargin } from '../utils/colorScale'

interface HeatmapProps {
  scenarios: ScenarioResult[]
  adoptionRates: number[]
  contributionRates: number[]
  viewMode: ViewMode
  onCellClick?: (scenario: ScenarioResult) => void
}

export default function Heatmap({
  scenarios,
  adoptionRates,
  contributionRates,
  viewMode,
  onCellClick,
}: HeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<ScenarioResult | null>(null)

  // Create a map for quick lookup
  const scenarioMap = useMemo(() => {
    const map = new Map<string, ScenarioResult>()
    scenarios.forEach((s) => {
      const key = `${s.adoption_rate}-${s.contribution_rate}`
      map.set(key, s)
    })
    return map
  }, [scenarios])

  // Sort rates for display
  const sortedAdoptionRates = useMemo(
    () => [...adoptionRates].sort((a, b) => a - b),
    [adoptionRates]
  )
  const sortedContributionRates = useMemo(
    () => [...contributionRates].sort((a, b) => b - a),
    [contributionRates]
  )

  const getScenario = (adoptionRate: number, contributionRate: number): ScenarioResult | undefined => {
    return scenarioMap.get(`${adoptionRate}-${contributionRate}`)
  }

  return (
    <div className="relative">
      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-xs text-gray-500 text-right whitespace-nowrap">
                Contrib. \ Adoption
              </th>
              {sortedAdoptionRates.map((rate) => (
                <th key={rate} className="p-2 text-xs text-gray-600 text-center whitespace-nowrap">
                  {formatPercentage(rate)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedContributionRates.map((contribRate) => (
              <tr key={contribRate}>
                <td className="p-2 text-xs text-gray-600 text-right whitespace-nowrap">
                  {formatPercentage(contribRate)}
                </td>
                {sortedAdoptionRates.map((adoptRate) => {
                  const scenario = getScenario(adoptRate, contribRate)
                  if (!scenario) {
                    return (
                      <td key={adoptRate} className="p-1">
                        <div className="w-8 h-8 bg-gray-100 rounded" />
                      </td>
                    )
                  }

                  const isHovered = hoveredCell === scenario
                  const color = getCellColor(scenario.status, scenario.margin, viewMode)

                  return (
                    <td key={adoptRate} className="p-1">
                      <div
                        onClick={() => onCellClick?.(scenario)}
                        onMouseEnter={() => setHoveredCell(scenario)}
                        onMouseLeave={() => setHoveredCell(null)}
                        className={`
                          w-8 h-8 rounded cursor-pointer transition-all
                          ${isHovered ? 'ring-2 ring-blue-500 ring-offset-1 scale-110' : ''}
                          ${scenario.status === 'FAIL' ? 'pattern-diagonal' : ''}
                        `}
                        style={{ backgroundColor: color }}
                        title={`${getStatusLabel(scenario.status)}: Adoption ${formatPercentage(scenario.adoption_rate)}, Contribution ${formatPercentage(scenario.contribution_rate)}`}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 p-3 min-w-[200px] z-10">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getCellColor(hoveredCell.status, hoveredCell.margin, 'PASS_FAIL') }}
            />
            <span className="font-semibold text-sm">{getStatusLabel(hoveredCell.status)}</span>
          </div>
          <div className="space-y-1 text-xs text-gray-600">
            <div className="flex justify-between">
              <span>Adoption Rate:</span>
              <span className="font-medium">{formatPercentage(hoveredCell.adoption_rate)}</span>
            </div>
            <div className="flex justify-between">
              <span>Contribution Rate:</span>
              <span className="font-medium">{formatPercentage(hoveredCell.contribution_rate)}</span>
            </div>
            <hr className="my-1" />
            <div className="flex justify-between">
              <span>NHCE ACP:</span>
              <span className="font-medium">{hoveredCell.nhce_acp?.toFixed(2) ?? 'N/A'}%</span>
            </div>
            <div className="flex justify-between">
              <span>HCE ACP:</span>
              <span className="font-medium">{hoveredCell.hce_acp?.toFixed(2) ?? 'N/A'}%</span>
            </div>
            <div className="flex justify-between">
              <span>Threshold:</span>
              <span className="font-medium">{hoveredCell.max_allowed_acp?.toFixed(2) ?? 'N/A'}%</span>
            </div>
            <div className="flex justify-between">
              <span>Margin:</span>
              <span className="font-medium">{formatMargin(hoveredCell.margin)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-green-500" />
          <span className="text-gray-600">Pass</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-amber-500" />
          <span className="text-gray-600">Risk</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-red-500" />
          <span className="text-gray-600">Fail</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-gray-500" />
          <span className="text-gray-600">Error</span>
        </div>
      </div>
    </div>
  )
}
