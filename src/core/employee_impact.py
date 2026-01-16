"""
Employee Impact Service for ACP Sensitivity Analyzer.

T015-T021: Service for computing employee-level impact views,
including individual contribution breakdowns and constraint analysis.
"""

import random
from typing import TYPE_CHECKING

from src.core.constants import get_415c_limit
from src.core.acp_eligibility import determine_acp_inclusion, plan_year_bounds
from src.core.models import (
    ConstraintStatus,
    EmployeeImpact,
    EmployeeImpactSummary,
    EmployeeImpactView,
    ExclusionInfo,
    ExcludedParticipant,
)

if TYPE_CHECKING:
    from src.storage.repository import ParticipantRepository, CensusRepository
    from src.storage.models import Participant


class EmployeeImpactService:
    """
    Service for computing employee-level impact views.

    T015-T016: Computes individual employee contribution breakdowns
    and constraint status for a given scenario.
    """

    def __init__(
        self,
        participant_repo: "ParticipantRepository",
        census_repo: "CensusRepository",
    ):
        """
        Initialize service with repository dependencies.

        Args:
            participant_repo: Repository for participant data access
            census_repo: Repository for census data access
        """
        self.participant_repo = participant_repo
        self.census_repo = census_repo

    def compute_impact(
        self,
        census_id: str,
        adoption_rate: float,
        contribution_rate: float,
        seed: int,
    ) -> EmployeeImpactView:
        """
        Compute employee-level impact view for a scenario.

        T017: Main entry point for employee impact computation.

        Args:
            census_id: Reference to census data
            adoption_rate: Fraction of HCEs participating (0.0 to 1.0)
            contribution_rate: Mega-backdoor as fraction of compensation
            seed: Random seed for HCE selection reproducibility

        Returns:
            Complete EmployeeImpactView with all employee details and summaries
        """
        # 1. Get census and participants
        census = self.census_repo.get(census_id)
        if census is None:
            raise ValueError(f"Census {census_id} not found")

        participants = self.participant_repo.get_by_census(census_id)
        plan_year_start, plan_year_end = plan_year_bounds(census.plan_year)

        # 2. Apply permissive disaggregation - filter by ACP eligibility
        includable_participants: list["Participant"] = []
        excluded_participants_list: list[ExcludedParticipant] = []
        terminated_before_entry_count = 0
        not_eligible_during_year_count = 0
        missing_dob_count = 0
        missing_hire_date_count = 0

        for participant in participants:
            inclusion = determine_acp_inclusion(
                dob=participant.dob,
                hire_date=participant.hire_date,
                termination_date=participant.termination_date,
                plan_year_start=plan_year_start,
                plan_year_end=plan_year_end,
            )
            if inclusion.acp_includable:
                includable_participants.append(participant)
            else:
                # Track exclusion reason
                reason = inclusion.acp_exclusion_reason
                if reason == "TERMINATED_BEFORE_ENTRY":
                    terminated_before_entry_count += 1
                elif reason == "NOT_ELIGIBLE_DURING_YEAR":
                    not_eligible_during_year_count += 1
                elif reason == "MISSING_DOB":
                    missing_dob_count += 1
                elif reason == "MISSING_HIRE_DATE":
                    missing_hire_date_count += 1

                # Build excluded participant record
                excluded_participants_list.append(
                    ExcludedParticipant(
                        employee_id=participant.employee_id or participant.internal_id,
                        is_hce=participant.is_hce,
                        exclusion_reason=reason,
                        eligibility_date=inclusion.eligibility_date.isoformat() if inclusion.eligibility_date else None,
                        entry_date=inclusion.entry_date.isoformat() if inclusion.entry_date else None,
                        termination_date=participant.termination_date.isoformat() if participant.termination_date else None,
                    )
                )

        excluded_count = len(excluded_participants_list)
        exclusion_breakdown = ExclusionInfo(
            total_excluded=excluded_count,
            terminated_before_entry_count=terminated_before_entry_count,
            not_eligible_during_year_count=not_eligible_during_year_count,
            missing_dob_count=missing_dob_count,
            missing_hire_date_count=missing_hire_date_count,
        )

        # 3. Get §415(c) limit for this plan year
        limit_415c = get_415c_limit(census.plan_year)

        # 3. Separate HCEs and NHCEs
        hces = [p for p in includable_participants if p.is_hce]
        nhces = [p for p in includable_participants if not p.is_hce]

        # 4. Select HCEs for mega-backdoor participation (reproduce with seed)
        selected_ids = self._select_hces(hces, adoption_rate, seed)

        # 5. Compute impact for each participant
        hce_impacts = [
            self._compute_employee_impact(
                p, limit_415c, contribution_rate, p.internal_id in selected_ids
            )
            for p in hces
        ]
        nhce_impacts = [
            self._compute_employee_impact(
                p, limit_415c, 0, False  # NHCEs don't get mega-backdoor
            )
            for p in nhces
        ]

        # 6. Compute summaries
        hce_summary = self._compute_summary(hce_impacts, "HCE")
        nhce_summary = self._compute_summary(nhce_impacts, "NHCE")

        return EmployeeImpactView(
            census_id=census_id,
            adoption_rate=adoption_rate,
            contribution_rate=contribution_rate,
            seed_used=seed,
            plan_year=census.plan_year,
            section_415c_limit=limit_415c,
            excluded_count=excluded_count,
            exclusion_breakdown=exclusion_breakdown,
            excluded_participants=excluded_participants_list,
            hce_employees=hce_impacts,
            nhce_employees=nhce_impacts,
            hce_summary=hce_summary,
            nhce_summary=nhce_summary,
        )

    def _select_hces(
        self,
        hces: list["Participant"],
        adoption_rate: float,
        seed: int,
    ) -> set[str]:
        """
        Select HCEs for mega-backdoor participation.

        Uses the same selection logic as scenario analysis to ensure
        reproducibility with the same seed.

        Args:
            hces: List of HCE participants
            adoption_rate: Fraction to select (0.0 to 1.0)
            seed: Random seed for reproducibility

        Returns:
            Set of internal_ids for selected HCEs
        """
        if not hces or adoption_rate <= 0:
            return set()

        # Use consistent rounding: round(n * rate + 0.5) for positive bias
        # This matches the scenario analysis logic
        num_selected = int(len(hces) * adoption_rate + 0.5)
        num_selected = min(num_selected, len(hces))  # Cap at total HCEs

        if num_selected == 0:
            return set()

        # Sort HCEs by internal_id for deterministic ordering before sampling
        sorted_hces = sorted(hces, key=lambda p: p.internal_id)

        # Use seed to get reproducible selection
        random.seed(seed)
        selected = random.sample(sorted_hces, num_selected)

        return {p.internal_id for p in selected}

    def _compute_employee_impact(
        self,
        participant: "Participant",
        limit_415c: int,
        contribution_rate: float,
        is_selected: bool,
    ) -> EmployeeImpact:
        """
        Compute impact for a single employee.

        T018: Calculates contribution amounts, available room,
        and constraint status for one participant.

        Args:
            participant: Participant data
            limit_415c: §415(c) annual additions limit
            contribution_rate: Mega-backdoor as fraction of compensation
            is_selected: Whether this HCE was selected for mega-backdoor

        Returns:
            EmployeeImpact with full breakdown
        """
        # Convert compensation from cents to dollars
        compensation = participant.compensation_cents / 100

        # Calculate contribution amounts (rates are percentages, not decimals)
        deferral = compensation * participant.deferral_rate / 100
        match = compensation * participant.match_rate / 100
        after_tax = compensation * participant.after_tax_rate / 100

        # Calculate mega-backdoor amounts
        if is_selected and participant.is_hce:
            requested = compensation * contribution_rate
        else:
            requested = 0.0

        # Calculate available room BEFORE mega-backdoor
        existing_total = deferral + match + after_tax
        available_before = limit_415c - existing_total

        # Calculate actual mega-backdoor (capped by available room)
        if is_selected:
            actual = min(requested, max(0, available_before))
        else:
            actual = 0.0

        # Calculate available room AFTER mega-backdoor
        available_after = available_before - actual

        # T020: Determine constraint status
        status, detail = self._classify_constraint(
            is_selected=is_selected,
            is_hce=participant.is_hce,
            requested=requested,
            actual=actual,
            limit_415c=limit_415c,
            available_before=available_before,
        )

        # Calculate individual ACP
        # ACP = (match + after_tax + mega_backdoor) / compensation * 100
        acp_contributions = match + after_tax + actual
        if compensation > 0:
            individual_acp = (acp_contributions / compensation) * 100
        else:
            individual_acp = None

        return EmployeeImpact(
            employee_id=participant.internal_id,
            is_hce=participant.is_hce,
            compensation=compensation,
            deferral_amount=deferral,
            match_amount=match,
            after_tax_amount=after_tax,
            section_415c_limit=limit_415c,
            available_room=available_after,
            mega_backdoor_amount=actual,
            requested_mega_backdoor=requested,
            individual_acp=individual_acp,
            constraint_status=status,
            constraint_detail=detail,
        )

    def _classify_constraint(
        self,
        is_selected: bool,
        is_hce: bool,
        requested: float,
        actual: float,
        limit_415c: int,
        available_before: float,
    ) -> tuple[ConstraintStatus, str]:
        """
        Classify constraint status and generate detail message.

        T020-T021: Determines status based on selection and limit calculations.

        Args:
            is_selected: Whether participant was selected for mega-backdoor
            is_hce: Whether participant is an HCE
            requested: Requested mega-backdoor amount
            actual: Actual mega-backdoor amount after constraints
            limit_415c: §415(c) limit
            available_before: Available room before mega-backdoor

        Returns:
            Tuple of (ConstraintStatus, detail_message)
        """
        if not is_selected or not is_hce:
            return (
                ConstraintStatus.NOT_SELECTED,
                "Not selected for mega-backdoor participation",
            )

        if actual == 0 and requested > 0:
            # Couldn't contribute anything - at or over limit
            return (
                ConstraintStatus.AT_LIMIT,
                f"§415(c) limit of ${limit_415c:,} reached with existing contributions",
            )

        if actual < requested:
            # Got something but less than requested
            return (
                ConstraintStatus.REDUCED,
                f"Reduced from ${requested:,.2f} to ${actual:,.2f} due to §415(c) limit",
            )

        # Got full requested amount
        return (
            ConstraintStatus.UNCONSTRAINED,
            "Received full mega-backdoor amount",
        )

    def _compute_summary(
        self,
        impacts: list[EmployeeImpact],
        group: str,
    ) -> EmployeeImpactSummary:
        """
        Compute summary statistics for a group.

        T019: Aggregates metrics across all employees in a group.

        Args:
            impacts: List of EmployeeImpact for the group
            group: "HCE" or "NHCE"

        Returns:
            EmployeeImpactSummary with aggregated metrics
        """
        total_count = len(impacts)

        if total_count == 0:
            # Empty group
            return EmployeeImpactSummary(
                group=group,
                total_count=0,
                at_limit_count=0 if group == "HCE" else None,
                reduced_count=0 if group == "HCE" else None,
                average_available_room=0.0 if group == "HCE" else None,
                total_mega_backdoor=0.0 if group == "HCE" else None,
                average_individual_acp=0.0,
                total_match=0.0,
                total_after_tax=0.0,
            )

        # Calculate totals
        total_match = sum(e.match_amount for e in impacts)
        total_after_tax = sum(e.after_tax_amount for e in impacts)

        # Calculate average ACP (exclude None values)
        valid_acps = [e.individual_acp for e in impacts if e.individual_acp is not None]
        if valid_acps:
            avg_acp = sum(valid_acps) / len(valid_acps)
        else:
            avg_acp = 0.0

        # HCE-specific calculations
        if group == "HCE":
            at_limit_count = sum(
                1 for e in impacts
                if e.constraint_status == ConstraintStatus.AT_LIMIT
            )
            reduced_count = sum(
                1 for e in impacts
                if e.constraint_status == ConstraintStatus.REDUCED
            )
            total_mega_backdoor = sum(e.mega_backdoor_amount for e in impacts)
            avg_available_room = sum(e.available_room for e in impacts) / total_count

            return EmployeeImpactSummary(
                group="HCE",
                total_count=total_count,
                at_limit_count=at_limit_count,
                reduced_count=reduced_count,
                average_available_room=avg_available_room,
                total_mega_backdoor=total_mega_backdoor,
                average_individual_acp=avg_acp,
                total_match=total_match,
                total_after_tax=total_after_tax,
            )
        else:
            # NHCE - no HCE-specific fields
            return EmployeeImpactSummary(
                group="NHCE",
                total_count=total_count,
                at_limit_count=None,
                reduced_count=None,
                average_available_room=None,
                total_mega_backdoor=None,
                average_individual_acp=avg_acp,
                total_match=total_match,
                total_after_tax=total_after_tax,
            )
