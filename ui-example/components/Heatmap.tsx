
import React, { useState } from 'react';
import { ScenarioResult, ViewMode, AnalysisStatus } from '../types';
import { STATUS_COLORS, STATUS_ICONS } from '../constants';

interface HeatmapProps {
  data: ScenarioResult[];
  viewMode: ViewMode;
  onCellClick: (scenario: ScenarioResult) => void;
}

const Heatmap: React.FC<HeatmapProps> = ({ data, viewMode, onCellClick }) => {
  const [hoveredCell, setHoveredCell] = useState<ScenarioResult | null>(null);

  const adoptions = Array.from(new Set(data.map(d => d.adoptionRate))).sort((a: number, b: number) => b - a);
  const contributions = Array.from(new Set(data.map(d => d.contributionRate))).sort((a: number, b: number) => a - b);

  const getCellStyles = (scenario: ScenarioResult) => {
    let classes = `w-14 h-11 m-0.5 rounded cursor-pointer transition-all hover:scale-110 flex items-center justify-center relative group overflow-hidden border border-black/5 `;
    
    if (viewMode === ViewMode.PASS_FAIL) {
      classes += STATUS_COLORS[scenario.status];
      // Add subtle patterns for colorblindness
      if (scenario.status === AnalysisStatus.FAIL) {
        classes += " [background-image:linear-gradient(45deg,rgba(0,0,0,0.1)_25%,transparent_25%,transparent_50%,rgba(0,0,0,0.1)_50%,rgba(0,0,0,0.1)_75%,transparent_75%,transparent)] [background-size:8px_8px]";
      }
    } else if (viewMode === ViewMode.MARGIN) {
      if (scenario.status === AnalysisStatus.FAIL) classes += ' bg-rose-500';
      else {
        const intensity = Math.max(10, Math.min(100, (scenario.margin / 3) * 100));
        classes += ' bg-emerald-500';
        return { className: classes, style: { opacity: `${intensity}%` } };
      }
    } else if (viewMode === ViewMode.RISK_ZONE) {
      classes += scenario.status === AnalysisStatus.RISK ? ' bg-amber-400 ring-2 ring-amber-600 ring-inset z-10' : ' bg-slate-200 opacity-40';
    }
    
    return { className: classes };
  };

  return (
    <div className="relative bg-white p-6 rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
      <div className="min-w-max pb-8">
        <div className="flex">
          <div className="w-20 shrink-0" />
          <div className="flex">
            {contributions.map(rate => (
              <div key={rate} className="w-14 text-center text-[9px] font-bold text-gray-400 uppercase py-2 tracking-tighter">
                {rate}%
              </div>
            ))}
          </div>
        </div>
        
        {adoptions.map(adopt => (
          <div key={adopt} className="flex items-center">
            <div className="w-20 shrink-0 text-right pr-3 text-[9px] font-bold text-gray-400 uppercase tracking-tighter">
              {adopt}% ADPT
            </div>
            <div className="flex">
              {contributions.map(cont => {
                const scenario = data.find(d => d.adoptionRate === adopt && d.contributionRate === cont)!;
                const styles = getCellStyles(scenario);
                return (
                  <div
                    key={`${adopt}-${cont}`}
                    {...styles}
                    onClick={() => onCellClick(scenario)}
                    onMouseEnter={() => setHoveredCell(scenario)}
                    onMouseLeave={() => setHoveredCell(null)}
                    aria-label={`Adoption ${adopt}%, Contribution ${cont}%: ${scenario.status}`}
                  >
                    {viewMode === ViewMode.PASS_FAIL && (
                      <span className="drop-shadow-sm scale-75">{STATUS_ICONS[scenario.status]}</span>
                    )}
                    {viewMode === ViewMode.MARGIN && (
                      <span className="text-[9px] font-black text-white drop-shadow-sm">
                        {scenario.margin > 0 ? `+${scenario.margin}` : scenario.margin}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        <div className="flex mt-2">
          <div className="w-20" />
          <div className="flex-1 text-center text-[10px] font-bold text-gray-400 uppercase tracking-widest pt-4">
            Contribution Multiplier →
          </div>
        </div>
      </div>

      <div className="absolute top-1/2 -left-16 -rotate-90 text-[10px] font-bold text-gray-400 uppercase tracking-widest h-0 w-0 flex items-center justify-center pointer-events-none">
        Adoption Rate →
      </div>

      {hoveredCell && (
        <div 
          className="absolute z-50 bg-slate-900/95 backdrop-blur shadow-2xl p-4 rounded-lg text-white text-[11px] w-56 border border-white/10 pointer-events-none animate-in fade-in zoom-in duration-200"
          style={{ bottom: '24px', right: '24px' }}
        >
          <div className="font-black text-[10px] uppercase tracking-widest text-indigo-400 border-b border-white/10 mb-2 pb-1 flex justify-between">
            <span>Scenario Data</span>
            <span className={hoveredCell.status === AnalysisStatus.PASS ? 'text-emerald-400' : 'text-rose-400'}>{hoveredCell.status}</span>
          </div>
          <div className="grid grid-cols-2 gap-y-1.5">
            <span className="text-gray-400">Adoption:</span> <span className="text-right font-bold">{hoveredCell.adoptionRate}%</span>
            <span className="text-gray-400">Contribution:</span> <span className="text-right font-bold">{hoveredCell.contributionRate}%</span>
            <span className="text-gray-400">HCE ACP:</span> <span className="text-right font-bold">{hoveredCell.hceAcp}%</span>
            <span className="text-gray-400">Threshold:</span> <span className="text-right font-bold">{hoveredCell.threshold}%</span>
            <div className="col-span-2 border-t border-white/10 mt-1.5 pt-1.5 flex justify-between font-black text-sm">
              <span>MARGIN</span>
              <span className={hoveredCell.margin < 0 ? 'text-rose-400' : 'text-emerald-400'}>
                {hoveredCell.margin}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Heatmap;
