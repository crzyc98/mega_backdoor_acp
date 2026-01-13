
import React, { useState, useMemo } from 'react';
import { Employee, ScenarioResult, ViewMode, AnalysisStatus } from '../types';
import { runScenario, getGridInsights } from '../utils/acpLogic';
import Heatmap from './Heatmap';
import { STATUS_COLORS, STATUS_ICONS } from '../constants';

interface AnalysisDashboardProps {
  employees: Employee[];
  onViewImpact: (scenario: ScenarioResult) => void;
}

const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({ employees, onViewImpact }) => {
  const [activeTab, setActiveTab] = useState<'single' | 'grid' | 'history'>('grid');
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.PASS_FAIL);
  const [adoptionRate, setAdoptionRate] = useState(50);
  const [contributionRate, setContributionRate] = useState(5);
  const [gridResults, setGridResults] = useState<ScenarioResult[]>([]);
  const [history, setHistory] = useState<ScenarioResult[]>([]);
  const [singleResult, setSingleResult] = useState<ScenarioResult | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioResult | null>(null);

  const runSingle = () => {
    const result = runScenario(employees, adoptionRate, contributionRate);
    setSingleResult(result);
    setHistory(prev => [result, ...prev].slice(0, 15));
  };

  const runGridPreset = (type: 'standard' | 'fine' | 'custom') => {
    const adoptions = type === 'standard' 
      ? [10, 25, 50, 75, 100] 
      : [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
    
    const contributions = type === 'standard'
      ? [1, 3, 5, 7, 10, 15]
      : [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15];
    
    const results: ScenarioResult[] = [];
    for (const adopt of adoptions) {
      for (const cont of contributions) {
        results.push(runScenario(employees, adopt, cont));
      }
    }
    setGridResults(results);
  };

  const insights = useMemo(() => gridResults.length > 0 ? getGridInsights(gridResults) : null, [gridResults]);

  const stats = useMemo(() => {
    if (gridResults.length === 0) return null;
    return {
      passCount: gridResults.filter(r => r.status === AnalysisStatus.PASS).length,
      riskCount: gridResults.filter(r => r.status === AnalysisStatus.RISK).length,
      failCount: gridResults.filter(r => r.status === AnalysisStatus.FAIL).length,
      total: gridResults.length,
      minMargin: Math.min(...gridResults.map(r => r.margin)),
      maxMargin: Math.max(...gridResults.map(r => r.margin)),
    };
  }, [gridResults]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="bg-white p-1 rounded-xl shadow-sm border border-gray-200 inline-flex shrink-0">
          <button onClick={() => setActiveTab('grid')} className={`px-5 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'grid' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'}`}>Grid Analysis</button>
          <button onClick={() => setActiveTab('single')} className={`px-5 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'single' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'}`}>Single Scenario</button>
          <button onClick={() => setActiveTab('history')} className={`px-5 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'history' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-700'}`}>History</button>
        </div>

        {activeTab === 'grid' && (
          <div className="flex items-center space-x-3 bg-gray-50 p-1.5 rounded-xl border border-gray-200">
            <span className="text-[10px] font-black text-gray-400 uppercase px-2">Presets:</span>
            <button onClick={() => runGridPreset('standard')} className="px-3 py-1.5 text-xs font-bold text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:text-indigo-600 transition-all shadow-sm">5×6 Standard</button>
            <button onClick={() => runGridPreset('fine')} className="px-3 py-1.5 text-xs font-bold text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:text-indigo-600 transition-all shadow-sm">11×13 Fine</button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
            <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest">Simulation Inputs</h3>
            <div className="space-y-5">
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-[10px] font-bold text-gray-500 uppercase">Adoption Rate</label>
                  <span className="text-[11px] font-black text-indigo-600">{adoptionRate}%</span>
                </div>
                <input type="range" min="0" max="100" step="5" value={adoptionRate} onChange={(e) => setAdoptionRate(parseInt(e.target.value))} className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600" />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-[10px] font-bold text-gray-500 uppercase">Contribution Rate</label>
                  <span className="text-[11px] font-black text-indigo-600">{contributionRate}%</span>
                </div>
                <input type="range" min="0" max="15" step="0.5" value={contributionRate} onChange={(e) => setContributionRate(parseFloat(e.target.value))} className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600" />
              </div>
            </div>
            <button 
              onClick={activeTab === 'single' ? runSingle : () => runGridPreset('fine')}
              className="w-full py-4 bg-indigo-600 text-white rounded-xl font-black text-sm uppercase tracking-widest shadow-lg shadow-indigo-100 hover:bg-indigo-700 hover:shadow-indigo-200 transition-all flex items-center justify-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>
              <span>{activeTab === 'single' ? 'Simulate' : 'Run Matrix'}</span>
            </button>
          </div>

          {activeTab === 'grid' && stats && insights && (
            <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
              <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest">Compliance Metrics</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                  <span className="text-xs font-bold text-emerald-700">PASS</span>
                  <span className="text-lg font-black text-emerald-800">{stats.passCount}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-amber-50 rounded-xl border border-amber-100">
                  <span className="text-xs font-bold text-amber-700">RISK</span>
                  <span className="text-lg font-black text-amber-800">{stats.riskCount}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-rose-50 rounded-xl border border-rose-100">
                  <span className="text-xs font-bold text-rose-700">FAIL</span>
                  <span className="text-lg font-black text-rose-800">{stats.failCount}</span>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-gray-100">
                <div className="flex justify-between items-center group">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">Max Safe Rate</span>
                    <span className="text-xs text-gray-400 font-medium leading-none">@ 50% Adoption</span>
                  </div>
                  <span className="text-xl font-black text-emerald-600">{insights.maxSafeRate}%</span>
                </div>
                {insights.firstFail && (
                  <div className="flex justify-between items-center">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter">First Failure</span>
                      <span className="text-xs text-gray-400 font-medium leading-none">Critical Threshold</span>
                    </div>
                    <span className="text-xs font-black text-rose-600 text-right">
                      {insights.firstFail.contributionRate}% Rate @<br/>{insights.firstFail.adoptionRate}% Adopt
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-3">
          {activeTab === 'history' ? (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                <h3 className="font-black text-gray-900 text-sm uppercase tracking-widest">Analysis History</h3>
                <button onClick={() => setHistory([])} className="text-[10px] text-rose-600 font-black uppercase hover:underline tracking-widest">Clear Records</button>
              </div>
              <table className="min-w-full divide-y divide-gray-100">
                <thead className="bg-gray-50/30">
                  <tr>
                    <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-tighter">Execution Time</th>
                    <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-tighter">Configuration</th>
                    <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-tighter">Compliance Status</th>
                    <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-tighter">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {history.map(h => (
                    <tr key={h.id} className="hover:bg-indigo-50/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-medium">{new Date(h.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-bold text-gray-900">
                        {h.adoptionRate}% Adopted · {h.contributionRate}% Contrib.
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black text-white uppercase tracking-wider ${STATUS_COLORS[h.status]}`}>
                          {h.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button onClick={() => onViewImpact(h)} className="text-indigo-600 hover:text-indigo-900 text-[10px] font-black uppercase tracking-widest">Analysis</button>
                      </td>
                    </tr>
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-6 py-20 text-center text-gray-400 text-sm font-medium italic">No simulation history found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : activeTab === 'single' ? (
            <div className="bg-white p-12 rounded-2xl border border-gray-200 shadow-sm flex flex-col items-center justify-center text-center space-y-8 min-h-[500px] animate-in zoom-in-95 duration-300">
              {singleResult ? (
                <div className="space-y-10 w-full max-w-2xl">
                  <div className={`mx-auto w-32 h-32 rounded-full flex items-center justify-center shadow-xl ${STATUS_COLORS[singleResult.status]} ring-8 ring-offset-4 ${singleResult.status === AnalysisStatus.FAIL ? 'ring-rose-100' : 'ring-emerald-100'}`}>
                    <div className="transform scale-[2.5]">{STATUS_ICONS[singleResult.status]}</div>
                  </div>
                  <div>
                    <h2 className="text-4xl font-black text-gray-900 tracking-tighter uppercase">{singleResult.status}</h2>
                    <p className="text-gray-500 mt-2 font-medium">Compliance margin of <span className={`font-black ${singleResult.margin < 0 ? 'text-rose-600' : 'text-emerald-600'}`}>{singleResult.margin}%</span> against testing threshold.</p>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex flex-col items-center">
                      <span className="text-[10px] font-black text-gray-400 uppercase mb-2">HCE ACP</span>
                      <span className="text-2xl font-black text-gray-900">{singleResult.hceAcp}%</span>
                    </div>
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex flex-col items-center">
                      <span className="text-[10px] font-black text-gray-400 uppercase mb-2">NHCE ACP</span>
                      <span className="text-2xl font-black text-gray-900">{singleResult.nhceAcp}%</span>
                    </div>
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex flex-col items-center">
                      <span className="text-[10px] font-black text-gray-400 uppercase mb-2">Threshold</span>
                      <span className="text-2xl font-black text-gray-900">{singleResult.threshold}%</span>
                    </div>
                    <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex flex-col items-center">
                      <span className="text-[10px] font-black text-gray-400 uppercase mb-2">Margin</span>
                      <span className={`text-2xl font-black ${singleResult.margin < 0 ? 'text-rose-600' : 'text-emerald-600'}`}>{singleResult.margin}%</span>
                    </div>
                  </div>
                  <button onClick={() => onViewImpact(singleResult)} className="inline-flex items-center px-10 py-4 bg-slate-900 text-white font-black text-sm uppercase tracking-widest rounded-xl hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
                    Drill-down to Employees
                  </button>
                </div>
              ) : (
                <div className="text-gray-300">
                   <svg className="w-24 h-24 mx-auto mb-6 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                   <p className="text-xl font-bold max-w-xs mx-auto text-gray-400">Run a single scenario to see detailed testing breakdown.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex justify-between items-center bg-white p-4 rounded-2xl border border-gray-200 shadow-sm">
                <div className="flex bg-gray-100 p-1 rounded-xl">
                  <button onClick={() => setViewMode(ViewMode.PASS_FAIL)} className={`px-4 py-1.5 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${viewMode === ViewMode.PASS_FAIL ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500'}`}>Pass/Fail</button>
                  <button onClick={() => setViewMode(ViewMode.MARGIN)} className={`px-4 py-1.5 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${viewMode === ViewMode.MARGIN ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500'}`}>Margin Map</button>
                  <button onClick={() => setViewMode(ViewMode.RISK_ZONE)} className={`px-4 py-1.5 text-[10px] font-black uppercase tracking-wider rounded-lg transition-all ${viewMode === ViewMode.RISK_ZONE ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500'}`}>Risk Zones</button>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                    {gridResults.length > 0 ? `${gridResults.length} Matrix Points Generated` : 'Ready to Run'}
                  </div>
                  <button className="p-2 text-gray-400 hover:text-indigo-600 transition-colors">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  </button>
                </div>
              </div>
              
              {gridResults.length > 0 ? (
                <Heatmap data={gridResults} viewMode={viewMode} onCellClick={setSelectedScenario} />
              ) : (
                <div className="bg-white p-20 rounded-2xl border border-gray-200 shadow-sm flex flex-col items-center justify-center text-center text-gray-300 min-h-[400px]">
                   <svg className="w-24 h-24 mx-auto mb-6 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                   <p className="text-xl font-bold max-w-xs mx-auto text-gray-400 uppercase tracking-tight">Select a preset above to visualize the compliance frontier.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedScenario && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-8 duration-500 border border-white/20">
            <div className={`p-8 text-white flex justify-between items-center ${STATUS_COLORS[selectedScenario.status]} shadow-inner`}>
              <div>
                <h3 className="text-2xl font-black uppercase tracking-tighter">Scenario Insight</h3>
                <p className="text-sm font-bold opacity-80 uppercase tracking-widest">{selectedScenario.adoptionRate}% Adopted · {selectedScenario.contributionRate}% Contrib.</p>
              </div>
              <button onClick={() => setSelectedScenario(null)} className="p-2 hover:bg-white/20 rounded-full transition-all group">
                <svg className="w-7 h-7 group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div className="p-8 space-y-8">
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-gray-50/80 p-5 rounded-2xl border border-gray-100 flex flex-col">
                  <span className="text-[10px] font-black text-gray-400 uppercase mb-1 tracking-wider">HCE ACP</span>
                  <span className="text-2xl font-black text-gray-900 leading-none">{selectedScenario.hceAcp}%</span>
                </div>
                <div className="bg-gray-50/80 p-5 rounded-2xl border border-gray-100 flex flex-col">
                  <span className="text-[10px] font-black text-gray-400 uppercase mb-1 tracking-wider">Threshold</span>
                  <span className="text-2xl font-black text-gray-900 leading-none">{selectedScenario.threshold}%</span>
                </div>
              </div>
              <div className="p-6 bg-indigo-50/50 rounded-2xl border border-indigo-100 flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="text-[10px] font-black text-indigo-900/50 uppercase tracking-widest">Compliance Margin</span>
                  <span className="text-xs font-bold text-indigo-900 opacity-60">Delta to Failure</span>
                </div>
                <span className={`text-4xl font-black tracking-tighter ${selectedScenario.margin < 0 ? 'text-rose-600' : 'text-emerald-600'}`}>{selectedScenario.margin}%</span>
              </div>
              <button 
                onClick={() => {
                  onViewImpact(selectedScenario);
                  setSelectedScenario(null);
                }}
                className="w-full py-5 bg-slate-900 text-white rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center space-x-3 shadow-2xl shadow-slate-200"
              >
                <span>Full Employee Audit</span>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" /></svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisDashboard;
