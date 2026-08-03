"""Tests for sequential invoice number allocation."""

from datetime import date

from models import Invoice, InvoiceDraft, Setting, db
from invoice_numbering import allocate_next_invoice_number, peek_next_invoice_number


def _set_next(user_id, value):
    setting = db.session.query(Setting).filter_by(user_id=user_id, key="next_invoice_number").first()
    if setting:
        setting.value = value
    else:
        db.session.add(Setting(user_id=user_id, key="next_invoice_number", value=value))
    db.session.commit()


def _clear_numbers(user_id):
    db.session.query(InvoiceDraft).filter_by(user_id=user_id).delete()
    db.session.query(Invoice).filter_by(user_id=user_id).delete()
    db.session.commit()


def test_allocate_starts_from_setting(app, test_user):
    with app.app_context():
        _clear_numbers(test_user.id)
        _set_next(test_user.id, "1001")
        assert peek_next_invoice_number(test_user.id) == "1001"
        assert allocate_next_invoice_number(test_user.id) == "1001"
        assert allocate_next_invoice_number(test_user.id) == "1002"


def test_allocate_skips_existing_invoice_and_draft(app, test_user, test_business, test_client_obj):
    with app.app_context():
        _clear_numbers(test_user.id)
        _set_next(test_user.id, "1001")
        inv = Invoice(
            user_id=test_user.id,
            invoice_number="1001",
            date=date.today(),
            due_date=date.today(),
            business_id=test_business.id,
            client_id=test_client_obj.id,
            status="sent",
        )
        db.session.add(inv)
        draft = InvoiceDraft(
            user_id=test_user.id,
            invoice_number="1002",
            payload="{}",
        )
        db.session.add(draft)
        db.session.commit()
        assert allocate_next_invoice_number(test_user.id) == "1003"
