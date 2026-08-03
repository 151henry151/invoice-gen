"""Tests for phone_utils formatting and parsing."""

from phone_utils import (
    compose_phone,
    format_us_national,
    is_valid_phone,
    parse_stored_phone,
)


def test_format_us_national_progressive():
    assert format_us_national("") == ""
    assert format_us_national("5") == "(5"
    assert format_us_national("555") == "(555"
    assert format_us_national("5551") == "(555) 1"
    assert format_us_national("555123") == "(555) 123"
    assert format_us_national("5551234") == "(555) 123-4"
    assert format_us_national("5551234567") == "(555) 123-4567"
    assert format_us_national("55512345678999") == "(555) 123-4567"


def test_compose_phone_us_default():
    assert compose_phone("1", "5551234567") == "+1 (555) 123-4567"
    assert compose_phone("1", "") == ""


def test_parse_stored_phone_defaults_to_us():
    assert parse_stored_phone("(555) 123-4567") == ("1", "5551234567")
    assert parse_stored_phone("5551234567") == ("1", "5551234567")
    assert parse_stored_phone("15551234567") == ("1", "5551234567")


def test_parse_stored_phone_with_plus():
    assert parse_stored_phone("+1 (555) 123-4567") == ("1", "5551234567")
    assert parse_stored_phone("+44 7700 900123") == ("44", "7700900123")


def test_is_valid_phone():
    assert is_valid_phone("+1 (555) 123-4567")
    assert is_valid_phone("5551234567")
    assert not is_valid_phone("555")
    assert not is_valid_phone("")
