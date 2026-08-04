"""Helpers for combining, splitting, and displaying multi-part addresses."""

from __future__ import annotations

from typing import Dict, Mapping, Optional


_BLANK_TOKENS = frozenset({"", "none", "null", "undefined", "nil"})


def blank(value: Optional[object]) -> str:
    """
    Normalize a contact/address value for display or storage.

    None and the literal strings "None"/"null" become empty so templates
    never render the word None on invoices. Comma-separated addresses also
    drop any segment that is itself blank/None.
    """
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if "," in text:
        parts = []
        for part in text.split(","):
            cleaned = part.strip()
            if cleaned and cleaned.lower() not in _BLANK_TOKENS:
                parts.append(cleaned)
        return ", ".join(parts)
    if text.lower() in _BLANK_TOKENS:
        return ""
    return text


def _clean_part(value: Optional[object]) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in _BLANK_TOKENS:
        return ""
    return text


def combine_address(
    address_line1: Optional[str],
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
) -> str:
    """Join address parts into the comma-separated storage format."""
    parts = []
    for value in (address_line1, address_line2, city, state, postal_code, country):
        cleaned = _clean_part(value)
        if cleaned:
            parts.append(cleaned)
    return ", ".join(parts)


def parse_address(address: Optional[str]) -> Dict[str, str]:
    """
    Split a stored address into components.

    Parses from the end (country, postal, state, city) so a missing
    address line 2 does not shift city/state/ZIP into the wrong fields.
    """
    empty = {
        "address_line1": "",
        "address_line2": "",
        "city": "",
        "state": "",
        "postal_code": "",
        "country": "",
    }
    cleaned = blank(address)
    if not cleaned:
        return empty

    parts = [p.strip() for p in cleaned.split(",") if p.strip() and blank(p)]
    if not parts:
        return empty

    result = dict(empty)
    if len(parts) == 1:
        result["address_line1"] = parts[0]
        return result

    if len(parts) >= 5:
        result["country"] = parts[-1]
        result["postal_code"] = parts[-2]
        result["state"] = parts[-3]
        result["city"] = parts[-4]
        street = parts[:-4]
        result["address_line1"] = street[0] if street else ""
        result["address_line2"] = ", ".join(street[1:]) if len(street) > 1 else ""
        return result

    if len(parts) == 4:
        if _looks_like_postal(parts[-1]):
            result["address_line1"] = parts[0]
            result["city"] = parts[1]
            result["state"] = parts[2]
            result["postal_code"] = parts[3]
            return result
        result["address_line1"] = parts[0]
        result["address_line2"] = parts[1]
        result["city"] = parts[2]
        result["state"] = parts[3]
        return result

    if len(parts) == 3:
        result["address_line1"] = parts[0]
        result["city"] = parts[1]
        result["state"] = parts[2]
        return result

    result["address_line1"] = parts[0]
    result["city"] = parts[1]
    return result


def _looks_like_postal(value: str) -> bool:
    compact = value.replace(" ", "")
    return bool(compact) and (
        compact.isdigit()
        or (len(compact) >= 5 and compact[:5].isdigit())
        or ("-" in compact and compact.replace("-", "").isalnum())
    )


def address_from_form(form: Mapping, prefix: str = "") -> Optional[str]:
    """
    Build a stored address from a form mapping.

    Accepts either a single `address` field (legacy/tests) or the split
    fields used by the address picker (`{prefix}address_line1`, etc.).
    Returns None when every part is blank so invoices omit the address.
    """
    legacy = blank(form.get("address"))
    line1_key = f"{prefix}address_line1"
    # Werkzeug ImmutableMultiDict supports .get; missing keys are fine.
    has_picker = any(
        blank(form.get(f"{prefix}{key}"))
        for key in (
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
        )
    )
    if legacy and not blank(form.get(line1_key)) and not has_picker:
        return legacy

    combined = combine_address(
        form.get(f"{prefix}address_line1"),
        form.get(f"{prefix}address_line2"),
        form.get(f"{prefix}city"),
        form.get(f"{prefix}state"),
        form.get(f"{prefix}postal_code"),
        form.get(f"{prefix}country"),
    )
    return combined or None
