# ACP Sensitivity Analysis Dashboard

A professional Streamlit dashboard for creating client-ready ACP (Actual Contribution Percentage) sensitivity analysis reports for mega-backdoor Roth 401(k) contributions.

## Features

### 📊 Executive Summary
- Key metrics overview
- Professional summary text (ready for client emails)
- Risk assessment
- Plan demographics
- Pass/fail statistics

### 🔍 Detailed Scenarios
- Interactive scenario selection
- Detailed analysis for each scenario
- Comparison tables
- Financial impact analysis

### ⚠️ Risk Analysis
- Risk zone identification
- Pass/fail heatmap visualization
- Margin distribution analysis
- Safe contribution thresholds

### 👥 Employee-Level Analysis
- Individual employee breakdowns
- § 415(c) limit compliance checking
- Mega-backdoor adoption impact
- HCE vs NHCE analysis

## Quick Start

### Option 1: Using the run script
```bash
./run_dashboard.sh
```

### Option 2: Manual launch
```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run streamlit_dashboard.py
```

## Usage for Client Communications

### 1. Executive Summary
- Navigate to "Executive Summary" in the sidebar
- Copy the formatted summary text
- Paste directly into client emails
- Include the risk matrix visualization

### 2. Detailed Analysis
- Select "Detailed Scenarios" 
- Choose relevant adoption/contribution rates
- Copy scenario analysis text
- Include comparison tables as needed

### 3. Risk Assessment
- Use "Risk Analysis" for risk zone identification
- Include heatmap visualizations
- Show margin distributions for context

### 4. Employee-Level Details
- Use "Employee-Level Analysis" for detailed breakdowns
- Show individual compliance with § 415(c) limits
- Demonstrate impact on specific employees

## Professional Features

### Client-Ready Formatting
- Professional styling and layout
- Easy copy/paste sections
- Executive summary format
- Clear risk assessments

### Compliance Checking
- § 415(c) limit enforcement
- ACP test methodology validation
- IRS regulation compliance
- Individual employee limit tracking

### Interactive Visualizations
- Risk heatmaps
- Margin analysis charts
- Scenario comparison tables
- Employee-level breakdowns

## Technical Details

### Data Sources
- `census.csv` - Employee demographic data
- `plan_constants.yaml` - IRS limits and regulations
- Analysis modules from the core ACP calculator

### Calculations
- Individual-level ACP calculations
- IRS two-part test implementation
- Contribution limits enforcement
- Monte Carlo scenario analysis

### Caching
- Analysis results are cached for performance
- Data updates require dashboard restart
- Cached results improve response times

## Tips for Client Presentations

1. **Start with Executive Summary**: Give clients the high-level view first
2. **Use Risk Matrix**: Visual representation is easier to understand
3. **Show Specific Scenarios**: Focus on realistic adoption rates
4. **Include Employee Details**: Demonstrate individual compliance
5. **Copy Professional Text**: Use the formatted summaries in emails

## File Structure
```
streamlit_dashboard.py    # Main dashboard application
run_dashboard.sh         # Launch script
requirements.txt         # Python dependencies
census.csv              # Employee data
plan_constants.yaml     # IRS limits
```

## Troubleshooting

### Common Issues
- **Port already in use**: Dashboard tries to use port 8501
- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Data not loading**: Check census.csv and plan_constants.yaml

### Performance Tips
- Use cached analysis results
- Restart dashboard when data changes
- Close unused browser tabs

## Customization

### Adding New Scenarios
- Modify `DEFAULT_ADOPTION_RATES` in constants.py
- Update `DEFAULT_CONTRIBUTION_RATES` for new ranges
- Restart dashboard to pick up changes

### Styling Changes
- Modify CSS in the dashboard file
- Update color schemes in visualizations
- Adjust layout and spacing

## Security Notes

- Dashboard runs locally by default
- No sensitive data is transmitted
- Use appropriate network security if deploying remotely
- Client data should be handled according to firm policies

---

*This dashboard is designed for professional use by qualified plan administrators and consultants. Analysis results should be reviewed by appropriate professionals before client communication.*