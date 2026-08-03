"""Helpers for combining and splitting stored multi-part addresses."""

from __future__ import annotations

from typing import Dict, Mapping, MutableMapping, Optional


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
    if address_line1 and str(address_line1).strip():
        parts.append(str(address_line1).strip())
    if address_line2 and str(address_line2).strip():
        parts.append(str(address_line2).strip())
    for value in (city, state, postal_code, country):
        if value and str(value).strip():
            parts.append(str(value).strip())
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
    if not address or not str(address).strip():
        return empty

    parts = [p.strip() for p in str(address).split(",") if p.strip()]
    if not parts:
        return empty

    result = dict(empty)
    if len(parts) == 1:
        result["address_line1"] = parts[0]
        return result

    # Prefer trailing country / postal / state / city when enough parts exist.
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
        # line1, city, state, postal (no country) OR line1, line2, city, state
        # Prefer interpreting as line1, city, state, postal when last looks like ZIP.
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

    # len == 2
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


def address_from_form(form: Mapping, prefix: str = "") -> str:
    """
    Build a stored address from a form mapping.

    Accepts either a single `address` field (legacy/tests) or the split
    fields used by the address picker (`{prefix}address_line1`, etc.).
    """
    legacy = form.get("address")
    if legacy and str(legacy).strip() and not form.get(f"{prefix}address_line1"):
        return str(legacy).strip()

    return combine_address(
        form.get(f"{prefix}address_line1"),
        form.get(f"{prefix}address_line2"),
        form.get(f"{prefix}city"),
        form.get(f"{prefix}state"),
        form.get(f"{prefix}postal_code"),
        form.get(f"{prefix}country"),
    )
