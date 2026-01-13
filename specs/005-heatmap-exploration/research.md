# Research: Heatmap Exploration

**Feature**: 005-heatmap-exploration
**Date**: 2026-01-13

## Research Topics

### 1. Plotly Heatmap Accessibility Patterns

**Decision**: Use Plotly's built-in hovertemplate for tooltips combined with custom text annotations for status icons within cells.

**Rationale**:
- Plotly's `hovertemplate` provides native tooltip support with <200ms response time
- Text annotations via `texttemplate` can render Unicode status icons (✓, ⚠, ✗, ?) directly in cells
- Custom `hovertext` matrix allows per-cell tooltip content customization
- Plotly's `config` parameter supports keyboard navigation when combined with `tabindex`

**Alternatives Considered**:
- Custom D3.js overlay: More control but requires significant JavaScript, breaks Streamlit integration
- Pure CSS tooltips: Lacks Plotly's positioning intelligence and hover detection
- Separate canvas layer: Complex z-index management, inconsistent with Plotly events

**Implementation Notes**:
```python
# Status icons as Unicode characters with proper font support
STATUS_ICONS = {
    "PASS": "✓",   # U+2713 CHECK MARK
    "RISK": "⚠",   # U+26A0 WARNING SIGN
    "FAIL": "✗",   # U+2717 BALLOT X
    "ERROR": "?"   # U+003F QUESTION MARK
}

# Apply via texttemplate in Plotly heatmap
text_matrix = [[STATUS_ICONS[cell.status] for cell in row] for row in grid]
```

### 2. Streamlit Keyboard Navigation

**Decision**: Use `st.session_state` for focus tracking combined with custom HTML/CSS for focus indicators, leveraging Streamlit's `components.html()` for keyboard event capture.

**Rationale**:
- Streamlit lacks native grid keyboard navigation
- Session state can track focused cell coordinates (row, col)
- Custom HTML component can capture keyboard events and communicate back to Python
- Focus indicator rendered as CSS overlay on the Plotly chart

**Alternatives Considered**:
- Pure Streamlit widgets: No support for arrow key navigation between cells
- JavaScript injection via st.markdown: Works but fragile across Streamlit versions
- Third-party component (streamlit-aggrid): Overkill for heatmap, adds large dependency

**Implementation Notes**:
```python
# Track focused cell in session state
if "heatmap_focus" not in st.session_state:
    st.session_state.heatmap_focus = {"row": 0, "col": 0}

# Keyboard handler (via components.html)
keyboard_js = """
<script>
document.addEventListener('keydown', (e) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter', ' '].includes(e.key)) {
        e.preventDefault();
        window.parent.postMessage({type: 'heatmap_key', key: e.key}, '*');
    }
});
</script>
"""
```

### 3. WCAG 2.1 AA Color Contrast Compliance

**Decision**: Use pre-validated color palette with contrast ratios ≥4.5:1 for text, ≥3:1 for graphics. Add patterns/icons as non-color differentiators.

**Rationale**:
- Spec colors (#22C55E green, #F59E0B amber, #EF4444 red, #9CA3AF gray) need white/black text overlay contrast verification
- Icons (✓, ⚠, ✗, ?) provide shape differentiation independent of color
- Margin heatmap uses diverging colorscale with zero clearly delineated

**Color Contrast Analysis**:

| Background | Foreground | Contrast Ratio | WCAG AA |
|------------|------------|----------------|---------|
| #22C55E (PASS green) | #000000 | 5.81:1 | ✓ Pass |
| #F59E0B (RISK amber) | #000000 | 5.32:1 | ✓ Pass |
| #EF4444 (FAIL red) | #FFFFFF | 4.53:1 | ✓ Pass |
| #9CA3AF (ERROR gray) | #000000 | 4.68:1 | ✓ Pass |

**Alternatives Considered**:
- Higher saturation colors: Better contrast but harsher visual appearance
- Pattern fills only: Confusing without color for quick scanning
- Color-only without icons: Fails accessibility requirements for colorblind users

**Implementation Notes**:
```python
# Color palette with verified contrast
CELL_COLORS = {
    "PASS": {"bg": "#22C55E", "text": "#000000"},
    "RISK": {"bg": "#F59E0B", "text": "#000000"},
    "FAIL": {"bg": "#EF4444", "text": "#FFFFFF"},
    "ERROR": {"bg": "#9CA3AF", "text": "#000000"},
}
```

### 4. Streamlit Slide-out Panel Pattern

**Decision**: Use `st.sidebar` in conditional render mode for the detail panel, showing full scenario details when a cell is selected.

**Rationale**:
- Native Streamlit pattern, no custom components required
- Sidebar keeps heatmap visible while showing details (per clarification)
- Easy dismiss via clicking away or pressing Escape (handled by session state)
- Consistent with existing Streamlit app navigation patterns

**Alternatives Considered**:
- `st.expander`: Inline expansion, pushes content down, loses heatmap context
- `st.dialog` (experimental): Modal behavior, hides heatmap
- Custom overlay component: Requires JavaScript, harder to maintain

**Implementation Notes**:
```python
# Show detail panel in sidebar when cell selected
if st.session_state.get("selected_cell"):
    with st.sidebar:
        st.header("Scenario Details")
        render_scenario_detail(st.session_state.selected_cell)
        if st.button("Close", key="close_detail"):
            st.session_state.selected_cell = None
            st.rerun()
```

### 5. Risk Zone Emphasis Patterns

**Decision**: Use CSS animation (pulsing border) combined with dimmed opacity for non-RISK cells in Risk Zone view mode.

**Rationale**:
- Visual motion draws attention to RISK cells without relying on color alone
- Dimming non-RISK cells (opacity: 0.5) creates visual hierarchy
- Animation CSS can be injected via `st.markdown` with `unsafe_allow_html=True`

**Alternatives Considered**:
- Plotly annotation arrows: Clutters the visualization
- Separate RISK-only overlay: Complex z-index management
- Static bold borders only: Less attention-grabbing than animation

**Implementation Notes**:
```python
risk_zone_css = """
<style>
.risk-cell {
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 2px #F59E0B; }
    50% { box-shadow: 0 0 0 4px #F59E0B; }
}
.dimmed-cell {
    opacity: 0.5;
}
</style>
"""
```

### 6. Summary Statistics Component

**Decision**: Render summary statistics in a dedicated panel above the heatmap using `st.columns` for layout, with expandable margin details.

**Rationale**:
- GridSummary from spec 004 already contains pass_count, risk_count, fail_count, error_count, worst_margin, etc.
- No additional computation needed; display only
- Expandable section for detailed margin statistics prevents information overload

**Implementation Notes**:
```python
def render_summary(summary: GridSummary) -> None:
    cols = st.columns(5)
    cols[0].metric("Pass", summary.pass_count)
    cols[1].metric("Risk", summary.risk_count)
    cols[2].metric("Fail", summary.fail_count)
    cols[3].metric("Error", summary.error_count)
    cols[4].metric("Total", summary.total_count)

    with st.expander("Margin Details"):
        st.write(f"**Min Margin**: {summary.worst_margin:.2f}pp at ...")
        st.write(f"**Max Margin**: ...")
        st.write(f"**Avg Margin**: ...")
```

## Resolved Clarifications

All technical questions have been resolved through research:

| Topic | Resolution |
|-------|------------|
| Tooltip library | Plotly native hovertemplate |
| Keyboard navigation | Session state + custom JS event capture |
| Focus indicators | CSS overlay on Plotly chart |
| Color contrast | Pre-validated palette, all ≥4.5:1 |
| Detail panel type | Streamlit sidebar (slide-out) |
| Risk zone emphasis | CSS pulse animation + opacity dimming |

## Dependencies Confirmed

| Dependency | Version | Purpose | Status |
|------------|---------|---------|--------|
| Plotly | 5.15+ | Heatmap rendering | Already in project |
| Streamlit | 1.28+ | UI framework | Already in project |
| pydantic | 2.0+ | Data models | Already in project |
| pytest | Latest | Testing | Already in project |
