
import React, { useState } from 'react';
import { REQUIRED_FIELDS } from '../constants';
import { Employee, CensusStats } from '../types';
import { generateCensusMock } from '../utils/acpLogic';

interface CensusUploadProps {
  onDataLoaded: (data: Employee[]) => void;
  currentData: Employee[];
}

const CensusUpload: React.FC<CensusUploadProps> = ({ onDataLoaded, currentData }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isMapping, setIsMapping] = useState(false);
  const [hceMode, setHceMode] = useState<'explicit' | 'threshold'>('threshold');
  const [hceThreshold, setHceThreshold] = useState(155000);

  const stats: CensusStats | null = currentData.length > 0 ? {
    totalCount: currentData.length,
    hceCount: currentData.filter(e => e.isHce).length,
    nhceCount: currentData.filter(e => !e.isHce).length,
    avgComp: currentData.reduce((a, b) => a + b.compensation, 0) / currentData.length,
    avgNhceAcp: (currentData.filter(e => !e.isHce).reduce((a, b) => a + (b.afterTax / b.compensation) * 100, 0) / currentData.filter(e => !e.isHce).length) || 0
  } : null;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setIsMapping(true);
    }
  };

  const finalizeImport = () => {
    // In a real app, this would parse the CSV using the mappings.
    // For this demo, we generate high-quality mock data based on user settings.
    const mockData = generateCensusMock(250);
    // Apply HCE logic
    const processed = mockData.map(e => ({
      ...e,
      isHce: hceMode === 'threshold' ? e.compensation >= hceThreshold : e.isHce
    }));
    onDataLoaded(processed);
    setIsMapping(false);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Upload Employee Census</h3>
            <p className="text-sm text-gray-500 mt-1">Import your census CSV to begin compliance testing.</p>
          </div>
          <div className="p-8 flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg m-6 bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer" onClick={() => document.getElementById('file-upload')?.click()}>
            <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm font-medium text-gray-700">{file ? file.name : 'Select CSV File'}</span>
            <input id="file-upload" type="file" className="hidden" accept=".csv" onChange={handleFileUpload} />
          </div>

          {isMapping && (
            <div className="p-6 bg-indigo-50 border-t border-indigo-100 animate-fade-in">
              <h4 className="font-semibold text-indigo-900 mb-4">Map CSV Columns</h4>
              <div className="grid grid-cols-2 gap-4 max-h-60 overflow-y-auto pr-2">
                {REQUIRED_FIELDS.map(field => (
                  <div key={field.id} className="flex items-center justify-between p-2 bg-white rounded border border-indigo-200">
                    <span className="text-xs font-semibold text-gray-600">{field.label}</span>
                    <select className="text-xs border-none bg-transparent text-indigo-600 font-medium focus:ring-0">
                      <option>Select column...</option>
                      <option selected>{field.label}</option>
                    </select>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button onClick={() => setIsMapping(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                <button onClick={finalizeImport} className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 shadow-sm font-medium">Finalize Import</button>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase">HCE Determination</label>
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button 
                    onClick={() => setHceMode('threshold')}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${hceMode === 'threshold' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500'}`}
                  >
                    Comp Threshold
                  </button>
                  <button 
                    onClick={() => setHceMode('explicit')}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${hceMode === 'explicit' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500'}`}
                  >
                    Explicit Flag
                  </button>
                </div>
              </div>
              {hceMode === 'threshold' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-2">THRESHOLD (2024)</label>
                  <input 
                    type="number" 
                    value={hceThreshold}
                    onChange={(e) => setHceThreshold(parseInt(e.target.value))}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              )}
            </div>
          </div>

          {stats && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
              <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Census Stats</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-[10px] font-bold text-gray-400 uppercase">HCE Count</span>
                  <span className="text-lg font-bold text-indigo-600">{stats.hceCount}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-[10px] font-bold text-gray-400 uppercase">NHCE Count</span>
                  <span className="text-lg font-bold text-indigo-600">{stats.nhceCount}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-[10px] font-bold text-gray-400 uppercase">Avg Comp</span>
                  <span className="text-sm font-bold text-gray-700">${Math.round(stats.avgComp).toLocaleString()}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-[10px] font-bold text-gray-400 uppercase">NHCE ACP</span>
                  <span className="text-sm font-bold text-gray-700">{stats.avgNhceAcp.toFixed(2)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CensusUpload;
