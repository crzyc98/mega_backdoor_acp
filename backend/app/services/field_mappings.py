"""
Field Mapping Configuration for CSV Import Wizard.

Defines the required census fields and their aliases for auto-suggestion.
Implements fuzzy matching for column name detection.
"""

from __future__ import annotations

from difflib import SequenceMatcher

# Required census fields for import
REQUIRED_FIELDS = [
    "ssn",
    "dob",
    "hire_date",
    "compensation",
    "employee_pre_tax",
    "employee_after_tax",
    "employee_roth",
    "employer_match",
    "employer_non_elective",
]

# Optional fields that enhance functionality
OPTIONAL_FIELDS = [
    "hce_status",
    "termination_date",
]

# Field display names for UI
FIELD_DISPLAY_NAMES = {
    "ssn": "Social Security Number",
    "dob": "Date of Birth",
    "hire_date": "Hire Date",
    "termination_date": "Termination Date",
    "hce_status": "HCE Status",
    "compensation": "Compensation",
    "employee_pre_tax": "Employee Pre-Tax Contributions",
    "employee_after_tax": "Employee After-Tax Contributions",
    "employee_roth": "Employee Roth Contributions",
    "employer_match": "Employer Match Contributions",
    "employer_non_elective": "Employer Non-Elective Contributions",
}

# Aliases for each required field (lowercase for matching)
FIELD_ALIASES: dict[str, list[str]] = {
    "ssn": [
        "ssn",
        "social security",
        "social security number",
        "ss#",
        "ss #",
        "ss",
        "social_security_number",
        "tax_id",
        "tax id",
        "taxid",
        "ssn_hash",
    ],
    "dob": [
        "dob",
        "date of birth",
        "birth date",
        "birthdate",
        "birth_date",
        "date_of_birth",
        "birthday",
        "bdate",
        "b_date",
    ],
    "hire_date": [
        "hire date",
        "hire_date",
        "hiredate",
        "date hired",
        "date_hired",
        "start date",
        "start_date",
        "startdate",
        "employment date",
        "employment_date",
        "original hire date",
        "original_hire_date",
    ],
    "compensation": [
        "compensation",
        "salary",
        "annual compensation",
        "annual_compensation",
        "wages",
        "annual salary",
        "annual_salary",
        "gross compensation",
        "gross_compensation",
        "total compensation",
        "total_compensation",
        "pay",
        "earnings",
        "annual pay",
        "annual_pay",
        "comp",
    ],
    "employee_pre_tax": [
        "pre tax",
        "pretax",
        "pre_tax",
        "pre-tax",
        "pre tax contributions",
        "pre-tax contributions",
        "pre_tax_contributions",
        "401k",
        "401(k)",
        "deferral",
        "deferrals",
        "ee pre tax",
        "ee_pre_tax",
        "ee pretax",
        "employee pre tax",
        "employee_pre_tax",
        "employee pretax",
        "traditional",
        "traditional 401k",
        "elective deferral",
        "elective_deferral",
        "employee deferral",
        "employee_deferral",
    ],
    "employee_after_tax": [
        "after tax",
        "aftertax",
        "after_tax",
        "after-tax",
        "after tax contributions",
        "after-tax contributions",
        "after_tax_contributions",
        "ee after tax",
        "ee_after_tax",
        "ee aftertax",
        "employee after tax",
        "employee_after_tax",
        "employee aftertax",
        "voluntary after tax",
        "voluntary_after_tax",
        "post tax",
        "post_tax",
        "posttax",
    ],
    "employee_roth": [
        "roth",
        "roth 401k",
        "roth_401k",
        "roth 401(k)",
        "ee roth",
        "ee_roth",
        "employee roth",
        "employee_roth",
        "roth deferral",
        "roth_deferral",
        "roth contributions",
        "roth_contributions",
        "roth contribution",
    ],
    "employer_match": [
        "match",
        "employer match",
        "employer_match",
        "er match",
        "er_match",
        "company match",
        "company_match",
        "matching",
        "matching contribution",
        "matching_contribution",
        "employer matching",
        "employer_matching",
        "safe harbor match",
        "safe_harbor_match",
    ],
    "employer_non_elective": [
        "non elective",
        "nonelective",
        "non_elective",
        "profit sharing",
        "profit_sharing",
        "profitsharing",
        "er non elective",
        "er_non_elective",
        "employer non elective",
        "employer_non_elective",
        "safe harbor",
        "safe_harbor",
        "qnec",
        "employer contribution",
        "employer_contribution",
        "discretionary",
    ],
    # Optional fields
    "termination_date": [
        "termination date",
        "termination_date",
        "terminationdate",
        "term date",
        "term_date",
        "termdate",
        "end date",
        "end_date",
        "separation date",
        "separation_date",
        "date terminated",
        "date_terminated",
        "last day",
        "last_day",
    ],
    "hce_status": [
        "hce status",
        "hce_status",
        "hcestatus",
        "hce",
        "is hce",
        "is_hce",
        "ishce",
        "highly compensated",
        "highly_compensated",
        "hce indicator",
        "hce_indicator",
        "hce flag",
        "hce_flag",
    ],
}

# Minimum confidence score for auto-suggestion
MIN_CONFIDENCE_THRESHOLD = 0.6


def normalize_header(header: str) -> str:
    """
    Normalize a column header for matching.

    Converts to lowercase and replaces underscores with spaces.
    """
    return header.lower().strip().replace("_", " ")


def calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculate string similarity using SequenceMatcher.

    Returns a score between 0.0 and 1.0.
    """
    return SequenceMatcher(None, s1, s2).ratio()


def find_best_match(
    header: str, aliases: list[str]
) -> tuple[bool, float]:
    """
    Find if a header matches any alias for a field.

    Args:
        header: Normalized column header
        aliases: List of aliases to match against

    Returns:
        Tuple of (is_match, confidence_score)
    """
    # Exact match
    if header in aliases:
        return True, 1.0

    # Check if header starts with any alias
    for alias in aliases:
        if header.startswith(alias) or alias.startswith(header):
            return True, 0.9

    # Fuzzy match
    best_score = 0.0
    for alias in aliases:
        score = calculate_similarity(header, alias)
        best_score = max(best_score, score)

    if best_score >= MIN_CONFIDENCE_THRESHOLD:
        return True, best_score

    return False, best_score


def suggest_mapping(headers: list[str]) -> tuple[dict[str, str], dict[str, float], list[str]]:
    """
    Auto-suggest column mappings based on header names.

    Args:
        headers: List of CSV column headers

    Returns:
        Tuple of:
        - mapping: dict mapping target field to source column
        - confidence_scores: dict mapping target field to confidence score
        - missing_fields: list of required fields not mapped
    """
    mapping: dict[str, str] = {}
    confidence_scores: dict[str, float] = {}

    # Create normalized header lookup
    normalized_headers = {normalize_header(h): h for h in headers}

    # Try to match each required field
    for field, aliases in FIELD_ALIASES.items():
        best_header = None
        best_score = 0.0

        for normalized, original in normalized_headers.items():
            # Skip if this header was already matched to a higher-priority field
            if original in mapping.values():
                continue

            is_match, score = find_best_match(normalized, aliases)
            if is_match and score > best_score:
                best_header = original
                best_score = score

        if best_header is not None:
            mapping[field] = best_header
            confidence_scores[field] = best_score

    # Determine missing fields
    missing_fields = [f for f in REQUIRED_FIELDS if f not in mapping]

    return mapping, confidence_scores, missing_fields


def validate_mapping(mapping: dict[str, str]) -> tuple[bool, list[str]]:
    """
    Validate that all required fields are mapped.

    Args:
        mapping: dict mapping target field to source column

    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing = [f for f in REQUIRED_FIELDS if f not in mapping or not mapping[f]]
    return len(missing) == 0, missing


def get_field_display_name(field: str) -> str:
    """Get the human-readable display name for a field."""
    return FIELD_DISPLAY_NAMES.get(field, field.replace("_", " ").title())
