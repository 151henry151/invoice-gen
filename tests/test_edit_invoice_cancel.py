"""Edit-invoice page must embed a pristine snapshot of the saved invoice and a
Discard-changes control so an in-progress edit can be abandoned and restored to
the generated invoice."""
import json


def _create_invoice(auth_client, business, client_obj, number):
    line_items = json.dumps(
        [
            {
                "type": "item",
                "description": "Widget assembly",
                "quantity": 2,
                "price": 25.0,
                "total": 50.0,
            },
            {
                "type": "labor",
                "description": "On-site install",
                "date": "2026-04-01",
                "hours": 1,
                "minutes": 30,
                "rate": 80.0,
                "total": 120.0,
            },
        ]
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
    return number


def test_edit_page_embeds_snapshot_and_discard_button(
    auth_client, test_business, test_client_obj
):
    number = _create_invoice(auth_client, test_business, test_client_obj, "INV-EDIT-001")

    resp = auth_client.get(f"/edit_invoice/{number}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # A pristine snapshot of the saved invoice is embedded for the client.
    assert "INVOICE_SNAPSHOT" in html
    assert "Widget assembly" in html
    assert "On-site install" in html

    # The page exposes the edit POST endpoint so saving updates (not duplicates).
    assert "EDIT_POST_URL" in html
    assert number in html

    # A control to abandon in-progress edits exists.
    assert "Discard changes" in html


def test_edit_snapshot_round_trips_line_items(
    auth_client, test_business, test_client_obj
):
    number = _create_invoice(auth_client, test_business, test_client_obj, "INV-EDIT-002")

    resp = auth_client.get(f"/edit_invoice/{number}")
    html = resp.get_data(as_text=True)

    # Extract the embedded JSON snapshot.
    marker = "const INVOICE_SNAPSHOT = "
    start = html.index(marker) + len(marker)
    end = html.index(";", start)
    snapshot = json.loads(html[start:end])

    assert snapshot["invoiceNumber"] == number
    assert snapshot["isConfirmed"] is True
    types = sorted(item["type"] for item in snapshot["items"])
    assert "item" in types
    assert "labor" in types
    labor = next(i for i in snapshot["items"] if i["type"] == "labor")
    assert int(labor["hours"]) == 1
    assert int(labor["minutes"]) == 30
