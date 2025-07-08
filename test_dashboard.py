#!/usr/bin/env python3
"""
Quick test to verify dashboard components work correctly
"""

import pandas as pd
import numpy as np
from acp_calculator import load_census, run_scenario_grid
from employee_level_analysis import analyze_employee_level_scenario
from constants import DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES
from enhancements import run_all_enhancements

def test_dashboard_components():
    """Test key dashboard components"""
    print("🧪 Testing Dashboard Components...")
    
    # Load data
    print("Loading census data...")
    df_census = load_census()
    
    print("Running scenario grid...")
    results_df = run_scenario_grid(df_census, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES)
    
    print("Running enhancements...")
    results_df, margin_stats = run_all_enhancements(results_df, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES)
    
    # Test data structure
    print("Testing data structure...")
    adoption_options = sorted(results_df['hce_adoption_rate'].unique())
    contribution_options = sorted(results_df['hce_contribution_percent'].unique())
    
    print(f"✓ Adoption options: {[f'{r*100:.0f}%' for r in adoption_options]}")
    print(f"✓ Contribution options: {[f'{r:.1f}%' for r in contribution_options]}")
    
    # Test multiselect defaults
    multiselect_defaults = [0.0, 0.1, 0.2, 0.25]
    valid_defaults = all(d in adoption_options for d in multiselect_defaults)
    print(f"✓ Multiselect defaults valid: {valid_defaults}")
    
    # Test selectbox defaults
    selectbox_adoption_default = adoption_options[1]  # Index 1
    selectbox_contribution_default = contribution_options[3]  # Index 3
    print(f"✓ Selectbox defaults: {selectbox_adoption_default*100:.0f}% adoption, {selectbox_contribution_default:.1f}% contribution")
    
    # Test employee-level analysis
    print("Testing employee-level analysis...")
    analysis_result = analyze_employee_level_scenario(
        df_census, 
        selectbox_adoption_default, 
        selectbox_contribution_default,
        "Test Scenario"
    )
    
    print(f"✓ Employee analysis completed: {analysis_result['scenario_summary']['pass_fail']}")
    
    # Test heatmap data
    print("Testing heatmap data...")
    pivot_data = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )
    
    pivot_margin = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='margin',
        aggfunc='first'
    )
    
    print(f"✓ Pivot tables created: {pivot_data.shape} shape")
    print(f"✓ Margin range: {pivot_margin.min().min():.2f}% to {pivot_margin.max().max():.2f}%")
    
    print("\n🎉 All dashboard components tested successfully!")
    return True

if __name__ == "__main__":
    test_dashboard_components()