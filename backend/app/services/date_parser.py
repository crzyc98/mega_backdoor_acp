"""
Date Format Parser Service for CSV Import Wizard.

T020: Provides date format detection and parsing with live preview.
"""

from datetime import datetime
from typing import NamedTuple


# Supported date formats with human-readable labels
DATE_FORMATS = [
    ("%m/%d/%Y", "MM/DD/YYYY"),      # US format
    ("%Y-%m-%d", "YYYY-MM-DD"),      # ISO format
    ("%d/%m/%Y", "DD/MM/YYYY"),      # European format
    ("%m/%d/%y", "MM/DD/YY"),        # US short
    ("%d/%m/%y", "DD/MM/YY"),        # European short
    ("%m-%d-%Y", "MM-DD-YYYY"),      # US with dashes
    ("%d-%m-%Y", "DD-MM-YYYY"),      # European with dashes
    ("%Y/%m/%d", "YYYY/MM/DD"),      # Asian format
    ("%m-%d-%y", "MM-DD-YY"),        # US short with dashes
    ("%d-%m-%y", "DD-MM-YY"),        # European short with dashes
]


class DateSample(NamedTuple):
    """Result of parsing a single date value."""
    raw_value: str
    parsed_date: str | None  # ISO format if valid
    display_date: str | None  # Human-readable format
    valid: bool
    error: str | None


class DateFormatOption(NamedTuple):
    """Information about a date format option."""
    format: str
    label: str
    success_rate: float
    recommended: bool


class DateFormatDetection(NamedTuple):
    """Result of date format auto-detection."""
    recommended_format: str
    formats: list[DateFormatOption]


class DateFormatPreview(NamedTuple):
    """Preview of date parsing with a specific format."""
    format: str
    format_label: str
    samples: list[DateSample]
    success_rate: float


def parse_date_with_format(value: str, fmt: str) -> tuple[datetime | None, str | None]:
    """
    Parse a date string with a specific format.

    Args:
        value: Date string to parse
        fmt: Python strptime format string

    Returns:
        Tuple of (parsed_datetime, error_message)
    """
    if not value or not value.strip():
        return None, "Empty value"

    value = str(value).strip()

    try:
        parsed = datetime.strptime(value, fmt)
        return parsed, None
    except ValueError as e:
        return None, str(e)


def parse_date_sample(value: str, fmt: str) -> DateSample:
    """
    Parse a date value and return a DateSample result.

    Args:
        value: Raw date value from CSV
        fmt: Python strptime format string

    Returns:
        DateSample with parsing results
    """
    parsed, error = parse_date_with_format(value, fmt)

    if parsed:
        return DateSample(
            raw_value=value,
            parsed_date=parsed.date().isoformat(),
            display_date=parsed.strftime("%B %d, %Y"),  # e.g., "January 15, 2020"
            valid=True,
            error=None,
        )
    else:
        return DateSample(
            raw_value=value,
            parsed_date=None,
            display_date=None,
            valid=False,
            error=error,
        )


def calculate_success_rate(values: list[str], fmt: str) -> float:
    """
    Calculate the success rate of parsing dates with a given format.

    Args:
        values: List of date strings to test
        fmt: Format to test

    Returns:
        Success rate as a float between 0.0 and 1.0
    """
    if not values:
        return 0.0

    successful = 0
    total = 0

    for value in values:
        if value and str(value).strip():
            total += 1
            parsed, _ = parse_date_with_format(value, fmt)
            if parsed:
                successful += 1

    if total == 0:
        return 0.0

    return successful / total


def detect_date_format(sample_values: list[str]) -> DateFormatDetection:
    """
    Auto-detect the most likely date format from sample values.

    Args:
        sample_values: List of sample date strings from the CSV

    Returns:
        DateFormatDetection with recommended format and all options
    """
    # Calculate success rate for each format
    format_scores: list[tuple[str, str, float]] = []

    for fmt, label in DATE_FORMATS:
        rate = calculate_success_rate(sample_values, fmt)
        format_scores.append((fmt, label, rate))

    # Sort by success rate (descending)
    format_scores.sort(key=lambda x: x[2], reverse=True)

    # The best format is the recommended one
    recommended_format = format_scores[0][0] if format_scores else DATE_FORMATS[0][0]
    best_rate = format_scores[0][2] if format_scores else 0.0

    # Build options list
    formats = []
    for fmt, label, rate in format_scores:
        formats.append(DateFormatOption(
            format=fmt,
            label=label,
            success_rate=rate,
            recommended=(fmt == recommended_format and best_rate > 0),
        ))

    return DateFormatDetection(
        recommended_format=recommended_format,
        formats=formats,
    )


def preview_date_format(sample_values: list[str], fmt: str) -> DateFormatPreview:
    """
    Preview how a specific format parses sample date values.

    Args:
        sample_values: List of sample date strings
        fmt: Format to preview

    Returns:
        DateFormatPreview with parsed samples and success rate
    """
    # Find label for format
    label = fmt  # Default to format itself
    for f, l in DATE_FORMATS:
        if f == fmt:
            label = l
            break

    # Parse samples
    samples = []
    for value in sample_values[:10]:  # Limit to 10 samples
        if value and str(value).strip():
            samples.append(parse_date_sample(value, fmt))

    # Calculate success rate
    success_rate = calculate_success_rate(sample_values, fmt)

    return DateFormatPreview(
        format=fmt,
        format_label=label,
        samples=samples,
        success_rate=success_rate,
    )


def get_date_column_values(
    df,
    column_mapping: dict[str, str],
    max_samples: int = 20,
) -> list[str]:
    """
    Extract sample values from date columns in a DataFrame.

    Args:
        df: pandas DataFrame with CSV data
        column_mapping: Map of target field to source column
        max_samples: Maximum number of samples to return

    Returns:
        List of sample date values from all date columns
    """
    date_fields = ["dob", "hire_date"]
    samples = []

    for field in date_fields:
        col = column_mapping.get(field)
        if col and col in df.columns:
            # Get non-empty values
            values = df[col].dropna().astype(str).tolist()
            values = [v for v in values if v.strip()]
            samples.extend(values[:max_samples])

    # Remove duplicates while preserving order
    seen = set()
    unique_samples = []
    for v in samples:
        if v not in seen:
            seen.add(v)
            unique_samples.append(v)
            if len(unique_samples) >= max_samples:
                break

    return unique_samples
