"""
Unit Tests for ACP Calculator Module.

Tests NHCE ACP calculation, HCE ACP calculation with simulated contributions,
and IRS dual test logic.
"""

from decimal import Decimal

import pytest

from app.services.acp_calculator import (
    calculate_individual_acp,
    calculate_group_acp,
    calculate_nhce_acp,
    calculate_hce_acp,
    apply_acp_test,
    calculate_margin,
    ACPResult,
)


class TestNHCEACPCalculation:
    """T017: Unit tests for NHCE ACP calculation."""

    def test_calculate_individual_acp_basic(self):
        """Individual ACP = (match + after_tax) / compensation * 100."""
        # Employee with $100,000 comp, 3% match ($3,000), 0% after-tax
        acp = calculate_individual_acp(
            match_cents=300000,  # $3,000
            after_tax_cents=0,
            compensation_cents=10000000  # $100,000
        )
        assert acp == Decimal("3.0")

    def test_calculate_individual_acp_with_after_tax(self):
        """Individual ACP includes after-tax contributions."""
        # Employee with $100,000 comp, 3% match ($3,000), 2% after-tax ($2,000)
        acp = calculate_individual_acp(
            match_cents=300000,  # $3,000
            after_tax_cents=200000,  # $2,000
            compensation_cents=10000000  # $100,000
        )
        assert acp == Decimal("5.0")

    def test_calculate_individual_acp_zero_compensation(self):
        """Zero compensation should return 0 ACP (avoid division by zero)."""
        acp = calculate_individual_acp(
            match_cents=100000,
            after_tax_cents=0,
            compensation_cents=0
        )
        assert acp == Decimal("0")

    def test_calculate_individual_acp_precision(self):
        """ACP calculation should maintain precision."""
        # $75,000 comp, $2,250 match (3%), $750 after-tax (1%) = 4%
        acp = calculate_individual_acp(
            match_cents=225000,  # $2,250
            after_tax_cents=75000,  # $750
            compensation_cents=7500000  # $75,000
        )
        assert acp == Decimal("4.0")

    def test_calculate_group_acp_average(self):
        """Group ACP is average of individual ACPs."""
        individual_acps = [
            Decimal("3.0"),
            Decimal("4.0"),
            Decimal("5.0"),
        ]
        group_acp = calculate_group_acp(individual_acps)
        assert group_acp == Decimal("4.0")

    def test_calculate_group_acp_empty(self):
        """Empty group should return 0 ACP."""
        group_acp = calculate_group_acp([])
        assert group_acp == Decimal("0")

    def test_calculate_nhce_acp_from_participants(self):
        """NHCE ACP should be calculated from NHCE participants only."""
        # Participants: list of (match_cents, after_tax_cents, compensation_cents, is_hce)
        participants = [
            # NHCE participants
            {"match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},  # 3%
            {"match_cents": 100000, "after_tax_cents": 50000, "compensation_cents": 5000000, "is_hce": False},  # 3%
            # HCE participant (should be excluded)
            {"match_cents": 300000, "after_tax_cents": 200000, "compensation_cents": 10000000, "is_hce": True},  # 5%
        ]

        nhce_acp = calculate_nhce_acp(participants)
        assert nhce_acp == Decimal("3.0")


class TestHCEACPCalculation:
    """T018: Unit tests for HCE ACP calculation with simulated contributions."""

    def test_calculate_hce_acp_no_adoption(self):
        """HCE ACP with 0% adoption should use existing rates."""
        participants = [
            {"match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 3%
            {"match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 4%
        ]

        # No HCEs adopt mega-backdoor
        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=[],
            contribution_rate=Decimal("6.0")  # 6% rate doesn't matter if no adoption
        )
        assert hce_acp == Decimal("3.5")  # Average of 3% and 4%

    def test_calculate_hce_acp_full_adoption(self):
        """HCE ACP with 100% adoption should add simulated contributions."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 3% base
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 4% base
        ]

        # All HCEs adopt at 6% contribution rate
        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=["hce1", "hce2"],
            contribution_rate=Decimal("6.0")
        )
        # hce1: (300000 + 600000) / 10000000 = 9%
        # hce2: (400000 + 600000) / 10000000 = 10%
        # Average: 9.5%
        assert hce_acp == Decimal("9.5")

    def test_calculate_hce_acp_partial_adoption(self):
        """HCE ACP with partial adoption - only selected HCEs get contribution."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 3% base
            {"internal_id": "hce2", "match_cents": 400000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 4% base
        ]

        # Only hce1 adopts at 6%
        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=["hce1"],
            contribution_rate=Decimal("6.0")
        )
        # hce1: (300000 + 600000) / 10000000 = 9%
        # hce2: 400000 / 10000000 = 4% (no adoption)
        # Average: 6.5%
        assert hce_acp == Decimal("6.5")

    def test_calculate_hce_acp_excludes_nhce(self):
        """HCE ACP should exclude NHCE participants."""
        participants = [
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},  # 3%
            {"internal_id": "nhce1", "match_cents": 200000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},  # 4%
        ]

        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=[],
            contribution_rate=Decimal("6.0")
        )
        assert hce_acp == Decimal("3.0")  # Only HCE1's 3%


class TestIRSDualTest:
    """T019: Unit tests for IRS dual test (1.25x and +2.0)."""

    def test_apply_acp_test_125x_wins(self):
        """1.25x test wins when NHCE ACP is high (>8%)."""
        nhce_acp = Decimal("10.0")  # 10%
        # 1.25x = 12.5%
        # +2.0 = 12.0% (cap = 20.0%, so uncapped applies)
        # 1.25x wins (higher threshold is more favorable)

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("11.0")  # 11% - should pass
        )

        assert result.limit_125 == Decimal("12.5")
        assert result.limit_2pct_capped == Decimal("12.0")
        assert result.effective_limit == Decimal("12.5")
        assert result.limiting_test == "1.25x"
        assert result.binding_rule == "1.25x"
        assert result.result == "PASS"

    def test_apply_acp_test_plus2_wins(self):
        """'+2.0' test wins when NHCE ACP is low (<8%)."""
        nhce_acp = Decimal("4.0")  # 4%
        # 1.25x = 5.0%
        # +2.0 = 6.0% (cap = 8.0%, so uncapped applies)
        # +2.0 wins (higher threshold is more favorable)

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("5.5")  # 5.5% - should pass (under 6.0%)
        )

        assert result.effective_limit == Decimal("6.0")
        assert result.limiting_test == "+2.0"
        assert result.binding_rule == "2pct/2x"
        assert result.result == "PASS"

    def test_apply_acp_test_fail(self):
        """Test should fail when HCE ACP exceeds threshold."""
        nhce_acp = Decimal("4.0")  # 4%
        # Threshold = 6.0% (+2.0 wins)

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("7.0")  # 7% - exceeds 6.0% threshold
        )

        assert result.result == "FAIL"
        assert result.effective_limit == Decimal("6.0")

    def test_apply_acp_test_boundary_pass(self):
        """Test should pass when HCE ACP exactly equals threshold."""
        nhce_acp = Decimal("4.0")  # 4%

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("6.0")  # Exactly at threshold
        )

        assert result.result == "PASS"

    def test_apply_acp_test_zero_nhce_acp(self):
        """Zero NHCE ACP should cap +2.0% at 0.0%."""
        nhce_acp = Decimal("0.0")
        # 1.25x = 0.0%
        # +2.0 = 2.0% (cap = 0.0%, so capped)

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("1.5")
        )

        assert result.limit_2pct_capped == Decimal("0.0")
        assert result.effective_limit == Decimal("0.0")
        assert result.limiting_test == "1.25x"
        assert result.result == "FAIL"

    def test_apply_acp_test_crossover_point(self):
        """At NHCE ACP = 8%, both tests give same threshold (10%)."""
        nhce_acp = Decimal("8.0")
        # 1.25x = 10.0%
        # +2.0 = 10.0%
        # Either wins (implementation may choose 1.25x)

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("9.0")
        )

        assert result.threshold == Decimal("10.0")
        assert result.result == "PASS"

    def test_apply_acp_test_cap_at_2x(self):
        """Cap at 2x should reduce the +2.0 limit when NHCE ACP is low."""
        nhce_acp = Decimal("1.0")  # 1%
        # 1.25x = 1.25%
        # +2.0 = 3.0% (uncapped)
        # 2x cap = 2.0% -> capped +2.0 = 2.0%

        result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("1.5")
        )

        assert result.limit_2pct_uncapped == Decimal("3.0")
        assert result.cap_2x == Decimal("2.0")
        assert result.limit_2pct_capped == Decimal("2.0")
        assert result.effective_limit == Decimal("2.0")
        assert result.binding_rule == "2pct/2x"

    def test_margin_sign_matches_result(self):
        """Margin sign should align with PASS/FAIL determination."""
        nhce_acp = Decimal("4.0")  # Effective limit = 6.0%

        pass_result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("5.0")
        )
        fail_result = apply_acp_test(
            nhce_acp=nhce_acp,
            hce_acp=Decimal("6.5")
        )

        assert pass_result.result == "PASS"
        assert pass_result.margin > 0
        assert fail_result.result == "FAIL"
        assert fail_result.margin < 0


class TestMarginCalculation:
    """Tests for margin calculation."""

    def test_margin_positive_for_pass(self):
        """Margin should be positive when test passes (room to spare)."""
        margin = calculate_margin(
            threshold=Decimal("6.0"),
            hce_acp=Decimal("5.0")
        )
        assert margin == Decimal("1.0")

    def test_margin_negative_for_fail(self):
        """Margin should be negative when test fails (exceeded by)."""
        margin = calculate_margin(
            threshold=Decimal("6.0"),
            hce_acp=Decimal("7.5")
        )
        assert margin == Decimal("-1.5")

    def test_margin_zero_at_boundary(self):
        """Margin should be zero when exactly at threshold."""
        margin = calculate_margin(
            threshold=Decimal("6.0"),
            hce_acp=Decimal("6.0")
        )
        assert margin == Decimal("0")


class TestACPResultIntegration:
    """Integration tests for complete ACP test workflow."""

    def test_full_acp_test_pass_scenario(self):
        """Complete ACP test should pass for conservative scenario."""
        # Setup: Low NHCE ACP, low HCE adoption
        participants = [
            # NHCEs with 3% average ACP
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            # HCE with 3% base
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        nhce_acp = calculate_nhce_acp(participants)
        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=[],  # No adoption
            contribution_rate=Decimal("6.0")
        )
        result = apply_acp_test(nhce_acp=nhce_acp, hce_acp=hce_acp)

        assert nhce_acp == Decimal("3.0")
        assert hce_acp == Decimal("3.0")
        assert result.result == "PASS"

    def test_full_acp_test_fail_scenario(self):
        """Complete ACP test should fail for aggressive scenario."""
        # Setup: Low NHCE ACP, full HCE adoption with high contribution
        participants = [
            # NHCEs with 3% average ACP
            {"internal_id": "nhce1", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            {"internal_id": "nhce2", "match_cents": 150000, "after_tax_cents": 0, "compensation_cents": 5000000, "is_hce": False},
            # HCE with 3% base
            {"internal_id": "hce1", "match_cents": 300000, "after_tax_cents": 0, "compensation_cents": 10000000, "is_hce": True},
        ]

        nhce_acp = calculate_nhce_acp(participants)
        hce_acp = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=["hce1"],  # Full adoption
            contribution_rate=Decimal("10.0")  # 10% contribution
        )
        result = apply_acp_test(nhce_acp=nhce_acp, hce_acp=hce_acp)

        assert nhce_acp == Decimal("3.0")
        # HCE: (300000 + 1000000) / 10000000 = 13%
        assert hce_acp == Decimal("13.0")
        # Threshold: 3% + 2.0% = 5.0% (+2.0 wins)
        assert result.threshold == Decimal("5.0")
        assert result.result == "FAIL"


class TestEdgeCases:
    """T086-T088: Edge case handling tests."""

    def test_zero_hces_returns_zero_hce_acp(self):
        """T086: Zero HCEs should return zero HCE ACP."""
        from app.services.acp_calculator import calculate_hce_acp
        from decimal import Decimal

        participants = [
            {"internal_id": "nhce1", "is_hce": False, "match_cents": 1000, "after_tax_cents": 0, "compensation_cents": 50000},
            {"internal_id": "nhce2", "is_hce": False, "match_cents": 2000, "after_tax_cents": 0, "compensation_cents": 60000},
        ]

        result = calculate_hce_acp(
            participants=participants,
            adopting_hce_ids=[],
            contribution_rate=Decimal("6.0")
        )

        assert result == Decimal("0")

    def test_zero_nhce_contribution_gives_zero_acp(self):
        """T087: Zero NHCE contributions should give NHCE ACP = 0."""
        from app.services.acp_calculator import calculate_nhce_acp

        participants = [
            {"internal_id": "nhce1", "is_hce": False, "match_cents": 0, "after_tax_cents": 0, "compensation_cents": 50000},
            {"internal_id": "nhce2", "is_hce": False, "match_cents": 0, "after_tax_cents": 0, "compensation_cents": 60000},
        ]

        result = calculate_nhce_acp(participants)

        assert result == 0

    def test_zero_nhce_acp_uses_plus2_threshold(self):
        """T087: Zero NHCE ACP should cap +2.0% threshold at 0.0%."""
        from app.services.acp_calculator import apply_acp_test
        from decimal import Decimal

        result = apply_acp_test(
            nhce_acp=Decimal("0"),
            hce_acp=Decimal("1.5")
        )

        assert result.limit_2pct_capped == Decimal("0")
        assert result.effective_limit == Decimal("0")
        assert result.limiting_test == "1.25x"
        assert result.result == "FAIL"

    def test_hce_acp_exceeds_threshold_returns_fail(self):
        """Test that HCE ACP exceeding threshold returns FAIL."""
        from app.services.acp_calculator import apply_acp_test
        from decimal import Decimal

        result = apply_acp_test(
            nhce_acp=Decimal("1.0"),  # Threshold = 3.0 (+2.0 wins)
            hce_acp=Decimal("3.5")    # Above threshold
        )

        assert result.result == "FAIL"
        assert result.margin < 0


class TestIRC415cLimitWarning:
    """T088: IRC 415(c) limit warning tests."""

    def test_under_415c_limit_no_warning(self):
        """Contributions under 415(c) limit should not warn."""
        from app.services.acp_calculator import check_415c_limit

        result = check_415c_limit(
            compensation_cents=20000000,  # $200,000
            deferral_cents=2300000,        # $23,000
            match_cents=800000,            # $8,000
            after_tax_cents=500000,        # $5,000
            simulated_after_tax_cents=1000000,  # $10,000
            plan_year=2025
        )

        # Total = $46,000, under any reasonable 415(c) limit
        assert not result["exceeds_limit"]
        assert result["warning_message"] is None

    def test_over_415c_limit_warns(self):
        """Contributions over 415(c) limit should warn but not block."""
        from app.services.acp_calculator import check_415c_limit

        result = check_415c_limit(
            compensation_cents=20000000,  # $200,000
            deferral_cents=2300000,        # $23,000
            match_cents=1000000,           # $10,000
            after_tax_cents=2000000,       # $20,000
            simulated_after_tax_cents=3000000,  # $30,000 more
            plan_year=2025
        )

        # Total = $83,000, over 2025 limit of $70,000
        assert result["exceeds_limit"]
        assert result["warning_message"] is not None
        assert "exceed" in result["warning_message"].lower()
        assert "415(c)" in result["warning_message"]

    def test_returns_contribution_totals(self):
        """Result should include contribution totals."""
        from app.services.acp_calculator import check_415c_limit

        result = check_415c_limit(
            compensation_cents=10000000,
            deferral_cents=1000000,
            match_cents=500000,
            after_tax_cents=200000,
            simulated_after_tax_cents=300000,
            plan_year=2025
        )

        assert "total_contributions" in result
        assert "limit" in result
        assert result["total_contributions"] == 2000000  # Sum of contributions
