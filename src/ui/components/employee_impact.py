"""
Employee Impact Table Component.

Renders the employee-level impact drill-down view with sortable,
filterable tables and constraint indicators.
"""

import io
from typing import Literal

import pandas as pd
import streamlit as st

from src.ui.theme.colors import COLORS


# Constraint status icons and colors for display - using theme colors
CONSTRAINT_ICONS = {
    "Unconstrained": "✓",
    "At §415(c) Limit": "!",
    "Reduced": "↓",
    "Not Selected": "—",
}

CONSTRAINT_COLORS = {
    "Unconstrained": COLORS.success,      # Emerald
    "At §415(c) Limit": COLORS.error,     # Rose
    "Reduced": COLORS.warning,            # Amber
    "Not Selected": COLORS.gray_400,      # Gray
}


def render_employee_impact_view(
    impact_data: dict,
    show_nhce: bool = True,
    default_sort: str = "individual_acp",
    default_ascending: bool = False,
) -> None:
    """
    Render the complete employee impact view.

    Args:
        impact_data: EmployeeImpactViewResponse dict from API
        show_nhce: Whether to include NHCE section
        default_sort: Default column to sort by
        default_ascending: Default sort direction
    """
    # Display scenario context header
    _render_scenario_context(impact_data)

    # Display summary panels side by side
    col1, col2 = st.columns(2)
    with col1:
        _render_summary_panel(impact_data["hce_summary"], "HCE")
    with col2:
        if show_nhce:
            _render_summary_panel(impact_data["nhce_summary"], "NHCE")

    st.divider()

    # Display constraint legend
    _render_constraint_legend()

    st.divider()

    # Tab navigation for HCE/NHCE tables
    if show_nhce:
        tab1, tab2 = st.tabs(["HCE Employees", "NHCE Employees"])

        with tab1:
            _render_employee_table(
                impact_data["hce_employees"],
                "HCE",
                default_sort,
                default_ascending,
            )

        with tab2:
            _render_employee_table(
                impact_data["nhce_employees"],
                "NHCE",
                default_sort,
                default_ascending,
            )
    else:
        _render_employee_table(
            impact_data["hce_employees"],
            "HCE",
            default_sort,
            default_ascending,
        )


def _render_scenario_context(impact_data: dict) -> None:
    """Render scenario context header."""
    st.subheader("Scenario Parameters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Adoption Rate",
            f"{impact_data['adoption_rate'] * 100:.0f}%",
        )

    with col2:
        st.metric(
            "Contribution Rate",
            f"{impact_data['contribution_rate'] * 100:.1f}%",
        )

    with col3:
        st.metric(
            "Plan Year",
            str(impact_data["plan_year"]),
        )

    with col4:
        st.metric(
            "§415(c) Limit",
            f"${impact_data['section_415c_limit']:,}",
        )

    st.caption(f"**Seed:** {impact_data['seed_used']}")


def _render_summary_panel(summary: dict, group: str) -> None:
    """Render summary panel for HCE or NHCE group."""
    st.subheader(f"{group} Summary")

    st.metric("Total Count", str(summary["total_count"]))

    if group == "HCE" and summary.get("at_limit_count") is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "At §415(c) Limit",
                str(summary["at_limit_count"]),
                help="Employees who cannot contribute due to §415(c) limit",
            )
        with col2:
            st.metric(
                "Reduced",
                str(summary.get("reduced_count", 0)),
                help="Employees receiving less than requested mega-backdoor",
            )

        if summary.get("total_mega_backdoor") is not None:
            st.metric(
                "Total Mega-Backdoor",
                f"${summary['total_mega_backdoor']:,.2f}",
            )

        if summary.get("average_available_room") is not None:
            st.metric(
                "Avg Available Room",
                f"${summary['average_available_room']:,.2f}",
            )

    st.metric(
        "Average ACP",
        f"{summary['average_individual_acp']:.2f}%",
    )

    st.metric(
        "Total Match",
        f"${summary['total_match']:,.2f}",
    )


def _render_constraint_legend() -> None:
    """Render constraint status legend."""
    st.caption("**Constraint Status Legend:**")

    cols = st.columns(4)
    for col, (status, icon) in zip(cols, CONSTRAINT_ICONS.items()):
        with col:
            color = CONSTRAINT_COLORS[status]
            st.markdown(
                f"<span style='color: {color};'>{icon}</span> {status}",
                unsafe_allow_html=True,
            )


def _render_employee_table(
    employees: list[dict],
    group: str,
    sort_by: str,
    ascending: bool,
) -> None:
    """
    Render sortable employee data table.

    Args:
        employees: List of EmployeeImpactResponse dicts
        group: "HCE" or "NHCE" for labeling
        sort_by: Column to sort by
        ascending: Sort direction
    """
    if not employees:
        st.info(f"No {group} employees in this census.")
        return

    # Sorting controls
    st.subheader(f"{group} Employee Details ({len(employees)} employees)")

    col1, col2 = st.columns([3, 1])

    sort_options = {
        "individual_acp": "Individual ACP",
        "compensation": "Compensation",
        "mega_backdoor_amount": "Mega-Backdoor Amount",
        "available_room": "Available Room",
        "constraint_status": "Constraint Status",
        "employee_id": "Employee ID",
    }

    with col1:
        selected_sort = st.selectbox(
            "Sort by",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=list(sort_options.keys()).index(sort_by) if sort_by in sort_options else 0,
            key=f"sort_{group}",
        )

    with col2:
        selected_direction = st.selectbox(
            "Order",
            options=["Descending", "Ascending"],
            index=0 if not ascending else 1,
            key=f"order_{group}",
        )

    ascending = selected_direction == "Ascending"

    # Filter controls
    filter_options = ["All"] + list(CONSTRAINT_ICONS.keys())
    if group == "HCE":
        selected_filter = st.selectbox(
            "Filter by Constraint Status",
            options=filter_options,
            key=f"filter_{group}",
        )
    else:
        selected_filter = "All"  # NHCE don't have constraint filtering

    # Convert to DataFrame
    df = pd.DataFrame(employees)

    # Apply filter
    if selected_filter != "All":
        df = df[df["constraint_status"] == selected_filter]

    # Apply sorting
    if selected_sort == "constraint_status":
        # Custom sort order for constraint status
        status_order = ["At §415(c) Limit", "Reduced", "Unconstrained", "Not Selected"]
        df["_sort_key"] = df["constraint_status"].map(
            {s: i for i, s in enumerate(status_order)}
        )
        df = df.sort_values("_sort_key", ascending=ascending)
        df = df.drop(columns=["_sort_key"])
    elif selected_sort in df.columns:
        df = df.sort_values(selected_sort, ascending=ascending)

    # Format display columns
    display_df = df[[
        "employee_id",
        "compensation",
        "deferral_amount",
        "match_amount",
        "after_tax_amount",
        "mega_backdoor_amount",
        "individual_acp",
        "available_room",
        "constraint_status",
    ]].copy()

    display_df.columns = [
        "Employee ID",
        "Compensation",
        "Deferral",
        "Match",
        "After-Tax",
        "Mega-Backdoor",
        "ACP (%)",
        "Available Room",
        "Constraint",
    ]

    # Format numeric columns
    display_df["Compensation"] = display_df["Compensation"].apply(
        lambda x: f"${x:,.0f}"
    )
    display_df["Deferral"] = display_df["Deferral"].apply(
        lambda x: f"${x:,.0f}"
    )
    display_df["Match"] = display_df["Match"].apply(
        lambda x: f"${x:,.0f}"
    )
    display_df["After-Tax"] = display_df["After-Tax"].apply(
        lambda x: f"${x:,.0f}"
    )
    display_df["Mega-Backdoor"] = display_df["Mega-Backdoor"].apply(
        lambda x: f"${x:,.0f}"
    )
    display_df["ACP (%)"] = display_df["ACP (%)"].apply(
        lambda x: f"{x:.2f}%" if x is not None else "N/A"
    )
    display_df["Available Room"] = display_df["Available Room"].apply(
        lambda x: f"${x:,.0f}"
    )

    # Add constraint icons
    display_df["Constraint"] = display_df["Constraint"].apply(
        lambda x: f"{CONSTRAINT_ICONS.get(x, '')} {x}"
    )

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(len(display_df) * 35 + 38, 500),  # Max 500px height
    )

    # Show count if filtered
    if selected_filter != "All":
        st.caption(f"Showing {len(display_df)} of {len(employees)} {group} employees")


def render_export_button(
    impact_data: dict,
    export_group: Literal["hce", "nhce", "all"] = "all",
    include_group_column: bool = True,
) -> None:
    """
    Render CSV export button.

    Args:
        impact_data: EmployeeImpactViewResponse dict
        export_group: Which group(s) to export
        include_group_column: Include Group column in export
    """
    # Prepare data for export
    employees = []
    if export_group in ("hce", "all"):
        for emp in impact_data["hce_employees"]:
            emp_copy = emp.copy()
            emp_copy["group"] = "HCE"
            employees.append(emp_copy)

    if export_group in ("nhce", "all"):
        for emp in impact_data["nhce_employees"]:
            emp_copy = emp.copy()
            emp_copy["group"] = "NHCE"
            employees.append(emp_copy)

    if not employees:
        st.warning("No employees to export.")
        return

    # Create DataFrame
    df = pd.DataFrame(employees)

    # Select and order columns
    columns = ["employee_id"]
    if include_group_column and export_group == "all":
        columns.append("group")
    columns.extend([
        "compensation",
        "deferral_amount",
        "match_amount",
        "after_tax_amount",
        "mega_backdoor_amount",
        "individual_acp",
        "available_room",
        "constraint_status",
    ])

    export_df = df[columns].copy()

    # Rename columns for export
    column_names = {
        "employee_id": "Employee ID",
        "group": "Group",
        "compensation": "Compensation",
        "deferral_amount": "Deferral",
        "match_amount": "Match",
        "after_tax_amount": "After-Tax",
        "mega_backdoor_amount": "Mega-Backdoor",
        "individual_acp": "Individual ACP (%)",
        "available_room": "Available Room",
        "constraint_status": "Constraint Status",
    }
    export_df = export_df.rename(columns=column_names)

    # Convert to CSV
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    # Create download button
    st.download_button(
        label="📥 Export to CSV",
        data=csv_data,
        file_name=f"employee_impact_{impact_data['census_id']}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_employee_detail_modal(employee: dict) -> None:
    """
    Render detailed view for a single employee.

    Args:
        employee: EmployeeImpactResponse dict
    """
    st.subheader(f"Employee: {employee['employee_id']}")

    # Status badge
    status = employee["constraint_status"]
    icon = CONSTRAINT_ICONS.get(status, "")
    color = CONSTRAINT_COLORS.get(status, "#000000")

    st.markdown(
        f"**Status:** <span style='color: {color};'>{icon} {status}</span>",
        unsafe_allow_html=True,
    )

    st.markdown(f"*{employee['constraint_detail']}*")

    st.divider()

    # Contribution breakdown
    st.write("**Contribution Breakdown:**")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Compensation", f"${employee['compensation']:,.2f}")
        st.metric("Deferral", f"${employee['deferral_amount']:,.2f}")
        st.metric("Match", f"${employee['match_amount']:,.2f}")

    with col2:
        st.metric("After-Tax", f"${employee['after_tax_amount']:,.2f}")
        st.metric("Mega-Backdoor", f"${employee['mega_backdoor_amount']:,.2f}")
        if employee.get("requested_mega_backdoor", 0) > employee.get("mega_backdoor_amount", 0):
            st.metric(
                "Requested",
                f"${employee['requested_mega_backdoor']:,.2f}",
                delta=f"-${employee['requested_mega_backdoor'] - employee['mega_backdoor_amount']:,.2f}",
                delta_color="inverse",
            )

    st.divider()

    # §415(c) analysis
    st.write("**§415(c) Analysis:**")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("§415(c) Limit", f"${employee['section_415c_limit']:,}")

    with col2:
        st.metric(
            "Available Room",
            f"${employee['available_room']:,.2f}",
            help="Remaining capacity after existing contributions",
        )

    # Individual ACP
    if employee.get("individual_acp") is not None:
        st.metric("Individual ACP", f"{employee['individual_acp']:.2f}%")
