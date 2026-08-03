"""Invoice number is assigned and not presented as an editable confirm flow."""

from models import Setting, db


def test_create_invoice_page_assigns_readonly_number(auth_client, app, test_user):
    with app.app_context():
        setting = db.session.query(Setting).filter_by(user_id=test_user.id, key="next_invoice_number").first()
        if setting:
            setting.value = "2040"
        else:
            db.session.add(Setting(user_id=test_user.id, key="next_invoice_number", value="2040"))
        db.session.commit()

    resp = auth_client.get("/create_invoice")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert 'id="invoice_number"' in html
    assert "2040" in html
    assert "confirmInvoiceBtn" not in html
    assert "Assigned automatically" in html
