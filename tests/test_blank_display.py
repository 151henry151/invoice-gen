"""Blank/None contact fields must not render as the word None."""

from address_utils import blank, combine_address


def test_blank_filters_none_and_none_string():
    assert blank(None) == ""
    assert blank("None") == ""
    assert blank("none") == ""
    assert blank("null") == ""
    assert blank("  ") == ""
    assert blank("402 Hewitt Rd") == "402 Hewitt Rd"


def test_combine_address_skips_none_string_parts():
    assert (
        combine_address("402 Hewitt Rd", None, "Bristol", "VT", "None", "None")
        == "402 Hewitt Rd, Bristol, VT"
    )
    assert combine_address("", "", "", "", "", "") == ""
    assert combine_address(None, None, None, None, None, None) == ""


def test_business_allows_fully_blank_address(auth_client, app, test_user):
    from models import Business, db

    resp = auth_client.post(
        "/business_details",
        data={
            "name": "Street Only Optional",
            "address_line1": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "country": "",
            "email": "a@example.com",
            "phone": "+1 (802) 555-1111",
            "source": "businesses",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        biz = (
            db.session.query(Business)
            .filter_by(user_id=test_user.id, name="Street Only Optional")
            .first()
        )
        assert biz is not None
        assert not biz.address


def test_view_invoice_omits_none_address(auth_client, app, test_user, test_business, test_client_obj):
    from datetime import date
    from models import Invoice, db

    with app.app_context():
        test_business.address = None
        test_client_obj.address = None
        test_client_obj.email = None
        inv = Invoice(
            user_id=test_user.id,
            invoice_number="9100",
            date=date.today(),
            due_date=date.today(),
            business_id=test_business.id,
            client_id=test_client_obj.id,
            status="draft",
        )
        db.session.add(inv)
        db.session.commit()

    resp = auth_client.get("/invoice/9100")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "None" not in html


def test_blank_strips_none_address_segments():
    assert blank("402 Hewitt Rd, Bristol, VT, None, United States") == (
        "402 Hewitt Rd, Bristol, VT, United States"
    )
    assert blank("402 Hewitt Rd, Bristol, VT, None, None") == "402 Hewitt Rd, Bristol, VT"


def test_address_from_form_allows_partial_address():
    from address_utils import address_from_form

    assert (
        address_from_form(
            {
                "address_line1": "402 Hewitt Rd",
                "city": "Bristol",
                "state": "VT",
                "postal_code": "",
                "country": "",
            }
        )
        == "402 Hewitt Rd, Bristol, VT"
    )
    assert address_from_form(
        {
            "address_line1": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "country": "",
        }
    ) is None
