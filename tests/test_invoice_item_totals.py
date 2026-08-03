"""Line item totals must be computed from quantity * price when missing/zero."""

from datetime import date

from models import Invoice, InvoiceItem, db


def test_create_invoice_recomputes_item_total_when_zero(
    auth_client, app, test_user, test_business, test_client_obj
):
    import json

    resp = auth_client.post(
        "/create_invoice",
        data={
            "invoice_number": "9001",
            "date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "client_id": str(test_client_obj.id),
            "business_id": str(test_business.id),
            "line_items_json": json.dumps(
                [
                    {
                        "type": "item",
                        "description": "Turnover cleaning",
                        "quantity": 1,
                        "price": 320.0,
                        "total": 0,  # buggy client payload
                    }
                ]
            ),
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    with app.app_context():
        inv = db.session.query(Invoice).filter_by(invoice_number="9001").first()
        assert inv is not None
        item = db.session.query(InvoiceItem).filter_by(invoice_id=inv.id).first()
        assert item is not None
        assert float(item.unit_price) == 320.0
        assert float(item.total) == 320.0


def test_create_invoice_recomputes_from_qty_and_price(
    auth_client, app, test_user, test_business, test_client_obj
):
    import json

    resp = auth_client.post(
        "/create_invoice",
        data={
            "invoice_number": "9002",
            "date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "client_id": str(test_client_obj.id),
            "business_id": str(test_business.id),
            "line_items_json": json.dumps(
                [
                    {
                        "type": "item",
                        "description": "Laundry",
                        "quantity": 2,
                        "price": 20.0,
                        "total": None,
                    }
                ]
            ),
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    with app.app_context():
        inv = db.session.query(Invoice).filter_by(invoice_number="9002").first()
        item = db.session.query(InvoiceItem).filter_by(invoice_id=inv.id).first()
        assert float(item.total) == 40.0
