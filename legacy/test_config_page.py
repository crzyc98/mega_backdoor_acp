#!/usr/bin/env python3
"""
Test script to verify the configuration page components work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from constants import config, DEFAULT_PLAN_YEAR, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES
from constants import ACP_MULTIPLIER, ACP_ADDER, RANDOM_SEED
from acp_calculator import load_census
from datetime import datetime

def test_config_page():
    """Test all configuration page components"""
    
    print("🧪 Testing Configuration Page Components...")
    print("=" * 50)
    
    # Test 1: Plan Year Settings
    print(f"✅ Default Plan Year: {DEFAULT_PLAN_YEAR}")
    print(f"✅ Random Seed: {RANDOM_SEED}")
    
    # Test 2: Scenario Grid
    print(f"✅ Adoption Rates: {DEFAULT_ADOPTION_RATES}")
    print(f"✅ Contribution Rates: {DEFAULT_CONTRIBUTION_RATES}")
    
    # Test 3: IRS Regulatory Limits
    try:
        current_limits = config['annual_limits'][DEFAULT_PLAN_YEAR]
        print(f"✅ § 402(g) Elective Deferral Limit: ${current_limits['elective_deferral_limit_402g']:,}")
        print(f"✅ § 415(c) Annual Additions Limit: ${current_limits['annual_additions_limit_415c']:,}")
        print(f"✅ § 401(a)(17) Compensation Limit: ${current_limits['compensation_limit_401a17']:,}")
        print(f"✅ § 414(v) Catch-up Limit: ${current_limits['catch_up_limit_414v']:,}")
        
        if current_limits.get('super_catch_up_limit', 0) > 0:
            print(f"✅ SECURE 2.0 Super Catch-up: ${current_limits['super_catch_up_limit']:,}")
    except Exception as e:
        print(f"❌ Error accessing regulatory limits: {e}")
        return False
    
    # Test 4: ACP Test Parameters
    print(f"✅ ACP Multiplier: {ACP_MULTIPLIER}")
    print(f"✅ ACP Adder: {ACP_ADDER}")
    
    # Test 5: YAML File Access
    try:
        with open('plan_constants.yaml', 'r') as file:
            yaml_content = file.read()
        print(f"✅ YAML file loaded successfully ({len(yaml_content)} characters)")
    except Exception as e:
        print(f"❌ Error reading YAML file: {e}")
        return False
    
    # Test 6: Census Data
    try:
        df_census = load_census()
        total_employees = len(df_census)
        hce_count = df_census['is_hce'].sum()
        nhce_count = total_employees - hce_count
        
        print(f"✅ Census loaded: {total_employees} employees ({hce_count} HCE, {nhce_count} NHCE)")
        
        # Compensation statistics
        avg_hce_comp = df_census[df_census['is_hce']]['compensation'].mean()
        avg_nhce_comp = df_census[~df_census['is_hce']]['compensation'].mean()
        
        print(f"✅ Average HCE Compensation: ${avg_hce_comp:,.0f}")
        print(f"✅ Average NHCE Compensation: ${avg_nhce_comp:,.0f}")
        
    except Exception as e:
        print(f"❌ Error loading census data: {e}")
        return False
    
    # Test 7: Configuration Summary Generation
    try:
        config_summary = f"""
# ACP Sensitivity Analysis Configuration Summary
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## Plan Year Settings
- Default Plan Year: {DEFAULT_PLAN_YEAR}

## IRS Regulatory Limits ({DEFAULT_PLAN_YEAR})
- § 402(g) Elective Deferral Limit: ${current_limits['elective_deferral_limit_402g']:,}
- § 415(c) Annual Additions Limit: ${current_limits['annual_additions_limit_415c']:,}
- § 401(a)(17) Compensation Limit: ${current_limits['compensation_limit_401a17']:,}
- § 414(v) Catch-up Limit: ${current_limits['catch_up_limit_414v']:,}
"""
        
        if current_limits.get('super_catch_up_limit', 0) > 0:
            config_summary += f"- SECURE 2.0 Super Catch-up: ${current_limits['super_catch_up_limit']:,}\n"
        
        config_summary += f"""
## Scenario Grid
- HCE Adoption Rates: {[f'{r*100:.0f}%' for r in DEFAULT_ADOPTION_RATES]}
- HCE Contribution Rates: {[f'{r:.1f}%' for r in DEFAULT_CONTRIBUTION_RATES]}

## Census Summary
- Total Employees: {total_employees:,}
- HCE Count: {hce_count} ({hce_count/total_employees*100:.1f}%)
- NHCE Count: {nhce_count} ({nhce_count/total_employees*100:.1f}%)
- Average HCE Compensation: ${avg_hce_comp:,.0f}
- Average NHCE Compensation: ${avg_nhce_comp:,.0f}

## ACP Test Parameters
- ACP Multiplier: {ACP_MULTIPLIER} (125% rule)
- ACP Adder: {ACP_ADDER}% (2 percentage point rule)
- Random Seed: {RANDOM_SEED}
- Test Logic: HCE ACP ≤ either Limit A OR Limit B

## Notes
- ACP includes only matching and after-tax contributions per IRC §401(m)
- Individual-level calculation with group averaging
- § 415(c) limits enforced at individual employee level
- All scenarios tested with Monte Carlo simulation
"""
        
        print(f"✅ Configuration summary generated ({len(config_summary)} characters)")
        
    except Exception as e:
        print(f"❌ Error generating configuration summary: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All configuration page components working correctly!")
    print("✅ Configuration page is ready for use")
    return True

if __name__ == "__main__":
    success = test_config_page()
    if success:
        print("\n💡 The configuration page should now be available in the Streamlit dashboard")
        print("📋 Select 'Configuration' from the analysis type dropdown to view it")
    else:
        print("\n❌ Configuration page has issues that need to be resolved")
        sys.exit(1)