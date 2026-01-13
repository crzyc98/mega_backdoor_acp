
import { Employee, ScenarioResult, AnalysisStatus, EmployeeImpactDetail, ConstraintStatus } from '../types';

const SECTION_415_LIMIT = 69000;

export const calculateThreshold = (nhceAcp: number): number => {
  const test1 = 1.25 * nhceAcp;
  const test2 = Math.min(2 + nhceAcp, 2 * nhceAcp);
  return Math.max(test1, test2);
};

export const getEmployeeImpacts = (
  employees: Employee[],
  adoptionRate: number,
  contributionRate: number
): EmployeeImpactDetail[] => {
  const hces = employees.filter(e => e.isHce);
  const numAdopters = Math.round(hces.length * (adoptionRate / 100));

  return employees.map((e, index) => {
    const isHce = e.isHce;
    const isAdopter = isHce && hces.indexOf(e) < numAdopters;
    
    const totalCurrent = e.preTax + e.roth + e.afterTax + e.match + e.nonElective;
    const room = Math.max(0, SECTION_415_LIMIT - totalCurrent);
    
    let megaAmount = 0;
    let constraintStatus = ConstraintStatus.NOT_SELECTED;

    if (isAdopter) {
      const requested = (contributionRate / 100) * e.compensation;
      megaAmount = Math.min(requested, room);
      
      if (room === 0) constraintStatus = ConstraintStatus.AT_LIMIT;
      else if (megaAmount < requested) constraintStatus = ConstraintStatus.REDUCED;
      else constraintStatus = ConstraintStatus.UNCONSTRAINED;
    }

    const individualAcp = ((e.afterTax + megaAmount) / e.compensation) * 100;

    return {
      ...e,
      megaAmount,
      individualAcp,
      constraintStatus,
      availableRoom: room
    };
  });
};

export const runScenario = (
  employees: Employee[],
  adoptionRate: number,
  contributionRate: number
): ScenarioResult => {
  const impacts = getEmployeeImpacts(employees, adoptionRate, contributionRate);
  
  const hceImpacts = impacts.filter(i => i.isHce);
  const nhceImpacts = impacts.filter(i => !i.isHce);

  const hceAcp = hceImpacts.reduce((a, b) => a + b.individualAcp, 0) / hceImpacts.length;
  const nhceAcp = nhceImpacts.reduce((a, b) => a + b.individualAcp, 0) / nhceImpacts.length;

  const threshold = calculateThreshold(nhceAcp);
  const margin = threshold - hceAcp;

  let status = AnalysisStatus.PASS;
  if (margin < 0) status = AnalysisStatus.FAIL;
  else if (margin < 0.25) status = AnalysisStatus.RISK;

  return {
    id: `res-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
    timestamp: Date.now(),
    adoptionRate,
    contributionRate,
    hceAcp: parseFloat(hceAcp.toFixed(3)),
    nhceAcp: parseFloat(nhceAcp.toFixed(3)),
    threshold: parseFloat(threshold.toFixed(3)),
    margin: parseFloat(margin.toFixed(3)),
    status
  };
};

export const generateCensusMock = (count: number = 200): Employee[] => {
  const employees: Employee[] = [];
  for (let i = 0; i < count; i++) {
    const isHce = Math.random() < 0.15;
    const comp = isHce 
      ? 160000 + Math.random() * 120000 
      : 45000 + Math.random() * 90000;
    
    employees.push({
      id: `EMP-${1000 + i}`,
      ssn: `***-**-${Math.floor(1000 + Math.random() * 9000)}`,
      dob: '1980-05-12',
      hireDate: '2018-03-20',
      compensation: comp,
      preTax: Math.min(23000, comp * 0.06),
      afterTax: 0,
      roth: 0,
      match: comp * 0.03,
      nonElective: comp * 0.02,
      isHce
    });
  }
  return employees;
};

export const getGridInsights = (results: ScenarioResult[]) => {
  const passes = results.filter(r => r.status === AnalysisStatus.PASS);
  const fails = results.filter(r => r.status === AnalysisStatus.FAIL);
  
  // Max safe rate is the highest contribution rate where at least 50% adoption still passes
  const safeAt50 = passes.filter(r => r.adoptionRate >= 50).sort((a,b) => b.contributionRate - a.contributionRate);
  const maxSafeRate = safeAt50.length > 0 ? safeAt50[0].contributionRate : 0;
  
  // First failure point: Lowest adoption and contribution rate that fails
  const firstFail = fails.sort((a,b) => a.contributionRate - b.contributionRate || a.adoptionRate - b.adoptionRate)[0];

  return {
    maxSafeRate,
    firstFail
  };
};
