# Contribution Limits Validation
# Enforces all IRS contribution limits for 401(k) plans

import pandas as pd
from constants import config, get_annual_limit, DEFAULT_PLAN_YEAR

def validate_contribution_limits(df_census, mega_backdoor_contributions, plan_year=None):
    """
    Validate all contribution limits for each participant
    
    Args:
        df_census: DataFrame with employee data
        mega_backdoor_contributions: Series with additional after-tax contributions
        plan_year: Plan year for limits (uses default if None)
        
    Returns:
        dict: Validation results with any violations
    """
    if plan_year is None:
        plan_year = DEFAULT_PLAN_YEAR
    
    # Get limits for plan year
    limits = {
        'compensation_limit_401a17': get_annual_limit(plan_year, 'compensation_limit_401a17'),
        'elective_deferral_limit_402g': get_annual_limit(plan_year, 'elective_deferral_limit_402g'),
        'annual_additions_limit_415c': get_annual_limit(plan_year, 'annual_additions_limit_415c'),
        'catch_up_limit_414v': get_annual_limit(plan_year, 'catch_up_limit_414v'),
        'super_catch_up_limit': get_annual_limit(plan_year, 'super_catch_up_limit')
    }
    
    violations = []
    df = df_census.copy()
    
    # Add mega-backdoor contributions
    df['mega_backdoor_after_tax'] = mega_backdoor_contributions
    
    for idx, employee in df.iterrows():
        emp_id = employee['employee_id']
        compensation = employee['compensation']
        
        # § 402(g) - Elective Deferrals (pre-tax + Roth 401k)
        elective_deferrals = employee['ee_pre_tax_amt'] + employee['ee_roth_amt']
        if elective_deferrals > limits['elective_deferral_limit_402g']:
            violations.append({
                'employee_id': emp_id,
                'violation_type': '§ 402(g) Elective Deferral Limit',
                'limit': limits['elective_deferral_limit_402g'],
                'actual': elective_deferrals,
                'excess': elective_deferrals - limits['elective_deferral_limit_402g']
            })
        
        # § 415(c) - Annual Additions (all employee + employer contributions)
        annual_additions = (employee['ee_pre_tax_amt'] + employee['ee_after_tax_amt'] + 
                          employee['ee_roth_amt'] + employee['mega_backdoor_after_tax'] + 
                          employee['er_match_amt'])
        
        # § 415(c) limit is lesser of dollar limit or 100% of compensation
        effective_415c_limit = min(limits['annual_additions_limit_415c'], compensation)
        
        if annual_additions > effective_415c_limit:
            violations.append({
                'employee_id': emp_id,
                'violation_type': '§ 415(c) Annual Additions Limit',
                'limit': effective_415c_limit,
                'actual': annual_additions,
                'excess': annual_additions - effective_415c_limit,
                'note': f'Limit is lesser of ${limits["annual_additions_limit_415c"]:,} or 100% of compensation (${compensation:,})'
            })
    
    return {
        'plan_year': plan_year,
        'limits': limits,
        'violations': violations,
        'total_violations': len(violations),
        'affected_employees': len(set(v['employee_id'] for v in violations))
    }

def apply_contribution_limits(df_census, mega_backdoor_percent, plan_year=None):
    """
    Apply contribution limits and reduce mega-backdoor contributions if necessary
    
    Args:
        df_census: DataFrame with employee data
        mega_backdoor_percent: Percentage for mega-backdoor contributions
        plan_year: Plan year for limits (uses default if None)
        
    Returns:
        tuple: (adjusted_contributions, validation_results)
    """
    if plan_year is None:
        plan_year = DEFAULT_PLAN_YEAR
    
    # Get limits for plan year
    limits = {
        'compensation_limit_401a17': get_annual_limit(plan_year, 'compensation_limit_401a17'),
        'elective_deferral_limit_402g': get_annual_limit(plan_year, 'elective_deferral_limit_402g'),
        'annual_additions_limit_415c': get_annual_limit(plan_year, 'annual_additions_limit_415c'),
        'catch_up_limit_414v': get_annual_limit(plan_year, 'catch_up_limit_414v'),
        'super_catch_up_limit': get_annual_limit(plan_year, 'super_catch_up_limit')
    }
    
    df = df_census.copy()
    adjusted_contributions = pd.Series(0.0, index=df.index)
    adjustments = []
    
    for idx, employee in df.iterrows():
        emp_id = employee['employee_id']
        compensation = employee['compensation']
        
        # Calculate proposed mega-backdoor contribution
        proposed_mega_backdoor = compensation * (mega_backdoor_percent / 100)
        
        # Check § 415(c) limit
        current_additions = (employee['ee_pre_tax_amt'] + employee['ee_after_tax_amt'] + 
                           employee['ee_roth_amt'] + employee['er_match_amt'])
        
        # § 415(c) limit is lesser of dollar limit or 100% of compensation
        effective_415c_limit = min(limits['annual_additions_limit_415c'], compensation)
        
        # Available room under § 415(c)
        available_415c_room = max(0, effective_415c_limit - current_additions)
        
        # Apply the limit
        actual_mega_backdoor = min(proposed_mega_backdoor, available_415c_room)
        adjusted_contributions[idx] = actual_mega_backdoor
        
        # Record adjustment if needed
        if actual_mega_backdoor < proposed_mega_backdoor:
            adjustments.append({
                'employee_id': emp_id,
                'compensation': compensation,
                'proposed_mega_backdoor': proposed_mega_backdoor,
                'actual_mega_backdoor': actual_mega_backdoor,
                'reduction': proposed_mega_backdoor - actual_mega_backdoor,
                'limiting_factor': '§ 415(c) Annual Additions Limit',
                'available_room': available_415c_room,
                'current_additions': current_additions,
                'limit': effective_415c_limit
            })
    
    # Validate final contributions
    validation_results = validate_contribution_limits(df, adjusted_contributions, plan_year)
    
    return adjusted_contributions, {
        'plan_year': plan_year,
        'limits': limits,
        'adjustments': adjustments,
        'total_adjustments': len(adjustments),
        'affected_employees': len(adjustments),
        'validation': validation_results
    }

def display_contribution_limits_summary(results):
    """Display summary of contribution limits and any violations/adjustments"""
    print(f"\n" + "=" * 80)
    print(f"CONTRIBUTION LIMITS VALIDATION - {results['plan_year']} PLAN YEAR")
    print("=" * 80)
    
    # Display limits
    limits = results['limits']
    print(f"§ 402(g) Elective Deferral Limit: ${limits['elective_deferral_limit_402g']:,}")
    print(f"§ 415(c) Annual Additions Limit: ${limits['annual_additions_limit_415c']:,}")
    print(f"§ 401(a)(17) Compensation Limit: ${limits['compensation_limit_401a17']:,}")
    print(f"§ 414(v) Catch-up Limit (age 50+): ${limits['catch_up_limit_414v']:,}")
    if limits['super_catch_up_limit'] > 0:
        print(f"SECURE 2.0 Super Catch-up (age 60-63): ${limits['super_catch_up_limit']:,}")
    
    # Display adjustments if any
    if 'adjustments' in results and results['adjustments']:
        print(f"\n📊 CONTRIBUTION ADJUSTMENTS:")
        print(f"   {results['total_adjustments']} employees had mega-backdoor contributions reduced")
        for adj in results['adjustments']:
            print(f"   Employee {adj['employee_id']}: ${adj['proposed_mega_backdoor']:,.0f} → ${adj['actual_mega_backdoor']:,.0f} "
                  f"(reduction: ${adj['reduction']:,.0f})")
    
    # Display violations if any
    if 'validation' in results and results['validation']['violations']:
        print(f"\n⚠️  VIOLATIONS FOUND:")
        for violation in results['validation']['violations']:
            print(f"   Employee {violation['employee_id']}: {violation['violation_type']}")
            print(f"      Limit: ${violation['limit']:,}, Actual: ${violation['actual']:,}, Excess: ${violation['excess']:,}")
    else:
        print(f"\n✅ No contribution limit violations found")