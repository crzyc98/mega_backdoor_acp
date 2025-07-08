import pandas as pd
import numpy as np
from datetime import datetime
from constants import ACP_MULTIPLIER, ACP_ADDER, RESULTS_FILE, RANDOM_SEED

def load_census(filename='census.csv'):
    """
    Load and validate census data from CSV file
    
    Args:
        filename: Path to CSV file containing employee data
        
    Returns:
        pd.DataFrame: Validated employee census data
        
    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    try:
        df = pd.read_csv(filename)
        required_cols = ['employee_id', 'is_hce', 'compensation', 'match_dollars']
        
        # Check required columns
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Need: {required_cols}")
        
        # Convert is_hce to boolean
        df['is_hce'] = df['is_hce'].astype(str).str.upper() == 'TRUE'
        
        # Validate data types and ranges
        if df['compensation'].dtype not in ['int64', 'float64']:
            raise ValueError("Compensation must be numeric")
        
        if df['match_dollars'].dtype not in ['int64', 'float64']:
            raise ValueError("Match dollars must be numeric")
        
        # Check for negative values
        if (df['compensation'] < 0).any():
            raise ValueError("Compensation cannot be negative")
        
        if (df['match_dollars'] < 0).any():
            raise ValueError("Match dollars cannot be negative")
        
        # Display summary statistics
        total_employees = len(df)
        hce_count = df['is_hce'].sum()
        nhce_count = total_employees - hce_count
        
        print(f"✓ Loaded {total_employees} employees ({hce_count} HCEs, {nhce_count} NHCEs)")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        raise
    except Exception as e:
        print(f"❌ Error loading census: {e}")
        raise

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
    
    # Calculate baseline NHCE ACP (just match contributions)
    nhce_acp = (nhce_data['match_dollars'] / nhce_data['compensation'] * 100).mean()
    
    # Simulate HCE after-tax contributions
    n_adopters = int(len(hce_data) * hce_adoption_rate)
    
    # Randomly select HCEs who will contribute (reproducible)
    np.random.seed(RANDOM_SEED)
    if n_adopters > 0:
        adopters = np.random.choice(hce_data.index, size=n_adopters, replace=False)
    else:
        adopters = []
    
    # Calculate after-tax contributions
    hce_data['after_tax_dollars'] = 0.0
    if len(adopters) > 0:
        hce_data.loc[adopters, 'after_tax_dollars'] = (
            hce_data.loc[adopters, 'compensation'] * (hce_contribution_percent / 100)
        )
    
    # Calculate HCE ACP (match + after-tax)
    hce_data['total_contributions'] = hce_data['match_dollars'] + hce_data['after_tax_dollars']
    hce_acp = (hce_data['total_contributions'] / hce_data['compensation'] * 100).mean()
    
    # Apply IRS ACP test (IRC §401(m))
    limit_a = nhce_acp * ACP_MULTIPLIER  # 1.25 factor
    limit_b = nhce_acp + ACP_ADDER       # 2.0 percentage point adder
    max_allowed_hce_acp = min(limit_a, limit_b)
    
    # Determine pass/fail
    passed = hce_acp <= max_allowed_hce_acp
    margin = max_allowed_hce_acp - hce_acp
    
    return {
        'hce_adoption_rate': hce_adoption_rate,
        'hce_contribution_percent': hce_contribution_percent,
        'nhce_acp': round(nhce_acp, 3),
        'hce_acp': round(hce_acp, 3),
        'max_allowed_hce_acp': round(max_allowed_hce_acp, 3),
        'margin': round(margin, 3),
        'pass_fail': 'PASS' if passed else 'FAIL',
        'n_hce_contributors': n_adopters
    }

if __name__ == "__main__":
    # Test the functions
    print("Testing ACP Calculator Functions...")
    print("=" * 50)
    
    # Test load_census
    df = load_census()
    print(f"Census loaded successfully: {len(df)} employees")
    
    # Test calculate_acp_for_scenario with different scenarios
    test_scenarios = [
        (0.0, 10.0),  # No adoption
        (1.0, 2.0),   # Full adoption, low contribution
        (0.5, 6.0),   # Half adoption, medium contribution
        (1.0, 12.0),  # Full adoption, high contribution
    ]
    
    print("\nTesting scenarios:")
    print("-" * 50)
    for adoption, contribution in test_scenarios:
        result = calculate_acp_for_scenario(df, adoption, contribution)
        print(f"Adoption: {adoption*100:3.0f}%, Contribution: {contribution:4.1f}% → {result['pass_fail']} "
              f"(margin: {result['margin']:6.2f}%)")
    
    print("\n✓ All tests completed successfully!")