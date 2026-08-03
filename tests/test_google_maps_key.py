"""Tests for Google Maps API key resolution."""
import os
from pathlib import Path

import app as app_module


def test_get_google_maps_api_key_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "env-key-123")
    monkeypatch.chdir(tmp_path)
    assert app_module.get_google_maps_api_key() == "env-key-123"


def test_get_google_maps_api_key_from_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "credentials.ini").write_text(
        "[production]\nGOOGLE_MAPS_API_KEY=file-key-456\n"
    )
    assert app_module.get_google_maps_api_key() == "file-key-456"


def test_client_details_includes_maps_key(auth_client, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "template-key-789")
    resp = auth_client.get("/client_details?new=true")
    assert resp.status_code == 200
    assert b"template-key-789" in resp.data
    assert b"maps.googleapis.com" in resp.data or b"address-autocomplete" in resp.data
