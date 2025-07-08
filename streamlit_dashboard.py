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
    
    # Create heatmap
    fig = px.imshow(
        pivot_numeric,
        labels=dict(x="HCE Adoption Rate", y="HCE Contribution Rate", color="Pass/Fail"),
        x=[f"{rate*100:.0f}%" for rate in pivot_numeric.columns],
        y=[f"{rate:.1f}%" for rate in pivot_numeric.index],
        color_continuous_scale=["red", "green"],
        title="ACP Test Results: Pass/Fail Matrix"
    )
    
    # Add text annotations
    for i, row in enumerate(pivot_data.index):
        for j, col in enumerate(pivot_data.columns):
            fig.add_annotation(
                x=j, y=i,
                text=pivot_data.loc[row, col],
                showarrow=False,
                font=dict(color="white", size=12, family="Arial Black")
            )
    
    fig.update_layout(
        width=800,
        height=500,
        font=dict(size=12)
    )
    
    return fig

def create_margin_analysis(results_df):
    """Create margin analysis visualization"""
    # Filter for scenarios with positive margins (passing scenarios)
    passing_scenarios = results_df[results_df['pass_fail'] == 'PASS']
    
    if len(passing_scenarios) == 0:
        return None
    
    # Create margin heatmap
    pivot_margin = passing_scenarios.pivot_table(
        index='hce_contribution_percent',
        columns='hce_adoption_rate',
        values='margin',
        aggfunc='first'
    )
    
    fig = px.imshow(
        pivot_margin,
        labels=dict(x="HCE Adoption Rate", y="HCE Contribution Rate", color="Margin %"),
        x=[f"{rate*100:.0f}%" for rate in pivot_margin.columns],
        y=[f"{rate:.1f}%" for rate in pivot_margin.index],
        color_continuous_scale="RdYlGn",
        title="ACP Test Margins (Passing Scenarios Only)"
    )
    
    # Add text annotations
    for i, row in enumerate(pivot_margin.index):
        for j, col in enumerate(pivot_margin.columns):
            value = pivot_margin.loc[row, col]
            if not pd.isna(value):
                fig.add_annotation(
                    x=j, y=i,
                    text=f"{value:.1f}%",
                    showarrow=False,
                    font=dict(color="black", size=10)
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
    max_safe_contribution = results_df[results_df['pass_fail'] == 'PASS']['hce_contribution_percent'].max()
    min_failing_contribution = results_df[results_df['pass_fail'] == 'FAIL']['hce_contribution_percent'].min()
    
    # Get census summary
    total_employees = len(df_census)
    hce_count = df_census['is_hce'].sum()
    nhce_count = total_employees - hce_count
    
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
    
    if pass_scenarios > 0:
        summary += f"- **✅ Safe Contribution Level:** Up to {max_safe_contribution:.1f}% contribution rate at any adoption level\n"
    
    if fail_scenarios > 0 and not pd.isna(min_failing_contribution):
        summary += f"- **⚠️ Risk Zone:** Failures begin at {min_failing_contribution:.1f}% contribution rate\n"
    
    # Add risk assessment
    if fail_scenarios == 0:
        summary += "- **🎯 Risk Assessment:** LOW - All tested scenarios pass ACP requirements\n"
    elif pass_scenarios > fail_scenarios:
        summary += "- **🎯 Risk Assessment:** MODERATE - Most scenarios pass, some restrictions apply\n"
    else:
        summary += "- **🎯 Risk Assessment:** HIGH - Significant restrictions on mega-backdoor contributions\n"
    
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
        ["Executive Summary", "Detailed Scenarios", "Risk Analysis", "Employee-Level Analysis"]
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
    
    elif analysis_type == "Detailed Scenarios":
        st.markdown('<div class="section-header">Detailed Scenario Analysis</div>', unsafe_allow_html=True)
        
        # Scenario selection
        st.sidebar.subheader("Select Scenarios")
        adoption_options = sorted(results_df['hce_adoption_rate'].unique())
        contribution_options = sorted(results_df['hce_contribution_percent'].unique())
        
        selected_adoption = st.sidebar.multiselect(
            "Adoption Rates:",
            adoption_options,
            default=[0.0, 0.25, 0.5, 1.0],
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
        adoption_rate = st.sidebar.selectbox(
            "Adoption Rate:",
            [0.0, 0.25, 0.5, 0.75, 1.0],
            index=1,
            format_func=lambda x: f"{x*100:.0f}%"
        )
        
        contribution_rate = st.sidebar.selectbox(
            "Contribution Rate:",
            [2.0, 4.0, 6.0, 8.0, 10.0, 12.0],
            index=3,
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
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    st.markdown("*This analysis is for informational purposes only and should be reviewed by qualified plan professionals.*")

if __name__ == "__main__":
    main()