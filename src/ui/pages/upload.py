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
    """Render the census upload form."""
    st.subheader("Upload New Census")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help=(
            "Upload a census CSV file with employee data. "
            "Required columns: Employee ID, HCE Status, Annual Compensation, "
            "Current Deferral Rate, Current Match Rate, Current After-Tax Rate"
        ),
    )

    # Configuration
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

    # Upload button
    if uploaded_file is not None:
        if st.button("Upload Census", type="primary"):
            upload_census(uploaded_file, int(plan_year), census_name)


def upload_census(file, plan_year: int, name: str) -> None:
    """Upload census to API."""
    try:
        # Prepare request
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        data = {"plan_year": str(plan_year)}
        if name:
            data["name"] = name

        # Make API request
        response = requests.post(
            f"{API_BASE_URL}/census",
            files=files,
            data=data,
            timeout=60,
        )

        if response.status_code == 201:
            census = response.json()
            st.success(f"Census uploaded successfully!")
            st.info(
                f"**Census ID:** {census['id']}\n\n"
                f"**Participants:** {census['participant_count']} "
                f"(HCE: {census['hce_count']}, NHCE: {census['nhce_count']})"
            )
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
    """Render list of uploaded censuses."""
    st.subheader("Uploaded Censuses")

    try:
        response = requests.get(f"{API_BASE_URL}/census", timeout=10)

        if response.status_code == 200:
            data = response.json()
            censuses = data.get("items", [])

            if not censuses:
                st.info("No censuses uploaded yet. Upload a census above to get started.")
                return

            # Display as table
            for census in censuses:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.write(f"**{census['name']}**")
                        st.caption(f"ID: {census['id'][:8]}...")

                    with col2:
                        st.write(f"Year: {census['plan_year']}")

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
