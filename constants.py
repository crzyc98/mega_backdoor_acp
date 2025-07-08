# ACP Sensitivity Analyzer - Constants
# IRS Regulation Constants for ACP Testing

# ACP Test Limits (IRC §401(m))
ACP_MULTIPLIER = 1.25  # Factor applied to NHCE ACP
ACP_ADDER = 2.00       # Percentage points added to NHCE ACP

# Output Files
RESULTS_FILE = 'acp_results.csv'
HEATMAP_FILE = 'acp_heatmap.csv'

# Data Validation Constants
HCE_THRESHOLD = 150000  # 2025 HCE compensation threshold
MIN_COMPENSATION = 10000  # Minimum reasonable compensation
MAX_COMPENSATION = 500000  # Maximum reasonable compensation

# Scenario Grid Defaults (MVP)
DEFAULT_ADOPTION_RATES = [0.0, 0.25, 0.50, 0.75, 1.0]
DEFAULT_CONTRIBUTION_RATES = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]

# Random Seed for Reproducibility
RANDOM_SEED = 42