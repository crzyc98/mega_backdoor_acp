"""
ACP Sensitivity Analyzer - Enhanced Features
Provides advanced visualizations, margin analysis, and Excel exports
"""

import pandas as pd
import numpy as np
from constants import DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES

def classify_risk(margin):
    """Classify scenarios by risk level based on margin"""
    if margin >= 1.0:
        return 'SAFE'
    elif margin >= -1.0:
        return 'RISK'
    else:
        return 'FAIL'

def create_ascii_heatmap(results_df, adoption_rates=None, contribution_rates=None):
    """Create ASCII heatmap showing pass/fail zones"""
    if adoption_rates is None:
        adoption_rates = DEFAULT_ADOPTION_RATES
    if contribution_rates is None:
        contribution_rates = DEFAULT_CONTRIBUTION_RATES
    
    # Add risk classification
    results_df['risk_zone'] = results_df['margin'].apply(classify_risk)
    
    symbols = {
        'SAFE': '■',   # Safe zone (margin >= 1.0%)
        'RISK': '▣',   # Risk zone (-1.0% <= margin < 1.0%)
        'FAIL': '□'    # Fail zone (margin < -1.0%)
    }
    
    print("\n" + "=" * 60)
    print("RISK HEATMAP")
    print("=" * 60)
    print("Legend: ■=SAFE (margin≥1%), ▣=RISK (-1%≤margin<1%), □=FAIL (margin<-1%)")
    print()
    
    # Header row
    print("     ", end="")
    for rate in adoption_rates:
        print(f"{rate*100:3.0f}%".center(6), end="")
    print()
    
    # Data rows
    for contrib_rate in contribution_rates:
        print(f"{contrib_rate:4.1f}%", end="")
        for adopt_rate in adoption_rates:
            # Find the scenario result
            scenario_result = results_df[
                (results_df['hce_adoption_rate'] == adopt_rate) &
                (results_df['hce_contribution_percent'] == contrib_rate)
            ]
            
            if len(scenario_result) > 0:
                risk_zone = scenario_result.iloc[0]['risk_zone']
                symbol = symbols.get(risk_zone, '?')
            else:
                symbol = '?'
            
            print(f"  {symbol}  ", end="")
        print()
    
    return results_df

def analyze_margins(results_df):
    """Analyze safety margins across scenarios"""
    # Add risk classification if not already present
    if 'risk_zone' not in results_df.columns:
        results_df['risk_zone'] = results_df['margin'].apply(classify_risk)
    
    # Generate margin statistics
    margin_stats = {
        'min_margin': results_df['margin'].min(),
        'max_margin': results_df['margin'].max(),
        'avg_margin': results_df['margin'].mean(),
        'median_margin': results_df['margin'].median(),
        'std_margin': results_df['margin'].std(),
        'safe_scenarios': len(results_df[results_df['risk_zone'] == 'SAFE']),
        'risk_scenarios': len(results_df[results_df['risk_zone'] == 'RISK']),
        'fail_scenarios': len(results_df[results_df['risk_zone'] == 'FAIL'])
    }
    
    print("\n" + "=" * 60)
    print("MARGIN ANALYSIS")
    print("=" * 60)
    print(f"Minimum margin: {margin_stats['min_margin']:+.2f}%")
    print(f"Maximum margin: {margin_stats['max_margin']:+.2f}%")
    print(f"Average margin: {margin_stats['avg_margin']:+.2f}%")
    print(f"Median margin:  {margin_stats['median_margin']:+.2f}%")
    print(f"Std deviation:  {margin_stats['std_margin']:.2f}%")
    print()
    print("Risk Zone Distribution:")
    print(f"  SAFE scenarios: {margin_stats['safe_scenarios']} (margin ≥ 1.0%)")
    print(f"  RISK scenarios: {margin_stats['risk_scenarios']} (-1.0% ≤ margin < 1.0%)")
    print(f"  FAIL scenarios: {margin_stats['fail_scenarios']} (margin < -1.0%)")
    
    return margin_stats

def add_chart_output(results_df, adoption_rates=None, contribution_rates=None):
    """Create Excel-compatible visualization data"""
    if adoption_rates is None:
        adoption_rates = DEFAULT_ADOPTION_RATES
    if contribution_rates is None:
        contribution_rates = DEFAULT_CONTRIBUTION_RATES
    
    # Create pivot for pass/fail
    pivot_passfail = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )
    
    # Create pivot for margins
    pivot_margins = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='margin',
        aggfunc='first'
    )
    
    # Create pivot for risk zones
    if 'risk_zone' not in results_df.columns:
        results_df['risk_zone'] = results_df['margin'].apply(classify_risk)
    
    pivot_risk_zones = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='risk_zone',
        aggfunc='first'
    )
    
    # Export to CSV files
    try:
        pivot_passfail.to_csv('acp_passfail_heatmap.csv')
        pivot_margins.to_csv('acp_margin_heatmap.csv')
        pivot_risk_zones.to_csv('acp_risk_zones_heatmap.csv')
        
        print("\n" + "=" * 60)
        print("EXCEL EXPORT")
        print("=" * 60)
        print("✓ Pass/Fail heatmap saved to: acp_passfail_heatmap.csv")
        print("✓ Margin heatmap saved to: acp_margin_heatmap.csv")
        print("✓ Risk zones heatmap saved to: acp_risk_zones_heatmap.csv")
        
        print("\nExcel Visualization Instructions:")
        print("1. Open any CSV file in Excel")
        print("2. Select data range (A1 to last column/row)")
        print("3. Insert > Charts > Conditional Formatting")
        print("4. For Pass/Fail: Apply color scale Green (PASS) to Red (FAIL)")
        print("5. For Margins: Apply color scale Red (negative) to Green (positive)")
        print("6. Add chart title: 'ACP Test Results by Scenario'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating Excel exports: {e}")
        return False

def generate_advanced_insights(results_df):
    """Generate advanced insights and recommendations"""
    print("\n" + "=" * 60)
    print("ADVANCED INSIGHTS & RECOMMENDATIONS")
    print("=" * 60)
    
    # Add risk classification if not present
    if 'risk_zone' not in results_df.columns:
        results_df['risk_zone'] = results_df['margin'].apply(classify_risk)
    
    # Find optimal scenarios (highest margins)
    safe_scenarios = results_df[results_df['risk_zone'] == 'SAFE']
    if len(safe_scenarios) > 0:
        best_scenario = safe_scenarios.loc[safe_scenarios['margin'].idxmax()]
        print(f"🎯 OPTIMAL SCENARIO:")
        print(f"   {best_scenario['hce_adoption_rate']*100:.0f}% adoption, {best_scenario['hce_contribution_percent']:.1f}% contribution")
        print(f"   Margin: {best_scenario['margin']:+.2f}% (SAFE)")
    
    # Find risk threshold - first scenario that enters risk zone
    risk_scenarios = results_df[results_df['risk_zone'] == 'RISK']
    if len(risk_scenarios) > 0:
        # Sort by adoption rate then contribution rate
        risk_scenarios_sorted = risk_scenarios.sort_values(['hce_adoption_rate', 'hce_contribution_percent'])
        first_risk = risk_scenarios_sorted.iloc[0]
        print(f"\n⚠️  RISK THRESHOLD:")
        print(f"   {first_risk['hce_adoption_rate']*100:.0f}% adoption, {first_risk['hce_contribution_percent']:.1f}% contribution")
        print(f"   Margin: {first_risk['margin']:+.2f}% (RISK)")
    
    # Calculate risk gradient - how quickly margins deteriorate
    adoption_rates = sorted(results_df['hce_adoption_rate'].unique())
    contribution_rates = sorted(results_df['hce_contribution_percent'].unique())
    
    print(f"\n📊 RISK GRADIENT ANALYSIS:")
    
    # Analyze impact of increasing adoption at fixed contribution
    fixed_contrib = contribution_rates[len(contribution_rates)//2]  # Middle contribution rate
    fixed_contrib_scenarios = results_df[results_df['hce_contribution_percent'] == fixed_contrib]
    if len(fixed_contrib_scenarios) > 1:
        margin_change = fixed_contrib_scenarios['margin'].iloc[-1] - fixed_contrib_scenarios['margin'].iloc[0]
        adoption_change = fixed_contrib_scenarios['hce_adoption_rate'].iloc[-1] - fixed_contrib_scenarios['hce_adoption_rate'].iloc[0]
        if adoption_change > 0:
            gradient = margin_change / (adoption_change * 100)  # Per percentage point of adoption
            print(f"   Adoption Impact: {gradient:.3f}% margin change per 1% adoption increase")
            print(f"   (at {fixed_contrib:.1f}% contribution rate)")
    
    # Analyze impact of increasing contribution at fixed adoption
    fixed_adopt = adoption_rates[len(adoption_rates)//2]  # Middle adoption rate
    fixed_adopt_scenarios = results_df[results_df['hce_adoption_rate'] == fixed_adopt]
    if len(fixed_adopt_scenarios) > 1:
        margin_change = fixed_adopt_scenarios['margin'].iloc[-1] - fixed_adopt_scenarios['margin'].iloc[0]
        contrib_change = fixed_adopt_scenarios['hce_contribution_percent'].iloc[-1] - fixed_adopt_scenarios['hce_contribution_percent'].iloc[0]
        if contrib_change > 0:
            gradient = margin_change / contrib_change
            print(f"   Contribution Impact: {gradient:.3f}% margin change per 1% contribution increase")
            print(f"   (at {fixed_adopt*100:.0f}% adoption rate)")
    
    # Generate recommendations based on risk tolerance
    print(f"\n💡 RECOMMENDATIONS:")
    
    # Conservative recommendation
    conservative_scenarios = results_df[results_df['margin'] >= 2.0]
    if len(conservative_scenarios) > 0:
        max_contrib_conservative = conservative_scenarios['hce_contribution_percent'].max()
        max_adopt_conservative = conservative_scenarios['hce_adoption_rate'].max()
        print(f"   Conservative (margin ≥ 2%): Up to {max_contrib_conservative:.1f}% contribution, {max_adopt_conservative*100:.0f}% adoption")
    
    # Moderate recommendation
    moderate_scenarios = results_df[results_df['margin'] >= 0.5]
    if len(moderate_scenarios) > 0:
        max_contrib_moderate = moderate_scenarios['hce_contribution_percent'].max()
        max_adopt_moderate = moderate_scenarios['hce_adoption_rate'].max()
        print(f"   Moderate (margin ≥ 0.5%): Up to {max_contrib_moderate:.1f}% contribution, {max_adopt_moderate*100:.0f}% adoption")
    
    # Aggressive recommendation
    aggressive_scenarios = results_df[results_df['pass_fail'] == 'PASS']
    if len(aggressive_scenarios) > 0:
        max_contrib_aggressive = aggressive_scenarios['hce_contribution_percent'].max()
        max_adopt_aggressive = aggressive_scenarios['hce_adoption_rate'].max()
        print(f"   Aggressive (any positive margin): Up to {max_contrib_aggressive:.1f}% contribution, {max_adopt_aggressive*100:.0f}% adoption")
    
    # Summary statistics
    total_scenarios = len(results_df)
    safe_count = len(results_df[results_df['risk_zone'] == 'SAFE'])
    risk_count = len(results_df[results_df['risk_zone'] == 'RISK'])
    fail_count = len(results_df[results_df['risk_zone'] == 'FAIL'])
    
    print(f"\n📈 RISK ASSESSMENT SUMMARY:")
    print(f"   {safe_count}/{total_scenarios} scenarios SAFE ({safe_count/total_scenarios*100:.1f}%)")
    print(f"   {risk_count}/{total_scenarios} scenarios RISK ({risk_count/total_scenarios*100:.1f}%)")
    print(f"   {fail_count}/{total_scenarios} scenarios FAIL ({fail_count/total_scenarios*100:.1f}%)")
    
    if safe_count > fail_count:
        print(f"   ✅ Overall assessment: FAVORABLE for mega-backdoor implementation")
    elif safe_count == fail_count:
        print(f"   ⚠️  Overall assessment: MIXED - careful parameter selection required")
    else:
        print(f"   ❌ Overall assessment: CHALLENGING - consider plan design modifications")

def run_all_enhancements(results_df, adoption_rates=None, contribution_rates=None):
    """Run all enhancement features"""
    print("\n" + "=" * 60)
    print("ENHANCED ACP SENSITIVITY ANALYSIS")
    print("=" * 60)
    
    # 1. ASCII Heatmap
    results_df = create_ascii_heatmap(results_df, adoption_rates, contribution_rates)
    
    # 2. Margin Analysis
    margin_stats = analyze_margins(results_df)
    
    # 3. Excel Export
    export_success = add_chart_output(results_df, adoption_rates, contribution_rates)
    
    # 4. Advanced Insights
    generate_advanced_insights(results_df)
    
    # 5. Professional Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("Enhanced features generated:")
    print("✓ ASCII Risk Heatmap")
    print("✓ Margin Analysis")
    print("✓ Excel Export Files" if export_success else "❌ Excel Export Failed")
    print("✓ Advanced Insights & Recommendations")
    print("\nFiles available for further analysis:")
    print("- acp_results.csv (detailed scenario data)")
    print("- acp_passfail_heatmap.csv (Excel-compatible pass/fail matrix)")
    print("- acp_margin_heatmap.csv (Excel-compatible margin analysis)")
    print("- acp_risk_zones_heatmap.csv (Excel-compatible risk zones)")
    
    return results_df, margin_stats

if __name__ == "__main__":
    # Demo with sample data
    print("Enhancement features demonstration...")
    print("Run from run_analysis.py with actual data for full functionality.")