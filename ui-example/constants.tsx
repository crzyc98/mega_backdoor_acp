
import React from 'react';

export const REQUIRED_FIELDS = [
  { id: 'ssn', label: 'SSN' },
  { id: 'dob', label: 'Date of Birth' },
  { id: 'hireDate', label: 'Hire Date' },
  { id: 'compensation', label: 'Compensation' },
  { id: 'preTax', label: 'Employee Pre-Tax' },
  { id: 'afterTax', label: 'Employee After-Tax' },
  { id: 'roth', label: 'Employee Roth' },
  { id: 'match', label: 'Employer Match' },
  { id: 'nonElective', label: 'Employer Non-Elective' },
];

export const STATUS_COLORS = {
  PASS: 'bg-emerald-500',
  RISK: 'bg-amber-400',
  FAIL: 'bg-rose-500',
  ERROR: 'bg-slate-400',
};

export const STATUS_ICONS = {
  PASS: (
    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
    </svg>
  ),
  RISK: (
    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  FAIL: (
    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  ERROR: (
    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};
