import pandas as pd
import numpy as np
from datetime import datetime
from acp_calculator import load_census, run_scenario_grid
from constants import RESULTS_FILE, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES
from enhancements import run_all_enhancements

def create_summary_pivot(results_df):
    """Create pivot table summary for easy visualization"""
    pivot = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )
    
    # Convert to numeric (1 = PASS, 0 = FAIL) for better visualization
    pivot_numeric = pivot.map(lambda x: 1 if x == 'PASS' else 0)
    
    return pivot, pivot_numeric

def display_detailed_calculations(results_df, adoption_rates, contribution_rates):
    """Display detailed ACP calculations for each scenario"""
    print("\n" + "=" * 100)
    print("DETAILED ACP CALCULATIONS")
    print("=" * 100)
    print("Formula: ACP = (Matching + After-Tax Contributions ÷ Total Compensation) × 100")
    print("IRS Test: HCE ACP ≤ min(NHCE ACP × 1.25, NHCE ACP + 2.0)")
    print("Note: ACP test only includes matching and after-tax contributions per IRC §401(m)")
    print("=" * 100)
    
    for adopt_rate in adoption_rates:
        for contrib_rate in contribution_rates:
            # Get scenario data
            scenario = results_df[
                (results_df['hce_adoption_rate'] == adopt_rate) &
                (results_df['hce_contribution_percent'] == contrib_rate)
            ].iloc[0]
            
            print(f"\n📊 Scenario: {adopt_rate*100:.0f}% adoption, {contrib_rate:.1f}% contribution")
            print(f"   ├─ NHCE Group ({int(scenario['nhce_count'])} employees):")
            print(f"   │  ├─ Matching + After-Tax Contributions: ${scenario['nhce_total_contributions']:,.0f}")
            print(f"   │  ├─ Total Compensation: ${scenario['nhce_total_compensation']:,.0f}")
            print(f"   │  └─ ACP: ${scenario['nhce_total_contributions']:,.0f} ÷ ${scenario['nhce_total_compensation']:,.0f} × 100 = {scenario['nhce_acp']:.3f}%")
            print(f"   │")
            print(f"   ├─ HCE Group ({int(scenario['hce_count'])} employees, {scenario['n_hce_contributors']} contributing):")
            print(f"   │  ├─ Baseline (Matching + After-Tax): ${scenario['hce_baseline_contributions']:,.0f}")
            print(f"   │  ├─ Mega-Backdoor After-Tax: ${scenario['hce_mega_backdoor_contributions']:,.0f}")
            print(f"   │  ├─ Total ACP Contributions: ${scenario['hce_total_contributions']:,.0f}")
            print(f"   │  ├─ Total Compensation: ${scenario['hce_total_compensation']:,.0f}")
            print(f"   │  └─ ACP: ${scenario['hce_total_contributions']:,.0f} ÷ ${scenario['hce_total_compensation']:,.0f} × 100 = {scenario['hce_acp']:.3f}%")
            print(f"   │")
            print(f"   └─ IRS Test Results:")
            print(f"      ├─ Limit A: {scenario['nhce_acp']:.3f}% × 1.25 = {scenario['nhce_acp'] * 1.25:.3f}%")
            print(f"      ├─ Limit B: {scenario['nhce_acp']:.3f}% + 2.0 = {scenario['nhce_acp'] + 2.0:.3f}%")
            print(f"      ├─ Max Allowed: min({scenario['nhce_acp'] * 1.25:.3f}%, {scenario['nhce_acp'] + 2.0:.3f}%) = {scenario['max_allowed_hce_acp']:.3f}%")
            print(f"      ├─ Margin: {scenario['max_allowed_hce_acp']:.3f}% - {scenario['hce_acp']:.3f}% = {scenario['margin']:+.3f}%")
            print(f"      └─ Result: {scenario['pass_fail']}")
            print(f"   {'-' * 90}")

def display_summary_matrix(results_df, adoption_rates, contribution_rates):
    """Display pass/fail matrix with visual symbols"""
    print("\n" + "=" * 50)
    print("SUMMARY MATRIX (PASS = ✓, FAIL = ✗)")
    print("=" * 50)
    
    # Header row
    print(f"{'Contrib %':<10}", end='')
    for rate in adoption_rates:
        print(f"{rate*100:.0f}% adopt".center(12), end='')
    print()
    print("-" * 70)
    
    # Data rows
    for contrib_rate in contribution_rates:
        print(f"{contrib_rate:>8.1f}%  ", end='')
        for adopt_rate in adoption_rates:
            result = results_df[
                (results_df['hce_adoption_rate'] == adopt_rate) &
                (results_df['hce_contribution_percent'] == contrib_rate)
            ]['pass_fail'].values[0]
            
            symbol = "   ✓   " if result == 'PASS' else "   ✗   "
            print(symbol.center(12), end='')
        print()

def extract_key_insights(results_df):
    """Extract and display key insights from results"""
    print("\n" + "=" * 50)
    print("KEY INSIGHTS")
    print("=" * 50)
    
    # Find failure scenarios
    fail_scenarios = results_df[results_df['pass_fail'] == 'FAIL']
    pass_scenarios = results_df[results_df['pass_fail'] == 'PASS']
    
    if len(fail_scenarios) > 0:
        # Find first failure (lowest risk threshold)
        first_fail = fail_scenarios.iloc[0]
        print(f"⚠️  First failure at: {first_fail['hce_adoption_rate']*100:.0f}% adoption, "
              f"{first_fail['hce_contribution_percent']:.1f}% contribution")
        
        # Find maximum safe contribution
        if len(pass_scenarios) > 0:
            max_safe = pass_scenarios['hce_contribution_percent'].max()
            print(f"✓ Safe zone: Up to {max_safe:.1f}% contribution at any adoption rate")
        
        # Additional insights
        worst_margin = fail_scenarios['margin'].min()
        print(f"📊 Worst case margin: {worst_margin:.2f}% (most severe failure)")
        
        # Risk analysis
        risk_scenarios = results_df[
            (results_df['pass_fail'] == 'PASS') & 
            (results_df['margin'] < 1.0)
        ]
        if len(risk_scenarios) > 0:
            print(f"⚠️  {len(risk_scenarios)} scenarios in risk zone (margin < 1.0%)")
    
    else:
        print("✓ All scenarios PASS! Plan has significant headroom.")
    
    # Summary statistics
    total_scenarios = len(results_df)
    pass_count = len(pass_scenarios)
    fail_count = len(fail_scenarios)
    
    print(f"\n📈 Summary Statistics:")
    print(f"   Total scenarios: {total_scenarios}")
    print(f"   PASS scenarios: {pass_count} ({pass_count/total_scenarios*100:.1f}%)")
    print(f"   FAIL scenarios: {fail_count} ({fail_count/total_scenarios*100:.1f}%)")
    
    if len(results_df) > 0:
        avg_margin = results_df['margin'].mean()
        print(f"   Average margin: {avg_margin:.2f}%")

def export_results(results_df, filename=RESULTS_FILE):
    """Export results to CSV file"""
    try:
        results_df.to_csv(filename, index=False)
        print(f"\n✓ Detailed results saved to {filename}")
        return True
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 50)
    print("ACP SENSITIVITY ANALYZER - MVP")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Load census data
    print("\nLoading census data...")
    try:
        df_census = load_census()
    except Exception as e:
        print(f"❌ Failed to load census data: {e}")
        return
    
    # Define scenario grid
    adoption_rates = DEFAULT_ADOPTION_RATES
    contribution_rates = DEFAULT_CONTRIBUTION_RATES
    
    print(f"\nScenario Configuration:")
    print(f"Adoption rates: {[f'{r*100:.0f}%' for r in adoption_rates]}")
    print(f"Contribution rates: {[f'{r:.1f}%' for r in contribution_rates]}")
    
    # Run scenario grid
    try:
        results_df = run_scenario_grid(df_census, adoption_rates, contribution_rates)
    except Exception as e:
        print(f"❌ Failed to run scenarios: {e}")
        return
    
    # Export detailed results
    export_results(results_df)
    
    # Display detailed ACP calculations
    display_detailed_calculations(results_df, adoption_rates, contribution_rates)
    
    # Create and display summary matrix
    display_summary_matrix(results_df, adoption_rates, contribution_rates)
    
    # Extract and display key insights
    extract_key_insights(results_df)
    
    # Create pivot tables for further analysis
    try:
        pivot, pivot_numeric = create_summary_pivot(results_df)
        print(f"\n✓ Pivot tables created for analysis")
    except Exception as e:
        print(f"❌ Error creating pivot tables: {e}")
    
    # Run enhanced features
    try:
        results_df, margin_stats = run_all_enhancements(results_df, adoption_rates, contribution_rates)
    except Exception as e:
        print(f"❌ Error running enhancements: {e}")
    
    print("\n" + "=" * 50)
    print("Analysis complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()