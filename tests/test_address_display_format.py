"""Invoice addresses display as normal postal lines, not comma-lists."""

from address_utils import format_address_display, parse_address


def test_format_address_display_standard_us():
    assert format_address_display(
        "402 Hewitt Rd, Bristol, VT, 05443, United States"
    ) == "402 Hewitt Rd\nBristol, VT 05443\nUnited States"


def test_format_address_display_omits_blank_zip_and_country():
    assert format_address_display("402 Hewitt Rd, Bristol, VT") == (
        "402 Hewitt Rd\nBristol, VT"
    )


def test_format_address_display_blank():
    assert format_address_display(None) == ""
    assert format_address_display("None") == ""


def test_parse_four_parts_with_country_no_zip():
    parsed = parse_address("402 Hewitt Rd, Bristol, VT, United States")
    assert parsed["address_line1"] == "402 Hewitt Rd"
    assert parsed["city"] == "Bristol"
    assert parsed["state"] == "VT"
    assert parsed["country"] == "United States"
    assert parsed["postal_code"] == ""


def test_view_invoice_address_not_comma_list(auth_client, app, test_user, test_business, test_client_obj):
    from datetime import date
    from models import Invoice, db

    with app.app_context():
        test_business.address = "402 Hewitt Rd, Bristol, VT, 05443, United States"
        test_client_obj.address = "10 Main St, Middlebury, VT, 05753"
        inv = Invoice(
            user_id=test_user.id,
            invoice_number="9101",
            date=date.today(),
            due_date=date.today(),
            business_id=test_business.id,
            client_id=test_client_obj.id,
            status="draft",
        )
        db.session.add(inv)
        db.session.commit()

    resp = auth_client.get("/invoice/9101")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "402 Hewitt Rd<br>Bristol, VT 05443<br>United States" in html
    assert "402 Hewitt Rd, Bristol, VT, 05443, United States" not in html
