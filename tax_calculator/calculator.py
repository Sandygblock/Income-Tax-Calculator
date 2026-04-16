"""
Core tax calculation engine.

Handles:
- Gross income aggregation across all heads
- Standard deduction
- Chapter VI-A deductions (Old Regime)
- Slab-wise tax computation
- Capital gains tax at special rates
- Surcharge with marginal relief
- Health & Education Cess (4%)
- Section 87A rebate (with marginal relief for New Regime)
- Side-by-side Old vs New regime comparison
"""

from dataclasses import dataclass, field
from typing import Optional

from .deductions import (
    Deductions,
    SalaryComponents,
    HousePropertyIncome,
    CapitalGains,
)
from .slabs import (
    OldRegimeSlabs,
    NewRegimeSlabs,
    SURCHARGE_RATES,
    CESS_RATE,
    _compute_slab_tax,
    NEW_REGIME_SLABS,
)


# ---------------------------------------------------------------------------
# Data classes for input
# ---------------------------------------------------------------------------

@dataclass
class IncomeInput:
    """All income sources provided by the user."""

    salary: SalaryComponents = field(default_factory=SalaryComponents)
    business_income: float = 0.0
    house_property: HousePropertyIncome = field(default_factory=HousePropertyIncome)
    capital_gains: CapitalGains = field(default_factory=CapitalGains)
    other_income: float = 0.0   # Interest, dividends, etc.
    is_salaried: bool = True     # Whether to apply standard deduction


# ---------------------------------------------------------------------------
# Tax computation result
# ---------------------------------------------------------------------------

@dataclass
class TaxResult:
    """Detailed tax computation result for a single regime."""

    regime: str = ""

    # Income heads
    gross_salary: float = 0.0
    hra_exemption: float = 0.0
    standard_deduction: float = 0.0
    business_income: float = 0.0
    house_property_income: float = 0.0
    capital_gains_normal: float = 0.0   # CG taxed at slab rates
    capital_gains_special: float = 0.0  # CG taxed at special rates (handled separately)
    other_income: float = 0.0

    # Deductions
    chapter_vi_a: float = 0.0

    # Tax computation
    gross_total_income: float = 0.0
    taxable_income: float = 0.0          # After deductions
    tax_on_normal_income: float = 0.0
    tax_on_special_cg: float = 0.0       # CG special rate tax
    total_tax_before_rebate: float = 0.0
    rebate_87a: float = 0.0
    tax_after_rebate: float = 0.0
    surcharge: float = 0.0
    cess: float = 0.0
    total_tax: float = 0.0               # Final tax payable

    # Deduction breakdown (old regime only)
    deduction_breakdown: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Main calculator class
# ---------------------------------------------------------------------------

class TaxCalculator:
    """Compute Indian income tax under Old and New regimes."""

    def __init__(self, income: IncomeInput, deductions: Deductions) -> None:
        self.income = income
        self.deductions = deductions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_old_regime(self) -> TaxResult:
        """Compute tax under Old Tax Regime."""
        return self._compute(regime="old")

    def compute_new_regime(self) -> TaxResult:
        """Compute tax under New Tax Regime."""
        return self._compute(regime="new")

    def compare(self) -> tuple:
        """
        Return (old_result, new_result, recommended_regime).
        recommended_regime is 'old' or 'new'.
        """
        old = self.compute_old_regime()
        new = self.compute_new_regime()
        recommended = "old" if old.total_tax <= new.total_tax else "new"
        return old, new, recommended

    # ------------------------------------------------------------------
    # Internal computation
    # ------------------------------------------------------------------

    def _compute(self, regime: str) -> TaxResult:
        """Core computation for a given regime."""
        result = TaxResult(regime=regime)
        inc = self.income
        ded = self.deductions

        # ── Step 1: Salary income ──────────────────────────────────────
        result.gross_salary = inc.salary.gross_salary

        if regime == "old":
            result.hra_exemption = inc.salary.hra_exemption()
        else:
            result.hra_exemption = 0.0  # HRA exemption not available in new regime

        salary_after_hra = result.gross_salary - result.hra_exemption

        if inc.is_salaried:
            if regime == "new":
                result.standard_deduction = NewRegimeSlabs.standard_deduction
            else:
                result.standard_deduction = OldRegimeSlabs.standard_deduction
        result.standard_deduction = min(result.standard_deduction, salary_after_hra)

        net_salary = salary_after_hra - result.standard_deduction

        # ── Step 2: Business income ────────────────────────────────────
        result.business_income = inc.business_income

        # ── Step 3: House property income ─────────────────────────────
        hp_income = inc.house_property.income_from_house_property()
        # Loss from HP capped at ₹2L set-off against other heads
        if hp_income < 0:
            hp_income = max(hp_income, -200_000)
        result.house_property_income = hp_income

        # ── Step 4: Capital Gains ──────────────────────────────────────
        # STCG normal-rate portion goes into normal slab income
        result.capital_gains_normal = inc.capital_gains.short_term_normal
        # Special-rate CGs are computed separately
        stcg_15 = inc.capital_gains.short_term_15pct
        ltcg_10 = inc.capital_gains.taxable_ltcg_10pct()
        ltcg_20 = inc.capital_gains.long_term_20pct
        result.capital_gains_special = stcg_15 + ltcg_10 + ltcg_20

        # ── Step 5: Other income ───────────────────────────────────────
        result.other_income = inc.other_income

        # ── Step 6: Gross Total Income ────────────────────────────────
        result.gross_total_income = (
            net_salary
            + result.business_income
            + result.house_property_income
            + result.capital_gains_normal
            + result.other_income
        )
        result.gross_total_income = max(0.0, result.gross_total_income)

        # ── Step 7: Deductions (Chapter VI-A – old regime only) ────────
        if regime == "old":
            ded_breakdown = {
                "80C": ded.sec_80c_total(),
                "80CCD(1B)": ded.sec_80ccd1b(),
                "80D": ded.sec_80d(),
                "80E": ded.sec_80e(),
                "80G": ded.sec_80g(),
                "80TTA/TTB": ded.sec_80tta_ttb(),
            }
            result.deduction_breakdown = ded_breakdown
            result.chapter_vi_a = min(
                sum(ded_breakdown.values()),
                result.gross_total_income,  # cannot exceed GTI
            )
        else:
            result.chapter_vi_a = 0.0

        # ── Step 8: Taxable income ─────────────────────────────────────
        result.taxable_income = max(0.0, result.gross_total_income - result.chapter_vi_a)

        # ── Step 9: Tax on normal slab income ─────────────────────────
        if regime == "new":
            result.tax_on_normal_income = NewRegimeSlabs.compute_tax(result.taxable_income)
        else:
            result.tax_on_normal_income = OldRegimeSlabs.compute_tax(result.taxable_income)

        # ── Step 10: Tax on special-rate capital gains ─────────────────
        result.tax_on_special_cg = (
            stcg_15 * 0.15
            + ltcg_10 * 0.10
            + ltcg_20 * 0.20
        )

        result.total_tax_before_rebate = (
            result.tax_on_normal_income + result.tax_on_special_cg
        )

        # ── Step 11: Rebate u/s 87A ────────────────────────────────────
        result.rebate_87a = self._compute_87a_rebate(
            regime=regime,
            taxable_income=result.taxable_income,
            tax_before_rebate=result.total_tax_before_rebate,
        )
        result.tax_after_rebate = max(
            0.0, result.total_tax_before_rebate - result.rebate_87a
        )

        # ── Step 12: Surcharge ─────────────────────────────────────────
        total_income_for_surcharge = result.taxable_income + result.capital_gains_special
        result.surcharge = self._compute_surcharge(
            regime=regime,
            income=total_income_for_surcharge,
            tax=result.tax_after_rebate,
        )

        # ── Step 13: Cess ──────────────────────────────────────────────
        result.cess = (result.tax_after_rebate + result.surcharge) * CESS_RATE

        # ── Step 14: Total tax ─────────────────────────────────────────
        result.total_tax = result.tax_after_rebate + result.surcharge + result.cess

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_87a_rebate(
        regime: str,
        taxable_income: float,
        tax_before_rebate: float,
    ) -> float:
        """
        Compute Section 87A rebate.

        Old Regime: Full rebate (up to ₹12,500) if taxable income ≤ ₹5,00,000.
        New Regime: Full rebate if taxable income ≤ ₹12,00,000
                    (marginal relief: if income just above ₹12L, tax capped
                     so that tax = income – ₹12,00,000).
        """
        if regime == "old":
            if taxable_income <= OldRegimeSlabs.rebate_87a_limit:
                return min(tax_before_rebate, 12_500)
            return 0.0
        else:
            limit = NewRegimeSlabs.rebate_87a_limit  # ₹12,00,000
            if taxable_income <= limit:
                return tax_before_rebate  # full rebate → zero tax
            # Marginal relief: tax payable should not exceed (income – limit)
            excess = taxable_income - limit
            marginal_tax = min(tax_before_rebate, excess)
            return max(0.0, tax_before_rebate - marginal_tax)

    @staticmethod
    def _compute_surcharge(regime: str, income: float, tax: float) -> float:
        """
        Compute surcharge with marginal relief.

        Surcharge rates:
          >₹50L  → 10%
          >₹1Cr  → 15%
          >₹2Cr  → 25%
          >₹5Cr  → 37% (old regime only; new regime caps at 25%)
        """
        if income <= 50_00_000:
            return 0.0

        # Determine applicable surcharge rate
        rate = 0.0
        for threshold, sr in SURCHARGE_RATES:
            if income > threshold:
                rate = sr

        if regime == "new" and rate > NewRegimeSlabs.surcharge_cap:
            rate = NewRegimeSlabs.surcharge_cap

        surcharge = tax * rate

        # Marginal relief on surcharge:
        # Tax + surcharge should not exceed tax at the lower threshold + excess income above threshold
        prev_threshold = 50_00_000
        for threshold, sr in SURCHARGE_RATES:
            if income > threshold:
                prev_threshold = threshold
            else:
                break

        # Find the surcharge rate at prev_threshold (one band below)
        prev_rate = 0.0
        for threshold, sr in SURCHARGE_RATES:
            if prev_threshold > threshold:
                prev_rate = sr

        # Tax + surcharge at the lower boundary
        if regime == "new" and prev_rate > NewRegimeSlabs.surcharge_cap:
            prev_rate = NewRegimeSlabs.surcharge_cap

        tax_at_threshold = _compute_slab_tax(
            prev_threshold,
            NEW_REGIME_SLABS if regime == "new" else OldRegimeSlabs.slabs,
        )
        tax_plus_surcharge_at_threshold = tax_at_threshold * (1 + prev_rate)

        # Tax + proposed surcharge for current income
        tax_plus_surcharge = tax + surcharge

        # Apply marginal relief
        excess_income = income - prev_threshold
        if tax_plus_surcharge > tax_plus_surcharge_at_threshold + excess_income:
            surcharge = max(
                0.0,
                tax_plus_surcharge_at_threshold + excess_income - tax,
            )

        return surcharge
