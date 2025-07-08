# ACP Sensitivity Calculator - 2-Hour MVP Implementation

## Quick Start (5 minutes)

### What You're Building

A Python script that:

1. Reads employee census data (CSV)
2. Simulates HCE mega-backdoor Roth adoption scenarios
3. Calculates ACP test pass/fail for each scenario
4. Outputs results to CSV

### Setup Commands

```bash
mkdir acp_analyzer_mvp
cd acp_analyzer_mvp
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install pandas numpy
```

## Implementation (1 hour 45 minutes)

### Step 1: Create Test Data (5 minutes)

Create `census.csv`:

```csv
employee_id,is_hce,compensation,match_dollars
1,TRUE,250000,7500
2,TRUE,200000,7500
3,TRUE,180000,7500
4,TRUE,175000,7500
5,FALSE,90000,4500
6,FALSE,85000,4250
7,FALSE,80000,4000
8,FALSE,75000,3750
9,FALSE,70000,3500
10,FALSE,65000,3250
11,FALSE,60000,3000
12,FALSE,55000,2750
```

### Step 2: Create the Main Script (40 minutes)

Create `run_analysis.py`:

```python
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
ACP_MULTIPLIER = 1.25
ACP_ADDER = 2.00
RESULTS_FILE = 'acp_results.csv'

def load_census(filename='census.csv'):
    """Load and validate census data"""
    try:
        df = pd.read_csv(filename)
        required_cols = ['employee_id', 'is_hce', 'compensation', 'match_dollars']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Need: {required_cols}")

        # Convert is_hce to boolean
        df['is_hce'] = df['is_hce'].astype(str).str.upper() == 'TRUE'

        print(f"✓ Loaded {len(df)} employees ({df['is_hce'].sum()} HCEs, {(~df['is_hce']).sum()} NHCEs)")
        return df
    except Exception as e:
        print(f"❌ Error loading census: {e}")
        exit(1)

def calculate_acp_for_scenario(df_census, hce_adoption_rate, hce_contribution_percent):
    """
    Calculate ACP test results for a single scenario

    Returns dict with scenario inputs and pass/fail result
    """
    # Work with a copy to avoid modifying original
    df = df_census.copy()

    # Separate HCEs and NHCEs
    hce_mask = df['is_hce']

    # Calculate baseline NHCE ACP (just match for now)
    nhce_data = df[~hce_mask]
    nhce_acp = (nhce_data['match_dollars'] / nhce_data['compensation'] * 100).mean()

    # Simulate HCE after-tax contributions
    hce_data = df[hce_mask].copy()
    n_adopters = int(len(hce_data) * hce_adoption_rate)

    # Randomly select HCEs who will contribute
    np.random.seed(42)  # For reproducibility
    adopters = np.random.choice(hce_data.index, size=n_adopters, replace=False)

    # Calculate after-tax contributions
    hce_data['after_tax_dollars'] = 0
    hce_data.loc[hce_data.index.isin(adopters), 'after_tax_dollars'] = (
        hce_data.loc[hce_data.index.isin(adopters), 'compensation'] *
        (hce_contribution_percent / 100)
    )

    # Calculate HCE ACP (match + after-tax)
    hce_data['total_contributions'] = hce_data['match_dollars'] + hce_data['after_tax_dollars']
    hce_acp = (hce_data['total_contributions'] / hce_data['compensation'] * 100).mean()

    # Apply ACP test
    limit_a = nhce_acp * ACP_MULTIPLIER
    limit_b = nhce_acp + ACP_ADDER
    max_allowed_hce_acp = min(limit_a, limit_b)

    passed = hce_acp <= max_allowed_hce_acp

    return {
        'hce_adoption_rate': hce_adoption_rate,
        'hce_contribution_percent': hce_contribution_percent,
        'nhce_acp': round(nhce_acp, 3),
        'hce_acp': round(hce_acp, 3),
        'max_allowed_hce_acp': round(max_allowed_hce_acp, 3),
        'margin': round(max_allowed_hce_acp - hce_acp, 3),
        'pass_fail': 'PASS' if passed else 'FAIL',
        'n_hce_contributors': n_adopters
    }

def run_scenario_grid(df_census, adoption_rates, contribution_rates):
    """Run all scenario combinations"""
    results = []
    total_scenarios = len(adoption_rates) * len(contribution_rates)

    print(f"\nRunning {total_scenarios} scenarios...")
    print("─" * 50)

    for i, adopt_rate in enumerate(adoption_rates):
        for j, contrib_rate in enumerate(contribution_rates):
            result = calculate_acp_for_scenario(df_census, adopt_rate, contrib_rate)
            results.append(result)

            # Progress indicator
            scenario_num = i * len(contribution_rates) + j + 1
            status = "✓" if result['pass_fail'] == 'PASS' else "✗"
            print(f"{status} Scenario {scenario_num}/{total_scenarios}: "
                  f"{adopt_rate*100:.0f}% adoption, {contrib_rate:.1f}% contribution "
                  f"→ {result['pass_fail']} (margin: {result['margin']:.2f}%)")

    return pd.DataFrame(results)

def create_summary_pivot(results_df):
    """Create a pivot table summary for easy visualization"""
    pivot = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )

    # Convert to numeric (1 = PASS, 0 = FAIL) for better visualization
    pivot_numeric = pivot.applymap(lambda x: 1 if x == 'PASS' else 0)

    return pivot, pivot_numeric

def main():
    """Main execution"""
    print("=" * 50)
    print("ACP SENSITIVITY ANALYZER - MVP")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Load data
    df_census = load_census()

    # Define scenario grid
    # Quick grid for 2-hour MVP (expand later)
    adoption_rates = [0.0, 0.25, 0.50, 0.75, 1.0]  # 0%, 25%, 50%, 75%, 100%
    contribution_rates = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]  # 2% to 12%

    # Run scenarios
    results_df = run_scenario_grid(df_census, adoption_rates, contribution_rates)

    # Save detailed results
    results_df.to_csv(RESULTS_FILE, index=False)
    print(f"\n✓ Detailed results saved to {RESULTS_FILE}")

    # Create and display summary
    pivot, pivot_numeric = create_summary_pivot(results_df)

    print("\n" + "=" * 50)
    print("SUMMARY MATRIX (PASS = ✓, FAIL = ✗)")
    print("=" * 50)
    print(f"{'Contrib %':<10}", end='')
    for rate in adoption_rates:
        print(f"{rate*100:.0f}% adopt".center(12), end='')
    print()
    print("-" * 70)

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

    # Quick insights
    print("\n" + "=" * 50)
    print("KEY INSIGHTS")
    print("=" * 50)

    fail_scenarios = results_df[results_df['pass_fail'] == 'FAIL']
    if len(fail_scenarios) > 0:
        first_fail = fail_scenarios.iloc[0]
        print(f"⚠️  First failure at: {first_fail['hce_adoption_rate']*100:.0f}% adoption, "
              f"{first_fail['hce_contribution_percent']:.1f}% contribution")

        max_safe = results_df[results_df['pass_fail'] == 'PASS']['hce_contribution_percent'].max()
        print(f"✓ Safe zone: Up to {max_safe:.1f}% contribution at any adoption rate")
    else:
        print("✓ All scenarios PASS! Plan has significant headroom.")

    print("\n" + "=" * 50)
    print("Analysis complete!")

if __name__ == "__main__":
    main()
```

### Step 3: Run and Test (10 minutes)

```bash
python run_analysis.py
```

Expected output:

- Console summary showing pass/fail matrix
- `acp_results.csv` with detailed results

### Step 4: Quick Enhancements (if time permits)

Add to the script:

```python
def add_chart_output(results_df):
    """Create a simple ASCII heatmap"""
    pivot_numeric = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='margin',
        aggfunc='first'
    )

    # Save for Excel/Google Sheets
    pivot_numeric.to_csv('acp_heatmap.csv')
    print("\n✓ Heatmap data saved to acp_heatmap.csv (import to Excel for visualization)")

# Add this line in main() after saving results:
add_chart_output(results_df)
```

## Testing Your Implementation (10 minutes)

### Verify Core Logic

1. Check that with 0% adoption, all scenarios PASS
2. Check that higher contribution % → more likely to FAIL
3. Verify NHCE ACP calculation matches manual calc

### Edge Cases to Test

- All HCEs contribute maximum
- No HCEs contribute
- Single HCE contributes

## What You've Accomplished

✅ **Working prototype** that validates the core ACP calculation logic  
✅ **Scenario engine** that tests multiple adoption/contribution combinations  
✅ **Clear output** showing pass/fail boundaries  
✅ **Foundation** for the full-scale system

## Next Steps (After MVP)

1. **Expand scenarios**: Finer grids (1% increments)
2. **Add match formulas**: Variable match rates
3. **Include QMAC/QNEC**: Corrective contribution modeling
4. **Build UI**: Web interface or Streamlit app
5. **Scale infrastructure**: DuckDB + dbt as specified in full PRD

---

**Time Check**: This implementation should take ~2 hours total. Focus on getting the core calculation right—everything else can be added later.
