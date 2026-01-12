"""
CSV Import Wizard Page.

Multi-step wizard for importing census data with:
- File upload and preview
- Auto-suggested column mapping
- Data validation
- Duplicate resolution
- Import execution
"""

import requests
import streamlit as st

from src.core.field_mappings import FIELD_DISPLAY_NAMES, REQUIRED_FIELDS


API_BASE_URL = "http://localhost:8000/api/v1"

# Wizard steps in order
WIZARD_STEPS = ["upload", "map", "validate", "preview", "confirm", "completed"]
STEP_LABELS = {
    "upload": "Upload",
    "map": "Map Columns",
    "validate": "Validate",
    "preview": "Preview",
    "confirm": "Confirm",
    "completed": "Done",
}


def init_wizard_state() -> None:
    """Initialize wizard session state."""
    if "wizard_session_id" not in st.session_state:
        st.session_state.wizard_session_id = None
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = "upload"
    if "wizard_session" not in st.session_state:
        st.session_state.wizard_session = None


def reset_wizard() -> None:
    """Reset wizard to initial state."""
    st.session_state.wizard_session_id = None
    st.session_state.wizard_step = "upload"
    st.session_state.wizard_session = None


def get_step_index(step: str) -> int:
    """Get the index of a step in the wizard."""
    try:
        return WIZARD_STEPS.index(step)
    except ValueError:
        return 0


def render_progress_bar() -> None:
    """Render the wizard progress indicator."""
    current_step = st.session_state.wizard_step
    current_index = get_step_index(current_step)

    # Progress bar
    progress = (current_index + 1) / len(WIZARD_STEPS)
    st.progress(progress)

    # Step indicators
    cols = st.columns(len(WIZARD_STEPS))
    for i, step in enumerate(WIZARD_STEPS):
        with cols[i]:
            if i < current_index:
                st.markdown(f"~~{STEP_LABELS[step]}~~")
            elif i == current_index:
                st.markdown(f"**{STEP_LABELS[step]}**")
            else:
                st.markdown(f"*{STEP_LABELS[step]}*")


def fetch_session() -> dict | None:
    """Fetch the current session from the API."""
    session_id = st.session_state.wizard_session_id
    if not session_id:
        return None

    try:
        response = requests.get(
            f"{API_BASE_URL}/import/sessions/{session_id}",
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code in (404, 410):
            # Session not found or expired
            reset_wizard()
            return None
    except requests.exceptions.RequestException:
        pass
    return None


# ============================================================================
# Step 1: Upload
# ============================================================================


def render_upload_step() -> None:
    """Render the file upload step."""
    st.subheader("Step 1: Upload Census CSV")
    st.write("Upload a CSV file containing census data for import.")

    # File size limit note
    st.info("Maximum file size: 50MB")

    # File uploader with progress
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a census CSV file with employee data including SSN, DOB, compensation, and contribution amounts.",
        key="wizard_file_upload",
    )

    if uploaded_file is not None:
        # Show file info
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")

        # Upload button
        if st.button("Upload and Continue", type="primary"):
            with st.spinner("Uploading file..."):
                create_session_and_upload(uploaded_file)


def create_session_and_upload(file) -> None:
    """Create import session and upload file."""
    try:
        files = {"file": (file.name, file.getvalue(), "text/csv")}

        response = requests.post(
            f"{API_BASE_URL}/import/sessions",
            files=files,
            timeout=60,
        )

        if response.status_code == 201:
            session = response.json()
            st.session_state.wizard_session_id = session["id"]
            st.session_state.wizard_step = "map"
            st.session_state.wizard_session = session
            st.success("File uploaded successfully!")
            st.rerun()
        elif response.status_code == 413:
            st.error("File size exceeds 50MB limit")
        elif response.status_code == 400:
            error = response.json().get("detail", "Invalid file")
            st.error(f"Upload failed: {error}")
        else:
            st.error(f"Upload failed: HTTP {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API server")
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")


# ============================================================================
# Step 2: Column Mapping
# ============================================================================


def render_mapping_step() -> None:
    """Render the column mapping step."""
    st.subheader("Step 2: Map Columns")

    session_id = st.session_state.wizard_session_id

    # Fetch file preview
    preview = fetch_file_preview(session_id)
    if not preview:
        st.error("Could not load file preview")
        return

    # Show sample data
    st.write("**File Preview:**")
    with st.expander("Show sample rows", expanded=False):
        import pandas as pd
        df = pd.DataFrame(preview["sample_rows"], columns=preview["headers"])
        st.dataframe(df, use_container_width=True)

    st.write(f"Total rows: {preview['total_rows']}")

    # Fetch auto-suggested mapping
    suggestion = fetch_mapping_suggestion(session_id)

    # Column mapping UI
    st.write("**Map source columns to census fields:**")
    st.caption("Auto-detected mappings shown. Adjust as needed.")

    headers = preview["headers"]
    mapping = {}

    # Create two-column layout for mapping
    col1, col2 = st.columns(2)

    for i, field in enumerate(REQUIRED_FIELDS):
        with col1 if i % 2 == 0 else col2:
            display_name = FIELD_DISPLAY_NAMES.get(field, field)
            suggested = suggestion.get("suggested_mapping", {}).get(field, "") if suggestion else ""
            confidence = suggestion.get("confidence_scores", {}).get(field, 0) if suggestion else 0

            # Show confidence indicator
            confidence_text = ""
            if suggested and confidence >= 0.9:
                confidence_text = " (High confidence)"
            elif suggested and confidence >= 0.6:
                confidence_text = " (Medium confidence)"

            selected = st.selectbox(
                f"{display_name}{confidence_text}",
                options=["-- Select Column --"] + headers,
                index=headers.index(suggested) + 1 if suggested in headers else 0,
                key=f"map_{field}",
            )

            if selected and selected != "-- Select Column --":
                mapping[field] = selected

    # Show missing fields warning
    missing = [f for f in REQUIRED_FIELDS if f not in mapping]
    if missing:
        st.warning(f"Missing required fields: {', '.join([FIELD_DISPLAY_NAMES.get(f, f) for f in missing])}")

    # Navigation buttons
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("Back", key="back_to_upload"):
            reset_wizard()
            st.rerun()

    with col_next:
        if st.button("Continue to Validation", type="primary", disabled=len(missing) > 0):
            save_mapping_and_continue(session_id, mapping)


def fetch_file_preview(session_id: str) -> dict | None:
    """Fetch file preview from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/import/sessions/{session_id}/preview",
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None


def fetch_mapping_suggestion(session_id: str) -> dict | None:
    """Fetch mapping suggestion from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/import/sessions/{session_id}/mapping/suggest",
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None


def save_mapping_and_continue(session_id: str, mapping: dict) -> None:
    """Save column mapping and proceed to validation."""
    try:
        response = requests.put(
            f"{API_BASE_URL}/import/sessions/{session_id}/mapping",
            json={"mapping": mapping},
            timeout=10,
        )

        if response.status_code == 200:
            st.session_state.wizard_step = "validate"
            st.rerun()
        else:
            error = response.json().get("detail", "Failed to save mapping")
            st.error(f"Error: {error}")

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to save mapping: {str(e)}")


# ============================================================================
# Step 3: Validation
# ============================================================================


def render_validation_step() -> None:
    """Render the validation step."""
    st.subheader("Step 3: Validate Data")

    session_id = st.session_state.wizard_session_id
    session = fetch_session()

    if not session:
        st.error("Session not found")
        return

    # Check if validation has been run
    if session.get("validation_summary"):
        render_validation_results(session_id, session["validation_summary"])
    else:
        st.write("Ready to validate your data against the column mappings.")
        st.write("Validation will check for:")
        st.markdown("""
        - **Invalid SSN format** - Must be exactly 9 digits
        - **Invalid dates** - DOB and hire date must be valid and not in the future
        - **Invalid amounts** - Compensation and contributions must be non-negative numbers
        - **Missing required values** - All required fields must have values
        - **Duplicate SSNs** - Within the uploaded file
        """)

        if st.button("Run Validation", type="primary"):
            run_validation(session_id)


def run_validation(session_id: str) -> None:
    """Run validation on the session."""
    with st.spinner("Validating data... This may take a moment for large files."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/import/sessions/{session_id}/validate",
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                st.success(f"Validation completed in {result.get('duration_seconds', 0):.1f} seconds")
                st.session_state.wizard_step = "preview"
                st.rerun()
            else:
                error = response.json().get("detail", "Validation failed")
                st.error(f"Error: {error}")

        except requests.exceptions.RequestException as e:
            st.error(f"Validation failed: {str(e)}")


def render_validation_results(session_id: str, summary: dict) -> None:
    """Render validation results summary."""
    st.write("**Validation Summary:**")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rows", summary["total_rows"])
    with col2:
        st.metric("Errors", summary["error_count"], delta_color="inverse")
    with col3:
        st.metric("Warnings", summary["warning_count"])
    with col4:
        st.metric("Valid Rows", summary["valid_count"])

    # Show issues if any
    if summary["error_count"] > 0 or summary["warning_count"] > 0:
        render_validation_issues(session_id)

    # Navigation
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("Back to Mapping", key="back_to_mapping"):
            st.session_state.wizard_step = "map"
            st.rerun()

    with col_next:
        if summary["error_count"] > 0:
            st.warning("Cannot proceed with errors. Fix issues and re-upload, or rows with errors will be rejected.")

        if st.button("Continue to Preview", type="primary"):
            st.session_state.wizard_step = "preview"
            st.rerun()


def render_validation_issues(session_id: str) -> None:
    """Render validation issues with filtering."""
    # Severity filter
    severity = st.selectbox(
        "Filter by severity",
        options=["all", "error", "warning", "info"],
        format_func=lambda x: x.title() if x != "all" else "All Issues",
    )

    # Fetch issues
    try:
        params = {"limit": 100}
        if severity != "all":
            params["severity"] = severity

        response = requests.get(
            f"{API_BASE_URL}/import/sessions/{session_id}/validation-issues",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            issues = data["items"]
            total = data["total"]

            st.write(f"Showing {len(issues)} of {total} issues")

            for issue in issues:
                severity_emoji = {"error": "", "warning": "", "info": ""}.get(issue["severity"], "")
                with st.expander(f"{severity_emoji} Row {issue['row_number']}: {issue['field_name']} - {issue['message']}"):
                    st.write(f"**Field:** {issue['field_name']}")
                    st.write(f"**Column:** {issue.get('source_column', 'N/A')}")
                    st.write(f"**Raw Value:** `{issue.get('raw_value', 'N/A')}`")
                    if issue.get("suggestion"):
                        st.write(f"**Suggestion:** {issue['suggestion']}")
                    if issue.get("related_row"):
                        st.write(f"**Related Row:** {issue['related_row']}")

    except requests.exceptions.RequestException:
        st.error("Failed to load validation issues")


# ============================================================================
# Step 4: Preview
# ============================================================================


def render_preview_step() -> None:
    """Render the import preview step."""
    st.subheader("Step 4: Import Preview")

    session_id = st.session_state.wizard_session_id

    # Fetch preview summary
    try:
        response = requests.get(
            f"{API_BASE_URL}/import/sessions/{session_id}/preview-import",
            timeout=10,
        )

        if response.status_code == 200:
            preview = response.json()
            render_preview_summary(preview)
        else:
            st.error("Failed to load import preview")
            return

    except requests.exceptions.RequestException:
        st.error("Failed to load import preview")
        return

    # Navigation
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("Back to Validation", key="back_to_validation"):
            st.session_state.wizard_step = "validate"
            st.rerun()

    with col_next:
        if st.button("Continue to Confirm", type="primary"):
            st.session_state.wizard_step = "confirm"
            st.rerun()


def render_preview_summary(preview: dict) -> None:
    """Render the import preview summary."""
    st.write("**Import Summary:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Rows", preview["total_rows"])
        st.metric("Will Import", preview["import_count"], delta_color="normal")

    with col2:
        st.metric("Will Reject", preview["reject_count"], delta_color="inverse")
        st.metric("With Warnings", preview["warning_count"])

    with col3:
        if preview.get("replace_count"):
            st.metric("Will Replace", preview["replace_count"])
        if preview.get("skip_count"):
            st.metric("Will Skip", preview["skip_count"])

    # Breakdown
    if preview["reject_count"] > 0:
        st.warning(f"{preview['reject_count']} rows will be rejected due to validation errors.")

    if preview["import_count"] > 0:
        st.success(f"{preview['import_count']} rows will be imported successfully.")


# ============================================================================
# Step 5: Confirm
# ============================================================================


def render_confirm_step() -> None:
    """Render the confirmation step."""
    st.subheader("Step 5: Confirm Import")

    session = fetch_session()
    if not session:
        st.error("Session not found")
        return

    st.write("Enter census details and confirm the import.")

    # Census name and plan year inputs
    col1, col2 = st.columns(2)

    with col1:
        census_name = st.text_input(
            "Census Name",
            value=session.get("original_filename", "").replace(".csv", ""),
            help="Name to identify this census",
        )

    with col2:
        from src.core.constants import DEFAULT_PLAN_YEAR
        plan_year = st.number_input(
            "Plan Year",
            min_value=2020,
            max_value=2100,
            value=DEFAULT_PLAN_YEAR,
        )

    client_name = st.text_input(
        "Client Name (optional)",
        placeholder="e.g., Acme Corporation",
    )

    # Save mapping profile option
    save_profile = st.checkbox("Save column mapping as a profile for future use")
    profile_name = None
    if save_profile:
        profile_name = st.text_input("Profile Name", placeholder="e.g., Standard Payroll Export")

    st.divider()

    # Navigation
    col_back, col_spacer, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("Back to Preview", key="back_to_preview"):
            st.session_state.wizard_step = "preview"
            st.rerun()

    with col_next:
        if st.button("Execute Import", type="primary"):
            execute_import(
                st.session_state.wizard_session_id,
                census_name,
                int(plan_year),
                client_name if client_name else None,
                save_profile,
                profile_name,
            )


def execute_import(
    session_id: str,
    census_name: str,
    plan_year: int,
    client_name: str | None,
    save_profile: bool,
    profile_name: str | None,
) -> None:
    """Execute the import."""
    with st.spinner("Executing import..."):
        try:
            request_body = {
                "census_name": census_name,
                "plan_year": plan_year,
                "save_mapping_profile": save_profile,
            }
            if client_name:
                request_body["client_name"] = client_name
            if profile_name:
                request_body["mapping_profile_name"] = profile_name

            response = requests.post(
                f"{API_BASE_URL}/import/sessions/{session_id}/execute",
                json=request_body,
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.wizard_import_result = result
                st.session_state.wizard_step = "completed"
                st.rerun()
            else:
                error = response.json().get("detail", "Import failed")
                st.error(f"Error: {error}")

        except requests.exceptions.RequestException as e:
            st.error(f"Import failed: {str(e)}")


# ============================================================================
# Step 6: Completed
# ============================================================================


def render_completed_step() -> None:
    """Render the completion step."""
    st.subheader("Import Complete!")

    result = st.session_state.get("wizard_import_result", {})
    summary = result.get("summary", {})

    st.success("Census data has been imported successfully!")

    # Show results
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Rows", summary.get("total_rows", 0))
    with col2:
        st.metric("Imported", summary.get("imported_count", 0))
    with col3:
        st.metric("Rejected", summary.get("rejected_count", 0))

    # Import log link
    if result.get("import_log_id"):
        st.write(f"**Import Log ID:** `{result['import_log_id']}`")

    if result.get("census_id"):
        st.write(f"**Census ID:** `{result['census_id']}`")

    st.divider()

    # Actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Import Another File", type="primary"):
            reset_wizard()
            st.rerun()

    with col2:
        if st.button("Go to Analysis"):
            reset_wizard()
            # Navigate to analysis page
            if result.get("census_id"):
                st.session_state["selected_census_id"] = result["census_id"]
            st.rerun()


# ============================================================================
# Main Render Function
# ============================================================================


def render() -> None:
    """Main render function for the import wizard page."""
    st.header("CSV Import Wizard")

    # Initialize state
    init_wizard_state()

    # Show progress bar
    render_progress_bar()

    st.divider()

    # Render current step
    step = st.session_state.wizard_step

    if step == "upload":
        render_upload_step()
    elif step == "map":
        render_mapping_step()
    elif step == "validate":
        render_validation_step()
    elif step == "preview":
        render_preview_step()
    elif step == "confirm":
        render_confirm_step()
    elif step == "completed":
        render_completed_step()

    # Cancel button (shown on all steps except completed)
    if step != "completed" and st.session_state.wizard_session_id:
        st.divider()
        if st.button("Cancel Import", type="secondary"):
            # Delete session
            try:
                requests.delete(
                    f"{API_BASE_URL}/import/sessions/{st.session_state.wizard_session_id}",
                    timeout=10,
                )
            except requests.exceptions.RequestException:
                pass
            reset_wizard()
            st.rerun()
