"""
Spacing and Border Radius Constants.

Defines consistent spacing scale and border radius values.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Spacing:
    """Spacing scale for margins, padding, and gaps."""

    # Spacing scale (rem values, base 16px)
    xs: str = "0.25rem"   # 4px
    sm: str = "0.5rem"    # 8px
    md: str = "0.75rem"   # 12px
    base: str = "1rem"    # 16px
    lg: str = "1.25rem"   # 20px
    xl: str = "1.5rem"    # 24px
    xxl: str = "2rem"     # 32px
    xxxl: str = "2.5rem"  # 40px
    xxxxl: str = "3rem"   # 48px

    # Pixel-based spacing for specific use cases
    px_4: str = "4px"
    px_8: str = "8px"
    px_12: str = "12px"
    px_16: str = "16px"
    px_20: str = "20px"
    px_24: str = "24px"
    px_32: str = "32px"


@dataclass(frozen=True)
class BorderRadius:
    """Border radius scale for rounded corners."""

    none: str = "0"
    sm: str = "0.125rem"   # 2px
    default: str = "0.25rem"  # 4px
    md: str = "0.375rem"   # 6px
    lg: str = "0.5rem"     # 8px
    xl: str = "0.75rem"    # 12px
    xxl: str = "1rem"      # 16px
    full: str = "9999px"   # Fully rounded (pills, circles)


# Singleton instances for easy import
SPACING = Spacing()
BORDER_RADIUS = BorderRadius()
