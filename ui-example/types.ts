
export interface Employee {
  id: string;
  ssn: string;
  dob: string;
  hireDate: string;
  compensation: number;
  preTax: number;
  afterTax: number;
  roth: number;
  match: number;
  nonElective: number;
  isHce: boolean;
}

export enum ConstraintStatus {
  UNCONSTRAINED = 'UNCONSTRAINED',
  AT_LIMIT = 'AT_LIMIT',
  REDUCED = 'REDUCED',
  NOT_SELECTED = 'NOT_SELECTED'
}

export interface EmployeeImpactDetail extends Employee {
  megaAmount: number;
  individualAcp: number;
  constraintStatus: ConstraintStatus;
  availableRoom: number;
}

export type ColumnMapping = {
  [K in keyof Omit<Employee, 'id' | 'isHce'>]: string;
};

export enum AnalysisStatus {
  PASS = 'PASS',
  RISK = 'RISK',
  FAIL = 'FAIL',
  ERROR = 'ERROR'
}

export interface ScenarioResult {
  adoptionRate: number;
  contributionRate: number;
  hceAcp: number;
  nhceAcp: number;
  threshold: number;
  margin: number;
  status: AnalysisStatus;
  id: string;
  timestamp: number;
}

export interface CensusStats {
  totalCount: number;
  hceCount: number;
  nhceCount: number;
  avgComp: number;
  avgNhceAcp: number;
}

export enum ViewMode {
  PASS_FAIL = 'PASS_FAIL',
  MARGIN = 'MARGIN',
  RISK_ZONE = 'RISK_ZONE'
}
