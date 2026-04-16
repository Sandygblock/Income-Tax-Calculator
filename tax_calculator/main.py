"""
Interactive CLI for the Indian Income Tax Calculator.

Run:
    python -m tax_calculator.main
or:
    python tax_calculator/main.py
"""

import sys
from typing import Tuple

from .calculator import TaxCalculator, IncomeInput, TaxResult
from .deductions import (
    Deductions,
    SalaryComponents,
    HousePropertyIncome,
    CapitalGains,
)
from .utils import (
    format_inr,
    format_pct,
    divider,
    section_header,
    row,
    input_amount,
    input_yes_no,
    input_choice,
)


# ─────────────────────────────────────────────────────────────────────────────
# Welcome banner
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║      🇮🇳  Indian Income Tax Calculator – FY 2025-26          ║
║              (Assessment Year 2026-27)                       ║
╚══════════════════════════════════════════════════════════════╝
"""


# ─────────────────────────────────────────────────────────────────────────────
# Input collection helpers
# ─────────────────────────────────────────────────────────────────────────────

def collect_salary() -> SalaryComponents:
    print(section_header("SALARY / WAGE INCOME"))
    basic = input_amount("  Basic Salary (annual): ₹")
    hra = input_amount("  HRA received (annual): ₹")
    da = input_amount("  Dearness Allowance (DA) (annual): ₹")
    special = input_amount("  Special Allowance (annual): ₹")
    other = input_amount("  Other Allowances (annual): ₹")

    rent_paid = 0.0
    is_metro = False
    if hra > 0:
        rent_paid = input_amount("  Annual Rent Paid (for HRA exemption, 0 if not paying rent): ₹")
        if rent_paid > 0:
            is_metro = input_yes_no("  Do you live in a metro city (Mumbai/Delhi/Chennai/Kolkata)?")

    return SalaryComponents(
        basic_salary=basic,
        hra_received=hra,
        da=da,
        special_allowance=special,
        other_allowances=other,
        rent_paid=rent_paid,
        is_metro=is_metro,
    )


def collect_house_property() -> HousePropertyIncome:
    print(section_header("INCOME FROM HOUSE PROPERTY"))
    has_property = input_yes_no("  Do you have any house property income / home loan?", default=False)
    if not has_property:
        return HousePropertyIncome()

    is_self_occupied = input_yes_no("  Is the property self-occupied?", default=True)
    annual_rent = 0.0
    municipal_tax = 0.0
    if not is_self_occupied:
        annual_rent = input_amount("  Annual Rent Received: ₹")
        municipal_tax = input_amount("  Municipal Taxes Paid (annual): ₹")

    interest = input_amount("  Home Loan Interest Paid (annual): ₹")

    return HousePropertyIncome(
        annual_rent_received=annual_rent,
        municipal_taxes_paid=municipal_tax,
        home_loan_interest=interest,
        is_self_occupied=is_self_occupied,
    )


def collect_capital_gains() -> CapitalGains:
    print(section_header("CAPITAL GAINS"))
    has_cg = input_yes_no("  Do you have any capital gains?", default=False)
    if not has_cg:
        return CapitalGains()

    print("  Short-Term Capital Gains:")
    stcg_15 = input_amount("    STCG on Equity/MF (STT paid) – taxed at 15%: ₹")
    stcg_normal = input_amount("    Other STCG (taxed at normal slab rates): ₹")

    print("  Long-Term Capital Gains:")
    ltcg_10 = input_amount("    LTCG on Equity/MF (STT paid) – ₹1.25L exempt, balance at 10%: ₹")
    ltcg_20 = input_amount("    Other LTCG with indexation – taxed at 20%: ₹")

    return CapitalGains(
        short_term_15pct=stcg_15,
        short_term_normal=stcg_normal,
        long_term_10pct=ltcg_10,
        long_term_20pct=ltcg_20,
    )


def collect_other_income() -> float:
    print(section_header("INCOME FROM OTHER SOURCES"))
    interest = input_amount("  Interest Income (FD, savings, etc.): ₹")
    dividends = input_amount("  Dividend Income: ₹")
    others = input_amount("  Other Income: ₹")
    return interest + dividends + others


def collect_business_income() -> float:
    print(section_header("INCOME FROM BUSINESS / PROFESSION"))
    return input_amount("  Net Profit from Business/Profession: ₹")


def collect_deductions(is_senior_citizen: bool) -> Deductions:
    print(section_header("DEDUCTIONS (Old Regime – Chapter VI-A)"))
    print("  (These are used only for Old Regime calculation)")

    print("\n  Section 80C (Max ₹1,50,000) – PPF / ELSS / LIC / EPF / NSC etc.")
    ppf = input_amount("    PPF: ₹")
    elss = input_amount("    ELSS / Tax-saving Mutual Funds: ₹")
    lic = input_amount("    LIC Premium: ₹")
    epf = input_amount("    EPF (employee contribution): ₹")
    nsc = input_amount("    NSC: ₹")
    principal = input_amount("    Home Loan Principal Repayment: ₹")
    tuition = input_amount("    Tuition Fees (children): ₹")
    other_80c = input_amount("    Other 80C investments: ₹")

    print("\n  Section 80CCD(1B) – Additional NPS (Max ₹50,000)")
    nps = input_amount("    Additional NPS contribution: ₹")

    print("\n  Section 80D – Health Insurance Premium")
    health_self = input_amount("    Self & Family (Max ₹25,000): ₹")
    health_parents = input_amount("    Parents' Health Insurance: ₹")
    parents_sr = input_yes_no("    Are your parents Senior Citizens (>60 yrs)?", default=False)

    print("\n  Section 80E – Education Loan Interest (No limit)")
    edu_interest = input_amount("    Education Loan Interest Paid: ₹")

    print("\n  Section 80G – Donations (100% deductible portion)")
    donations = input_amount("    Eligible Donations: ₹")

    print("\n  Section 80TTA / 80TTB – Interest Income")
    savings_int = input_amount("    Savings/Deposit Interest (for deduction claim): ₹")

    return Deductions(
        ppf=ppf, elss=elss, lic_premium=lic, epf=epf, nsc=nsc,
        home_loan_principal=principal, tuition_fees=tuition, other_80c=other_80c,
        nps_additional=nps,
        health_insurance_self=health_self,
        health_insurance_parents=health_parents,
        parents_senior_citizen=parents_sr,
        education_loan_interest=edu_interest,
        donations_80g=donations,
        savings_interest=savings_int,
        is_senior_citizen=is_senior_citizen,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Result display
# ─────────────────────────────────────────────────────────────────────────────

def display_result(result: TaxResult) -> None:
    """Print a detailed tax computation breakdown."""
    label = "NEW REGIME" if result.regime == "new" else "OLD REGIME"
    print(section_header(f"TAX COMPUTATION – {label}"))

    print(f"\n  {'Income Head':<38} {'Amount':>20}")
    print(f"  {divider('─', 58)}")

    if result.gross_salary:
        print(row("Gross Salary", format_inr(result.gross_salary)))
    if result.hra_exemption:
        print(row("  Less: HRA Exemption", f"({format_inr(result.hra_exemption)})"))
    if result.standard_deduction:
        print(row("  Less: Standard Deduction", f"({format_inr(result.standard_deduction)})"))
    if result.business_income:
        print(row("Business / Profession Income", format_inr(result.business_income)))
    if result.house_property_income:
        print(row("House Property Income / (Loss)", format_inr(result.house_property_income)))
    if result.capital_gains_normal:
        print(row("Capital Gains (Normal Rate)", format_inr(result.capital_gains_normal)))
    if result.capital_gains_special:
        print(row("Capital Gains (Special Rate)", format_inr(result.capital_gains_special)))
    if result.other_income:
        print(row("Other Sources", format_inr(result.other_income)))

    print(f"  {divider('─', 58)}")
    print(row("Gross Total Income", format_inr(result.gross_total_income)))

    if result.chapter_vi_a:
        print(f"\n  {'Deductions (Chapter VI-A)':<38}")
        for sec, amt in result.deduction_breakdown.items():
            if amt:
                print(row(f"    Section {sec}", format_inr(amt)))
        print(f"  {divider('─', 58)}")
        print(row("Total Deductions", f"({format_inr(result.chapter_vi_a)})"))

    print(f"  {divider('─', 58)}")
    print(row("Taxable Income", format_inr(result.taxable_income)))
    print()

    print(f"  {'Tax Computation':<38}")
    print(f"  {divider('─', 58)}")
    print(row("Tax on Normal Income", format_inr(result.tax_on_normal_income)))
    if result.tax_on_special_cg:
        print(row("Tax on Special Rate CG", format_inr(result.tax_on_special_cg)))
    print(row("Total Tax (before rebate)", format_inr(result.total_tax_before_rebate)))
    if result.rebate_87a:
        print(row("  Less: Rebate u/s 87A", f"({format_inr(result.rebate_87a)})"))
    print(row("Tax after Rebate", format_inr(result.tax_after_rebate)))
    if result.surcharge:
        print(row("Add: Surcharge", format_inr(result.surcharge)))
    print(row("Add: Health & Education Cess (4%)", format_inr(result.cess)))
    print(f"  {divider('═', 58)}")
    print(row("TOTAL TAX PAYABLE", format_inr(result.total_tax)))
    print(f"  {divider('═', 58)}")


def display_comparison(old: TaxResult, new: TaxResult, recommended: str) -> None:
    """Display side-by-side comparison and recommendation."""
    print(section_header("COMPARISON: OLD vs NEW REGIME"))

    w = 60
    print(f"\n  {'':30} {'OLD REGIME':>13} {'NEW REGIME':>13}")
    print(f"  {divider('─', 56)}")

    def cmp_row(label: str, old_val: float, new_val: float) -> None:
        marker_old = " ◀" if old_val < new_val and old_val >= 0 else "  "
        marker_new = " ◀" if new_val < old_val and new_val >= 0 else "  "
        print(
            f"  {label:<30} {format_inr(old_val):>13}{marker_old[:1]}"
            f"  {format_inr(new_val):>13}{marker_new[:1]}"
        )

    cmp_row("Gross Total Income", old.gross_total_income, new.gross_total_income)
    cmp_row("Deductions", old.chapter_vi_a, new.chapter_vi_a)
    cmp_row("Taxable Income", old.taxable_income, new.taxable_income)
    cmp_row("Tax (before rebate)", old.total_tax_before_rebate, new.total_tax_before_rebate)
    cmp_row("Rebate u/s 87A", old.rebate_87a, new.rebate_87a)
    cmp_row("Surcharge", old.surcharge, new.surcharge)
    cmp_row("Cess (4%)", old.cess, new.cess)
    print(f"  {divider('═', 56)}")
    cmp_row("TOTAL TAX PAYABLE", old.total_tax, new.total_tax)
    print(f"  {divider('═', 56)}")

    savings = abs(old.total_tax - new.total_tax)
    better = "OLD REGIME" if recommended == "old" else "NEW REGIME"
    print(f"\n  ✅ Recommendation: Go with the {better}")
    if savings > 0:
        print(f"     You save {format_inr(savings)} by choosing the {better}.")
    else:
        print("     Both regimes result in the same tax liability.")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)
    print("  Enter your income and investment details below.")
    print("  Press Enter to skip any field (defaults to 0).\n")

    # ── Personal details ───────────────────────────────────────────────
    print(section_header("PERSONAL DETAILS"))
    is_senior = input_yes_no("  Are you a Senior Citizen (age 60–80)?", default=False)
    is_super_senior = False
    if is_senior:
        is_super_senior = input_yes_no("  Are you a Super Senior Citizen (age > 80)?", default=False)
    is_salaried = input_yes_no("  Are you a salaried employee?", default=True)

    # ── Income inputs ──────────────────────────────────────────────────
    salary = SalaryComponents()
    if is_salaried:
        salary = collect_salary()

    business = collect_business_income()
    house_property = collect_house_property()
    capital_gains = collect_capital_gains()
    other_income = collect_other_income()

    # ── Deductions ─────────────────────────────────────────────────────
    deductions = collect_deductions(is_senior_citizen=is_senior or is_super_senior)

    # ── Compute ────────────────────────────────────────────────────────
    income_input = IncomeInput(
        salary=salary,
        business_income=business,
        house_property=house_property,
        capital_gains=capital_gains,
        other_income=other_income,
        is_salaried=is_salaried,
    )

    calculator = TaxCalculator(income=income_input, deductions=deductions)
    old_result, new_result, recommended = calculator.compare()

    # ── Display results ────────────────────────────────────────────────
    display_result(old_result)
    display_result(new_result)
    display_comparison(old_result, new_result, recommended)

    # ── Ask to recalculate ─────────────────────────────────────────────
    again = input_yes_no("  Would you like to recalculate?", default=False)
    if again:
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Exiting. Goodbye! 👋\n")
        sys.exit(0)
