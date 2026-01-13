"""
CSS Generation Utilities.

Generates CSS strings for Streamlit styling using theme constants.
"""

from src.ui.theme.colors import COLORS
from src.ui.theme.typography import TYPOGRAPHY
from src.ui.theme.spacing import SPACING, BORDER_RADIUS
from src.ui.theme.shadows import SHADOWS


def get_base_css() -> str:
    """Generate base CSS for global styling (typography, layout)."""
    return f"""
    /* Global Typography */
    html, body, [class*="st-"] {{
        font-family: {TYPOGRAPHY.font_family};
    }}

    /* Main container styling */
    .main .block-container {{
        padding-top: {SPACING.xl};
        padding-bottom: {SPACING.xl};
        max-width: 1200px;
    }}

    /* Headings */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-weight: {TYPOGRAPHY.weight_bold};
        color: {COLORS.gray_900};
        letter-spacing: {TYPOGRAPHY.tracking_tight};
    }}

    h1, .stMarkdown h1 {{
        font-weight: {TYPOGRAPHY.weight_extrabold};
    }}

    /* Body text */
    p, .stMarkdown p {{
        color: {COLORS.gray_700};
        line-height: {TYPOGRAPHY.leading_relaxed};
    }}

    /* Subtle text */
    .stCaption, small {{
        color: {COLORS.gray_500};
    }}
    """


def get_card_css() -> str:
    """Generate CSS for card-based layouts."""
    return f"""
    /* Card container styling */
    .acp-card {{
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xl};
        box-shadow: {SHADOWS.sm};
        margin-bottom: {SPACING.lg};
    }}

    .acp-card-header {{
        font-weight: {TYPOGRAPHY.weight_semibold};
        font-size: 1.125rem;
        color: {COLORS.gray_900};
        margin-bottom: {SPACING.md};
        padding-bottom: {SPACING.sm};
        border-bottom: 1px solid {COLORS.gray_100};
    }}

    /* Streamlit expander as card */
    .streamlit-expanderHeader {{
        font-weight: {TYPOGRAPHY.weight_semibold};
        color: {COLORS.gray_900};
    }}

    /* Divider styling */
    hr {{
        border: none;
        border-top: 1px solid {COLORS.gray_200};
        margin: {SPACING.xl} 0;
    }}
    """


def get_navigation_css() -> str:
    """Generate CSS for navigation and sidebar styling."""
    return f"""
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: {COLORS.gray_50};
    }}

    [data-testid="stSidebar"] .stMarkdown h1 {{
        color: {COLORS.primary};
        font-weight: {TYPOGRAPHY.weight_extrabold};
        font-size: 1.5rem;
        letter-spacing: {TYPOGRAPHY.tracking_tight};
    }}

    /* Sidebar navigation items */
    [data-testid="stSidebar"] .stRadio > div {{
        gap: {SPACING.xs};
    }}

    [data-testid="stSidebar"] .stRadio label {{
        padding: {SPACING.sm} {SPACING.md};
        border-radius: {BORDER_RADIUS.lg};
        transition: background-color 0.2s ease;
    }}

    [data-testid="stSidebar"] .stRadio label:hover {{
        background-color: {COLORS.gray_100};
    }}

    /* Active navigation state */
    [data-testid="stSidebar"] .stRadio [data-checked="true"] label,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {{
        background-color: {COLORS.primary_light};
        color: {COLORS.primary};
        font-weight: {TYPOGRAPHY.weight_semibold};
    }}

    /* Step number badges */
    .step-number {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: {BORDER_RADIUS.full};
        background: {COLORS.primary};
        color: {COLORS.white};
        font-size: 0.75rem;
        font-weight: {TYPOGRAPHY.weight_bold};
        margin-right: {SPACING.sm};
    }}
    """


def get_button_css() -> str:
    """Generate CSS for button styling (T049)."""
    return f"""
    /* === T049: Button Styling with Padding, Border-radius, Shadow, Hover === */

    /* Primary button */
    .stButton > button[kind="primary"],
    .stButton > button {{
        background: linear-gradient(180deg, {COLORS.primary} 0%, {COLORS.primary_hover} 100%);
        color: {COLORS.white};
        border: none;
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.md} {SPACING.xl};
        font-weight: {TYPOGRAPHY.weight_semibold};
        font-size: 1rem;
        box-shadow: {SHADOWS.sm}, 0 1px 2px rgba(79, 70, 229, 0.2);
        transition: all 0.2s ease;
        cursor: pointer;
    }}

    .stButton > button:hover {{
        background: linear-gradient(180deg, {COLORS.primary_hover} 0%, #3730A3 100%);
        box-shadow: {SHADOWS.md}, 0 4px 6px rgba(79, 70, 229, 0.25);
        transform: translateY(-2px);
    }}

    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: {SHADOWS.sm};
    }}

    .stButton > button:focus {{
        outline: none;
        box-shadow: {SHADOWS.md}, 0 0 0 3px {COLORS.primary_light};
    }}

    /* Secondary/outline button */
    .stButton > button[kind="secondary"] {{
        background: {COLORS.white};
        color: {COLORS.gray_700};
        border: 1px solid {COLORS.gray_300};
        box-shadow: {SHADOWS.xs};
    }}

    .stButton > button[kind="secondary"]:hover {{
        background: {COLORS.gray_50};
        border-color: {COLORS.gray_400};
        color: {COLORS.gray_900};
        box-shadow: {SHADOWS.sm};
    }}

    /* Download button special styling */
    .stDownloadButton > button {{
        background: {COLORS.success};
        color: {COLORS.white};
        border: none;
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.md} {SPACING.xl};
        font-weight: {TYPOGRAPHY.weight_semibold};
        box-shadow: {SHADOWS.sm}, 0 1px 2px rgba(16, 185, 129, 0.2);
        transition: all 0.2s ease;
    }}

    .stDownloadButton > button:hover {{
        background: #059669;
        box-shadow: {SHADOWS.md}, 0 4px 6px rgba(16, 185, 129, 0.25);
        transform: translateY(-2px);
    }}

    /* Form submit button */
    .stForm [data-testid="stFormSubmitButton"] button {{
        background: {COLORS.primary};
        color: {COLORS.white};
        border: none;
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.md} {SPACING.xl};
        font-weight: {TYPOGRAPHY.weight_semibold};
        width: auto;
        min-width: 120px;
    }}

    /* Link-style button */
    .stButton > button[kind="tertiary"] {{
        background: transparent;
        color: {COLORS.primary};
        border: none;
        padding: {SPACING.sm} {SPACING.md};
        box-shadow: none;
    }}

    .stButton > button[kind="tertiary"]:hover {{
        background: {COLORS.primary_light};
        transform: none;
        box-shadow: none;
    }}

    /* Disabled button state */
    .stButton > button:disabled {{
        background: {COLORS.gray_200};
        color: {COLORS.gray_400};
        cursor: not-allowed;
        box-shadow: none;
        transform: none;
    }}

    .stButton > button:disabled:hover {{
        background: {COLORS.gray_200};
        transform: none;
        box-shadow: none;
    }}
    """


def get_form_css() -> str:
    """Generate CSS for form control styling (T048-T052)."""
    return f"""
    /* === T050: Input Field Styling === */
    /* Text input fields */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {{
        border-radius: {BORDER_RADIUS.lg};
        border: 1px solid {COLORS.gray_300};
        padding: {SPACING.sm} {SPACING.md};
        font-size: 1rem;
        color: {COLORS.gray_900};
        background: {COLORS.white};
        transition: all 0.2s ease;
    }}

    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus {{
        border-color: {COLORS.primary};
        box-shadow: 0 0 0 3px {COLORS.primary_light};
        outline: none;
    }}

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: {COLORS.gray_400};
    }}

    /* Input labels */
    .stTextInput label,
    .stNumberInput label,
    .stTextArea label {{
        font-weight: {TYPOGRAPHY.weight_medium};
        color: {COLORS.gray_700};
        margin-bottom: {SPACING.xs};
    }}

    /* === T051: Selectbox/Dropdown Styling === */
    .stSelectbox [data-baseweb="select"] {{
        border-radius: {BORDER_RADIUS.lg};
    }}

    .stSelectbox [data-baseweb="select"] > div {{
        border-radius: {BORDER_RADIUS.lg};
        border: 1px solid {COLORS.gray_300};
        background: {COLORS.white};
        transition: all 0.2s ease;
    }}

    .stSelectbox [data-baseweb="select"]:focus-within > div {{
        border-color: {COLORS.primary};
        box-shadow: 0 0 0 3px {COLORS.primary_light};
    }}

    .stSelectbox [data-baseweb="select"] > div:hover {{
        border-color: {COLORS.gray_400};
    }}

    /* Dropdown menu */
    [data-baseweb="popover"] [data-baseweb="menu"] {{
        border-radius: {BORDER_RADIUS.lg};
        box-shadow: {SHADOWS.lg};
        border: 1px solid {COLORS.gray_200};
    }}

    [data-baseweb="menu"] li {{
        padding: {SPACING.sm} {SPACING.md};
        transition: background-color 0.15s ease;
    }}

    [data-baseweb="menu"] li:hover {{
        background: {COLORS.gray_50};
    }}

    [data-baseweb="menu"] li[aria-selected="true"] {{
        background: {COLORS.primary_light};
        color: {COLORS.primary};
    }}

    /* Multiselect */
    .stMultiSelect [data-baseweb="select"] > div {{
        border-radius: {BORDER_RADIUS.lg};
        border: 1px solid {COLORS.gray_300};
    }}

    .stMultiSelect [data-baseweb="tag"] {{
        background: {COLORS.primary_light};
        border-radius: {BORDER_RADIUS.md};
    }}

    /* === T048: Slider Styling (Indigo Accent) === */
    /* Slider track */
    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {{
        background: {COLORS.gray_200};
    }}

    .stSlider > div > div > div {{
        background: {COLORS.gray_200};
        height: 6px;
        border-radius: {BORDER_RADIUS.full};
    }}

    /* Active portion (indigo accent) */
    .stSlider > div > div > div > div {{
        background: {COLORS.primary};
        height: 6px;
        border-radius: {BORDER_RADIUS.full};
    }}

    /* Slider thumb/handle */
    .stSlider > div > div > div > div > div {{
        background: {COLORS.primary};
        border: 3px solid {COLORS.white};
        box-shadow: {SHADOWS.md};
        width: 20px;
        height: 20px;
        border-radius: {BORDER_RADIUS.full};
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}

    .stSlider > div > div > div > div > div:hover {{
        transform: scale(1.1);
        box-shadow: {SHADOWS.lg};
    }}

    /* Slider value label */
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {{
        color: {COLORS.gray_500};
        font-size: 0.875rem;
    }}

    /* === T052: File Uploader Styling === */
    .stFileUploader {{
        margin-bottom: {SPACING.md};
    }}

    .stFileUploader > div {{
        border: 2px dashed {COLORS.gray_300};
        border-radius: {BORDER_RADIUS.xl};
        padding: {SPACING.xxl};
        background: {COLORS.gray_50};
        transition: all 0.2s ease;
        text-align: center;
    }}

    .stFileUploader > div:hover {{
        border-color: {COLORS.primary};
        background: {COLORS.primary_light};
    }}

    .stFileUploader > div.dragover {{
        border-color: {COLORS.primary};
        background: {COLORS.primary_light};
        border-style: solid;
    }}

    /* File uploader button */
    .stFileUploader button {{
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_300};
        color: {COLORS.gray_700};
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.sm} {SPACING.lg};
        font-weight: {TYPOGRAPHY.weight_medium};
        transition: all 0.2s ease;
    }}

    .stFileUploader button:hover {{
        background: {COLORS.gray_50};
        border-color: {COLORS.primary};
        color: {COLORS.primary};
    }}

    /* Uploaded file display */
    .stFileUploader [data-testid="stFileUploaderFile"] {{
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.sm} {SPACING.md};
        margin-top: {SPACING.sm};
    }}

    /* === Checkbox and Radio Styling === */
    .stCheckbox label,
    .stRadio label {{
        font-weight: {TYPOGRAPHY.weight_medium};
        color: {COLORS.gray_700};
    }}

    .stCheckbox input:checked + span::before {{
        background: {COLORS.primary};
    }}

    .stRadio div[role="radiogroup"] label {{
        padding: {SPACING.xs} {SPACING.sm};
        border-radius: {BORDER_RADIUS.md};
        transition: background-color 0.15s ease;
    }}

    .stRadio div[role="radiogroup"] label:hover {{
        background: {COLORS.gray_50};
    }}

    /* === Date and Time Input === */
    .stDateInput input,
    .stTimeInput input {{
        border-radius: {BORDER_RADIUS.lg};
        border: 1px solid {COLORS.gray_300};
        padding: {SPACING.sm} {SPACING.md};
    }}

    .stDateInput input:focus,
    .stTimeInput input:focus {{
        border-color: {COLORS.primary};
        box-shadow: 0 0 0 3px {COLORS.primary_light};
        outline: none;
    }}
    """


def get_table_css() -> str:
    """Generate CSS for table styling."""
    return f"""
    /* DataFrames and tables */
    .stDataFrame {{
        border-radius: {BORDER_RADIUS.lg};
        overflow: hidden;
    }}

    .stDataFrame thead tr th {{
        background: {COLORS.gray_50};
        font-weight: {TYPOGRAPHY.weight_semibold};
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: {TYPOGRAPHY.tracking_widest};
        color: {COLORS.gray_500};
        padding: {SPACING.md} {SPACING.lg};
        border-bottom: 1px solid {COLORS.gray_200};
    }}

    .stDataFrame tbody tr td {{
        padding: {SPACING.sm} {SPACING.lg};
        border-bottom: 1px solid {COLORS.gray_100};
        color: {COLORS.gray_700};
    }}

    .stDataFrame tbody tr:hover {{
        background: {COLORS.gray_50};
    }}

    /* Metric styling */
    [data-testid="stMetric"] {{
        background: {COLORS.white};
        border: 1px solid {COLORS.gray_200};
        border-radius: {BORDER_RADIUS.lg};
        padding: {SPACING.md};
    }}

    [data-testid="stMetric"] label {{
        font-size: 0.875rem;
        color: {COLORS.gray_500};
        text-transform: uppercase;
        letter-spacing: {TYPOGRAPHY.tracking_wide};
    }}

    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-weight: {TYPOGRAPHY.weight_bold};
        color: {COLORS.gray_900};
    }}
    """


def get_status_css() -> str:
    """Generate CSS for status indicators and badges."""
    return f"""
    /* Status badges */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: {SPACING.xs};
        padding: {SPACING.xs} {SPACING.md};
        border-radius: {BORDER_RADIUS.full};
        font-weight: {TYPOGRAPHY.weight_semibold};
        font-size: 0.875rem;
    }}

    .status-badge.status-pass {{
        background: {COLORS.success_light};
        color: {COLORS.success_text};
    }}

    .status-badge.status-risk {{
        background: {COLORS.warning_light};
        color: {COLORS.warning_text};
    }}

    .status-badge.status-fail {{
        background: {COLORS.error_light};
        color: {COLORS.error_text};
    }}

    .status-badge.status-error {{
        background: {COLORS.gray_100};
        color: {COLORS.gray_600};
    }}

    /* Large status indicator */
    .status-large {{
        display: flex;
        align-items: center;
        gap: {SPACING.md};
        padding: {SPACING.lg} {SPACING.xl};
        border-radius: {BORDER_RADIUS.xl};
        font-size: 1.25rem;
        font-weight: {TYPOGRAPHY.weight_bold};
    }}

    .status-large.status-pass {{
        background: {COLORS.success_light};
        color: {COLORS.success};
        border: 1px solid {COLORS.success};
    }}

    .status-large.status-risk {{
        background: {COLORS.warning_light};
        color: {COLORS.warning_text};
        border: 1px solid {COLORS.warning};
    }}

    .status-large.status-fail {{
        background: {COLORS.error_light};
        color: {COLORS.error};
        border: 1px solid {COLORS.error};
    }}

    .status-icon {{
        font-size: 1.5rem;
    }}
    """


def get_alert_css() -> str:
    """Generate CSS for Streamlit alert overrides."""
    return f"""
    /* Success alert */
    .stAlert [data-baseweb="notification"] {{
        border-radius: {BORDER_RADIUS.lg};
    }}

    /* Info alert */
    .stAlert > div[data-baseweb="notification"][class*="info"] {{
        background: {COLORS.primary_light};
        border-left: 4px solid {COLORS.primary};
    }}

    /* Warning alert */
    .stAlert > div[data-baseweb="notification"][class*="warning"] {{
        background: {COLORS.warning_light};
        border-left: 4px solid {COLORS.warning};
    }}

    /* Error alert */
    .stAlert > div[data-baseweb="notification"][class*="error"] {{
        background: {COLORS.error_light};
        border-left: 4px solid {COLORS.error};
    }}

    /* Success alert */
    .stAlert > div[data-baseweb="notification"][class*="success"] {{
        background: {COLORS.success_light};
        border-left: 4px solid {COLORS.success};
    }}
    """


def get_all_css() -> str:
    """Combine all CSS sections into a single stylesheet."""
    return "\n".join([
        "/* === ACP Theme Styles === */",
        get_base_css(),
        get_card_css(),
        get_navigation_css(),
        get_button_css(),
        get_form_css(),
        get_table_css(),
        get_status_css(),
        get_alert_css(),
    ])
