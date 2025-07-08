"""
ACP Sensitivity Analysis Dashboard
Professional Streamlit dashboard for client-ready mega-backdoor Roth analysis results
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io

# Import our analysis modules
from acp_calculator import load_census, run_scenario_grid
from employee_level_analysis import analyze_employee_level_scenario
from constants import DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES, DEFAULT_PLAN_YEAR
from enhancements import run_all_enhancements

# Page configuration
st.set_page_config(
    page_title="ACP Sensitivity Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .copy-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    .highlight-success {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .highlight-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .highlight-danger {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_analysis_data():
    """Load and cache the analysis data"""
    try:
        # Load census data
        df_census = load_census()
        
        # Run scenario grid
        results_df = run_scenario_grid(df_census, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES)
        
        # Run enhancements
        results_df, margin_stats = run_all_enhancements(results_df, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES)
        
        return df_census, results_df, margin_stats
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

def create_risk_heatmap(results_df):
    """Create a risk heatmap visualization"""
    # Create pivot table for heatmap
    pivot_data = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='pass_fail',
        aggfunc='first'
    )
    
    # Convert to numeric for color mapping
    pivot_numeric = pivot_data.map(lambda x: 1 if x == 'PASS' else 0)
    
    # Check if we have both pass and fail scenarios
    unique_values = pivot_numeric.values.flatten()
    unique_values = unique_values[~pd.isna(unique_values)]
    has_both_outcomes = len(set(unique_values)) > 1
    
    # Create color scale based on data
    if has_both_outcomes:
        color_scale = [[0, "red"], [1, "green"]]
        colorbar_title = "Pass/Fail"
    else:
        # If all scenarios are the same, use a different color scheme
        if all(unique_values == 1):
            color_scale = [[0, "lightgreen"], [1, "green"]]
            colorbar_title = "All Pass"
        else:
            color_scale = [[0, "red"], [1, "darkred"]]
            colorbar_title = "All Fail"
    
    # Create heatmap
    fig = px.imshow(
        pivot_numeric,
        labels=dict(x="HCE Adoption Rate", y="HCE Contribution Rate", color=colorbar_title),
        x=[f"{rate*100:.0f}%" for rate in pivot_numeric.columns],
        y=[f"{rate:.1f}%" for rate in pivot_numeric.index],
        color_continuous_scale=color_scale,
        title="ACP Test Results: Pass/Fail Matrix",
        text_auto=False  # Disable automatic text to control manually
    )
    
    # Add text annotations with appropriate color
    text_color = "white" if has_both_outcomes else "black"
    
    # Create text array for the heatmap
    text_array = []
    for i, row in enumerate(pivot_data.index):
        text_row = []
        for j, col in enumerate(pivot_data.columns):
            text_row.append(pivot_data.loc[row, col])
        text_array.append(text_row)
    
    # Update the heatmap with text
    fig.update_traces(
        text=text_array,
        texttemplate="%{text}",
        textfont=dict(color=text_color, size=14, family="Arial Black")
    )
    
    fig.update_layout(
        width=800,
        height=500,
        font=dict(size=12)
    )
    
    return fig

def create_margin_analysis(results_df):
    """Create margin analysis visualization"""
    # Create margin heatmap for all scenarios
    pivot_margin = results_df.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='margin',
        aggfunc='first'
    )
    
    # Determine color range based on data
    min_margin = pivot_margin.min().min()
    max_margin = pivot_margin.max().max()
    
    # Create color scale that highlights positive vs negative margins
    if min_margin < 0:
        color_scale = "RdYlGn"  # Red for negative, Green for positive
        title = "ACP Test Margins (Negative = Fail, Positive = Pass)"
    else:
        color_scale = "Greens"  # All positive margins
        title = "ACP Test Margins (All Scenarios Pass)"
    
    fig = px.imshow(
        pivot_margin,
        labels=dict(x="HCE Adoption Rate", y="HCE Contribution Rate", color="Margin %"),
        x=[f"{rate*100:.0f}%" for rate in pivot_margin.columns],
        y=[f"{rate:.1f}%" for rate in pivot_margin.index],
        color_continuous_scale=color_scale,
        title=title,
        text_auto=False  # Disable automatic text to control manually
    )
    
    # Create text array for the margin heatmap
    text_array = []
    for i, row in enumerate(pivot_margin.index):
        text_row = []
        for j, col in enumerate(pivot_margin.columns):
            value = pivot_margin.loc[row, col]
            if not pd.isna(value):
                text_row.append(f"{value:+.1f}%")
            else:
                text_row.append("")
        text_array.append(text_row)
    
    # Update the heatmap with text
    # Use black text for better readability on the green color scheme
    text_color = "black" if min_margin >= 0 else "white"
    fig.update_traces(
        text=text_array,
        texttemplate="%{text}",
        textfont=dict(color=text_color, size=12, family="Arial Black")
    )
    
    fig.update_layout(
        width=800,
        height=500,
        font=dict(size=12)
    )
    
    return fig

def format_executive_summary(results_df, df_census):
    """Format executive summary for client communication"""
    total_scenarios = len(results_df)
    pass_scenarios = len(results_df[results_df['pass_fail'] == 'PASS'])
    fail_scenarios = total_scenarios - pass_scenarios
    
    # Find key insights
    pass_scenarios_df = results_df[results_df['pass_fail'] == 'PASS']
    fail_scenarios_df = results_df[results_df['pass_fail'] == 'FAIL']
    
    max_safe_contribution = pass_scenarios_df['hce_contribution_percent'].max() if len(pass_scenarios_df) > 0 else None
    min_failing_contribution = fail_scenarios_df['hce_contribution_percent'].min() if len(fail_scenarios_df) > 0 else None
    
    # Get census summary
    total_employees = len(df_census)
    hce_count = df_census['is_hce'].sum()
    nhce_count = total_employees - hce_count
    
    # Calculate margin statistics
    avg_margin = results_df['margin'].mean()
    min_margin = results_df['margin'].min()
    max_margin = results_df['margin'].max()
    
    summary = f"""
## Executive Summary - ACP Sensitivity Analysis

**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}
**Plan Year:** {DEFAULT_PLAN_YEAR}

### Plan Demographics
- **Total Employees:** {total_employees:,}
- **HCE Employees:** {hce_count} ({hce_count/total_employees*100:.1f}%)
- **NHCE Employees:** {nhce_count} ({nhce_count/total_employees*100:.1f}%)

### Analysis Results
- **Total Scenarios Tested:** {total_scenarios}
- **Passing Scenarios:** {pass_scenarios} ({pass_scenarios/total_scenarios*100:.1f}%)
- **Failing Scenarios:** {fail_scenarios} ({fail_scenarios/total_scenarios*100:.1f}%)

### Key Findings
"""
    
    if pass_scenarios > 0 and max_safe_contribution is not None:
        summary += f"- **✅ Safe Contribution Level:** Up to {max_safe_contribution:.1f}% contribution rate tested successfully\n"
    
    if fail_scenarios > 0 and min_failing_contribution is not None:
        summary += f"- **⚠️ Risk Zone:** Failures begin at {min_failing_contribution:.1f}% contribution rate\n"
    
    # Add margin analysis
    summary += f"- **📊 Margin Analysis:** Average margin {avg_margin:+.2f}% (range: {min_margin:+.2f}% to {max_margin:+.2f}%)\n"
    
    # Add risk assessment
    if fail_scenarios == 0:
        summary += "- **🎯 Risk Assessment:** LOW - All tested scenarios pass ACP requirements\n"
        summary += "- **💡 Recommendation:** Plan has significant headroom for mega-backdoor contributions\n"
    elif pass_scenarios > fail_scenarios:
        summary += "- **🎯 Risk Assessment:** MODERATE - Most scenarios pass, some restrictions apply\n"
        summary += "- **💡 Recommendation:** Proceed with caution at higher contribution rates\n"
    else:
        summary += "- **🎯 Risk Assessment:** HIGH - Significant restrictions on mega-backdoor contributions\n"
        summary += "- **💡 Recommendation:** Consider lower contribution rates or reduced adoption\n"
    
    return summary

def format_detailed_scenarios(results_df, selected_scenarios=None):
    """Format detailed scenario analysis"""
    if selected_scenarios is None:
        # Select key scenarios for client review
        selected_scenarios = [
            (0.0, 8.0),   # No adoption baseline
            (0.25, 8.0),  # Conservative adoption
            (0.5, 8.0),   # Moderate adoption
            (1.0, 6.0),   # High adoption, lower contribution
            (1.0, 12.0),  # Aggressive scenario
        ]
    
    detailed_analysis = "\n## Detailed Scenario Analysis\n\n"
    
    for adoption, contribution in selected_scenarios:
        scenario_data = results_df[
            (results_df['hce_adoption_rate'] == adoption) &
            (results_df['hce_contribution_percent'] == contribution)
        ]
        
        if len(scenario_data) == 0:
            continue
            
        row = scenario_data.iloc[0]
        
        # Determine scenario name
        if adoption == 0.0:
            scenario_name = "Baseline (No Mega-Backdoor)"
        elif adoption <= 0.25:
            scenario_name = "Conservative Adoption"
        elif adoption <= 0.5:
            scenario_name = "Moderate Adoption"
        elif adoption <= 0.75:
            scenario_name = "High Adoption"
        else:
            scenario_name = "Maximum Adoption"
        
        status_emoji = "✅" if row['pass_fail'] == 'PASS' else "❌"
        
        detailed_analysis += f"""
### {scenario_name} - {adoption*100:.0f}% Adoption, {contribution:.1f}% Contribution {status_emoji}

**Test Results:**
- HCE ACP: {row['hce_acp']:.2f}%
- NHCE ACP: {row['nhce_acp']:.2f}%
- IRS Limit A: {row['limit_a']:.2f}%
- IRS Limit B: {row['limit_b']:.2f}%
- Margin: {row['margin']:+.2f}%
- **Result: {row['pass_fail']}**

**Financial Impact:**
- Participating HCEs: {row['n_hce_contributors']} employees
- Mega-Backdoor Contributions: ${row['hce_mega_backdoor_contributions']:,.0f}
- Total HCE Contributions: ${row['hce_total_contributions']:,.0f}

---
"""
    
    return detailed_analysis

def main():
    """Main dashboard function"""
    # Header
    st.markdown('<div class="main-header">🎯 ACP Sensitivity Analysis Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading analysis data..."):
        df_census, results_df, margin_stats = load_analysis_data()
    
    if df_census is None or results_df is None:
        st.error("Failed to load analysis data. Please check your data files.")
        return
    
    # Sidebar controls
    st.sidebar.header("📋 Analysis Controls")
    
    # Analysis type selection
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type:",
        ["Executive Summary", "Detailed Scenarios", "Risk Analysis", "Employee-Level Analysis", "Configuration"]
    )
    
    # Main content area
    if analysis_type == "Executive Summary":
        st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        total_scenarios = len(results_df)
        pass_scenarios = len(results_df[results_df['pass_fail'] == 'PASS'])
        fail_scenarios = total_scenarios - pass_scenarios
        
        with col1:
            st.metric("Total Scenarios", total_scenarios)
        with col2:
            st.metric("Passing Scenarios", pass_scenarios, f"{pass_scenarios/total_scenarios*100:.1f}%")
        with col3:
            st.metric("Failing Scenarios", fail_scenarios, f"{fail_scenarios/total_scenarios*100:.1f}%")
        with col4:
            max_safe = results_df[results_df['pass_fail'] == 'PASS']['hce_contribution_percent'].max()
            st.metric("Max Safe Contribution", f"{max_safe:.1f}%")
        
        # Executive summary text
        summary_text = format_executive_summary(results_df, df_census)
        
        st.markdown('<div class="copy-section">', unsafe_allow_html=True)
        st.markdown(summary_text)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Risk heatmap
        st.markdown('<div class="section-header">Risk Matrix</div>', unsafe_allow_html=True)
        risk_fig = create_risk_heatmap(results_df)
        st.plotly_chart(risk_fig, use_container_width=True)
        
        # Margin analysis
        margin_fig = create_margin_analysis(results_df)
        if margin_fig:
            st.markdown('<div class="section-header">Margin Analysis</div>', unsafe_allow_html=True)
            st.plotly_chart(margin_fig, use_container_width=True)
            
            # Add explanation for all-pass scenarios
            if fail_scenarios == 0:
                st.info("💡 **Great News!** All tested scenarios pass the ACP requirements. This indicates your plan has significant headroom for mega-backdoor Roth contributions across all tested adoption and contribution rates.")
    
    elif analysis_type == "Detailed Scenarios":
        st.markdown('<div class="section-header">Detailed Scenario Analysis</div>', unsafe_allow_html=True)
        
        # Scenario selection
        st.sidebar.subheader("Select Scenarios")
        adoption_options = sorted(results_df['hce_adoption_rate'].unique())
        contribution_options = sorted(results_df['hce_contribution_percent'].unique())
        
        selected_adoption = st.sidebar.multiselect(
            "Adoption Rates:",
            adoption_options,
            default=[0.0, 0.1, 0.2, 0.25],
            format_func=lambda x: f"{x*100:.0f}%"
        )
        
        selected_contribution = st.sidebar.multiselect(
            "Contribution Rates:",
            contribution_options,
            default=[6.0, 8.0, 10.0, 12.0],
            format_func=lambda x: f"{x:.1f}%"
        )
        
        # Generate detailed analysis
        selected_scenarios = [(a, c) for a in selected_adoption for c in selected_contribution]
        detailed_text = format_detailed_scenarios(results_df, selected_scenarios)
        
        st.markdown('<div class="copy-section">', unsafe_allow_html=True)
        st.markdown(detailed_text)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Scenario comparison table
        st.markdown('<div class="section-header">Scenario Comparison Table</div>', unsafe_allow_html=True)
        
        filtered_results = results_df[
            (results_df['hce_adoption_rate'].isin(selected_adoption)) &
            (results_df['hce_contribution_percent'].isin(selected_contribution))
        ]
        
        display_columns = [
            'hce_adoption_rate', 'hce_contribution_percent', 'nhce_acp', 'hce_acp',
            'margin', 'pass_fail', 'n_hce_contributors', 'hce_mega_backdoor_contributions'
        ]
        
        display_df = filtered_results[display_columns].copy()
        display_df['hce_adoption_rate'] = display_df['hce_adoption_rate'].apply(lambda x: f"{x*100:.0f}%")
        display_df['hce_contribution_percent'] = display_df['hce_contribution_percent'].apply(lambda x: f"{x:.1f}%")
        display_df['hce_mega_backdoor_contributions'] = display_df['hce_mega_backdoor_contributions'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True)
    
    elif analysis_type == "Risk Analysis":
        st.markdown('<div class="section-header">Risk Analysis</div>', unsafe_allow_html=True)
        
        # Risk zones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Safe Zone")
            safe_scenarios = results_df[results_df['pass_fail'] == 'PASS']
            if len(safe_scenarios) > 0:
                st.write(f"**{len(safe_scenarios)}** scenarios pass ACP requirements")
                st.write(f"**Max safe contribution:** {safe_scenarios['hce_contribution_percent'].max():.1f}%")
                st.write(f"**Average margin:** {safe_scenarios['margin'].mean():.2f}%")
            else:
                st.write("No safe scenarios found")
        
        with col2:
            st.markdown("### 🔴 Risk Zone")
            risk_scenarios = results_df[results_df['pass_fail'] == 'FAIL']
            if len(risk_scenarios) > 0:
                st.write(f"**{len(risk_scenarios)}** scenarios fail ACP requirements")
                st.write(f"**First failure at:** {risk_scenarios['hce_contribution_percent'].min():.1f}%")
                st.write(f"**Worst margin:** {risk_scenarios['margin'].min():.2f}%")
            else:
                st.write("No failing scenarios found")
        
        # Risk heatmap
        risk_fig = create_risk_heatmap(results_df)
        st.plotly_chart(risk_fig, use_container_width=True)
        
        # Margin distribution
        st.markdown('<div class="section-header">Margin Distribution</div>', unsafe_allow_html=True)
        
        fig = px.histogram(
            results_df, 
            x='margin', 
            color='pass_fail',
            title="Distribution of ACP Test Margins",
            labels={'margin': 'Margin (%)', 'count': 'Number of Scenarios'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Employee-Level Analysis":
        st.markdown('<div class="section-header">Employee-Level Analysis</div>', unsafe_allow_html=True)
        
        # Scenario selection for employee analysis
        st.sidebar.subheader("Select Scenario")
        adoption_options = sorted(results_df['hce_adoption_rate'].unique())
        contribution_options = sorted(results_df['hce_contribution_percent'].unique())
        
        adoption_rate = st.sidebar.selectbox(
            "Adoption Rate:",
            adoption_options,
            index=1,  # Default to second option (0.05 = 5%)
            format_func=lambda x: f"{x*100:.0f}%"
        )
        
        contribution_rate = st.sidebar.selectbox(
            "Contribution Rate:",
            contribution_options,
            index=3,  # Default to fourth option (8.0%)
            format_func=lambda x: f"{x:.1f}%"
        )
        
        # Run employee-level analysis
        with st.spinner("Running employee-level analysis..."):
            analysis_result = analyze_employee_level_scenario(
                df_census, 
                adoption_rate, 
                contribution_rate,
                f"{adoption_rate*100:.0f}% Adoption, {contribution_rate:.1f}% Contribution"
            )
        
        summary = analysis_result['scenario_summary']
        hce_details = analysis_result['hce_details']
        nhce_details = analysis_result['nhce_details']
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Test Result", summary['pass_fail'])
        with col2:
            st.metric("Margin", f"{summary['margin']:.2f}%")
        with col3:
            st.metric("Mega-Backdoor Users", summary['total_mega_backdoor_users'])
        
        # Employee details
        st.markdown("### HCE Employee Details")
        
        # Format HCE details for display
        hce_display = hce_details.copy()
        hce_display['compensation'] = hce_display['compensation'].apply(lambda x: f"${x:,.0f}")
        hce_display['total_contributions'] = hce_display['total_contributions'].apply(lambda x: f"${x:,.0f}")
        hce_display['mega_backdoor_contribution'] = hce_display['mega_backdoor_contribution'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(hce_display, use_container_width=True)
        
        # NHCE summary
        st.markdown("### NHCE Summary")
        st.write(f"**Average ACP:** {summary['nhce_acp']:.2f}%")
        st.write(f"**Employee Count:** {len(nhce_details)}")
    
    elif analysis_type == "Configuration":
        st.markdown('<div class="section-header">Analysis Configuration</div>', unsafe_allow_html=True)
        
        # Import configuration modules
        from constants import config, DEFAULT_PLAN_YEAR, DEFAULT_ADOPTION_RATES, DEFAULT_CONTRIBUTION_RATES
        import yaml
        
        # Display plan year and scenario configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Plan Year Settings")
            st.write(f"**Default Plan Year:** {DEFAULT_PLAN_YEAR}")
            
            st.markdown("### 📈 Scenario Grid")
            st.write("**HCE Adoption Rates:**")
            for rate in DEFAULT_ADOPTION_RATES:
                st.write(f"  • {rate*100:.0f}%")
            
            st.write("**HCE Contribution Rates:**")
            for rate in DEFAULT_CONTRIBUTION_RATES:
                st.write(f"  • {rate:.1f}%")
        
        with col2:
            st.markdown("### ⚖️ IRS Regulatory Limits")
            
            # Display current year limits
            current_limits = config['annual_limits'][str(DEFAULT_PLAN_YEAR)]
            
            st.write(f"**§ 402(g) Elective Deferral Limit:** ${current_limits['elective_deferral_limit_402g']:,}")
            st.write(f"**§ 415(c) Annual Additions Limit:** ${current_limits['annual_additions_limit_415c']:,}")
            st.write(f"**§ 401(a)(17) Compensation Limit:** ${current_limits['compensation_limit_401a17']:,}")
            st.write(f"**§ 414(v) Catch-up Limit (Age 50+):** ${current_limits['catch_up_limit_414v']:,}")
            if current_limits.get('super_catch_up_limit', 0) > 0:
                st.write(f"**SECURE 2.0 Super Catch-up (Age 60-63):** ${current_limits['super_catch_up_limit']:,}")
        
        # Display full YAML configuration
        st.markdown('<div class="section-header">Complete YAML Configuration</div>', unsafe_allow_html=True)
        
        # Read and display the YAML file
        try:
            with open('plan_constants.yaml', 'r') as file:
                yaml_content = file.read()
            
            st.markdown("#### 📄 plan_constants.yaml")
            st.code(yaml_content, language='yaml')
            
        except FileNotFoundError:
            st.error("⚠️ plan_constants.yaml file not found")
        except Exception as e:
            st.error(f"⚠️ Error reading configuration: {e}")
        
        # ACP Test Configuration
        st.markdown('<div class="section-header">ACP Test Parameters</div>', unsafe_allow_html=True)
        
        from constants import ACP_MULTIPLIER, ACP_ADDER, RANDOM_SEED
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🧮 Test Formulas")
            st.write("**ACP Calculation:**")
            st.code("ACP = (Matching + After-Tax Contributions) ÷ Compensation × 100", language='text')
            
            st.write("**Individual Level Calculation:**")
            st.code("Group ACP = Average of individual employee ACP rates", language='text')
            
        with col2:
            st.markdown("#### 📊 IRS Test Limits")
            st.write(f"**Limit A:** NHCE ACP × {ACP_MULTIPLIER} (125% rule)")
            st.write(f"**Limit B:** NHCE ACP + {ACP_ADDER}% (2 percentage point rule)")
            st.write("**Pass Criteria:** HCE ACP ≤ either Limit A OR Limit B")
            
            st.markdown("#### 🎲 Simulation Settings")
            st.write(f"**Random Seed:** {RANDOM_SEED}")
            st.write("**Purpose:** Ensures reproducible HCE selection")
        
        # Display census summary
        st.markdown('<div class="section-header">Census Data Summary</div>', unsafe_allow_html=True)
        
        # Census statistics
        total_employees = len(df_census)
        hce_count = df_census['is_hce'].sum()
        nhce_count = total_employees - hce_count
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Employees", total_employees)
            st.metric("HCE Count", hce_count)
            st.metric("NHCE Count", nhce_count)
        
        with col2:
            st.metric("HCE Percentage", f"{hce_count/total_employees*100:.1f}%")
            
            # Compensation statistics
            avg_hce_comp = df_census[df_census['is_hce']]['compensation'].mean()
            avg_nhce_comp = df_census[~df_census['is_hce']]['compensation'].mean()
            
            st.metric("Avg HCE Compensation", f"${avg_hce_comp:,.0f}")
            st.metric("Avg NHCE Compensation", f"${avg_nhce_comp:,.0f}")
        
        with col3:
            # Total compensation
            total_comp = df_census['compensation'].sum()
            hce_comp_pct = df_census[df_census['is_hce']]['compensation'].sum() / total_comp * 100
            
            st.metric("Total Compensation", f"${total_comp:,.0f}")
            st.metric("HCE Compensation %", f"{hce_comp_pct:.1f}%")
            
            # Contribution statistics
            total_contributions = (df_census['er_match_amt'] + df_census['ee_pre_tax_amt'] + 
                                 df_census['ee_after_tax_amt'] + df_census['ee_roth_amt']).sum()
            st.metric("Total Baseline Contributions", f"${total_contributions:,.0f}")
        
        # Configuration export
        st.markdown('<div class="section-header">Export Configuration</div>', unsafe_allow_html=True)
        
        # Create downloadable configuration summary
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
        
        st.download_button(
            label="📥 Download Configuration Summary",
            data=config_summary,
            file_name=f"acp_config_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    st.markdown("*This analysis is for informational purposes only and should be reviewed by qualified plan professionals.*")

if __name__ == "__main__":
    main()