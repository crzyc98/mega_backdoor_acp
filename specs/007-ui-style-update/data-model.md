# Data Model: UI Style Update

**Feature**: 007-ui-style-update
**Date**: 2026-01-13

## Overview

This feature does not introduce new persistent data entities. The "data model" for this feature consists of theme configuration constants that define the visual styling system.

---

## Theme Configuration Entities

### 1. ColorPalette

Defines all color values used in the application styling.

| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `primary` | str | Primary brand color (indigo) | `#4F46E5` |
| `primary_hover` | str | Primary hover state | `#4338CA` |
| `primary_light` | str | Light primary background | `#EEF2FF` |
| `primary_text` | str | Text on primary backgrounds | `#3730A3` |
| `success` | str | Success/PASS status | `#10B981` |
| `success_light` | str | Light success background | `#ECFDF5` |
| `warning` | str | Warning/RISK status | `#FBBF24` |
| `warning_light` | str | Light warning background | `#FFFBEB` |
| `error` | str | Error/FAIL status | `#F43F5E` |
| `error_light` | str | Light error background | `#FFF1F2` |
| `gray_50` | str | Lightest gray | `#F9FAFB` |
| `gray_100` | str | Light gray | `#F3F4F6` |
| `gray_200` | str | Border gray | `#E5E7EB` |
| `gray_400` | str | Placeholder text | `#9CA3AF` |
| `gray_500` | str | Secondary text | `#6B7280` |
| `gray_700` | str | Body text | `#374151` |
| `gray_900` | str | Heading text | `#111827` |
| `slate_900` | str | Dark backgrounds | `#0F172A` |

### 2. StatusConfig

Maps analysis statuses to visual properties.

| Status | Color Field | Icon | Light Background |
|--------|-------------|------|------------------|
| `PASS` | `success` | `✓` | `success_light` |
| `RISK` | `warning` | `⚠` | `warning_light` |
| `FAIL` | `error` | `✗` | `error_light` |
| `ERROR` | `gray_400` | `?` | `gray_100` |

### 3. ConstraintStatusConfig

Maps constraint statuses to visual properties.

| Status | Color Field | Icon | Description |
|--------|-------------|------|-------------|
| `Unconstrained` | `success` | `✓` | Full contribution feasible |
| `Reduced` | `warning` | `↓` | Capped by section 415(c) |
| `At §415(c) Limit` | `error` | `!` | No remaining 415 room |
| `Not Selected` | `gray_400` | `—` | Not participating |

### 4. Typography

Defines font styling constants.

| Field | Type | Value |
|-------|------|-------|
| `font_family` | str | `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| `weight_normal` | int | 400 |
| `weight_medium` | int | 500 |
| `weight_semibold` | int | 600 |
| `weight_bold` | int | 700 |
| `weight_extrabold` | int | 800 |
| `weight_black` | int | 900 |
| `tracking_tight` | str | `-0.025em` |
| `tracking_wide` | str | `0.025em` |
| `tracking_wider` | str | `0.05em` |
| `tracking_widest` | str | `0.1em` |

### 5. Spacing

Defines spacing scale (in rem).

| Name | Value | Pixels |
|------|-------|--------|
| `xs` | `0.25rem` | 4px |
| `sm` | `0.5rem` | 8px |
| `md` | `0.75rem` | 12px |
| `base` | `1rem` | 16px |
| `lg` | `1.25rem` | 20px |
| `xl` | `1.5rem` | 24px |
| `2xl` | `2rem` | 32px |
| `3xl` | `2.5rem` | 40px |
| `4xl` | `3rem` | 48px |

### 6. BorderRadius

Defines border radius scale.

| Name | Value | Use Case |
|------|-------|----------|
| `sm` | `0.125rem` | Small elements |
| `default` | `0.25rem` | Buttons, inputs |
| `md` | `0.375rem` | - |
| `lg` | `0.5rem` | Cards |
| `xl` | `0.75rem` | Larger cards |
| `2xl` | `1rem` | Main containers |
| `full` | `9999px` | Pills, badges |

### 7. Shadow

Defines box shadow values.

| Name | CSS Value |
|------|-----------|
| `sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| `default` | `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` |
| `md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` |
| `lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` |
| `xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` |

---

## Entity Relationships

```text
ColorPalette ──────┬── StatusConfig (uses color fields)
                   ├── ConstraintStatusConfig (uses color fields)
                   └── CSS Generation (references all fields)

Typography ────────┬── CSS Generation (applies to selectors)
                   └── Component styling

Spacing ───────────┬── CSS Generation (padding, margin, gap)
                   └── Component layouts

BorderRadius ──────┬── Card components
                   └── Button/input styling

Shadow ────────────┬── Card components
                   └── Modal overlays
```

---

## Validation Rules

1. **ColorPalette**: All values must be valid CSS hex colors (`#RRGGBB` format)
2. **Typography weights**: Must be in range 100-900, multiples of 100
3. **Spacing/BorderRadius**: Must be valid CSS length values with units
4. **Shadow**: Must be valid CSS box-shadow values

---

## State Transitions

N/A - Theme configuration is static at runtime. No state changes.

---

## Data Volume Assumptions

- Single instance of each configuration entity
- Loaded once at application startup
- No persistence required (constants defined in code)
