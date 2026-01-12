"""
Census Upload Page.

Handles census file upload, validation, and management.
"""

import io

import requests
import streamlit as st

from src.core.constants import DEFAULT_PLAN_YEAR


API_BASE_URL = "http://localhost:8000/api/v1"


def render_upload_form() -> None:
    """Render the census upload form with column mapping and HCE mode support."""
    st.subheader("Upload New Census")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help=(
            "Upload a census CSV file with employee data. "
            "Required columns depend on HCE mode."
        ),
    )

    # Configuration - Row 1
    col1, col2 = st.columns(2)

    with col1:
        plan_year = st.number_input(
            "Plan Year",
            min_value=2020,
            max_value=2100,
            value=DEFAULT_PLAN_YEAR,
            help="The plan year for ACP analysis",
        )

    with col2:
        census_name = st.text_input(
            "Census Name (optional)",
            placeholder="e.g., Q4 2025 Census",
            help="Optional name to identify this census",
        )

    # Configuration - Row 2
    col3, col4 = st.columns(2)

    with col3:
        client_name = st.text_input(
            "Client Name (optional)",
            placeholder="e.g., Acme Corporation",
            help="Client or organization name for this census",
        )

    with col4:
        hce_mode = st.selectbox(
            "HCE Determination Mode",
            options=["explicit", "compensation_threshold"],
            format_func=lambda x: "Explicit (HCE flag in CSV)" if x == "explicit" else "Compensation Threshold (by plan year)",
            help=(
                "Explicit: Use HCE Status column from CSV. "
                "Compensation Threshold: Determine HCE based on compensation vs IRS threshold for plan year."
            ),
        )

    # Show column mapping detection if file uploaded
    column_mapping = None
    if uploaded_file is not None:
        with st.expander("Column Mapping (click to customize)"):
            st.info("Auto-detected column mappings. Adjust if needed.")
            column_mapping = detect_and_configure_mapping(uploaded_file, hce_mode)

    # Upload button
    if uploaded_file is not None:
        if st.button("Upload Census", type="primary"):
            upload_census(
                uploaded_file,
                int(plan_year),
                census_name,
                client_name,
                hce_mode,
                column_mapping,
            )


def detect_and_configure_mapping(file, hce_mode: str) -> dict | None:
    """Detect and allow configuration of column mapping."""
    import json

    try:
        # Call API to detect column mapping
        file.seek(0)
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        data = {"hce_mode": hce_mode}

        response = requests.post(
            f"{API_BASE_URL}/census/column-mapping/detect",
            files=files,
            data=data,
            timeout=30,
        )

        if response.status_code == 200:
            detection = response.json()
            source_columns = detection["source_columns"]
            suggested = detection["suggested_mapping"]
            required = detection["required_fields"]
            missing = detection["missing_fields"]

            if missing:
                st.warning(f"Missing required fields: {', '.join(missing)}")

            # Allow users to adjust mappings
            mapping = {}
            for target_field in required:
                current = suggested.get(target_field, "")
                selected = st.selectbox(
                    f"Map '{target_field}' to:",
                    options=[""] + source_columns,
                    index=source_columns.index(current) + 1 if current in source_columns else 0,
                    key=f"mapping_{target_field}",
                )
                if selected:
                    mapping[target_field] = selected

            return mapping if mapping else None
        else:
            st.error("Failed to detect column mapping")
            return None

    except Exception as e:
        st.error(f"Column detection failed: {str(e)}")
        return None


def upload_census(
    file,
    plan_year: int,
    name: str,
    client_name: str | None = None,
    hce_mode: str = "explicit",
    column_mapping: dict | None = None,
) -> None:
    """Upload census to API with extended parameters."""
    import json

    try:
        # Prepare request
        file.seek(0)
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        data = {
            "plan_year": str(plan_year),
            "hce_mode": hce_mode,
        }
        if name:
            data["name"] = name
        if client_name:
            data["client_name"] = client_name
        if column_mapping:
            data["column_mapping"] = json.dumps(column_mapping)

        # Make API request
        response = requests.post(
            f"{API_BASE_URL}/census",
            files=files,
            data=data,
            timeout=60,
        )

        if response.status_code == 201:
            census = response.json()
            st.success("Census uploaded successfully!")

            # Show extended info including new fields
            info_parts = [
                f"**Census ID:** {census['id']}",
                f"**Name:** {census['name']}",
            ]
            if census.get("client_name"):
                info_parts.append(f"**Client:** {census['client_name']}")
            info_parts.append(f"**HCE Mode:** {census.get('hce_mode', 'explicit')}")
            info_parts.append(
                f"**Participants:** {census['participant_count']} "
                f"(HCE: {census['hce_count']}, NHCE: {census['nhce_count']})"
            )
            if census.get("avg_compensation"):
                info_parts.append(f"**Avg Compensation:** ${census['avg_compensation']:,.2f}")
            if census.get("avg_deferral_rate"):
                info_parts.append(f"**Avg Deferral Rate:** {census['avg_deferral_rate']:.2f}%")

            st.info("\n\n".join(info_parts))

            # Store census ID in session for analysis
            st.session_state["selected_census_id"] = census["id"]
            st.session_state["selected_census_name"] = census["name"]
            st.rerun()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Upload failed: {error_detail}")

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to API server. "
            "Make sure the API is running on localhost:8000"
        )
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")


def render_census_list() -> None:
    """Render list of uploaded censuses with extended fields."""
    st.subheader("Uploaded Censuses")

    try:
        response = requests.get(f"{API_BASE_URL}/census", timeout=10)

        if response.status_code == 200:
            data = response.json()
            censuses = data.get("items", [])

            if not censuses:
                st.info("No censuses uploaded yet. Upload a census above to get started.")
                return

            # Display as table with extended info
            for census in censuses:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.write(f"**{census['name']}**")
                        if census.get('client_name'):
                            st.caption(f"Client: {census['client_name']}")
                        st.caption(f"ID: {census['id'][:8]}...")

                    with col2:
                        st.write(f"Year: {census['plan_year']}")
                        hce_mode_display = "Explicit" if census.get('hce_mode') == 'explicit' else "Threshold"
                        st.caption(f"HCE Mode: {hce_mode_display}")

                    with col3:
                        st.write(f"Participants: {census['participant_count']}")
                        st.caption(f"HCE: {census['hce_count']} | NHCE: {census['nhce_count']}")

                    with col4:
                        # Select button
                        if st.button("Select", key=f"select_{census['id']}"):
                            st.session_state["selected_census_id"] = census["id"]
                            st.session_state["selected_census_name"] = census["name"]
                            st.success(f"Selected: {census['name']}")
                            st.rerun()

                        # Delete button
                        if st.button("Delete", key=f"delete_{census['id']}", type="secondary"):
                            delete_census(census["id"])

                    st.divider()

        else:
            st.error("Failed to load censuses")

    except requests.exceptions.ConnectionError:
        st.warning(
            "Could not connect to API server. "
            "Make sure the API is running on localhost:8000"
        )
    except Exception as e:
        st.error(f"Error loading censuses: {str(e)}")


def delete_census(census_id: str) -> None:
    """Delete a census."""
    try:
        response = requests.delete(f"{API_BASE_URL}/census/{census_id}", timeout=10)

        if response.status_code == 204:
            st.success("Census deleted successfully!")
            # Clear selection if this census was selected
            if st.session_state.get("selected_census_id") == census_id:
                st.session_state.pop("selected_census_id", None)
                st.session_state.pop("selected_census_name", None)
            st.rerun()
        else:
            st.error("Failed to delete census")

    except Exception as e:
        st.error(f"Delete failed: {str(e)}")


def render_selected_census() -> None:
    """Show currently selected census."""
    if "selected_census_id" in st.session_state:
        st.sidebar.success(
            f"**Selected Census:**\n{st.session_state.get('selected_census_name', 'Unknown')}"
        )
        st.sidebar.caption(f"ID: {st.session_state['selected_census_id'][:8]}...")


def render() -> None:
    """Main render function for upload page."""
    st.header("Upload Census Data")

    # Show selected census in sidebar
    render_selected_census()

    # Upload form
    render_upload_form()

    st.divider()

    # Census list
    render_census_list()
