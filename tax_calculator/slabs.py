"""
Tax slab definitions for Old and New Tax Regimes (FY 2025-26 / AY 2026-27).

Each slab entry is a tuple: (upper_limit, rate)
where upper_limit of None means "no upper limit" (highest slab).
"""

from typing import List, Tuple, Optional

# Slab type: (upper_limit_inclusive, tax_rate_fraction)
Slab = Tuple[Optional[int], float]


# ---------------------------------------------------------------------------
# New Tax Regime – FY 2025-26 (AY 2026-27)
# Standard deduction: ₹75,000
# Rebate u/s 87A: full rebate if taxable income ≤ ₹12,00,000
# Surcharge capped at 25%
# ---------------------------------------------------------------------------
NEW_REGIME_SLABS: List[Slab] = [
    (400_000, 0.00),    # Up to ₹4,00,000 – Nil
    (800_000, 0.05),    # ₹4,00,001 – ₹8,00,000 – 5%
    (1_200_000, 0.10),  # ₹8,00,001 – ₹12,00,000 – 10%
    (1_600_000, 0.15),  # ₹12,00,001 – ₹16,00,000 – 15%
    (2_000_000, 0.20),  # ₹16,00,001 – ₹20,00,000 – 20%
    (2_400_000, 0.25),  # ₹20,00,001 – ₹24,00,000 – 25%
    (None, 0.30),       # Above ₹24,00,000 – 30%
]

NEW_REGIME_STANDARD_DEDUCTION: int = 75_000
NEW_REGIME_87A_LIMIT: int = 1_200_000  # ₹12,00,000
NEW_REGIME_SURCHARGE_CAP: float = 0.25  # 25%

# ---------------------------------------------------------------------------
# Old Tax Regime
# Standard deduction: ₹50,000 (for salaried)
# Rebate u/s 87A: full rebate if taxable income ≤ ₹5,00,000
# ---------------------------------------------------------------------------
OLD_REGIME_SLABS: List[Slab] = [
    (250_000, 0.00),    # Up to ₹2,50,000 – Nil
    (500_000, 0.05),    # ₹2,50,001 – ₹5,00,000 – 5%
    (1_000_000, 0.20),  # ₹5,00,001 – ₹10,00,000 – 20%
    (None, 0.30),       # Above ₹10,00,000 – 30%
]

OLD_REGIME_STANDARD_DEDUCTION: int = 50_000
OLD_REGIME_87A_LIMIT: int = 500_000  # ₹5,00,000

# ---------------------------------------------------------------------------
# Surcharge rates (common thresholds; new regime caps at 25%)
# ---------------------------------------------------------------------------
SURCHARGE_RATES: List[Tuple[int, float]] = [
    (50_00_000, 0.10),   # > ₹50 lakh → 10%
    (1_00_00_000, 0.15), # > ₹1 crore → 15%
    (2_00_00_000, 0.25), # > ₹2 crore → 25%
    (5_00_00_000, 0.37), # > ₹5 crore → 37% (old regime only)
]

# Health & Education Cess rate
CESS_RATE: float = 0.04  # 4%


class OldRegimeSlabs:
    """Tax slab configuration for the Old Tax Regime."""

    slabs: List[Slab] = OLD_REGIME_SLABS
    standard_deduction: int = OLD_REGIME_STANDARD_DEDUCTION
    rebate_87a_limit: int = OLD_REGIME_87A_LIMIT
    surcharge_cap: Optional[float] = None  # no cap in old regime

    @staticmethod
    def compute_tax(taxable_income: float) -> float:
        """Compute tax before surcharge/cess using old regime slabs."""
        return _compute_slab_tax(taxable_income, OLD_REGIME_SLABS)


class NewRegimeSlabs:
    """Tax slab configuration for the New Tax Regime."""

    slabs: List[Slab] = NEW_REGIME_SLABS
    standard_deduction: int = NEW_REGIME_STANDARD_DEDUCTION
    rebate_87a_limit: int = NEW_REGIME_87A_LIMIT
    surcharge_cap: float = NEW_REGIME_SURCHARGE_CAP

    @staticmethod
    def compute_tax(taxable_income: float) -> float:
        """Compute tax before surcharge/cess using new regime slabs."""
        return _compute_slab_tax(taxable_income, NEW_REGIME_SLABS)


def _compute_slab_tax(income: float, slabs: List[Slab]) -> float:
    """
    Calculate tax based on progressive slab rates.

    Args:
        income: Taxable income (after all deductions/exemptions).
        slabs: List of (upper_limit, rate) tuples in ascending order.

    Returns:
        Total tax computed across all applicable slabs.
    """
    tax = 0.0
    prev_limit = 0

    for upper_limit, rate in slabs:
        if income <= 0:
            break
        if upper_limit is None:
            # Highest slab – apply rate to everything above prev_limit
            slab_income = income - prev_limit
        else:
            slab_income = min(income, upper_limit) - prev_limit

        if slab_income > 0:
            tax += slab_income * rate

        if upper_limit is not None:
            prev_limit = upper_limit
        if upper_limit is not None and income <= upper_limit:
            break

    return tax
