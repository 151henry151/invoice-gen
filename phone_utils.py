"""Phone number parsing and US-style national formatting helpers."""

from __future__ import annotations

import re
from typing import Tuple


# Common dialing codes shown in the country selector (code, label).
COUNTRY_OPTIONS = (
    ("1", "United States / Canada (+1)"),
    ("44", "United Kingdom (+44)"),
    ("61", "Australia (+61)"),
    ("353", "Ireland (+353)"),
    ("33", "France (+33)"),
    ("49", "Germany (+49)"),
    ("52", "Mexico (+52)"),
    ("91", "India (+91)"),
)


def digits_only(value: str) -> str:
    """Return only digit characters from value."""
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def format_us_national(digits: str) -> str:
    """Format up to 10 national digits as (XXX) XXX-XXXX progressively."""
    d = digits_only(digits)[:10]
    if not d:
        return ""
    if len(d) <= 3:
        return f"({d}"
    if len(d) <= 6:
        return f"({d[:3]}) {d[3:]}"
    return f"({d[:3]}) {d[3:6]}-{d[6:]}"


def format_national(digits: str, country_code: str = "1") -> str:
    """Format national digits for display; US/Canada use NANP grouping."""
    code = digits_only(country_code) or "1"
    d = digits_only(digits)
    if code == "1":
        return format_us_national(d)
    d = d[:15]
    groups = [d[i : i + 3] for i in range(0, len(d), 3)]
    return " ".join(g for g in groups if g)


def compose_phone(country_code: str, national_digits: str) -> str:
    """Build a stored phone string: +{code} {formatted national}."""
    code = digits_only(country_code) or "1"
    national = digits_only(national_digits)
    if not national:
        return ""
    formatted = format_national(national, code)
    return f"+{code} {formatted}".strip()


def parse_stored_phone(value: str) -> Tuple[str, str]:
    """
    Parse a stored phone into (country_code, national_digits).

    Defaults to country code 1 (USA/Canada) when no leading +code is present.
    """
    if not value:
        return "1", ""
    text = value.strip()
    if text.startswith("+"):
        rest = text[1:]
        known = sorted((c for c, _ in COUNTRY_OPTIONS), key=len, reverse=True)
        for code in known:
            if rest.startswith(code):
                national = digits_only(rest[len(code) :])
                if code == "1" and len(national) == 11 and national.startswith("1"):
                    national = national[1:]
                return code, national
        m = re.match(r"(\d{1,3})\s*(.*)$", rest)
        if m:
            return m.group(1), digits_only(m.group(2))
    digits = digits_only(text)
    if len(digits) == 11 and digits.startswith("1"):
        return "1", digits[1:]
    if len(digits) == 10:
        return "1", digits
    return "1", digits


def is_valid_phone(value: str) -> bool:
    """Return True when the phone has enough digits to be usable."""
    if not value or not value.strip():
        return False
    code, national = parse_stored_phone(value)
    if code == "1":
        return len(national) == 10
    return 6 <= len(national) <= 15
