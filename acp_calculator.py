import pandas as pd
import numpy as np
from datetime import datetime
from constants import ACP_MULTIPLIER, ACP_ADDER, RESULTS_FILE, RANDOM_SEED, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES, DEFAULT_PLAN_YEAR, get_compensation_limit
from contribution_limits import apply_contribution_limits

def apply_compensation_cap(df, plan_year=None):
    """
    Apply § 401(a)(17) compensation cap to census data
    
    Args:
        df: DataFrame with employee data
        plan_year: Plan year for compensation limit (uses default if None)
        
    Returns:
        pd.DataFrame: DataFrame with capped compensation
    """
    if plan_year is None:
        plan_year = DEFAULT_PLAN_YEAR
    
    # Get compensation limit for plan year
    comp_limit = get_compensation_limit(plan_year)
    
    # Apply cap and track how many employees were affected
    original_comp = df['compensation'].copy()
    df['compensation'] = df['compensation'].clip(upper=comp_limit)
    
    # Count employees affected by cap
    affected_count = (original_comp > comp_limit).sum()
    if affected_count > 0:
        print(f"✓ Applied § 401(a)(17) compensation cap of ${comp_limit:,} to {affected_count} employee(s)")
    
    return df

def load_census(filename='census.csv', plan_year=None):
    """
    Load and validate census data from CSV file
    
    Args:
        filename: Path to CSV file containing employee data
        plan_year: Plan year for compensation limits (uses default if None)
        
    Returns:
        pd.DataFrame: Validated employee census data with compensation cap applied
        
    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    try:
        df = pd.read_csv(filename)
        required_cols = ['employee_id', 'is_hce', 'compensation', 'er_match_amt', 'ee_pre_tax_amt', 'ee_after_tax_amt', 'ee_roth_amt']
        
        # Check required columns
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Need: {required_cols}")
        
        # Convert is_hce to boolean
        df['is_hce'] = df['is_hce'].astype(str).str.upper() == 'TRUE'
        
        # Validate data types and ranges
        numeric_cols = ['compensation', 'er_match_amt', 'ee_pre_tax_amt', 'ee_after_tax_amt', 'ee_roth_amt']
        
        for col in numeric_cols:
            if df[col].dtype not in ['int64', 'float64']:
                raise ValueError(f"{col} must be numeric")
        
        # Check for negative values
        for col in numeric_cols:
            if (df[col] < 0).any():
                raise ValueError(f"{col} cannot be negative")
        
        # Display summary statistics
        total_employees = len(df)
        hce_count = df['is_hce'].sum()
        nhce_count = total_employees - hce_count
        
        print(f"✓ Loaded {total_employees} employees ({hce_count} HCEs, {nhce_count} NHCEs)")
        
        # Apply compensation cap per § 401(a)(17)
        df = apply_compensation_cap(df, plan_year)
        
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        raise
    except Exception as e:
        print(f"❌ Error loading census: {e}")
        raise

def get_census_breakdown(df_census):
    """Get detailed breakdown of census data for calculations"""
    hce_data = df_census[df_census['is_hce']].copy()
    nhce_data = df_census[~df_census['is_hce']].copy()
    
    # NHCE calculations
    nhce_total_contributions = (nhce_data['er_match_amt'] + nhce_data['ee_pre_tax_amt'] + 
                               nhce_data['ee_after_tax_amt'] + nhce_data['ee_roth_amt'])
    nhce_total_compensation = nhce_data['compensation'].sum()
    nhce_total_contrib_dollars = nhce_total_contributions.sum()
    
    # HCE baseline calculations
    hce_baseline_contributions = (hce_data['er_match_amt'] + hce_data['ee_pre_tax_amt'] + 
                                 hce_data['ee_after_tax_amt'] + hce_data['ee_roth_amt'])
    hce_total_compensation = hce_data['compensation'].sum()
    hce_baseline_contrib_dollars = hce_baseline_contributions.sum()
    
    return {
        'nhce_count': len(nhce_data),
        'nhce_total_compensation': nhce_total_compensation,
        'nhce_total_contributions': nhce_total_contrib_dollars,
        'hce_count': len(hce_data),
        'hce_total_compensation': hce_total_compensation,
        'hce_baseline_contributions': hce_baseline_contrib_dollars
    }

def calculate_acp_for_scenario(df_census, hce_adoption_rate, hce_contribution_percent):
    """
    Calculate ACP test results for a single scenario
    
    Args:
        df_census: DataFrame with employee data
        hce_adoption_rate: Float 0.0-1.0 (percentage adopting as decimal)
        hce_contribution_percent: Float 0.0-25.0 (contribution percentage)
    
    Returns:
        dict: Scenario results with all metrics
    """
    # Input validation
    if not 0.0 <= hce_adoption_rate <= 1.0:
        raise ValueError("HCE adoption rate must be between 0.0 and 1.0")
    
    if not 0.0 <= hce_contribution_percent <= 25.0:
        raise ValueError("HCE contribution percent must be between 0.0 and 25.0")
    
    # Work with a copy to avoid modifying original
    df = df_census.copy()
    
    # Separate HCEs and NHCEs
    hce_mask = df['is_hce']
    nhce_data = df[~hce_mask]
    hce_data = df[hce_mask].copy()
    
    # Validate we have both HCEs and NHCEs
    if len(nhce_data) == 0:
        raise ValueError("No NHCEs found in census data")
    
    if len(hce_data) == 0:
        raise ValueError("No HCEs found in census data")
    
    # Calculate baseline NHCE ACP (only matching + after-tax contributions per IRC §401(m))
    nhce_data['individual_acp'] = (nhce_data['er_match_amt'] + nhce_data['ee_after_tax_amt']) / nhce_data['compensation'] * 100
    nhce_acp = nhce_data['individual_acp'].mean()
    
    # Simulate HCE after-tax contributions
    n_adopters = int(len(hce_data) * hce_adoption_rate)
    
    # Randomly select HCEs who will contribute (reproducible)
    np.random.seed(RANDOM_SEED)
    if n_adopters > 0:
        adopters = np.random.choice(hce_data.index, size=n_adopters, replace=False)
    else:
        adopters = []
    
    # Calculate after-tax contributions with contribution limits
    hce_data['after_tax_dollars'] = 0.0
    if len(adopters) > 0:
        # Apply contribution limits to mega-backdoor contributions
        adjusted_contributions, limits_results = apply_contribution_limits(
            hce_data.loc[adopters], hce_contribution_percent
        )
        hce_data.loc[adopters, 'after_tax_dollars'] = adjusted_contributions
        
        # Display any adjustments made for debugging
        if limits_results['total_adjustments'] > 0:
            print(f"  📊 § 415(c) adjustments made: {limits_results['total_adjustments']} employees affected")
    
    # Calculate HCE ACP (only matching + after-tax contributions per IRC §401(m))
    hce_data['total_contributions'] = (hce_data['er_match_amt'] + hce_data['ee_after_tax_amt'] + 
                                     hce_data['after_tax_dollars'])
    hce_data['individual_acp'] = hce_data['total_contributions'] / hce_data['compensation'] * 100
    hce_acp = hce_data['individual_acp'].mean()
    
    # Get detailed breakdown for display
    nhce_total_contributions = (nhce_data['er_match_amt'] + nhce_data['ee_after_tax_amt']).sum()
    nhce_total_compensation = nhce_data['compensation'].sum()
    
    hce_baseline_contributions = (hce_data['er_match_amt'] + hce_data['ee_after_tax_amt']).sum()
    hce_mega_backdoor_contributions = hce_data['after_tax_dollars'].sum()
    hce_total_contributions = hce_data['total_contributions'].sum()
    hce_total_compensation = hce_data['compensation'].sum()
    
    # Apply IRS ACP test (IRC §401(m))
    limit_a = nhce_acp * ACP_MULTIPLIER  # 1.25 factor
    limit_b = nhce_acp + ACP_ADDER       # 2.0 percentage point adder
    
    # Pass if HCE ACP is ≤ either limit (not both)
    passed_limit_a = hce_acp <= limit_a
    passed_limit_b = hce_acp <= limit_b
    passed = passed_limit_a or passed_limit_b
    
    # For reporting purposes, use the higher limit (more generous)
    max_allowed_hce_acp = max(limit_a, limit_b)
    margin = max_allowed_hce_acp - hce_acp
    
    return {
        'hce_adoption_rate': hce_adoption_rate,
        'hce_contribution_percent': hce_contribution_percent,
        'nhce_acp': round(nhce_acp, 3),
        'hce_acp': round(hce_acp, 3),
        'max_allowed_hce_acp': round(max_allowed_hce_acp, 3),
        'margin': round(margin, 3),
        'pass_fail': 'PASS' if passed else 'FAIL',
        'n_hce_contributors': n_adopters,
        # Detailed breakdown
        'nhce_total_contributions': round(nhce_total_contributions, 0),
        'nhce_total_compensation': round(nhce_total_compensation, 0),
        'hce_baseline_contributions': round(hce_baseline_contributions, 0),
        'hce_mega_backdoor_contributions': round(hce_mega_backdoor_contributions, 0),
        'hce_total_contributions': round(hce_total_contributions, 0),
        'hce_total_compensation': round(hce_total_compensation, 0),
        'nhce_count': len(nhce_data),
        'hce_count': len(hce_data),
        # Additional limit details
        'limit_a': round(limit_a, 3),
        'limit_b': round(limit_b, 3),
        'passed_limit_a': passed_limit_a,
        'passed_limit_b': passed_limit_b
    }

def run_scenario_grid(df_census, adoption_rates=None, contribution_rates=None):
    """
    Run all scenario combinations and return results
    
    Args:
        df_census: DataFrame with employee data
        adoption_rates: List of adoption rates (0.0-1.0). Uses defaults if None
        contribution_rates: List of contribution percentages (0.0-25.0). Uses defaults if None
    
    Returns:
        pd.DataFrame: Results with all scenarios
    """
    # Use default grids if not provided
    if adoption_rates is None:
        adoption_rates = DEFAULT_ADOPTION_RATES
    if contribution_rates is None:
        contribution_rates = DEFAULT_CONTRIBUTION_RATES
    
    # Validate inputs
    if not adoption_rates or not contribution_rates:
        raise ValueError("Adoption rates and contribution rates cannot be empty")
    
    for rate in adoption_rates:
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"Adoption rate {rate} must be between 0.0 and 1.0")
    
    for rate in contribution_rates:
        if not 0.0 <= rate <= 25.0:
            raise ValueError(f"Contribution rate {rate} must be between 0.0 and 25.0")
    
    # Calculate total scenarios
    total_scenarios = len(adoption_rates) * len(contribution_rates)
    
    # Display header
    print(f"\nRunning {total_scenarios} scenarios...")
    print("─" * 50)
    
    # Initialize results list
    results = []
    scenario_num = 0
    
    # Loop through all combinations
    for i, adopt_rate in enumerate(adoption_rates):
        for j, contrib_rate in enumerate(contribution_rates):
            scenario_num += 1
            
            # Calculate ACP for this scenario
            result = calculate_acp_for_scenario(df_census, adopt_rate, contrib_rate)
            results.append(result)
            
            # Display progress
            status = "✓" if result['pass_fail'] == 'PASS' else "✗"
            print(f"{status} Scenario {scenario_num}/{total_scenarios}: "
                  f"{adopt_rate*100:.0f}% adoption, {contrib_rate:.1f}% contribution "
                  f"→ {result['pass_fail']} (margin: {result['margin']:+.2f}%)")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by adoption rate, then contribution rate
    results_df = results_df.sort_values(['hce_adoption_rate', 'hce_contribution_percent'])
    
    # Validate results
    if len(results_df) != total_scenarios:
        raise ValueError(f"Expected {total_scenarios} results, got {len(results_df)}")
    
    # Check for missing data
    if results_df.isnull().any().any():
        raise ValueError("Results contain missing data")
    
    print(f"\n✓ Completed {total_scenarios} scenarios successfully")
    
    return results_df

if __name__ == "__main__":
    # Test the functions
    print("Testing ACP Calculator Functions...")
    print("=" * 50)
    
    # Test load_census
    df = load_census()
    print(f"Census loaded successfully: {len(df)} employees")
    
    # Test individual scenarios
    print("\nTesting individual scenarios:")
    print("-" * 50)
    test_scenarios = [
        (0.0, 10.0),  # No adoption
        (1.0, 2.0),   # Full adoption, low contribution
        (0.5, 6.0),   # Half adoption, medium contribution
        (1.0, 12.0),  # Full adoption, high contribution
    ]
    
    for adoption, contribution in test_scenarios:
        result = calculate_acp_for_scenario(df, adoption, contribution)
        print(f"Adoption: {adoption*100:3.0f}%, Contribution: {contribution:4.1f}% → {result['pass_fail']} "
              f"(margin: {result['margin']:6.2f}%)")
    
    # Test scenario grid
    print("\nTesting scenario grid:")
    print("=" * 50)
    results_df = run_scenario_grid(df)
    
    # Display summary
    print(f"\nGrid Results Summary:")
    print(f"Total scenarios: {len(results_df)}")
    print(f"PASS scenarios: {len(results_df[results_df['pass_fail'] == 'PASS'])}")
    print(f"FAIL scenarios: {len(results_df[results_df['pass_fail'] == 'FAIL'])}")
    
    print("\n✓ All tests completed successfully!")