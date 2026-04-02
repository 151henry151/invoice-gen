"""Create-invoice POST redirect must be a relative path so fetch(redirect:'manual') can read Location behind HTTPS."""
import json


def test_create_invoice_success_redirect_is_not_absolute_http(auth_client, test_business, test_client_obj):
    line_items = json.dumps(
        [
            {
                "type": "item",
                "description": "Test line",
                "quantity": 1,
                "price": 10.0,
                "total": 10.0,
            }
        ]
    )
    response = auth_client.post(
        "/create_invoice",
        data={
            "invoice_number": "INV-SUBMIT-001",
            "date": "2026-04-01",
            "due_date": "2026-04-15",
            "client_id": str(test_client_obj.id),
            "business_id": str(test_business.id),
            "line_items_json": line_items,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    loc = response.headers.get("Location", "")
    assert "invoice_list" in loc
    assert not loc.startswith("http://"), loc
