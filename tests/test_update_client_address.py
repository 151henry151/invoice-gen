"""Regression: editing a client must persist address picker fields."""

from models import Client, db


def test_update_client_saves_address_picker_fields(auth_client, test_client_obj, app):
    response = auth_client.post(
        "/update_client",
        data={
            "client_id": str(test_client_obj.id),
            "name": "Jasmine Blair",
            "client_address_line1": "10 Church St",
            "client_address_line2": "",
            "client_city": "Middlebury",
            "client_state": "VT",
            "client_postal_code": "05753",
            "client_country": "United States",
            "email": "jy_blair@hotmail.com",
            "phone": "+1 (802) 555-1212",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        client = db.session.get(Client, test_client_obj.id)
        assert client.name == "Jasmine Blair"
        assert client.email == "jy_blair@hotmail.com"
        assert "10 Church St" in (client.address or "")
        assert "Middlebury" in (client.address or "")
        assert "05753" in (client.address or "")
        assert client.phone == "+1 (802) 555-1212"


def test_create_client_from_address_picker_fields(auth_client, app, test_user):
    response = auth_client.post(
        "/update_client",
        data={
            "name": "New Client Co",
            "client_address_line1": "1 Main St",
            "client_city": "Burlington",
            "client_state": "VT",
            "client_postal_code": "05401",
            "client_country": "United States",
            "email": "new@example.com",
            "phone": "+1 (802) 555-9999",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        client = (
            db.session.query(Client)
            .filter_by(user_id=test_user.id, name="New Client Co")
            .first()
        )
        assert client is not None
        assert "1 Main St" in client.address
        assert "Burlington" in client.address
