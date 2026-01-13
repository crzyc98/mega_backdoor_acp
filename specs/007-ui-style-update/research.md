# Research: UI Style Update

**Feature**: 007-ui-style-update
**Date**: 2026-01-13

## Research Areas

This document consolidates research findings for styling a Streamlit application with custom CSS to match the design patterns from the `ui-example/` React reference.

---

## 1. Streamlit CSS Injection Methods

### Decision: Use `st.markdown()` with `unsafe_allow_html=True` for global CSS

### Rationale
Streamlit provides limited native styling options but allows raw HTML/CSS injection via `st.markdown()`. This is the standard approach for custom styling without external packages.

### Alternatives Considered
| Alternative | Evaluation |
|-------------|------------|
| `streamlit-extras` package | Adds external dependency; limited customization |
| Custom Streamlit components | Overkill for CSS-only changes; requires npm/React tooling |
| `.streamlit/config.toml` theme | Only supports primary/secondary colors, fonts; insufficient |
| External CSS file with `<link>` | Security restrictions in Streamlit prevent external file loading |

### Implementation Pattern
```python
def inject_css(css: str) -> None:
    """Inject custom CSS into Streamlit page."""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

---

## 2. Streamlit Selector Patterns for CSS Targeting

### Decision: Use Streamlit's internal CSS class patterns with appropriate specificity

### Rationale
Streamlit generates specific class names for components. Research shows consistent patterns across versions 1.28+.

### Key Selectors
| Component | Selector Pattern |
|-----------|-----------------|
| Main container | `.main .block-container` |
| Sidebar | `[data-testid="stSidebar"]` |
| Buttons (primary) | `.stButton > button[kind="primary"]` or `.stButton button` |
| Sliders | `.stSlider` |
| Selectbox | `.stSelectbox` |
| Text input | `.stTextInput` |
| Metrics | `[data-testid="stMetric"]` or `[data-testid="metric-container"]` |
| Dataframes | `.stDataFrame` |
| Tabs | `.stTabs [data-baseweb="tab-list"]` |
| Radio buttons | `.stRadio` |
| Expander | `.streamlit-expanderHeader` |
| Divider | `hr` |

### Alternatives Considered
| Alternative | Evaluation |
|-------------|------------|
| Using `!important` everywhere | Fragile, maintainability issues |
| Inline styles via st.markdown | Inconsistent, no reusability |

### Notes
- Streamlit may change internal class names between major versions
- Test selectors against current Streamlit version (1.28+)
- Use `data-testid` attributes where available (more stable)

---

## 3. Color Palette Definition

### Decision: Adopt Tailwind CSS color palette values from ui-example

### Rationale
The React reference uses Tailwind CSS colors. Using identical hex values ensures visual consistency with the design inspiration.

### Color Mapping
| Purpose | Tailwind Class | Hex Value |
|---------|---------------|-----------|
| Primary (Indigo 600) | `bg-indigo-600` | `#4F46E5` |
| Primary Hover (Indigo 700) | `bg-indigo-700` | `#4338CA` |
| Primary Light (Indigo 50) | `bg-indigo-50` | `#EEF2FF` |
| Primary Text (Indigo 800) | `text-indigo-800` | `#3730A3` |
| Success (Emerald 500) | `bg-emerald-500` | `#10B981` |
| Success Light (Emerald 50) | `bg-emerald-50` | `#ECFDF5` |
| Warning (Amber 400) | `bg-amber-400` | `#FBBF24` |
| Warning Light (Amber 50) | `bg-amber-50` | `#FFFBEB` |
| Error (Rose 500) | `bg-rose-500` | `#F43F5E` |
| Error Light (Rose 50) | `bg-rose-50` | `#FFF1F2` |
| Gray 50 | `bg-gray-50` | `#F9FAFB` |
| Gray 100 | `bg-gray-100` | `#F3F4F6` |
| Gray 200 | `bg-gray-200` | `#E5E7EB` |
| Gray 400 | `text-gray-400` | `#9CA3AF` |
| Gray 500 | `text-gray-500` | `#6B7280` |
| Gray 700 | `text-gray-700` | `#374151` |
| Gray 900 | `text-gray-900` | `#111827` |
| Slate 900 | `bg-slate-900` | `#0F172A` |

### Alternatives Considered
| Alternative | Evaluation |
|-------------|------------|
| Streamlit default theme colors | Doesn't match design reference |
| Material Design colors | Different aesthetic, not matching reference |
| Custom color palette | Unnecessary when reference uses standard Tailwind |

---

## 4. Typography System

### Decision: Use system font stack with Tailwind-inspired sizing

### Rationale
The React reference uses Tailwind's default typography. System fonts load instantly and match the reference aesthetic.

### Font Stack
```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Font Weights
| Purpose | Weight | Tailwind Class |
|---------|--------|----------------|
| Regular | 400 | `font-normal` |
| Medium | 500 | `font-medium` |
| Semibold | 600 | `font-semibold` |
| Bold | 700 | `font-bold` |
| Extra Bold | 800 | `font-extrabold` |
| Black | 900 | `font-black` |

### Letter Spacing (Tracking)
| Style | Value | Use Case |
|-------|-------|----------|
| Tight | `-0.025em` | Large headings |
| Normal | `0` | Body text |
| Wide | `0.025em` | Buttons |
| Wider | `0.05em` | Badges |
| Widest | `0.1em` | Table headers, labels |

---

## 5. Spacing and Border Radius

### Decision: Use Tailwind spacing scale for consistency

### Rationale
Matches the reference design system; provides predictable, harmonious spacing.

### Spacing Scale (in rem, base 16px)
| Name | Value | Pixels |
|------|-------|--------|
| 1 | 0.25rem | 4px |
| 2 | 0.5rem | 8px |
| 3 | 0.75rem | 12px |
| 4 | 1rem | 16px |
| 5 | 1.25rem | 20px |
| 6 | 1.5rem | 24px |
| 8 | 2rem | 32px |
| 10 | 2.5rem | 40px |
| 12 | 3rem | 48px |

### Border Radius
| Name | Value | Use Case |
|------|-------|----------|
| sm | 0.125rem (2px) | Small elements |
| DEFAULT | 0.25rem (4px) | Buttons, inputs |
| md | 0.375rem (6px) | - |
| lg | 0.5rem (8px) | Cards |
| xl | 0.75rem (12px) | Larger cards |
| 2xl | 1rem (16px) | Main containers |
| full | 9999px | Pills, avatars |

---

## 6. Shadow System

### Decision: Use subtle shadows matching Tailwind's shadow utilities

### Rationale
The reference uses `shadow-sm`, `shadow-md`, `shadow-lg` for depth hierarchy.

### Shadow Values
| Name | CSS Value |
|------|-----------|
| sm | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| DEFAULT | `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` |
| md | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` |
| lg | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` |
| xl | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` |

---

## 7. Plotly Theme Integration

### Decision: Configure Plotly chart templates to match theme colors

### Rationale
Plotly charts (heatmap) need consistent colors with the rest of the UI.

### Implementation Pattern
```python
import plotly.graph_objects as go
import plotly.io as pio

# Define custom template
pio.templates["acp_theme"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="system-ui, sans-serif"),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
)
pio.templates.default = "acp_theme"
```

### Heatmap Colorscale Updates
Current colorscale in `heatmap_constants.py` should be updated to use exact theme colors:
- PASS: `#10B981` (emerald-500)
- RISK: `#FBBF24` (amber-400)
- FAIL: `#F43F5E` (rose-500)
- ERROR: `#9CA3AF` (gray-400)

---

## 8. Streamlit Navigation Styling

### Decision: Replace sidebar radio with styled tab-like navigation

### Rationale
The reference uses horizontal tabs with numbered steps. Streamlit's native sidebar radio can be styled to appear as tabs.

### Implementation Approach
1. Keep sidebar for navigation (Streamlit constraint)
2. Style radio buttons to look like vertical step indicators
3. Add numbered prefixes to labels
4. Use CSS to style active/inactive states

### CSS Pattern
```css
/* Style sidebar radio as step navigation */
[data-testid="stSidebar"] .stRadio > div {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

[data-testid="stSidebar"] .stRadio label {
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s;
}

[data-testid="stSidebar"] .stRadio label:hover {
    background-color: #F3F4F6;
}

[data-testid="stSidebar"] .stRadio [data-checked="true"] label {
    background-color: #EEF2FF;
    color: #4F46E5;
    font-weight: 600;
}
```

---

## 9. Component HTML Patterns

### Decision: Use consistent HTML structure for custom components

### Rationale
Custom components (cards, badges, metrics) need predictable markup for CSS targeting.

### Card Component HTML
```html
<div class="acp-card">
    <div class="acp-card-header">Title</div>
    <div class="acp-card-body">Content</div>
</div>
```

### Status Badge HTML
```html
<span class="acp-status acp-status--pass">
    <span class="acp-status-icon">✓</span>
    <span class="acp-status-text">PASS</span>
</span>
```

### Metric Card HTML
```html
<div class="acp-metric">
    <span class="acp-metric-label">HCE ACP</span>
    <span class="acp-metric-value">4.52%</span>
</div>
```

---

## 10. Browser Compatibility

### Decision: Target modern browsers only (no IE11 support)

### Rationale
Streamlit itself requires modern browsers. CSS features like CSS variables, flexbox, and grid are safe to use.

### Safe CSS Features
- CSS Custom Properties (variables)
- Flexbox
- CSS Grid
- `backdrop-filter` (with fallback)
- Transitions and transforms
- System font stack

### Not Supported / Avoid
- IE11-specific hacks
- Vendor prefixes for features with >95% support

---

## Summary

All research items resolved. No NEEDS CLARIFICATION markers remain. Key findings:

1. **CSS Injection**: Use `st.markdown()` with `unsafe_allow_html=True`
2. **Selectors**: Use `data-testid` attributes where available for stability
3. **Colors**: Tailwind CSS palette (indigo/emerald/amber/rose/gray)
4. **Typography**: System font stack, weights 400-900, tracking for headers
5. **Spacing**: Tailwind spacing scale (4px base increments)
6. **Shadows**: Tailwind shadow utilities
7. **Plotly**: Custom template with theme colors
8. **Navigation**: Styled sidebar radio as step indicators
9. **Components**: Consistent CSS class naming (`.acp-*` prefix)
10. **Compatibility**: Modern browsers only
