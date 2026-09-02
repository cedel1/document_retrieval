"""Tests for the Kramerius 5 server implementation."""

import re

import pytest

from src.servers.kramerius_5_server import Kramerius5ServerType
from test.servers.fixtures import DOCUMENT_URL, PAGE_PATTERN


class FakeGetter:
    def __init__(self):
        self.calls = []

    def get_pages(self, document_url: str, search_attribute: str | dict):
        self.calls.append((document_url, search_attribute))
        return ["uuid-1", "uuid-2"]


class FailingGetter:
    def __init__(self):
        self.calls = []

    def get_pages(self, document_url: str, search_attribute: str | dict):
        self.calls.append((document_url, search_attribute))
        raise ValueError("bad")


class SuccessAfterFailingGetter:
    def __init__(self):
        self.calls = []

    def get_pages(self, document_url: str, search_attribute: str | dict):
        self.calls.append((document_url, search_attribute))
        return ["uuid-3"]


def test_server_metadata_matches_kramerius_5_configuration():
    server = Kramerius5ServerType()

    assert server.server_type == "kramerius"
    assert server.server_version == 5
    assert "dom_selenium" in server.document_page_methods
    assert server.document_page_methods["dom_selenium"]["id"].pattern == r"page-id-uuid:([a-f0-9-]+)"


def test_get_document_pages_uses_helper_class_and_returned_values(monkeypatch):
    server = Kramerius5ServerType()
    captured = {}

    def fake_get_class_from_name(name):
        captured["name"] = name
        return FakeGetter

    monkeypatch.setattr(server, "_get_class_name", lambda page_method: "FakeGetter")
    monkeypatch.setattr(server, "_get_class_from_name", fake_get_class_from_name)

    result = server.get_document_pages(DOCUMENT_URL)

    assert result == ["uuid-1", "uuid-2"]
    assert captured["name"] == "FakeGetter"


def test_get_document_pages_retries_next_method_when_first_fails(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {
        "dom_selenium": PAGE_PATTERN,
        "simple_dom": PAGE_PATTERN,
    }

    defs = {
        "FailingGetter": FailingGetter,
        "SuccessAfterFailingGetter": SuccessAfterFailingGetter,
    }

    def fake_get_class_name(page_method):
        mapping = {
            "dom_selenium": "FailingGetter",
            "simple_dom": "SuccessAfterFailingGetter",
        }
        return mapping[page_method]

    def fake_get_class_from_name(name):
        return defs[name]

    monkeypatch.setattr(server, "_get_class_name", fake_get_class_name)
    monkeypatch.setattr(server, "_get_class_from_name", fake_get_class_from_name)

    result = server.get_document_pages(DOCUMENT_URL)

    assert result == ["uuid-3"]


def test_get_document_pages_raises_when_every_strategy_fails(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": PAGE_PATTERN}

    monkeypatch.setattr(server, "_get_class_name", lambda page_method: "FailingGetter")
    monkeypatch.setattr(server, "_get_class_from_name", lambda name: FailingGetter)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        server.get_document_pages(DOCUMENT_URL)
