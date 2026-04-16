# 🇮🇳 Indian Income Tax Calculator

A comprehensive **Python-based Indian Income Tax Calculator** for **FY 2025-26 (AY 2026-27)**.  
Supports both the **Old Tax Regime** and the **New Tax Regime**, with detailed deduction and exemption support, surcharge, cess, Section 87A rebate with marginal relief, and a side-by-side comparison to help you choose the better regime.

---

## Features

| Feature | Details |
|---|---|
| **Tax Regimes** | Old Regime & New Regime (FY 2025-26) |
| **Income Heads** | Salary, Business/Profession, House Property, Capital Gains, Other Sources |
| **Deductions** | 80C, 80CCD(1B), 80D, 80E, 80G, 80TTA/TTB, HRA Exemption, Home Loan Interest |
| **HRA Exemption** | Full 10(13A) computation (metro vs non-metro) |
| **Surcharge** | 10% / 15% / 25% / 37% with marginal relief |
| **Cess** | 4% Health & Education Cess |
| **Section 87A** | Old regime (≤₹5L) & New regime (≤₹12L) with marginal relief |
| **Capital Gains** | STCG @15%, LTCG @10% (with ₹1.25L exemption), LTCG @20% |
| **CLI** | Interactive menu-driven interface with ₹ Indian formatting |
| **Tests** | 46 unit tests covering all core logic |

---

## Project Structure

```
Income-Tax-Calculator/
├── README.md
├── requirements.txt
├── tax_calculator/
│   ├── __init__.py
│   ├── main.py          ← CLI entry point
│   ├── calculator.py    ← Core tax computation engine
│   ├── deductions.py    ← Deductions & exemption logic
│   ├── slabs.py         ← Tax slab definitions (Old & New regime)
│   └── utils.py         ← Indian number formatting & input helpers
└── tests/
    ├── __init__.py
    └── test_calculator.py  ← Unit tests (46 tests)
```

---

## Requirements

- **Python 3.8+**
- No external dependencies (standard library only)

---

## Quick Start

### Run the Interactive CLI

```bash
# From the project root:
python -m tax_calculator.main
```

Or directly:

```bash
python tax_calculator/main.py
```

### Run the Tests

```bash
python -m unittest discover -s tests -v
```

---

## Tax Regimes (FY 2025-26)

### New Tax Regime (Default)

Standard Deduction: **₹75,000**

| Income Range | Tax Rate |
|---|---|
| Up to ₹4,00,000 | Nil |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |

**Section 87A Rebate**: Full rebate if taxable income ≤ ₹12,00,000 (with marginal relief).  
**Surcharge cap**: 25%.

### Old Tax Regime

Standard Deduction: **₹50,000** (salaried)

| Income Range | Tax Rate |
|---|---|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

**Section 87A Rebate**: Rebate up to ₹12,500 if taxable income ≤ ₹5,00,000.

---

## Surcharge & Cess

| Income | Surcharge Rate |
|---|---|
| > ₹50 Lakh | 10% |
| > ₹1 Crore | 15% |
| > ₹2 Crore | 25% |
| > ₹5 Crore | 37% (Old Regime only; New Regime capped at 25%) |

**Health & Education Cess**: 4% on (Tax + Surcharge)

---

## Deductions – Old Regime

| Section | Description | Limit |
|---|---|---|
| 80C | PPF, ELSS, LIC, EPF, NSC, Home Loan Principal, Tuition Fees | ₹1,50,000 |
| 80CCD(1B) | Additional NPS contribution | ₹50,000 |
| 80D | Health Insurance – self & family | ₹25,000 |
| 80D | Health Insurance – parents | ₹25,000 (₹50,000 for senior citizen parents) |
| 80E | Education Loan Interest | No limit |
| 80G | Donations | Actual (100% deductible portion) |
| 80TTA | Savings Account Interest (non-senior) | ₹10,000 |
| 80TTB | Interest Income (senior citizens) | ₹50,000 |
| 10(13A) | HRA Exemption | Min of actual HRA / 50%–40% of Basic+DA / Rent–10% of Basic+DA |
| 24(b) | Home Loan Interest – self-occupied | ₹2,00,000 |

---

## Usage Example (Python API)

```python
from tax_calculator.calculator import TaxCalculator, IncomeInput
from tax_calculator.deductions import Deductions, SalaryComponents

# Salaried person with ₹15 LPA gross salary
salary = SalaryComponents(
    basic_salary=700_000,
    hra_received=300_000,
    special_allowance=500_000,
    rent_paid=240_000,
    is_metro=True,
)

income = IncomeInput(salary=salary, is_salaried=True)

deductions = Deductions(
    ppf=150_000,
    nps_additional=50_000,
    health_insurance_self=25_000,
)

calc = TaxCalculator(income=income, deductions=deductions)
old_result, new_result, recommended = calc.compare()

print(f"Old Regime Tax: ₹{old_result.total_tax:,.0f}")
print(f"New Regime Tax: ₹{new_result.total_tax:,.0f}")
print(f"Recommended: {recommended.upper()} REGIME")
```

**Output:**
```
Old Regime Tax: ₹1,26,360
New Regime Tax: ₹97,500
Recommended: NEW REGIME
```

---

## CLI Walkthrough

```
╔══════════════════════════════════════════════════════════════╗
║      🇮🇳  Indian Income Tax Calculator – FY 2025-26          ║
║              (Assessment Year 2026-27)                       ║
╚══════════════════════════════════════════════════════════════╝

  Enter your income and investment details below.
  Press Enter to skip any field (defaults to 0).

══════════════════════════════════════════════════════════════
  PERSONAL DETAILS
══════════════════════════════════════════════════════════════
  Are you a Senior Citizen (age 60–80)? [y/N]: n
  Are you a salaried employee? [Y/n]: y

══════════════════════════════════════════════════════════════
  SALARY / WAGE INCOME
══════════════════════════════════════════════════════════════
  Basic Salary (annual): ₹700000
  HRA received (annual): ₹300000
  ...

══════════════════════════════════════════════════════════════
  TAX COMPUTATION – OLD REGIME
══════════════════════════════════════════════════════════════

  Income Head                                           Amount
  ──────────────────────────────────────────────────────────
  Gross Salary                                   ₹15,00,000
    Less: HRA Exemption                         (₹1,70,000)
    Less: Standard Deduction                      (₹50,000)
  ...
  TOTAL TAX PAYABLE                               ₹1,26,360
  ══════════════════════════════════════════════════════════
```

---

## License

This project is open source and available under the [MIT License](LICENSE).
