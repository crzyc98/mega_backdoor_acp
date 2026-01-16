# Feature Specification: Normalize Rate Inputs & HCE/NHCE Validation

**Feature Branch**: `014-normalize-rate-inputs`
**Created**: 2026-01-16
**Status**: Draft
**Input**: User description: "Normalize rate inputs on backend to expect decimals (0.06 for 6%). Strict API contract with OpenAPI schemas requiring decimal range inputs. Frontend must submit decimals. Census parser must reliably detect HCE/NHCE canonical forms, normalize to boolean, and return structured error if 0 NHCEs or 0 HCEs after parsing."

## Clarifications

### Session 2026-01-16

- Q: How should V1 API endpoints (using percentage format 0-100) be handled? → A: Remove V1 endpoints entirely in this feature (breaking change)
- Q: How should HCE status be determined? → A: By compensation threshold based on plan year: 2024=$155k, 2025=$160k, 2026-2028=$160k. Employees with compensation >= threshold are HCE.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - API Rate Input Standardization (Priority: P1)

As a frontend developer, I want the API to consistently expect decimal rates (e.g., 0.06 for 6%) so that I can build predictable, error-free integrations without worrying about unit conversions.

**Why this priority**: This is the core of the feature. Without standardized rate inputs, the system will continue to have inconsistent behavior between V1 (percentages 0-100) and V2 (decimals 0-1) APIs, causing integration errors and maintenance burden.

**Independent Test**: Can be fully tested by submitting rate values to API endpoints and verifying validation errors for out-of-range inputs. Delivers immediate value by catching incorrect rate formats at the API boundary.

**Acceptance Scenarios**:

1. **Given** a user submits `adoption_rate: 0.75` (decimal), **When** the API validates the request, **Then** the request is accepted as valid (75% adoption)
2. **Given** a user submits `adoption_rate: 75` (percentage integer), **When** the API validates the request, **Then** the request is rejected with a clear error message explaining the expected decimal format
3. **Given** a user submits `contribution_rate: 0.06` (decimal), **When** the API validates the request, **Then** the request is accepted as valid (6% contribution)
4. **Given** a user submits `adoption_rate: 1.5` (exceeds 1.0), **When** the API validates the request, **Then** the request is rejected with validation error stating value must be between 0.0 and 1.0

---

### User Story 2 - Census HCE/NHCE Calculation & Validation (Priority: P1)

As a plan administrator, I want the system to automatically determine HCE/NHCE status based on compensation and plan year so that I don't need to manually categorize employees or maintain an HCE column in my census files.

**Why this priority**: Census data is the foundation for all ACP calculations. Automatic HCE determination based on IRS thresholds ensures accuracy and reduces data entry errors. If the resulting distribution is invalid (all HCE or all NHCE), the entire analysis becomes meaningless.

**Independent Test**: Can be fully tested by uploading census CSV files with compensation data and verifying correct HCE classification based on plan year thresholds.

**Acceptance Scenarios**:

1. **Given** a census file with plan year 2024 and an employee earning $160,000, **When** the parser processes the file, **Then** the employee is classified as HCE (compensation >= $155,000 threshold)
2. **Given** a census file with plan year 2024 and an employee earning $150,000, **When** the parser processes the file, **Then** the employee is classified as NHCE (compensation < $155,000 threshold)
3. **Given** a census file with plan year 2025 and an employee earning $160,000, **When** the parser processes the file, **Then** the employee is classified as HCE (compensation >= $160,000 threshold)
4. **Given** a census file with plan year 2025 and an employee earning $159,000, **When** the parser processes the file, **Then** the employee is classified as NHCE (compensation < $160,000 threshold)
5. **Given** a parsed census where all employees have compensation above the threshold (0 NHCEs), **When** validation completes, **Then** a structured error message is returned indicating the census lacks NHCE participants
6. **Given** a parsed census where all employees have compensation below the threshold (0 HCEs), **When** validation completes, **Then** a structured error message is returned indicating the census lacks HCE participants

---

### User Story 3 - Frontend Rate Submission (Priority: P2)

As a frontend application, I need to submit all rate values as decimals to maintain consistency with the backend contract, ensuring users see clear validation messages when rates are incorrectly formatted.

**Why this priority**: Depends on P1 (API standardization). Once the backend contract is strict, the frontend must comply. This ensures end-to-end consistency.

**Independent Test**: Can be fully tested by verifying frontend form submissions convert displayed percentages to decimals before API calls.

**Acceptance Scenarios**:

1. **Given** a user enters "6" in a contribution rate field displayed as percentage, **When** the form submits to the API, **Then** the value is sent as `0.06` (decimal)
2. **Given** a user enters "75" in an adoption rate field displayed as percentage, **When** the form submits to the API, **Then** the value is sent as `0.75` (decimal)
3. **Given** a user enters an invalid rate value, **When** the API returns a validation error, **Then** the frontend displays a user-friendly error message explaining the expected format

---

### Edge Cases

- What happens when a rate value is exactly 0.0 or exactly 1.0? → Should be accepted as valid boundary values
- What happens when a rate value is submitted as a string "0.06"? → Should be coerced to numeric and accepted
- What happens when compensation is exactly at the threshold (e.g., $160,000 for 2025)? → Employee is classified as HCE (>= comparison)
- What happens when compensation is null/missing? → Census should be rejected with error identifying rows with missing compensation
- What happens when plan year is not provided? → API should require plan_year parameter for HCE calculation
- What happens when plan year is outside known range (e.g., 2023 or 2029)? → Return error with supported plan year range
- What happens when census has exactly 1 HCE and many NHCEs? → Should be accepted (valid distribution)
- What happens when census has exactly 1 NHCE and many HCEs? → Should be accepted (valid distribution)

## Requirements *(mandatory)*

### Functional Requirements

**Rate Input Normalization:**

- **FR-001**: All API endpoints MUST accept rate values (adoption_rate, contribution_rate) as decimal fractions in the range 0.0 to 1.0 (e.g., 0.06 represents 6%)
- **FR-002**: OpenAPI schemas MUST define rate fields with `ge=0.0, le=1.0` constraints and include a clear description stating "Decimal fraction (0.0 to 1.0), e.g., 0.06 for 6%"
- **FR-003**: API MUST reject rate values outside the 0.0-1.0 range with a structured validation error that includes the field name, submitted value, and expected range
- **FR-004**: V1 API endpoints using percentage format (0-100) MUST be removed entirely; only decimal-format endpoints will remain (breaking change)
- **FR-005**: Backend services MUST NOT perform percentage-to-decimal conversions; all internal processing assumes decimal inputs

**Census HCE/NHCE Determination:**

- **FR-006**: System MUST determine HCE status by comparing employee compensation to IRS thresholds based on plan year:
  - 2024: $155,000
  - 2025: $160,000
  - 2026-2028: $160,000
- **FR-007**: Employees with compensation >= threshold for the plan year MUST be classified as HCE; employees below threshold MUST be classified as NHCE
- **FR-008**: Census parsing MUST require a valid plan_year parameter (2024-2028); requests without plan_year or with unsupported years MUST be rejected with a structured error
- **FR-009**: After HCE calculation, the system MUST validate that the census contains at least 1 HCE participant AND at least 1 NHCE participant
- **FR-010**: If census validation fails (0 HCEs or 0 NHCEs), API MUST return a structured error response with:
  - Error code indicating the specific validation failure
  - Human-readable message explaining the issue
  - Count of HCEs and NHCEs found
  - The compensation threshold used for the plan year
  - Suggested remediation action

**Frontend Integration:**

- **FR-011**: Frontend MUST convert user-entered percentage values to decimals before API submission (e.g., user enters "6", frontend submits 0.06)
- **FR-012**: Frontend MUST display rate values to users as percentages for readability while storing/transmitting as decimals

### Key Entities

- **Rate Value**: A decimal fraction representing a percentage (0.0-1.0). Used for adoption_rate, contribution_rate in scenario analysis.
- **HCE Status**: A boolean value indicating whether a participant is a Highly Compensated Employee (true) or Non-Highly Compensated Employee (false). Determined by comparing compensation to IRS threshold for the plan year.
- **HCE Compensation Threshold**: IRS-defined annual compensation limit that determines HCE status. Varies by plan year (2024: $155k, 2025-2028: $160k).
- **Census Validation Result**: The outcome of parsing a census file, including participant counts by HCE status, the threshold used, and any validation errors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of API rate input fields enforce decimal range (0.0-1.0) with clear validation error messages
- **SC-002**: Census parser correctly classifies HCE/NHCE status based on compensation thresholds for all supported plan years (2024-2028) with 100% accuracy
- **SC-003**: Census files with invalid HCE distributions (0 HCEs or 0 NHCEs) are rejected with structured error messages in 100% of cases
- **SC-004**: Frontend-to-backend rate value transmission uses decimals exclusively, eliminating percentage/decimal confusion errors
- **SC-005**: OpenAPI schema documentation clearly describes decimal format expectations for all rate fields
- **SC-006**: Zero runtime errors caused by rate format mismatches between frontend and backend

## Assumptions

- V1 API endpoints will be removed in this feature; all consumers must use the decimal-format V2 API
- HCE status is always calculated from compensation; explicit HCE columns in census files are ignored in favor of compensation-based determination
- Frontend percentage-to-decimal conversion is a UI concern; the API contract is strictly decimal-only
- The structured error format for HCE distribution failures will follow existing API error patterns in the codebase
