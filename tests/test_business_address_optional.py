"""ZIP and country are optional on business details."""

from models import Business, db


def test_business_details_allows_blank_zip_and_country(auth_client, app, test_user):
    resp = auth_client.post(
        "/business_details",
        data={
            "name": "Optional Address Biz",
            "address_line1": "402 Hewitt Rd",
            "address_line2": "",
            "city": "Bristol",
            "state": "VT",
            "postal_code": "",
            "country": "",
            "email": "biz@example.com",
            "phone": "+1 (802) 555-0000",
            "source": "businesses",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        biz = (
            db.session.query(Business)
            .filter_by(user_id=test_user.id, name="Optional Address Biz")
            .first()
        )
        assert biz is not None
        assert "402 Hewitt Rd" in biz.address
        assert "Bristol" in biz.address
        assert "VT" in biz.address
        assert "United States" not in (biz.address or "")
        # ZIP should not appear as an empty trailing segment requirement
        assert "05443" not in (biz.address or "")
