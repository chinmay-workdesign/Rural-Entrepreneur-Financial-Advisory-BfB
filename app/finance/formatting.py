import re


def format_inr(amount: float) -> str:
    """Indian digit grouping: 250000 -> ₹2,50,000."""
    whole = int(round(amount))
    digits = str(abs(whole))
    if len(digits) > 3:
        head = ",".join(re.findall(r"\d{1,2}", digits[:-3][::-1]))[::-1]
        digits = f"{head},{digits[-3:]}"
    return f"₹{'-' if whole < 0 else ''}{digits}"
