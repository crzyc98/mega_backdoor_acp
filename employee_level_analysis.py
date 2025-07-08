"""
Employee-Level Analysis for ACP Sensitivity Analyzer
Shows detailed breakdown of individual employee contributions and impact
"""

import pandas as pd
import numpy as np
from acp_calculator import load_census, calculate_acp_for_scenario
from contribution_limits import apply_contribution_limits
from constants import RANDOM_SEED

def analyze_employee_level_scenario(df_census, hce_adoption_rate, hce_contribution_percent, scenario_name=""):
    """
    Analyze a single scenario with detailed employee-level breakdown
    
    Returns:
        dict: Contains both scenario summary and detailed employee data
    """
    # Work with a copy
    df = df_census.copy()
    
    # Separate HCEs and NHCEs
    hce_mask = df['is_hce']
    nhce_data = df[~hce_mask].copy()
    hce_data = df[hce_mask].copy()
    
    # Calculate baseline NHCE ACP contributions (only matching + after-tax per IRC §401(m))
    nhce_data['acp_contributions'] = (
        nhce_data['er_match_amt'] + nhce_data['ee_after_tax_amt']
    )
    nhce_data['acp_contribution_rate'] = (
        nhce_data['acp_contributions'] / nhce_data['compensation'] * 100
    )
    
    # Calculate total baseline contributions for display
    nhce_data['total_baseline_contributions'] = (
        nhce_data['er_match_amt'] + nhce_data['ee_pre_tax_amt'] + 
        nhce_data['ee_after_tax_amt'] + nhce_data['ee_roth_amt']
    )
    nhce_data['baseline_contribution_rate'] = (
        nhce_data['total_baseline_contributions'] / nhce_data['compensation'] * 100
    )
    
    # Simulate HCE mega-backdoor adoption
    n_adopters = int(len(hce_data) * hce_adoption_rate)
    
    # Select HCEs who will contribute (reproducible)
    np.random.seed(RANDOM_SEED)
    if n_adopters > 0:
        adopters = np.random.choice(hce_data.index, size=n_adopters, replace=False)
    else:
        adopters = []
    
    # Calculate HCE contributions with contribution limits
    hce_data['mega_backdoor_contribution'] = 0.0
    hce_data['uses_mega_backdoor'] = False
    
    if len(adopters) > 0:
        # Apply contribution limits to mega-backdoor contributions
        adjusted_contributions, limits_results = apply_contribution_limits(
            hce_data.loc[adopters], hce_contribution_percent
        )
        hce_data.loc[adopters, 'mega_backdoor_contribution'] = adjusted_contributions
        hce_data.loc[adopters, 'uses_mega_backdoor'] = True
        
        # Display any adjustments made
        if limits_results['total_adjustments'] > 0:
            print(f"  📊 § 415(c) adjustments made: {limits_results['total_adjustments']} employees affected")
            for adj in limits_results['adjustments']:
                print(f"    Employee {adj['employee_id']}: ${adj['proposed_mega_backdoor']:,.0f} → ${adj['actual_mega_backdoor']:,.0f}")
    else:
        print("  📊 No HCE employees selected for mega-backdoor contributions")
    
    # Calculate ACP contributions for HCEs (only matching + after-tax per IRC §401(m))
    hce_data['acp_contributions'] = (
        hce_data['er_match_amt'] + hce_data['ee_after_tax_amt'] + hce_data['mega_backdoor_contribution']
    )
    hce_data['acp_contribution_rate'] = (
        hce_data['acp_contributions'] / hce_data['compensation'] * 100
    )
    
    # Calculate total contributions for display
    hce_data['total_baseline_contributions'] = (
        hce_data['er_match_amt'] + hce_data['ee_pre_tax_amt'] + 
        hce_data['ee_after_tax_amt'] + hce_data['ee_roth_amt']
    )
    hce_data['total_contributions'] = (
        hce_data['total_baseline_contributions'] + hce_data['mega_backdoor_contribution']
    )
    hce_data['baseline_contribution_rate'] = (
        hce_data['total_baseline_contributions'] / hce_data['compensation'] * 100
    )
    hce_data['total_contribution_rate'] = (
        hce_data['total_contributions'] / hce_data['compensation'] * 100
    )
    
    # Calculate ACP test results (use ACP contributions, not total contributions)
    nhce_acp = nhce_data['acp_contribution_rate'].mean()
    hce_acp = hce_data['acp_contribution_rate'].mean()
    
    # IRS two-part test (pass if HCE ACP ≤ either limit, not both)
    from constants import ACP_MULTIPLIER, ACP_ADDER
    limit_a = nhce_acp * ACP_MULTIPLIER
    limit_b = nhce_acp + ACP_ADDER
    
    # Pass if HCE ACP is ≤ either limit (not both)
    passed_limit_a = hce_acp <= limit_a
    passed_limit_b = hce_acp <= limit_b
    passed = passed_limit_a or passed_limit_b
    
    # For reporting purposes, use the higher limit (more generous)
    max_allowed_hce_acp = max(limit_a, limit_b)
    margin = max_allowed_hce_acp - hce_acp
    
    return {
        'scenario_summary': {
            'scenario_name': scenario_name,
            'hce_adoption_rate': hce_adoption_rate,
            'hce_contribution_percent': hce_contribution_percent,
            'nhce_acp': round(nhce_acp, 3),
            'hce_acp': round(hce_acp, 3),
            'max_allowed_hce_acp': round(max_allowed_hce_acp, 3),
            'margin': round(margin, 3),
            'pass_fail': 'PASS' if passed else 'FAIL',
            'total_mega_backdoor_users': len(adopters),
            'total_mega_backdoor_dollars': hce_data['mega_backdoor_contribution'].sum()
        },
        'nhce_details': nhce_data[[
            'employee_id', 'compensation', 'er_match_amt', 'ee_pre_tax_amt', 
            'ee_after_tax_amt', 'ee_roth_amt', 'total_baseline_contributions', 
            'baseline_contribution_rate'
        ]].round(2),
        'hce_details': hce_data[[
            'employee_id', 'compensation', 'er_match_amt', 'ee_pre_tax_amt', 
            'ee_after_tax_amt', 'ee_roth_amt', 'total_baseline_contributions',
            'baseline_contribution_rate', 'uses_mega_backdoor', 'mega_backdoor_contribution',
            'total_contributions', 'total_contribution_rate', 'acp_contributions', 'acp_contribution_rate'
        ]].round(2)
    }

def display_employee_level_analysis(analysis_result):
    """Display detailed employee-level analysis"""
    summary = analysis_result['scenario_summary']
    nhce_details = analysis_result['nhce_details']
    hce_details = analysis_result['hce_details']
    
    print("=" * 80)
    print(f"EMPLOYEE-LEVEL ANALYSIS: {summary['scenario_name']}")
    print("=" * 80)
    
    # Scenario summary
    print(f"📊 SCENARIO PARAMETERS:")
    print(f"   HCE Adoption Rate: {summary['hce_adoption_rate']*100:.0f}%")
    print(f"   HCE Contribution Rate: {summary['hce_contribution_percent']:.1f}%")
    print(f"   Result: {summary['pass_fail']} (Margin: {summary['margin']:+.2f}%)")
    
    # Mega-backdoor usage summary
    print(f"\n🎯 MEGA-BACKDOOR USAGE:")
    print(f"   Total Users: {summary['total_mega_backdoor_users']} employees")
    print(f"   Total Dollars: ${summary['total_mega_backdoor_dollars']:,.0f}")
    print(f"   Average per User: ${summary['total_mega_backdoor_dollars']/max(summary['total_mega_backdoor_users'], 1):,.0f}")
    
    # NHCE Details
    print(f"\n👥 NHCE EMPLOYEES ({len(nhce_details)} employees):")
    print(f"   Average Contribution Rate: {summary['nhce_acp']:.2f}%")
    print("   " + "-" * 70)
    for _, employee in nhce_details.iterrows():
        print(f"   ID {employee['employee_id']}: ${employee['compensation']:,.0f} comp → "
              f"${employee['total_baseline_contributions']:,.0f} contrib ({employee['baseline_contribution_rate']:.1f}%)")
    
    # HCE Details
    print(f"\n🏆 HCE EMPLOYEES ({len(hce_details)} employees):")
    print(f"   Average ACP Rate: {summary['hce_acp']:.2f}%")
    print("   " + "-" * 90)
    for _, employee in hce_details.iterrows():
        mega_status = "✅ USES MEGA-BACKDOOR" if employee['uses_mega_backdoor'] else "❌ No mega-backdoor"
        baseline_str = f"${employee['total_baseline_contributions']:,.0f}"
        mega_str = f"${employee['mega_backdoor_contribution']:,.0f}" if employee['uses_mega_backdoor'] else "$0"
        total_str = f"${employee['total_contributions']:,.0f}"
        acp_str = f"${employee['acp_contributions']:,.0f}"
        
        # Check § 415(c) limit compliance
        from constants import get_annual_limit, DEFAULT_PLAN_YEAR
        limit_415c = get_annual_limit(DEFAULT_PLAN_YEAR, 'annual_additions_limit_415c')
        effective_limit = min(limit_415c, employee['compensation'])
        compliance = "✅" if employee['total_contributions'] <= effective_limit else "⚠️ EXCEEDS LIMIT"
        
        print(f"   ID {employee['employee_id']}: ${employee['compensation']:,.0f} comp → "
              f"{baseline_str} baseline + {mega_str} mega = {total_str} total "
              f"({employee['total_contribution_rate']:.1f}%) | ACP: {acp_str} ({employee['acp_contribution_rate']:.1f}%) "
              f"| § 415(c): {compliance} {mega_status}")
    
    # Impact analysis
    mega_backdoor_users = hce_details[hce_details['uses_mega_backdoor'] == True]
    non_users = hce_details[hce_details['uses_mega_backdoor'] == False]
    
    if len(mega_backdoor_users) > 0:
        print(f"\n📈 IMPACT ANALYSIS:")
        print(f"   Mega-backdoor users avg rate: {mega_backdoor_users['total_contribution_rate'].mean():.2f}%")
        print(f"   Non-users avg rate: {non_users['total_contribution_rate'].mean():.2f}%")
        print(f"   Contribution rate increase: {mega_backdoor_users['total_contribution_rate'].mean() - mega_backdoor_users['baseline_contribution_rate'].mean():.2f}%")

def run_employee_level_scenarios():
    """Run multiple scenarios with employee-level analysis"""
    print("🔍 LOADING EMPLOYEE-LEVEL ANALYSIS...")
    
    # Load census data
    df_census = load_census()
    
    # Define interesting scenarios to analyze
    scenarios = [
        {"adoption": 0.0, "contribution": 8.0, "name": "No Adoption (Baseline)"},
        {"adoption": 0.25, "contribution": 8.0, "name": "25% Adoption, 8% Contribution"},
        {"adoption": 0.5, "contribution": 8.0, "name": "50% Adoption, 8% Contribution"},
        {"adoption": 1.0, "contribution": 6.0, "name": "100% Adoption, 6% Contribution"},
        {"adoption": 1.0, "contribution": 12.0, "name": "100% Adoption, 12% Contribution (Aggressive)"},
    ]
    
    for scenario in scenarios:
        analysis = analyze_employee_level_scenario(
            df_census, 
            scenario["adoption"], 
            scenario["contribution"], 
            scenario["name"]
        )
        display_employee_level_analysis(analysis)
        print("\n" + "=" * 80 + "\n")

def export_employee_level_data():
    """Export employee-level analysis to CSV"""
    df_census = load_census()
    
    # Analyze a few key scenarios and export
    scenarios = [
        {"adoption": 0.25, "contribution": 8.0, "name": "25pct_adoption_8pct_contrib"},
        {"adoption": 0.5, "contribution": 8.0, "name": "50pct_adoption_8pct_contrib"},
        {"adoption": 1.0, "contribution": 6.0, "name": "100pct_adoption_6pct_contrib"},
    ]
    
    for scenario in scenarios:
        analysis = analyze_employee_level_scenario(
            df_census, 
            scenario["adoption"], 
            scenario["contribution"], 
            scenario["name"]
        )
        
        # Export HCE details (most interesting)
        filename = f"employee_level_hce_{scenario['name']}.csv"
        analysis['hce_details'].to_csv(filename, index=False)
        print(f"✓ Exported HCE employee details to: {filename}")
        
        # Export NHCE details
        filename = f"employee_level_nhce_{scenario['name']}.csv"
        analysis['nhce_details'].to_csv(filename, index=False)
        print(f"✓ Exported NHCE employee details to: {filename}")

if __name__ == "__main__":
    # Run employee-level analysis
    run_employee_level_scenarios()
    
    # Export detailed data
    print("\n" + "=" * 80)
    print("EXPORTING EMPLOYEE-LEVEL DATA...")
    print("=" * 80)
    export_employee_level_data()