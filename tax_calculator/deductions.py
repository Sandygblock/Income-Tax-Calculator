"""
Deductions and exemptions applicable under the Old Tax Regime.

Most deductions are NOT available under the New Tax Regime (except
standard deduction of ₹75,000 which is handled in slabs.py).
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Section-wise deduction limits
# ---------------------------------------------------------------------------
SEC_80C_LIMIT: int = 150_000        # ₹1,50,000
SEC_80CCD1B_LIMIT: int = 50_000     # ₹50,000 (additional NPS)
SEC_80D_SELF_LIMIT: int = 25_000    # ₹25,000 (self & family)
SEC_80D_PARENTS_LIMIT: int = 25_000 # ₹25,000 (non-senior parents)
SEC_80D_PARENTS_SR_LIMIT: int = 50_000  # ₹50,000 (senior citizen parents)
SEC_80TTA_LIMIT: int = 10_000       # ₹10,000 (savings interest, non-senior)
SEC_80TTB_LIMIT: int = 50_000       # ₹50,000 (interest, senior citizens)
SEC_24B_LIMIT: int = 200_000        # ₹2,00,000 (home loan interest)
SEC_80G_QUALIFYING_LIMIT_PCT: float = 0.10  # 10% of adjusted gross income


@dataclass
class SalaryComponents:
    """Breakdown of salary/wage income."""

    basic_salary: float = 0.0
    hra_received: float = 0.0        # HRA received from employer
    da: float = 0.0                  # Dearness Allowance (forms part of salary)
    special_allowance: float = 0.0
    other_allowances: float = 0.0
    # For HRA exemption calculation
    rent_paid: float = 0.0           # Annual rent paid
    is_metro: bool = False           # Living in metro city (Mumbai/Delhi/Chennai/Kolkata)

    @property
    def gross_salary(self) -> float:
        """Total salary before standard deduction."""
        return (
            self.basic_salary
            + self.hra_received
            + self.da
            + self.special_allowance
            + self.other_allowances
        )

    def hra_exemption(self) -> float:
        """
        Calculate HRA exemption u/s 10(13A).

        Exemption is the MINIMUM of:
        1. Actual HRA received
        2. 50% of (Basic + DA) for metro / 40% for non-metro
        3. Rent paid – 10% of (Basic + DA)
        """
        if self.hra_received <= 0 or self.rent_paid <= 0:
            return 0.0

        basic_da = self.basic_salary + self.da
        pct = 0.50 if self.is_metro else 0.40
        limit1 = self.hra_received
        limit2 = basic_da * pct
        limit3 = max(0.0, self.rent_paid - 0.10 * basic_da)
        return min(limit1, limit2, limit3)


@dataclass
class HousePropertyIncome:
    """Income / Loss from house property."""

    annual_rent_received: float = 0.0   # Gross annual rent
    municipal_taxes_paid: float = 0.0   # Municipal taxes paid by owner
    home_loan_interest: float = 0.0     # Annual home loan interest paid
    is_self_occupied: bool = False       # True if self-occupied property

    def net_annual_value(self) -> float:
        """NAV = Annual rent – Municipal taxes (0 for self-occupied)."""
        if self.is_self_occupied:
            return 0.0
        return max(0.0, self.annual_rent_received - self.municipal_taxes_paid)

    def standard_deduction_30pct(self) -> float:
        """30% standard deduction on NAV u/s 24(a)."""
        return self.net_annual_value() * 0.30

    def interest_deduction(self) -> float:
        """
        Deduction for home loan interest u/s 24(b).
        Self-occupied: capped at ₹2,00,000.
        Let-out: no cap (full interest allowed), but loss set-off capped at ₹2L against salary.
        """
        if self.is_self_occupied:
            return min(self.home_loan_interest, SEC_24B_LIMIT)
        return self.home_loan_interest

    def income_from_house_property(self) -> float:
        """
        Net income (or loss) from house property.
        Loss is expressed as a negative value.
        """
        nav = self.net_annual_value()
        std_ded = self.standard_deduction_30pct()
        interest_ded = self.interest_deduction()
        return nav - std_ded - interest_ded


@dataclass
class CapitalGains:
    """Capital gains income."""

    short_term_15pct: float = 0.0   # STCG taxed at flat 15% (equity STT paid)
    short_term_normal: float = 0.0  # STCG taxed at normal slab rates
    long_term_10pct: float = 0.0    # LTCG taxed at flat 10% (equity > ₹1.25L exempt)
    long_term_20pct: float = 0.0    # LTCG taxed at 20% with indexation (other assets)

    LTCG_EQUITY_EXEMPTION: int = 125_000  # ₹1,25,000 exemption on LTCG from equity

    def taxable_ltcg_10pct(self) -> float:
        """LTCG on equity after ₹1,25,000 exemption."""
        return max(0.0, self.long_term_10pct - self.LTCG_EQUITY_EXEMPTION)


@dataclass
class Deductions:
    """All deductions/investments under the Old Tax Regime."""

    # Section 80C
    ppf: float = 0.0
    elss: float = 0.0
    lic_premium: float = 0.0
    epf: float = 0.0
    nsc: float = 0.0
    home_loan_principal: float = 0.0
    tuition_fees: float = 0.0
    other_80c: float = 0.0

    # Section 80CCD(1B) – additional NPS over 80C
    nps_additional: float = 0.0

    # Section 80D – Health Insurance
    health_insurance_self: float = 0.0       # self + family
    health_insurance_parents: float = 0.0    # parents
    parents_senior_citizen: bool = False      # True if parents are senior citizens

    # Section 80E – Education Loan Interest
    education_loan_interest: float = 0.0

    # Section 80G – Donations (100% deductible portion)
    donations_80g: float = 0.0

    # Section 80TTA / 80TTB – Savings/deposit interest
    savings_interest: float = 0.0
    is_senior_citizen: bool = False

    def sec_80c_total(self) -> float:
        """Total eligible 80C investments (capped at ₹1,50,000)."""
        total = (
            self.ppf + self.elss + self.lic_premium + self.epf + self.nsc
            + self.home_loan_principal + self.tuition_fees + self.other_80c
        )
        return min(total, SEC_80C_LIMIT)

    def sec_80ccd1b(self) -> float:
        """Additional NPS contribution capped at ₹50,000."""
        return min(self.nps_additional, SEC_80CCD1B_LIMIT)

    def sec_80d(self) -> float:
        """Health insurance deduction (self + parents, with senior citizen limits)."""
        self_ded = min(self.health_insurance_self, SEC_80D_SELF_LIMIT)
        parents_limit = SEC_80D_PARENTS_SR_LIMIT if self.parents_senior_citizen else SEC_80D_PARENTS_LIMIT
        parents_ded = min(self.health_insurance_parents, parents_limit)
        return self_ded + parents_ded

    def sec_80e(self) -> float:
        """Education loan interest – no upper limit."""
        return max(0.0, self.education_loan_interest)

    def sec_80g(self) -> float:
        """Donations u/s 80G (100% deductible portion entered by user)."""
        return max(0.0, self.donations_80g)

    def sec_80tta_ttb(self) -> float:
        """Savings/deposit interest deduction."""
        if self.is_senior_citizen:
            return min(self.savings_interest, SEC_80TTB_LIMIT)
        return min(self.savings_interest, SEC_80TTA_LIMIT)

    def total_deductions(self) -> float:
        """Sum of all Chapter VI-A deductions."""
        return (
            self.sec_80c_total()
            + self.sec_80ccd1b()
            + self.sec_80d()
            + self.sec_80e()
            + self.sec_80g()
            + self.sec_80tta_ttb()
        )
