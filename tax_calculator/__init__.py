"""Indian Income Tax Calculator package."""

from .calculator import TaxCalculator
from .deductions import Deductions
from .slabs import OldRegimeSlabs, NewRegimeSlabs

__all__ = ["TaxCalculator", "Deductions", "OldRegimeSlabs", "NewRegimeSlabs"]
