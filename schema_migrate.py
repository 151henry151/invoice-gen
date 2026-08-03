"""Lightweight SQLite schema upgrades for invoice-gen."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import inspect, text

from models import db


def _sqlite_columns(table: str):
    rows = db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}  # name


def ensure_invoice_draft_schema():
    """
    Upgrade invoice_draft from one-row-per-user to many drafts with invoice_number.

    Safe to call on every startup. No-op when schema already matches.
    """
    bind = db.session.get_bind()
    inspector = inspect(bind)
    if "invoice_draft" not in inspector.get_table_names():
        return

    cols = _sqlite_columns("invoice_draft")
    if "invoice_number" in cols:
        return

    # Recreate table with new shape.
    db.session.execute(text("PRAGMA foreign_keys=OFF"))
    db.session.execute(
        text(
            """
            CREATE TABLE invoice_draft_new (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                invoice_number VARCHAR(50) NOT NULL,
                payload TEXT NOT NULL,
                updated_at DATETIME NOT NULL,
                CONSTRAINT uq_invoice_draft_user_number UNIQUE (user_id, invoice_number),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """
        )
    )
    old_rows = db.session.execute(
        text("SELECT id, user_id, payload, updated_at FROM invoice_draft")
    ).fetchall()
    for row in old_rows:
        draft_id, user_id, payload, updated_at = row
        number = None
        try:
            data = json.loads(payload) if payload else {}
            number = data.get("invoiceNumber") or data.get("invoice_number")
        except Exception:
            number = None
        if not number:
            number = f"DRAFT-{draft_id}"
        updated_at = updated_at or datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        db.session.execute(
            text(
                """
                INSERT INTO invoice_draft_new (id, user_id, invoice_number, payload, updated_at)
                VALUES (:id, :user_id, :invoice_number, :payload, :updated_at)
                """
            ),
            {
                "id": draft_id,
                "user_id": user_id,
                "invoice_number": str(number),
                "payload": payload or "{}",
                "updated_at": updated_at,
            },
        )
    db.session.execute(text("DROP TABLE invoice_draft"))
    db.session.execute(text("ALTER TABLE invoice_draft_new RENAME TO invoice_draft"))
    db.session.execute(text("PRAGMA foreign_keys=ON"))
    db.session.commit()
