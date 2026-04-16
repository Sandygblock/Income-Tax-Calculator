"""
Utility helpers: Indian number formatting and display helpers.
"""

from typing import Union


def format_inr(amount: Union[int, float], symbol: bool = True) -> str:
    """
    Format a number in Indian number system with ₹ symbol.

    Examples:
        1500000  -> ₹15,00,000
        75000    -> ₹75,000
        250      -> ₹250
    """
    amount = round(amount, 2)
    negative = amount < 0
    amount = abs(amount)

    # Split into integer and decimal parts
    int_part = int(amount)
    dec_part = round(amount - int_part, 2)

    # Indian grouping: last 3 digits, then groups of 2
    s = str(int_part)
    if len(s) > 3:
        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + "," + result
            s = s[:-2]
    else:
        result = s

    if dec_part:
        dec_str = f"{dec_part:.2f}"[1:]  # e.g. ".50"
        result += dec_str

    if negative:
        result = "-" + result

    if symbol:
        return f"₹{result}"
    return result


def format_pct(rate: float) -> str:
    """Format a decimal rate as a percentage string."""
    pct = rate * 100
    if pct == int(pct):
        return f"{int(pct)}%"
    return f"{pct:.1f}%"


def divider(char: str = "─", width: int = 60) -> str:
    """Return a horizontal divider line."""
    return char * width


def section_header(title: str, width: int = 60) -> str:
    """Return a formatted section header."""
    return f"\n{divider('═', width)}\n  {title}\n{divider('═', width)}"


def row(label: str, value: str, width: int = 60) -> str:
    """Return a formatted label-value row."""
    label_width = width - 22
    return f"  {label:<{label_width}} {value:>20}"


def input_amount(prompt: str, allow_zero: bool = True) -> float:
    """
    Prompt user for a monetary amount, accepting plain numbers or
    comma-separated Indian format.  Returns float.
    """
    while True:
        raw = input(prompt).strip().replace(",", "").replace("₹", "").replace(" ", "")
        if raw == "" and allow_zero:
            return 0.0
        try:
            val = float(raw)
            if val < 0:
                print("  ⚠ Please enter a non-negative value.")
                continue
            return val
        except ValueError:
            print("  ⚠ Invalid input. Please enter a numeric value.")


def input_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for yes/no answer."""
    hint = " [Y/n]" if default else " [y/N]"
    while True:
        raw = input(prompt + hint + ": ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        if raw == "":
            return default
        print("  ⚠ Please enter Y or N.")


def input_choice(prompt: str, choices: list) -> str:
    """Prompt for one of a set of choices (case-insensitive)."""
    choices_lower = [c.lower() for c in choices]
    while True:
        raw = input(prompt).strip().lower()
        if raw in choices_lower:
            return raw
        print(f"  ⚠ Please enter one of: {', '.join(choices)}")
