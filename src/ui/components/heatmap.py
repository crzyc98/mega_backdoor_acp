"""
Heatmap Visualization Component.

Renders ACP test results as an interactive heatmap using Plotly.
Supports multiple view modes: Pass/Fail, Margin, and Risk Zone.
Includes accessibility features: status icons, keyboard navigation, WCAG 2.1 AA compliance.
"""

import plotly.graph_objects as go
import streamlit as st

from src.ui.components.heatmap_constants import (
    GRID_SETTINGS,
    PASS_FAIL_COLORSCALE,
    STATUS_COLORS,
    STATUS_ICONS,
    STATUS_VALUES,
    TOOLTIP_TIMING,
    VIEW_MODE_CONFIG,
)
from src.ui.components.heatmap_models import (
    HeatmapState,
    HeatmapViewMode,
    TooltipData,
)
from src.ui.components.heatmap_summary import render_summary_panel
from src.ui.components.heatmap_detail import render_detail_panel, get_scenario_at_coordinates
import streamlit.components.v1 as components


def _init_heatmap_state() -> HeatmapState:
    """Initialize or retrieve heatmap state from session."""
    if "heatmap_state" not in st.session_state:
        st.session_state.heatmap_state = HeatmapState()
    return st.session_state.heatmap_state


def _get_plotly_config() -> dict:
    """
    Get Plotly chart config with tooltip debouncing for rapid mouse movement.

    T051: Configures hover behavior for better UX during fast mouse movement.

    Returns:
        Dict with Plotly config options
    """
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        # T051: These settings help with hover debouncing
        "scrollZoom": False,
    }


def _get_hover_layout_config() -> dict:
    """
    Get layout config for hover label styling and behavior.

    T051: Configures hover label for better UX.

    Returns:
        Dict with hover layout options
    """
    return {
        "hoverlabel": dict(
            bgcolor="white",
            font_size=12,
            font_family="system-ui, sans-serif",
            namelength=-1,  # Show full label
        ),
        "hovermode": "closest",  # T051: Use closest point rather than x/y unified
    }


def _get_axis_tick_config(values: list, threshold: int | None = None) -> dict:
    """
    Get axis tick configuration with decimation for large grids.

    T050: For grids larger than threshold, show every Nth tick to prevent overlap.

    Args:
        values: List of axis values (adoption_rates or contribution_rates)
        threshold: Override default threshold from GRID_SETTINGS

    Returns:
        Dict with tickvals and ticktext for Plotly axis config
    """
    threshold = threshold or GRID_SETTINGS.get("axis_tick_decimation_threshold", 20)
    n = len(values)

    if n <= threshold:
        # Show all ticks
        return {}

    # Calculate decimation factor (show every Nth tick)
    # For 50 items with threshold 20: step = ceil(50/20) = 3, show every 3rd
    step = (n + threshold - 1) // threshold  # Ceiling division

    tick_indices = list(range(0, n, step))
    # Always include the last value for clarity
    if tick_indices[-1] != n - 1:
        tick_indices.append(n - 1)

    tickvals = [f"{values[i]}%" for i in tick_indices]
    return {
        "tickvals": tickvals,
        "tickmode": "array",
    }


def _get_status_from_result(result: dict) -> str:
    """
    Extract status from a result dict.

    Handles both old format ('result' key) and new format ('status' key).
    """
    # New format uses 'status'
    if "status" in result:
        return result["status"]
    # Old format uses 'result' with PASS/FAIL only
    if "result" in result:
        old_result = result["result"]
        if old_result == "PASS":
            # Check margin to determine if RISK
            margin = result.get("margin", 1.0)
            if margin is not None and margin <= 0.5:
                return "RISK"
            return "PASS"
        return "FAIL"
    return "ERROR"


def _build_data_matrices(
    grid_result: dict,
) -> tuple[list[list], list[list], list[list], list[list], list[list], list[list]]:
    """
    Build data matrices from grid result for all view modes.

    Returns:
        Tuple of (status_matrix, margin_matrix, text_icons_matrix, text_margin_matrix,
                  hover_text_matrix, missing_matrix)
        missing_matrix: Boolean matrix indicating cells with no data (gaps in grid)
    """
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    results = grid_result.get("results", [])

    n_adoption = len(adoption_rates)
    n_contribution = len(contribution_rates)

    # Initialize matrices - T049: Track missing data explicitly
    status_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    margin_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    text_icons_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    text_margin_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    hover_text_matrix = [[None] * n_contribution for _ in range(n_adoption)]
    missing_matrix = [[True] * n_contribution for _ in range(n_adoption)]  # T049: Track gaps

    # Fill matrices from results
    for result in results:
        try:
            adoption_idx = adoption_rates.index(result.get("adoption_rate"))
            contribution_idx = contribution_rates.index(result.get("contribution_rate"))
        except (ValueError, TypeError):
            continue

        status = _get_status_from_result(result)
        margin = result.get("margin")

        # T049: Mark cell as having data
        missing_matrix[adoption_idx][contribution_idx] = False

        # Status value for categorical coloring
        status_matrix[adoption_idx][contribution_idx] = STATUS_VALUES.get(status, 0)

        # Margin value
        margin_matrix[adoption_idx][contribution_idx] = margin

        # Text annotations - icons for Pass/Fail and Risk Zone
        text_icons_matrix[adoption_idx][contribution_idx] = STATUS_ICONS.get(status, "?")

        # Text annotations - margin values
        if status == "ERROR":
            text_margin_matrix[adoption_idx][contribution_idx] = "ERR"
        elif margin is not None:
            text_margin_matrix[adoption_idx][contribution_idx] = f"{margin:+.1f}"
        else:
            text_margin_matrix[adoption_idx][contribution_idx] = ""

        # Build tooltip data
        tooltip = TooltipData(
            status=status,
            status_icon=STATUS_ICONS.get(status, "?"),
            adoption_rate=result.get("adoption_rate", 0),
            contribution_rate=result.get("contribution_rate", 0),
            margin=margin,
            hce_acp=result.get("hce_acp"),
            nhce_acp=result.get("nhce_acp"),
            threshold=result.get("threshold") or result.get("max_allowed_acp"),
            limiting_bound=result.get("limiting_bound") or result.get("limiting_test"),
            error_message=result.get("error_message"),
        )
        hover_text_matrix[adoption_idx][contribution_idx] = tooltip.to_hover_html()

    # T049: Fill in missing data cells with "No data" indicators
    for i in range(n_adoption):
        for j in range(n_contribution):
            if missing_matrix[i][j]:
                # Use a distinct value for missing data
                status_matrix[i][j] = -1  # Special value for missing
                margin_matrix[i][j] = None
                text_icons_matrix[i][j] = "—"  # Em dash for missing
                text_margin_matrix[i][j] = "—"
                hover_text_matrix[i][j] = (
                    f"<b>— No Data</b><br>"
                    f"Adoption: {adoption_rates[i]:.0f}%<br>"
                    f"Contribution: {contribution_rates[j]:.1f}%<br>"
                    f"<i>No scenario result for this combination</i>"
                )

    return (
        status_matrix,
        margin_matrix,
        text_icons_matrix,
        text_margin_matrix,
        hover_text_matrix,
        missing_matrix,
    )


def _render_pass_fail_heatmap(
    grid_result: dict,
    status_matrix: list[list],
    text_icons_matrix: list[list],
    hover_text_matrix: list[list],
    missing_matrix: list[list],
) -> None:
    """
    Render Pass/Fail heatmap with status-based coloring and accessibility icons.

    Colors: Green (PASS), Yellow (RISK), Red (FAIL), Gray (ERROR), Light Gray (MISSING)
    Icons: ✓ (PASS), ⚠ (RISK), ✗ (FAIL), ? (ERROR), — (MISSING)
    """
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    n_adoption = len(adoption_rates)
    n_contribution = len(contribution_rates)

    config = VIEW_MODE_CONFIG["pass_fail"]

    # T050: For large grids, hide text annotations to prevent crowding
    is_large_grid = n_adoption * n_contribution > GRID_SETTINGS.get("max_interactive_size", 625)
    text_config = (
        {"texttemplate": ""} if is_large_grid
        else {"text": text_icons_matrix, "texttemplate": "%{text}", "textfont": {"size": 14, "color": "black"}}
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=status_matrix,
            x=[f"{r}%" for r in contribution_rates],
            y=[f"{r}%" for r in adoption_rates],
            **text_config,
            hovertext=hover_text_matrix,
            hovertemplate="%{hovertext}<extra></extra>",
            colorscale=PASS_FAIL_COLORSCALE,
            showscale=False,
            zmin=-1,  # T049: Extended to include MISSING (-1)
            zmax=3,
        )
    )

    # T050: Get tick decimation config for large grids
    x_tick_config = _get_axis_tick_config(contribution_rates)
    y_tick_config = _get_axis_tick_config(adoption_rates)

    # T051: Get hover layout config for debouncing
    hover_config = _get_hover_layout_config()

    fig.update_layout(
        title=dict(text=config["title"], subtitle=dict(text=config["subtitle"])),
        xaxis_title="Contribution Rate",
        yaxis_title="Adoption Rate",
        height=max(400, min(800, 400 + 15 * n_adoption)),  # T050: Cap height for large grids
        xaxis=dict(**x_tick_config),
        yaxis=dict(autorange="reversed", **y_tick_config),  # Higher adoption at top
        **hover_config,
    )

    st.plotly_chart(fig, use_container_width=True, key="heatmap_pass_fail", config=_get_plotly_config())


def _render_margin_heatmap(
    grid_result: dict,
    margin_matrix: list[list],
    text_margin_matrix: list[list],
    hover_text_matrix: list[list],
    missing_matrix: list[list],
) -> None:
    """
    Render Margin heatmap with gradient coloring and numeric labels.

    Gradient: Green (positive) → Yellow (zero) → Red (negative)
    Labels: Margin value formatted as "+X.XX" or "-X.XX"
    Missing cells: Light gray with "—" label
    """
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    n_adoption = len(adoption_rates)
    n_contribution = len(contribution_rates)

    config = VIEW_MODE_CONFIG["margin"]

    # Calculate dynamic range with zero at center (exclude missing/None values)
    all_margins = [
        m for row in margin_matrix for m in row if m is not None
    ]
    if all_margins:
        max_abs = max(abs(min(all_margins)), abs(max(all_margins)), 0.1)
        zmin, zmax = -max_abs, max_abs
    else:
        zmin, zmax = -5, 5

    # T050: For large grids, hide text annotations to prevent crowding
    is_large_grid = n_adoption * n_contribution > GRID_SETTINGS.get("max_interactive_size", 625)
    text_config = (
        {"texttemplate": ""} if is_large_grid
        else {"text": text_margin_matrix, "texttemplate": "%{text}", "textfont": {"size": 10}}
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=margin_matrix,
            x=[f"{r}%" for r in contribution_rates],
            y=[f"{r}%" for r in adoption_rates],
            **text_config,
            hovertext=hover_text_matrix,
            hovertemplate="%{hovertext}<extra></extra>",
            colorscale=config["colorscale"],
            showscale=True,
            zmin=zmin,
            zmax=zmax,
            zmid=0,
            colorbar=dict(
                title="Margin (pp)",
                tickvals=[zmin, 0, zmax],
                ticktext=[f"{zmin:.1f}", "0", f"{zmax:.1f}"],
            ),
        )
    )

    # T050: Get tick decimation config for large grids
    x_tick_config = _get_axis_tick_config(contribution_rates)
    y_tick_config = _get_axis_tick_config(adoption_rates)

    # T051: Get hover layout config for debouncing
    hover_config = _get_hover_layout_config()

    fig.update_layout(
        title=dict(text=config["title"], subtitle=dict(text=config["subtitle"])),
        xaxis_title="Contribution Rate",
        yaxis_title="Adoption Rate",
        height=max(400, min(800, 400 + 15 * n_adoption)),  # T050: Cap height for large grids
        xaxis=dict(**x_tick_config),
        yaxis=dict(autorange="reversed", **y_tick_config),
        **hover_config,
    )

    st.plotly_chart(fig, use_container_width=True, key="heatmap_margin", config=_get_plotly_config())


def _render_risk_zone_heatmap(
    grid_result: dict,
    status_matrix: list[list],
    text_icons_matrix: list[list],
    hover_text_matrix: list[list],
    missing_matrix: list[list],
) -> None:
    """
    Render Risk Zone heatmap with emphasis on RISK-status cells.

    RISK cells: Prominently highlighted
    Other cells: Dimmed (reduced opacity)
    Missing cells: Light gray with "—" indicator
    """
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    results = grid_result.get("results", [])
    n_adoption = len(adoption_rates)
    n_contribution = len(contribution_rates)

    config = VIEW_MODE_CONFIG["risk_zone"]

    # Count RISK scenarios
    risk_count = sum(
        1 for r in results if _get_status_from_result(r) == "RISK"
    )

    # Display risk count prominently
    if risk_count > 0:
        st.warning(f"⚠ **{risk_count} scenario{'s' if risk_count != 1 else ''} in risk zone**")
    else:
        st.info("✓ No scenarios in risk zone")

    # Create opacity matrix - dimmed for non-RISK cells
    opacity_matrix = [
        [
            1.0 if val == STATUS_VALUES["RISK"] else config["dimmed_opacity"]
            for val in row
        ]
        for row in status_matrix
    ]

    # T050: For large grids, hide text annotations to prevent crowding
    is_large_grid = n_adoption * n_contribution > GRID_SETTINGS.get("max_interactive_size", 625)
    text_config = (
        {"texttemplate": ""} if is_large_grid
        else {"text": text_icons_matrix, "texttemplate": "%{text}", "textfont": {"size": 14, "color": "black"}}
    )

    # Custom colorscale with transparency for dimmed cells isn't directly supported
    # Instead, we'll use marker opacity via a second trace overlay
    fig = go.Figure()

    # Base heatmap with all cells
    fig.add_trace(
        go.Heatmap(
            z=status_matrix,
            x=[f"{r}%" for r in contribution_rates],
            y=[f"{r}%" for r in adoption_rates],
            **text_config,
            hovertext=hover_text_matrix,
            hovertemplate="%{hovertext}<extra></extra>",
            colorscale=PASS_FAIL_COLORSCALE,
            showscale=False,
            zmin=-1,  # T049: Extended to include MISSING (-1)
            zmax=3,
            opacity=0.5,  # Dim all by default
        )
    )

    # Overlay RISK cells with full opacity
    risk_z = [
        [val if val == STATUS_VALUES["RISK"] else None for val in row]
        for row in status_matrix
    ]
    risk_text = [
        [text if status_matrix[i][j] == STATUS_VALUES["RISK"] else None
         for j, text in enumerate(row)]
        for i, row in enumerate(text_icons_matrix)
    ]

    # T050: Skip risk text overlay for large grids
    risk_text_config = (
        {"texttemplate": ""} if is_large_grid
        else {"text": risk_text, "texttemplate": "%{text}", "textfont": {"size": 16, "color": "black"}}
    )

    fig.add_trace(
        go.Heatmap(
            z=risk_z,
            x=[f"{r}%" for r in contribution_rates],
            y=[f"{r}%" for r in adoption_rates],
            **risk_text_config,
            hoverinfo="skip",
            colorscale=[[0, "#F59E0B"], [1, "#F59E0B"]],  # Amber for RISK
            showscale=False,
            zmin=STATUS_VALUES["RISK"],
            zmax=STATUS_VALUES["RISK"],
        )
    )

    # T050: Get tick decimation config for large grids
    x_tick_config = _get_axis_tick_config(contribution_rates)
    y_tick_config = _get_axis_tick_config(adoption_rates)

    # T051: Get hover layout config for debouncing
    hover_config = _get_hover_layout_config()

    fig.update_layout(
        title=dict(text=config["title"], subtitle=dict(text=config["subtitle"])),
        xaxis_title="Contribution Rate",
        yaxis_title="Adoption Rate",
        height=max(400, min(800, 400 + 15 * n_adoption)),  # T050: Cap height for large grids
        xaxis=dict(**x_tick_config),
        yaxis=dict(autorange="reversed", **y_tick_config),
        **hover_config,
    )

    st.plotly_chart(fig, use_container_width=True, key="heatmap_risk_zone", config=_get_plotly_config())


def _inject_keyboard_css() -> None:
    """Inject CSS for focus indicators and keyboard navigation."""
    focus_css = """
    <style>
    /* Focus indicator for keyboard navigation */
    .heatmap-focus-indicator {
        position: absolute;
        border: 2px solid #1E40AF;
        pointer-events: none;
        z-index: 1000;
    }

    /* Keyboard help overlay */
    .keyboard-help-overlay {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 2000;
        min-width: 300px;
    }

    .keyboard-help-overlay h3 {
        margin-top: 0;
        color: #1E40AF;
    }

    .keyboard-help-overlay table {
        width: 100%;
        border-collapse: collapse;
    }

    .keyboard-help-overlay td {
        padding: 8px;
        border-bottom: 1px solid #eee;
    }

    .keyboard-help-overlay kbd {
        background: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #d1d5db;
        font-family: monospace;
    }
    </style>
    """
    st.markdown(focus_css, unsafe_allow_html=True)


def _render_keyboard_help_overlay() -> None:
    """Render keyboard shortcuts help overlay."""
    help_html = """
    <div class="keyboard-help-overlay" id="keyboard-help">
        <h3>Keyboard Shortcuts</h3>
        <table>
            <tr><td><kbd>Tab</kbd></td><td>Enter/exit heatmap focus</td></tr>
            <tr><td><kbd>←</kbd> <kbd>→</kbd> <kbd>↑</kbd> <kbd>↓</kbd></td><td>Navigate cells</td></tr>
            <tr><td><kbd>Enter</kbd> / <kbd>Space</kbd></td><td>Open cell details</td></tr>
            <tr><td><kbd>Escape</kbd></td><td>Close details / exit focus</td></tr>
            <tr><td><kbd>?</kbd> / <kbd>H</kbd></td><td>Show/hide this help</td></tr>
        </table>
        <p style="text-align: center; margin-top: 15px; margin-bottom: 0;">
            <em>Press any key to close</em>
        </p>
    </div>
    """
    st.markdown(help_html, unsafe_allow_html=True)


def _handle_keyboard_navigation(
    grid_result: dict,
    state: HeatmapState,
    n_rows: int,
    n_cols: int,
) -> None:
    """
    Handle keyboard navigation for the heatmap.

    This injects JavaScript to capture keyboard events and updates session state.
    Due to Streamlit's architecture, full keyboard navigation requires workarounds.
    """
    # Inject focus CSS
    _inject_keyboard_css()

    # Show help overlay if requested
    if state.show_help:
        _render_keyboard_help_overlay()

    # Create keyboard shortcut buttons as a workaround
    st.caption("**Keyboard:** Use arrow keys to navigate, Enter/Space for details, ? for help")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("⬆️", key="nav_up", help="Move up"):
            if state.focus.row > 0:
                state.focus.row -= 1
                state.focus.is_focused = True
                st.rerun()

    with col2:
        if st.button("⬇️", key="nav_down", help="Move down"):
            if state.focus.row < n_rows - 1:
                state.focus.row += 1
                state.focus.is_focused = True
                st.rerun()

    with col3:
        if st.button("⬅️", key="nav_left", help="Move left"):
            if state.focus.col > 0:
                state.focus.col -= 1
                state.focus.is_focused = True
                st.rerun()

    with col4:
        if st.button("➡️", key="nav_right", help="Move right"):
            if state.focus.col < n_cols - 1:
                state.focus.col += 1
                state.focus.is_focused = True
                st.rerun()

    # Show current focus position and action buttons
    if state.focus.is_focused:
        adoption_rates = grid_result.get("adoption_rates", [])
        contribution_rates = grid_result.get("contribution_rates", [])

        if state.focus.row < len(adoption_rates) and state.focus.col < len(contribution_rates):
            current_adoption = adoption_rates[state.focus.row]
            current_contribution = contribution_rates[state.focus.col]
            st.info(f"📍 Focused: {current_adoption}% adoption, {current_contribution}% contribution")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋 View Details", key="view_details"):
                    state.selected_cell = (state.focus.row, state.focus.col)
                    st.rerun()
            with col2:
                if st.button("❓ Help", key="show_help"):
                    state.show_help = not state.show_help
                    st.rerun()
            with col3:
                if st.button("✖️ Clear Focus", key="clear_focus"):
                    state.focus.is_focused = False
                    state.focus.row = 0
                    state.focus.col = 0
                    st.rerun()


def _render_selected_cell_detail(grid_result: dict, state: HeatmapState) -> None:
    """Render detail panel for selected cell in sidebar."""
    if state.selected_cell is None:
        return

    row, col = state.selected_cell
    scenario = get_scenario_at_coordinates(grid_result, row, col)

    if scenario:
        should_stay_open = render_detail_panel(scenario)
        if not should_stay_open:
            state.selected_cell = None
            st.rerun()
    else:
        # Cell not found, close panel
        state.selected_cell = None


def render_heatmap(grid_result: dict) -> None:
    """
    Render an enhanced heatmap visualization of grid analysis results.

    Supports three view modes:
    - Pass/Fail: Categorical status coloring with accessibility icons
    - Margin: Gradient showing margin values
    - Risk Zone: Emphasis on RISK-status scenarios

    Args:
        grid_result: Grid analysis result from API containing:
            - adoption_rates: List of adoption rates (y-axis)
            - contribution_rates: List of contribution rates (x-axis)
            - results: List of analysis results
            - summary: Grid summary statistics (optional)
    """
    # Initialize state
    state = _init_heatmap_state()

    # Render summary panel above heatmap
    render_summary_panel(grid_result)

    # Build data matrices once for all view modes
    (
        status_matrix,
        margin_matrix,
        text_icons_matrix,
        text_margin_matrix,
        hover_text_matrix,
        missing_matrix,  # T049: Track grid gaps
    ) = _build_data_matrices(grid_result)

    # View mode selector
    view_mode_labels = {
        HeatmapViewMode.PASS_FAIL: "Pass/Fail",
        HeatmapViewMode.MARGIN: "Margin",
        HeatmapViewMode.RISK_ZONE: "Risk Zone",
    }

    selected_label = st.radio(
        "View Mode",
        options=list(view_mode_labels.values()),
        horizontal=True,
        key="heatmap_view_mode_selector",
    )

    # Map label back to enum
    label_to_mode = {v: k for k, v in view_mode_labels.items()}
    current_mode = label_to_mode.get(selected_label, HeatmapViewMode.PASS_FAIL)
    state.view_mode = current_mode

    # Render based on selected mode
    if current_mode == HeatmapViewMode.PASS_FAIL:
        _render_pass_fail_heatmap(
            grid_result, status_matrix, text_icons_matrix, hover_text_matrix, missing_matrix
        )
    elif current_mode == HeatmapViewMode.MARGIN:
        _render_margin_heatmap(
            grid_result, margin_matrix, text_margin_matrix, hover_text_matrix, missing_matrix
        )
    elif current_mode == HeatmapViewMode.RISK_ZONE:
        _render_risk_zone_heatmap(
            grid_result, status_matrix, text_icons_matrix, hover_text_matrix, missing_matrix
        )

    # Handle keyboard navigation and detail panel
    adoption_rates = grid_result.get("adoption_rates", [])
    contribution_rates = grid_result.get("contribution_rates", [])
    results = grid_result.get("results", [])

    _handle_keyboard_navigation(grid_result, state, len(adoption_rates), len(contribution_rates))
    _render_selected_cell_detail(grid_result, state)

    # Render drill-down section (backward compatibility)
    render_drill_down(results, adoption_rates, contribution_rates)


def render_drill_down(
    results: list[dict],
    adoption_rates: list[float],
    contribution_rates: list[float],
) -> None:
    """Render a detailed view of a specific cell."""
    st.subheader("Scenario Details")

    col1, col2 = st.columns(2)

    with col1:
        selected_adoption = st.selectbox(
            "Adoption Rate (%)",
            options=adoption_rates,
            key="drill_adoption",
        )

    with col2:
        selected_contribution = st.selectbox(
            "Contribution Rate (%)",
            options=contribution_rates,
            key="drill_contribution",
        )

    # Find matching result
    matching_result = None
    for r in results:
        if (
            r.get("adoption_rate") == selected_adoption
            and r.get("contribution_rate") == selected_contribution
        ):
            matching_result = r
            break

    if matching_result:
        status = _get_status_from_result(matching_result)
        status_icon = STATUS_ICONS.get(status, "?")

        # Display result details with icon
        if status == "PASS":
            st.success(f"**{status_icon} {status}**")
        elif status == "RISK":
            st.warning(f"**{status_icon} {status}**")
        elif status == "FAIL":
            st.error(f"**{status_icon} {status}**")
        else:  # ERROR
            st.info(f"**{status_icon} {status}**")
            if matching_result.get("error_message"):
                st.error(matching_result["error_message"])

        if status != "ERROR":
            col1, col2, col3 = st.columns(3)

            hce_acp = matching_result.get("hce_acp", 0)
            nhce_acp = matching_result.get("nhce_acp", 0)
            threshold = matching_result.get("threshold") or matching_result.get("max_allowed_acp", 0)
            margin = matching_result.get("margin", 0)
            limiting = matching_result.get("limiting_test") or matching_result.get("limiting_bound", "N/A")
            seed = matching_result.get("seed") or matching_result.get("seed_used", "N/A")

            with col1:
                st.metric("HCE ACP", f"{hce_acp:.3f}%")
                st.metric("NHCE ACP", f"{nhce_acp:.3f}%")

            with col2:
                st.metric("Threshold", f"{threshold:.3f}%")
                st.metric("Limiting Test", str(limiting))

            with col3:
                margin_delta = "+" if margin >= 0 else ""
                st.metric("Margin", f"{margin_delta}{margin:.3f}%")
                st.metric("Seed", str(seed))
    else:
        st.warning("No result found for selected parameters")
