
import React, { useState, useMemo } from 'react';
import { Employee, ScenarioResult, EmployeeImpactDetail, ConstraintStatus } from '../types';
import { getEmployeeImpacts } from '../utils/acpLogic';

interface EmployeeImpactProps {
  employees: Employee[];
  scenario: ScenarioResult;
}

const EmployeeImpact: React.FC<EmployeeImpactProps> = ({ employees, scenario }) => {
  const [activeType, setActiveType] = useState<'hce' | 'nhce'>('hce');
  const [searchTerm, setSearchTerm] = useState('');
  const [constraintFilter, setConstraintFilter] = useState<ConstraintStatus | 'ALL'>('ALL');
  const [minComp, setMinComp] = useState<string>('');
  const [maxComp, setMaxComp] = useState<string>('');
  const [onlyMega, setOnlyMega] = useState(false);

  const impacts = useMemo(() => 
    getEmployeeImpacts(employees, scenario.adoptionRate, scenario.contributionRate), 
    [employees, scenario]
  );

  const filteredData = useMemo(() => {
    let subset = impacts.filter(e => activeType === 'hce' ? e.isHce : !e.isHce);
    
    if (searchTerm) {
      subset = subset.filter(e => e.id.toLowerCase().includes(searchTerm.toLowerCase()));
    }
    
    if (constraintFilter !== 'ALL' && activeType === 'hce') {
      subset = subset.filter(e => e.constraintStatus === constraintFilter);
    }

    if (minComp) {
      subset = subset.filter(e => e.compensation >= parseFloat(minComp));
    }

    if (maxComp) {
      subset = subset.filter(e => e.compensation <= parseFloat(maxComp));
    }

    if (onlyMega && activeType === 'hce') {
      subset = subset.filter(e => e.megaAmount > 0);
    }

    return subset;
  }, [impacts, activeType, searchTerm, constraintFilter, minComp, maxComp, onlyMega]);

  const summaryStats = useMemo(() => {
    const subset = impacts.filter(e => activeType === 'hce' ? e.isHce : !e.isHce);
    const avgAcp = subset.reduce((a, b) => a + b.individualAcp, 0) / subset.length;
    const constrainedCount = subset.filter(e => e.constraintStatus === ConstraintStatus.REDUCED || e.constraintStatus === ConstraintStatus.AT_LIMIT).length;
    
    return {
      avgAcp: avgAcp.toFixed(2),
      totalMega: subset.reduce((a, b) => a + b.megaAmount, 0).toLocaleString(),
      constrainedCount
    };
  }, [impacts, activeType]);

  const renderConstraintIcon = (status: ConstraintStatus) => {
    switch(status) {
      case ConstraintStatus.UNCONSTRAINED:
        return <div className="flex items-center space-x-1"><span className="text-emerald-500 font-black">✓</span><span className="text-[10px] text-gray-400 font-bold uppercase">Clear</span></div>;
      case ConstraintStatus.AT_LIMIT:
        return <div className="flex items-center space-x-1"><span className="text-rose-500 font-black">!</span><span className="text-[10px] text-rose-500 font-bold uppercase">Full</span></div>;
      case ConstraintStatus.REDUCED:
        return <div className="flex items-center space-x-1"><span className="text-amber-500 font-black">↓</span><span className="text-[10px] text-amber-500 font-bold uppercase">Limit</span></div>;
      default:
        return <span className="text-gray-200">—</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-8 rounded-3xl border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div className="space-y-2">
          <h2 className="text-2xl font-black text-gray-900 tracking-tighter uppercase">Detailed Impact Analysis</h2>
          <div className="flex items-center flex-wrap gap-2 text-xs font-bold">
            <span className="px-2 py-1 bg-indigo-50 text-indigo-600 rounded-lg">{scenario.adoptionRate}% Adoption Target</span>
            <span className="px-2 py-1 bg-indigo-50 text-indigo-600 rounded-lg">{scenario.contributionRate}% Applied Multiplier</span>
            <span className={`px-2 py-1 rounded-lg ${scenario.margin < 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>Current Margin: {scenario.margin}%</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-8 md:border-l border-gray-100 md:pl-8">
          <div className="flex flex-col">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Group Avg ACP</span>
            <span className="text-2xl font-black text-gray-900">{summaryStats.avgAcp}%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">New Volume</span>
            <span className="text-2xl font-black text-indigo-600">${summaryStats.totalMega}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">415 Constraints</span>
            <span className="text-2xl font-black text-amber-600">{summaryStats.constrainedCount}</span>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex bg-gray-100 p-1 rounded-xl shadow-inner shrink-0">
            <button onClick={() => setActiveType('hce')} className={`px-6 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${activeType === 'hce' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>HCEs</button>
            <button onClick={() => setActiveType('nhce')} className={`px-6 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${activeType === 'nhce' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>NHCEs</button>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full justify-end">
            {activeType === 'hce' && (
              <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
                <input type="checkbox" checked={onlyMega} onChange={e => setOnlyMega(e.target.checked)} className="rounded text-indigo-600" id="mega-only" />
                <label htmlFor="mega-only" className="text-[10px] font-black text-gray-500 uppercase cursor-pointer">Mega Only</label>
              </div>
            )}
            
            <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
              <span className="text-[10px] font-black text-gray-400 uppercase">Comp Range</span>
              <input type="number" placeholder="Min" value={minComp} onChange={e => setMinComp(e.target.value)} className="w-20 bg-transparent text-[11px] font-bold border-none focus:ring-0 p-0" />
              <span className="text-gray-300">-</span>
              <input type="number" placeholder="Max" value={maxComp} onChange={e => setMaxComp(e.target.value)} className="w-20 bg-transparent text-[11px] font-bold border-none focus:ring-0 p-0" />
            </div>

            <div className="relative">
              <input type="text" placeholder="Search Employee ID..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 pr-4 py-2 text-[11px] font-bold border border-gray-200 rounded-xl focus:ring-indigo-500 bg-gray-50 w-48" />
              <svg className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
            
            <button className="px-4 py-2 bg-slate-900 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-slate-800 shadow-lg shadow-slate-200">Export CSV</button>
          </div>
        </div>

        <div className="rounded-xl border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50/50">
                <tr>
                  <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">Employee Profile</th>
                  <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">Earnings</th>
                  <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">Base Pre-Tax</th>
                  <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">§415 Capacity</th>
                  {activeType === 'hce' && (
                    <>
                      <th className="px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest">Sim. Contribution</th>
                      <th className="px-6 py-4 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Constraint</th>
                    </>
                  )}
                  <th className="px-6 py-4 text-right text-[10px] font-black text-gray-400 uppercase tracking-widest">Impact ACP</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-50">
                {filteredData.slice(0, 150).map((emp) => (
                  <tr key={emp.id} className="hover:bg-indigo-50/30 transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <span className="text-xs font-black text-gray-900">{emp.id}</span>
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Plan Member · Active</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs font-bold text-gray-700">${Math.round(emp.compensation).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs font-bold text-gray-500">${Math.round(emp.preTax).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs font-bold text-gray-400">${Math.round(emp.availableRoom).toLocaleString()}</td>
                    {activeType === 'hce' && (
                      <>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {emp.megaAmount > 0 ? (
                            <span className="text-xs font-black text-indigo-600">${Math.round(emp.megaAmount).toLocaleString()}</span>
                          ) : (
                            <span className="text-xs font-black text-gray-200">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex justify-center">{renderConstraintIcon(emp.constraintStatus)}</div>
                        </td>
                      </>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className={`text-xs font-black px-2 py-1 rounded-lg ${activeType === 'hce' ? 'bg-indigo-50 text-indigo-700' : 'bg-gray-50 text-gray-700'}`}>
                        {emp.individualAcp.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredData.length === 0 && (
                  <tr><td colSpan={7} className="px-6 py-24 text-center text-gray-400 text-sm font-bold uppercase tracking-widest opacity-30 italic">No Employee Records Found</td></tr>
                )}
              </tbody>
            </table>
            {filteredData.length > 150 && (
              <div className="p-6 bg-gray-50/50 border-t border-gray-100 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">
                Optimization Active: Showing first 150 of {filteredData.length} relevant records.
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 px-2">
        <div className="flex flex-wrap justify-center gap-6">
          <div className="flex items-center space-x-2"><span className="text-emerald-500 font-black">✓</span><span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Full Contribution Feasible</span></div>
          <div className="flex items-center space-x-2"><span className="text-amber-500 font-black">↓</span><span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Capped by §415(c)</span></div>
          <div className="flex items-center space-x-2"><span className="text-rose-500 font-black">!</span><span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">No Remaining 415 Room</span></div>
        </div>
        <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-t md:border-t-0 pt-4 md:pt-0">
          Source Authority: 26 U.S. Code § 415(c) · 2024 Limitation ($69,000)
        </div>
      </div>
    </div>
  );
};

export default EmployeeImpact;
