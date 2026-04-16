"""Unit tests for the Indian Income Tax Calculator core logic."""

import unittest

from tax_calculator.slabs import (
    OldRegimeSlabs,
    NewRegimeSlabs,
    _compute_slab_tax,
    OLD_REGIME_SLABS,
    NEW_REGIME_SLABS,
)
from tax_calculator.deductions import (
    Deductions,
    SalaryComponents,
    HousePropertyIncome,
    CapitalGains,
)
from tax_calculator.calculator import TaxCalculator, IncomeInput
from tax_calculator.utils import format_inr


# ─────────────────────────────────────────────────────────────────────────────
# Slab tax tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSlabTax(unittest.TestCase):

    # Old regime
    def test_old_zero_income(self):
        self.assertEqual(OldRegimeSlabs.compute_tax(0), 0.0)

    def test_old_below_basic_exemption(self):
        self.assertEqual(OldRegimeSlabs.compute_tax(200_000), 0.0)

    def test_old_at_basic_exemption(self):
        self.assertEqual(OldRegimeSlabs.compute_tax(250_000), 0.0)

    def test_old_5pct_slab(self):
        # ₹3,00,000 → 5% on ₹50,000 = ₹2,500
        self.assertAlmostEqual(OldRegimeSlabs.compute_tax(300_000), 2_500.0)

    def test_old_at_5lakh(self):
        # 5% on ₹2,50,000 = ₹12,500
        self.assertAlmostEqual(OldRegimeSlabs.compute_tax(500_000), 12_500.0)

    def test_old_20pct_slab(self):
        # 5% on ₹2,50,000 = ₹12,500 + 20% on ₹1,00,000 = ₹20,000 → ₹32,500
        self.assertAlmostEqual(OldRegimeSlabs.compute_tax(600_000), 32_500.0)

    def test_old_30pct_slab(self):
        # 5% on ₹2.5L = 12,500 + 20% on ₹5L = 1,00,000 + 30% on ₹1L = 30,000 → ₹1,42,500
        self.assertAlmostEqual(OldRegimeSlabs.compute_tax(1_100_000), 142_500.0)

    # New regime
    def test_new_zero_income(self):
        self.assertEqual(NewRegimeSlabs.compute_tax(0), 0.0)

    def test_new_below_exemption(self):
        self.assertEqual(NewRegimeSlabs.compute_tax(400_000), 0.0)

    def test_new_5pct_slab(self):
        # 5% on ₹1,00,000 = ₹5,000
        self.assertAlmostEqual(NewRegimeSlabs.compute_tax(500_000), 5_000.0)

    def test_new_at_8lakh(self):
        # 5% on ₹4,00,000 = ₹20,000
        self.assertAlmostEqual(NewRegimeSlabs.compute_tax(800_000), 20_000.0)

    def test_new_10pct_slab(self):
        # 5% on 4L = 20,000 + 10% on 2L = 20,000 → 40,000
        self.assertAlmostEqual(NewRegimeSlabs.compute_tax(1_000_000), 40_000.0)

    def test_new_at_12lakh(self):
        # 5% on 4L = 20,000 + 10% on 4L = 40,000 → 60,000
        self.assertAlmostEqual(NewRegimeSlabs.compute_tax(1_200_000), 60_000.0)


# ─────────────────────────────────────────────────────────────────────────────
# Deduction tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDeductions(unittest.TestCase):

    def test_80c_capped_at_1_5_lakh(self):
        d = Deductions(ppf=100_000, elss=100_000)
        self.assertEqual(d.sec_80c_total(), 150_000)

    def test_80c_below_limit(self):
        d = Deductions(ppf=50_000, elss=30_000)
        self.assertEqual(d.sec_80c_total(), 80_000)

    def test_80ccd1b_capped(self):
        d = Deductions(nps_additional=80_000)
        self.assertEqual(d.sec_80ccd1b(), 50_000)

    def test_80d_non_senior_parents(self):
        d = Deductions(health_insurance_self=20_000, health_insurance_parents=30_000, parents_senior_citizen=False)
        # self capped at 25,000 → 20,000; parents capped at 25,000 → 25,000
        self.assertEqual(d.sec_80d(), 45_000)

    def test_80d_senior_parents(self):
        d = Deductions(health_insurance_self=25_000, health_insurance_parents=50_000, parents_senior_citizen=True)
        # self → 25,000; parents → 50,000
        self.assertEqual(d.sec_80d(), 75_000)

    def test_80e_no_limit(self):
        d = Deductions(education_loan_interest=200_000)
        self.assertEqual(d.sec_80e(), 200_000)

    def test_80tta_capped(self):
        d = Deductions(savings_interest=15_000, is_senior_citizen=False)
        self.assertEqual(d.sec_80tta_ttb(), 10_000)

    def test_80ttb_senior(self):
        d = Deductions(savings_interest=60_000, is_senior_citizen=True)
        self.assertEqual(d.sec_80tta_ttb(), 50_000)

    def test_total_deductions(self):
        d = Deductions(
            ppf=150_000,
            nps_additional=50_000,
            health_insurance_self=25_000,
        )
        expected = 150_000 + 50_000 + 25_000
        self.assertEqual(d.total_deductions(), expected)


# ─────────────────────────────────────────────────────────────────────────────
# HRA exemption tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHRAExemption(unittest.TestCase):

    def test_hra_metro_limit_by_basic(self):
        s = SalaryComponents(basic_salary=600_000, hra_received=300_000, da=0, rent_paid=250_000, is_metro=True)
        # limit1 = 300,000; limit2 = 50% * 600,000 = 300,000; limit3 = 250,000 - 60,000 = 190,000
        self.assertAlmostEqual(s.hra_exemption(), 190_000.0)

    def test_hra_non_metro(self):
        s = SalaryComponents(basic_salary=500_000, hra_received=200_000, da=0, rent_paid=180_000, is_metro=False)
        # limit1 = 200,000; limit2 = 40% * 500,000 = 200,000; limit3 = 180,000 - 50,000 = 130,000
        self.assertAlmostEqual(s.hra_exemption(), 130_000.0)

    def test_hra_no_rent_paid(self):
        s = SalaryComponents(basic_salary=600_000, hra_received=200_000, rent_paid=0)
        self.assertEqual(s.hra_exemption(), 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# House property tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHouseProperty(unittest.TestCase):

    def test_self_occupied_loss(self):
        hp = HousePropertyIncome(home_loan_interest=200_000, is_self_occupied=True)
        # NAV = 0, no 30% deduction, interest capped at ₹2L
        self.assertAlmostEqual(hp.income_from_house_property(), -200_000.0)

    def test_let_out_positive(self):
        hp = HousePropertyIncome(annual_rent_received=300_000, municipal_taxes_paid=20_000,
                                  home_loan_interest=50_000, is_self_occupied=False)
        nav = 300_000 - 20_000  # 280,000
        std_ded = nav * 0.30     # 84,000
        # interest = 50,000
        expected = nav - std_ded - 50_000  # 280,000 - 84,000 - 50,000 = 146,000
        self.assertAlmostEqual(hp.income_from_house_property(), expected)


# ─────────────────────────────────────────────────────────────────────────────
# Capital gains tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCapitalGains(unittest.TestCase):

    def test_ltcg_exemption(self):
        cg = CapitalGains(long_term_10pct=200_000)
        # ₹2L – ₹1.25L = ₹75,000 taxable
        self.assertAlmostEqual(cg.taxable_ltcg_10pct(), 75_000.0)

    def test_ltcg_within_exemption(self):
        cg = CapitalGains(long_term_10pct=100_000)
        self.assertEqual(cg.taxable_ltcg_10pct(), 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end TaxCalculator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTaxCalculator(unittest.TestCase):

    def _make_calc(self, gross_salary: float, deductions: Deductions = None,
                   is_salaried: bool = True) -> TaxCalculator:
        salary = SalaryComponents(basic_salary=gross_salary)
        income = IncomeInput(salary=salary, is_salaried=is_salaried)
        ded = deductions or Deductions()
        return TaxCalculator(income=income, deductions=ded)

    # ── 87A rebate ─────────────────────────────────────────────────────

    def test_new_regime_zero_tax_below_12L(self):
        """New regime: income ≤ ₹12L → zero tax after 87A rebate."""
        calc = self._make_calc(gross_salary=12_00_000)
        result = calc.compute_new_regime()
        # Taxable = 12,00,000 - 75,000 std deduction = 11,25,000 ≤ 12,00,000 → full rebate
        self.assertEqual(result.total_tax, 0.0)

    def test_new_regime_12lakh_exact_taxable(self):
        """Taxable income exactly ₹12L in new regime → zero tax."""
        # Gross = 12,75,000 → after std ded 75,000 = 12,00,000 → rebate applies
        calc = self._make_calc(gross_salary=12_75_000)
        result = calc.compute_new_regime()
        self.assertEqual(result.total_tax, 0.0)

    def test_old_regime_zero_tax_below_5L(self):
        """Old regime: taxable income ≤ ₹5L → zero tax after 87A rebate."""
        # Gross 5L, std ded 50K, taxable = 4.5L ≤ 5L → rebate
        calc = self._make_calc(gross_salary=5_00_000)
        result = calc.compute_old_regime()
        self.assertEqual(result.total_tax, 0.0)

    def test_old_regime_87a_exactly_at_limit(self):
        """Old regime: taxable income = ₹5,00,000 → rebate ≤ ₹12,500."""
        calc = self._make_calc(gross_salary=5_50_000)
        result = calc.compute_old_regime()
        # taxable = 5,50,000 - 50,000 = 5,00,000 → rebate = 12,500 → zero tax
        self.assertEqual(result.total_tax, 0.0)

    # ── Old regime deductions ──────────────────────────────────────────

    def test_old_regime_80c_reduces_tax(self):
        ded_no = Deductions()
        ded_with = Deductions(ppf=150_000)
        calc_no = self._make_calc(gross_salary=8_00_000, deductions=ded_no)
        calc_with = self._make_calc(gross_salary=8_00_000, deductions=ded_with)
        self.assertGreater(
            calc_no.compute_old_regime().total_tax,
            calc_with.compute_old_regime().total_tax,
        )

    def test_new_regime_80c_has_no_effect(self):
        ded_no = Deductions()
        ded_with = Deductions(ppf=150_000)
        calc_no = self._make_calc(gross_salary=15_00_000, deductions=ded_no)
        calc_with = self._make_calc(gross_salary=15_00_000, deductions=ded_with)
        self.assertEqual(
            calc_no.compute_new_regime().total_tax,
            calc_with.compute_new_regime().total_tax,
        )

    # ── Surcharge ──────────────────────────────────────────────────────

    def test_surcharge_applied_above_50_lakh(self):
        calc = self._make_calc(gross_salary=60_00_000)
        result = calc.compute_new_regime()
        self.assertGreater(result.surcharge, 0.0)

    def test_no_surcharge_below_50_lakh(self):
        calc = self._make_calc(gross_salary=40_00_000)
        result = calc.compute_new_regime()
        self.assertEqual(result.surcharge, 0.0)

    # ── Cess ───────────────────────────────────────────────────────────

    def test_cess_is_4_pct(self):
        calc = self._make_calc(gross_salary=20_00_000)
        result = calc.compute_new_regime()
        expected_cess = round((result.tax_after_rebate + result.surcharge) * 0.04, 2)
        self.assertAlmostEqual(result.cess, expected_cess, places=1)

    # ── Comparison ─────────────────────────────────────────────────────

    def test_compare_returns_three_values(self):
        calc = self._make_calc(gross_salary=10_00_000)
        old, new, rec = calc.compare()
        self.assertIn(rec, ("old", "new"))

    def test_comparison_recommends_lower_tax(self):
        calc = self._make_calc(gross_salary=15_00_000)
        old, new, rec = calc.compare()
        if old.total_tax <= new.total_tax:
            self.assertEqual(rec, "old")
        else:
            self.assertEqual(rec, "new")


# ─────────────────────────────────────────────────────────────────────────────
# Utility tests
# ─────────────────────────────────────────────────────────────────────────────

class TestUtils(unittest.TestCase):

    def test_format_inr_lakhs(self):
        self.assertEqual(format_inr(1_500_000), "₹15,00,000")

    def test_format_inr_thousands(self):
        self.assertEqual(format_inr(75_000), "₹75,000")

    def test_format_inr_small(self):
        self.assertEqual(format_inr(250), "₹250")

    def test_format_inr_crore(self):
        self.assertEqual(format_inr(10_000_000), "₹1,00,00,000")

    def test_format_inr_zero(self):
        self.assertEqual(format_inr(0), "₹0")

    def test_format_inr_no_symbol(self):
        self.assertEqual(format_inr(50_000, symbol=False), "50,000")


if __name__ == "__main__":
    unittest.main()
