"""Tests for the REST API getter helper."""

import requests

import pytest
import responses
from src.helper_services.rest_api_getter import RestApiGetterMethod
from test.helper_services.fixtures import api_payload


@pytest.fixture
def rest_api_getter():
    """Fixture providing a RestApiGetterMethod instance."""
    return RestApiGetterMethod("https://example.com/api")


@responses.activate
def test_get_pages_calls_api_with_expected_parameters_and_returns_payload(rest_api_getter, api_payload):
    responses.add(responses.GET, "https://example.com/api", json=api_payload, status=200)

    result = rest_api_getter.get_pages("https://example.com/document", "pages")

    assert result == api_payload["pages"]
    assert responses.calls[0].request.url == "https://example.com/api"


@responses.activate
def test_get_pages_returns_empty_list_when_search_key_is_missing(rest_api_getter):
    responses.add(responses.GET, "https://example.com/api", json={"other_pages": ["abc"]}, status=200)

    assert rest_api_getter.get_pages("https://example.com/document", "pages") == []


@responses.activate
def test_get_pages_returns_empty_list_when_request_fails(rest_api_getter):
    responses.add(responses.GET, "https://example.com/api", body=requests.RequestException("timeout"))

    assert rest_api_getter.get_pages("https://example.com/document", "pages") == []


@responses.activate
def test_get_document_source_handles_request_exception(rest_api_getter):
    responses.add(responses.GET, "https://example.com/api", body=requests.RequestException("network"))

    assert rest_api_getter.get_document_source("https://example.com/document") is None


@responses.activate
def test_get_document_source_handles_non_200(rest_api_getter, api_payload):
    responses.add(responses.GET, "https://example.com/api", json=api_payload, status=500)

    assert rest_api_getter.get_document_source("https://example.com/document") is None


@responses.activate
def test_get_document_source_handles_raise_for_status():
    responses.add(responses.GET, "http://api", status=500)
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
