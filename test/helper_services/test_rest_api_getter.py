"""Tests for the REST API getter helper."""

import requests
from requests import HTTPError

from src.helper_services.rest_api_getter import RestApiGetterMethod
from test.helper_services.fixtures import API_PAYLOAD, FakeResponse


class RaiseResp:
    def raise_for_status(self):
        raise requests.HTTPError("bad status")

    def json(self):
        return {}


def test_get_pages_calls_api_with_expected_parameters_and_returns_payload(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")
    captured = {}

    def fake_get(url, **kwargs):
        captured["source_url"] = url
        captured["kwargs"] = kwargs
        response = FakeResponse(json_data=API_PAYLOAD)
        response.raise_for_status = lambda: captured.__setitem__("raise_for_status_called", True)
        return response

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    result = getter.get_pages("https://example.com/document", "pages")

    assert result == API_PAYLOAD["pages"]
    assert captured["source_url"] == "https://example.com/api"
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


def test_get_document_source_handles_request_exception(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")

    def fake_get(*args, **kwargs):
        raise requests.RequestException("network")

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    assert getter.get_document_source("https://example.com/document") is None


def test_get_document_source_handles_non_200(monkeypatch):
    getter = RestApiGetterMethod("https://example.com/api")

    def fake_get(*args, **kwargs):
        return FakeResponse(json_data=API_PAYLOAD, exc=HTTPError("bad status"))

    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", fake_get)

    assert getter.get_document_source("https://example.com/document") is None


def test_get_document_source_handles_raise_for_status(monkeypatch):
    monkeypatch.setattr("src.helper_services.rest_api_getter.requests.get", lambda *a, **k: RaiseResp())

    inst = RestApiGetterMethod("http://api")
    assert inst.get_document_source("/doc") is None


def test_get_pages_handles_none_document_source(monkeypatch):
    monkeypatch.setattr(RestApiGetterMethod, "get_document_source", lambda self, url: None)

    inst = RestApiGetterMethod("http://api")
    assert inst.get_pages("/doc", "pages") == []


def test_get_title_handles_json_error(monkeypatch):
    class BadResp:
        def json(self):
            raise ValueError("bad json")

    monkeypatch.setattr(RestApiGetterMethod, "get_document_source", lambda self, url: BadResp())

    inst = RestApiGetterMethod("http://api")
    assert inst.get_title("/doc", "//h1") == ""
    assert inst.get_subtitle("/doc", "//h1") == ""
