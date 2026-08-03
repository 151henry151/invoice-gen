"""Tests for address combine/parse and form extraction."""

from address_utils import address_from_form, combine_address, parse_address


def test_combine_address_omits_empty_line2():
    assert (
        combine_address("123 Main St", "", "Springfield", "VT", "05156", "United States")
        == "123 Main St, Springfield, VT, 05156, United States"
    )


def test_parse_address_without_line2_keeps_city_state_zip():
    parsed = parse_address("123 Main St, Springfield, VT, 05156, United States")
    assert parsed["address_line1"] == "123 Main St"
    assert parsed["address_line2"] == ""
    assert parsed["city"] == "Springfield"
    assert parsed["state"] == "VT"
    assert parsed["postal_code"] == "05156"
    assert parsed["country"] == "United States"


def test_parse_address_with_line2():
    parsed = parse_address("123 Main St, Apt 2, Springfield, VT, 05156, United States")
    assert parsed["address_line1"] == "123 Main St"
    assert parsed["address_line2"] == "Apt 2"
    assert parsed["city"] == "Springfield"


def test_address_from_form_prefers_split_client_fields():
    form = {
        "client_address_line1": "123 Main St",
        "client_address_line2": "",
        "client_city": "Springfield",
        "client_state": "VT",
        "client_postal_code": "05156",
        "client_country": "United States",
    }
    assert (
        address_from_form(form, prefix="client_")
        == "123 Main St, Springfield, VT, 05156, United States"
    )


def test_address_from_form_legacy_address_field():
    assert address_from_form({"address": "123 Legacy Rd"}, prefix="client_") == "123 Legacy Rd"
