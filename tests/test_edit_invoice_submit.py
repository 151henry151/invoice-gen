"""Editing an invoice must persist changes and redirect to the invoice list
with a relative Location so the create/edit page's fetch(redirect:'follow')
treats the save as successful."""
import json

from models import db, Invoice


def _create(auth_client, business, client_obj, number):
    line_items = json.dumps(
        [{"type": "item", "description": "Original line", "quantity": 1, "price": 10.0, "total": 10.0}]
    )
    resp = auth_client.post(
        "/create_invoice",
        data={
            "invoice_number": number,
            "date": "2026-04-01",
            "due_date": "2026-04-15",
            "client_id": str(client_obj.id),
            "business_id": str(business.id),
            "line_items_json": line_items,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302


def test_edit_invoice_post_redirects_relative_to_list(
    auth_client, test_business, test_client_obj
):
    number = "INV-EDIT-SUBMIT-001"
    _create(auth_client, test_business, test_client_obj, number)

    updated = json.dumps(
        [{"type": "item", "description": "Updated line", "quantity": 3, "price": 5.0, "total": 15.0}]
    )
    resp = auth_client.post(
        f"/edit_invoice/{number}",
        data={
            "invoice_number": number,
            "date": "2026-04-02",
            "due_date": "2026-04-16",
            "client_id": str(test_client_obj.id),
            "business_id": str(test_business.id),
            "line_items_json": updated,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    loc = resp.headers.get("Location", "")
    assert "invoice_list" in loc
    assert not loc.startswith("http://"), loc

    invoice = db.session.query(Invoice).filter_by(invoice_number=number).first()
    assert invoice is not None
    descriptions = [i.description for i in invoice.items]
    assert "Updated line" in descriptions
    assert "Original line" not in descriptions
