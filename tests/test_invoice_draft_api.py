"""Tests for multi-draft invoice autosave API."""

import json

from models import InvoiceDraft, Setting, db
from invoice_numbering import allocate_next_invoice_number


def test_create_two_drafts_keeps_both(auth_client, app, test_user):
    with app.app_context():
        setting = db.session.query(Setting).filter_by(user_id=test_user.id, key="next_invoice_number").first()
        if setting:
            setting.value = "3001"
        else:
            db.session.add(Setting(user_id=test_user.id, key="next_invoice_number", value="3001"))
        db.session.commit()

    r1 = auth_client.post("/api/invoice-drafts")
    r2 = auth_client.post("/api/invoice-drafts")
    assert r1.status_code == 200
    assert r2.status_code == 200
    d1 = r1.get_json()["draft"]
    d2 = r2.get_json()["draft"]
    assert d1["invoice_number"] != d2["invoice_number"]

    listed = auth_client.get("/api/invoice-drafts").get_json()["drafts"]
    assert len(listed) >= 2
    numbers = {d["invoice_number"] for d in listed}
    assert d1["invoice_number"] in numbers
    assert d2["invoice_number"] in numbers


def test_put_updates_specific_draft(auth_client, app, test_user):
    created = auth_client.post("/api/invoice-drafts").get_json()["draft"]
    draft_id = created["id"]
    payload = {
        "draftId": draft_id,
        "invoiceNumber": created["invoice_number"],
        "date": "2026-08-03",
        "items": [{"type": "note", "description": "hello", "total": "0"}],
        "savedAt": 123,
    }
    rv = auth_client.put(
        "/api/invoice-draft",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert rv.status_code == 200
    got = auth_client.get(f"/api/invoice-draft?draft_id={draft_id}").get_json()
    assert got["draft"]["date"] == "2026-08-03"
    assert len(got["draft"]["items"]) == 1


def test_delete_one_draft_leaves_others(auth_client, app, test_user):
    d1 = auth_client.post("/api/invoice-drafts").get_json()["draft"]
    d2 = auth_client.post("/api/invoice-drafts").get_json()["draft"]
    auth_client.delete(f"/api/invoice-draft?draft_id={d1['id']}")
    listed = auth_client.get("/api/invoice-drafts").get_json()["drafts"]
    ids = {d["id"] for d in listed}
    assert d1["id"] not in ids
    assert d2["id"] in ids


def test_create_invoice_new_redirects_to_draft(auth_client, app, test_user):
    with app.app_context():
        setting = db.session.query(Setting).filter_by(user_id=test_user.id, key="next_invoice_number").first()
        if setting:
            setting.value = "4001"
        else:
            db.session.add(Setting(user_id=test_user.id, key="next_invoice_number", value="4001"))
        db.session.commit()

    resp = auth_client.get("/create_invoice?new=1", follow_redirects=False)
    assert resp.status_code in (302, 303)
    loc = resp.headers["Location"]
    assert "draft_id=" in loc

    resp2 = auth_client.get(loc, follow_redirects=True)
    assert resp2.status_code == 200
    assert b"4001" in resp2.data
    assert b"confirmInvoiceBtn" not in resp2.data
