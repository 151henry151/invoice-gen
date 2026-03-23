"""Tests for server-side invoice draft autosave API."""
import json
import os
import tempfile
import unittest

from app import app as flask_app
from models import db, User, InvoiceDraft
from werkzeug.security import generate_password_hash


class InvoiceDraftApiTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        flask_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()
        self._ctx = flask_app.app_context()
        self._ctx.push()
        db.create_all()
        user = User(
            username="draftuser",
            email="draft@example.com",
            password=generate_password_hash("secret"),
        )
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self._ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["username"] = "draftuser"

    def test_get_empty_draft(self):
        self._login()
        rv = self.client.get("/api/invoice-draft")
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIsNone(data["draft"])
        self.assertIsNone(data["updated_at"])

    def test_put_get_roundtrip(self):
        self._login()
        payload = {"date": "2025-01-01", "items": [], "savedAt": 1}
        rv = self.client.put(
            "/api/invoice-draft",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)
        rv2 = self.client.get("/api/invoice-draft")
        self.assertEqual(rv2.status_code, 200)
        data = json.loads(rv2.data)
        self.assertEqual(data["draft"]["date"], "2025-01-01")
        self.assertIsNotNone(data["updated_at"])

    def test_delete_clears_draft(self):
        self._login()
        self.client.put(
            "/api/invoice-draft",
            data=json.dumps({"savedAt": 1}),
            content_type="application/json",
        )
        rv = self.client.delete("/api/invoice-draft")
        self.assertEqual(rv.status_code, 200)
        row = db.session.query(InvoiceDraft).filter_by(user_id=self.user_id).first()
        self.assertIsNone(row)

    def test_prefixed_path_put(self):
        self._login()
        rv = self.client.put(
            "/invoice/api/invoice-draft",
            data=json.dumps({"savedAt": 2}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 200)


if __name__ == "__main__":
    unittest.main()
