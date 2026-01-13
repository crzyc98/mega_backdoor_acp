
import React, { useState } from 'react';
import Layout from './components/Layout';
import CensusUpload from './components/CensusUpload';
import AnalysisDashboard from './components/AnalysisDashboard';
import EmployeeImpact from './components/EmployeeImpact';
import { Employee, ScenarioResult } from './types';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [censusData, setCensusData] = useState<Employee[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioResult | null>(null);

  const handleCensusLoaded = (data: Employee[]) => {
    setCensusData(data);
    setActiveTab('analysis');
  };

  const handleViewImpact = (scenario: ScenarioResult) => {
    setSelectedScenario(scenario);
    setActiveTab('impact');
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'upload' && (
        <CensusUpload onDataLoaded={handleCensusLoaded} currentData={censusData} />
      )}
      
      {activeTab === 'analysis' && (
        censusData.length > 0 ? (
          <AnalysisDashboard 
            employees={censusData} 
            onViewImpact={handleViewImpact} 
          />
        ) : (
          <div className="bg-white p-20 rounded-2xl border border-gray-200 text-center shadow-sm">
            <div className="bg-indigo-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">No Census Data Found</h2>
            <p className="text-gray-500 mt-2 max-w-sm mx-auto">Please upload your employee data in the Census tab before running a compliance analysis.</p>
            <button 
              onClick={() => setActiveTab('upload')}
              className="mt-8 px-8 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-lg hover:bg-indigo-700 transition-all"
            >
              Go to Upload
            </button>
          </div>
        )
      )}

      {activeTab === 'impact' && (
        selectedScenario ? (
          <EmployeeImpact employees={censusData} scenario={selectedScenario} />
        ) : (
          <div className="bg-white p-20 rounded-2xl border border-gray-200 text-center shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900">No Scenario Selected</h2>
            <p className="text-gray-500 mt-2">Run an analysis first and click "View Impact" on a specific result.</p>
            <button 
              onClick={() => setActiveTab('analysis')}
              className="mt-8 px-8 py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-lg hover:bg-indigo-700 transition-all"
            >
              Go to Analysis
            </button>
          </div>
        )
      )}

      {activeTab === 'export' && (
        <div className="max-w-3xl mx-auto space-y-8 py-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-extrabold text-gray-900">Export Compliance Report</h2>
            <p className="text-gray-500">Generate audit-ready documentation for IRS nondiscrimination testing.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer border-t-4 border-t-indigo-500">
              <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Audit PDF Report</h3>
              <p className="text-sm text-gray-500 mb-6">A formatted document showing testing methodology, summary results, and pass/fail certification.</p>
              <button className="w-full py-3 border-2 border-indigo-600 text-indigo-600 font-bold rounded-xl hover:bg-indigo-50">Generate PDF</button>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer border-t-4 border-t-emerald-500">
              <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Full Census CSV</h3>
              <p className="text-sm text-gray-500 mb-6">Comprehensive raw data including all calculated employee-level ACPs for external validation.</p>
              <button className="w-full py-3 border-2 border-emerald-600 text-emerald-600 font-bold rounded-xl hover:bg-emerald-50">Download Data</button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default App;
