# ACP Sensitivity Analyzer - Constants
# Configuration loaded from plan_constants.yaml

import yaml
import os

# Load configuration from YAML file
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'plan_constants.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Load configuration
config = load_config()

# ACP Test Limits (IRC §401(m))
ACP_MULTIPLIER = config['acp_test']['multiplier']
ACP_ADDER = config['acp_test']['adder']

# Output Files
RESULTS_FILE = config['output_files']['results_file']
HEATMAP_FILE = config['output_files']['heatmap_file']

# Data Validation Constants
MIN_COMPENSATION = config['data_validation']['min_compensation']
MAX_COMPENSATION = config['data_validation']['max_compensation']

# Scenario Grid Defaults (MVP)
DEFAULT_ADOPTION_RATES = config['scenario_defaults']['adoption_rates']
DEFAULT_CONTRIBUTION_RATES = config['scenario_defaults']['contribution_rates']

# Random Seed for Reproducibility
RANDOM_SEED = config['random_seed']

# Helper functions for plan year specific values
def get_annual_limit(plan_year, limit_type):
    """Get annual limit for specific plan year and limit type"""
    return config['annual_limits'][plan_year][limit_type]

def get_hce_threshold(plan_year):
    """Get HCE threshold for specific plan year"""
    return get_annual_limit(plan_year, 'hce_threshold')

def get_compensation_limit(plan_year):
    """Get § 401(a)(17) compensation limit for specific plan year"""
    return get_annual_limit(plan_year, 'compensation_limit_401a17')

def get_elective_deferral_limit(plan_year):
    """Get § 402(g) elective deferral limit for specific plan year"""
    return get_annual_limit(plan_year, 'elective_deferral_limit_402g')

def get_annual_additions_limit(plan_year):
    """Get § 415(c) annual additions limit for specific plan year"""
    return get_annual_limit(plan_year, 'annual_additions_limit_415c')

# Default plan year
DEFAULT_PLAN_YEAR = config['default_plan_year']

# Backward compatibility - use default plan year values
HCE_THRESHOLD = get_hce_threshold(DEFAULT_PLAN_YEAR)
COMPENSATION_LIMIT_401A17 = get_compensation_limit(DEFAULT_PLAN_YEAR)