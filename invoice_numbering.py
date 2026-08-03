"""Per-user sequential invoice number allocation."""

from __future__ import annotations

from typing import Iterable, Optional, Set

from models import Invoice, InvoiceDraft, Setting, db


def _digit_values(values: Iterable[str]) -> Set[int]:
    nums: Set[int] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text.isdigit():
            nums.add(int(text))
    return nums


def _format_number(value: int, width: int) -> str:
    return str(value).zfill(max(width, len(str(value))))


def used_invoice_numbers(user_id: int) -> Set[str]:
    """Return invoice numbers already used by saved invoices or drafts."""
    used = {
        row.invoice_number
        for row in db.session.query(Invoice.invoice_number).filter_by(user_id=user_id).all()
        if row.invoice_number
    }
    used.update(
        {
            row.invoice_number
            for row in db.session.query(InvoiceDraft.invoice_number)
            .filter_by(user_id=user_id)
            .all()
            if getattr(row, "invoice_number", None)
        }
    )
    return used


def peek_next_invoice_number(user_id: int) -> str:
    """Return the next invoice number without reserving it."""
    setting = (
        db.session.query(Setting)
        .filter_by(user_id=user_id, key="next_invoice_number")
        .first()
    )
    raw = setting.value if setting and setting.value else "1001"
    width = len(raw) if str(raw).isdigit() else 4
    start = int(raw) if str(raw).isdigit() else 1001
    used = used_invoice_numbers(user_id)
    used_nums = _digit_values(used)
    candidate = max([start - 1] + list(used_nums)) + 1
    if candidate < start:
        candidate = start
    while _format_number(candidate, width) in used or str(candidate) in used:
        candidate += 1
    return _format_number(candidate, width)


def allocate_next_invoice_number(user_id: int) -> str:
    """
    Reserve and return the next sequential invoice number for the user.

    Advances the user's next_invoice_number setting past the allocated value.
    """
    number = peek_next_invoice_number(user_id)
    setting = (
        db.session.query(Setting)
        .filter_by(user_id=user_id, key="next_invoice_number")
        .first()
    )
    width = len(number)
    nxt = int(number) + 1
    formatted_next = _format_number(nxt, width)
    if setting:
        setting.value = formatted_next
    else:
        db.session.add(
            Setting(user_id=user_id, key="next_invoice_number", value=formatted_next)
        )
    db.session.commit()
    return number
