"""Tests for the REST API getter helper."""

import requests

from src.helper_services.rest_api_getter import RestApiGetterMethod
from test.helper_services.fixtures import API_PAYLOAD, FakeResponse


def test_get_pages_calls_api_with_expected_parameters_and_returns_payload(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        response = FakeResponse(json_data=API_PAYLOAD)
        response.raise_for_status = lambda: captured.__setitem__("raise_for_status_called", True)
        return response

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    result = getter.get_pages("https://example.com/document", "pages")

    assert result == API_PAYLOAD["pages"]
    assert captured["url"] == "https://example.com/api"
    assert captured["kwargs"]["timeout"] == 30
    assert captured["kwargs"]["verify"] is False
    assert captured["raise_for_status_called"] is True


def test_get_pages_returns_empty_list_when_search_key_is_missing(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")

    def fake_get(*args, **kwargs):
        response = FakeResponse(json_data={"other_pages": ["abc"]})
        response.raise_for_status = lambda: None
        return response

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    assert getter.get_pages("https://example.com/document", "pages") == []


def test_get_pages_returns_empty_list_when_request_fails(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")

    def fake_get(*args, **kwargs):
        raise requests.RequestException("timeout")

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    assert getter.get_pages("https://example.com/document", "pages") == []
