import pytest
from .ensure_dict import ensure_dict


def test_returns_dict_when_given_dict():
    candidate = {"foo": "bar"}
    result = ensure_dict(candidate)
    assert result == candidate  # Should return same dict
    assert result is candidate  # Same reference, not a copy

def test_wraps_string_with_default_key():
    candidate = "value"
    result = ensure_dict(candidate)
    assert result == {"input": "value"}

def test_wraps_string_with_custom_key():
    candidate = "value"
    result = ensure_dict(candidate, key="custom")
    assert result == {"custom": "value"}

def test_wraps_int_with_custom_key():
    candidate = 14
    result = ensure_dict(candidate, key="my_number")
    assert result == {"my_number": 14}

def test_empty_dict_returns_same():
    candidate = {}
    result = ensure_dict(candidate)
    assert result == {}
    assert result is candidate

def test_empty_string_returns_wrapped():
    candidate = ""
    result = ensure_dict(candidate)
    assert result == {"input": ""}

