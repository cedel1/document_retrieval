"""Tests for the Kramerius 5 server implementation."""

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

    def fake_get_class_from_name(self, name):
        captured["name"] = name
        return FakeGetter

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "FakeGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class_from_name)

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

    def fake_get_class_name(self, page_method):
        mapping = {
            "dom_selenium": "FailingGetter",
            "simple_dom": "SuccessAfterFailingGetter",
        }
        return mapping[page_method]

    def fake_get_class_from_name(self, name):
        return defs[name]

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", fake_get_class_name)
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class_from_name)

    result = server.get_document_pages(DOCUMENT_URL)

    assert result == ["uuid-3"]


def test_get_document_pages_raises_when_every_strategy_fails(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": PAGE_PATTERN}

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "FailingGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: FailingGetter)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        server.get_document_pages(DOCUMENT_URL)


def test_get_document_pages_reuses_active_getter():
    server = Kramerius5ServerType()

    class ActiveGetter:
        def get_pages(self, document_url, xpath):
            return ["active-page"]

    server.active_getter_instance = ActiveGetter()

    assert server.get_document_pages(DOCUMENT_URL) == ["active-page"]


def test_get_document_pages_discards_active_getter_after_failure(monkeypatch):
    server = Kramerius5ServerType()

    class ActiveGetter:
        def get_pages(self, document_url, xpath):
            raise ValueError("stale getter")

    server.active_getter_instance = ActiveGetter()
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "FakeGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: FakeGetter)

    assert server.get_document_pages(DOCUMENT_URL) == ["uuid-1", "uuid-2"]
    assert isinstance(server.active_getter_instance, FakeGetter)


def test_get_document_pages_raises_when_getter_returns_no_pages(monkeypatch):
    server = Kramerius5ServerType()

    class EmptyGetter:
        def get_pages(self, document_url, search_attribute):
            return []

    server.document_page_methods = {"empty": PAGE_PATTERN}
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "EmptyGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: EmptyGetter)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        server.get_document_pages(DOCUMENT_URL)


def test_get_document_name_returns_value_when_helper_finds_it(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": None}

    class NameGetter:
        def get_title(self, document_url, xpath):
            return "Found Title"

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "NameGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: NameGetter)

    assert server.get_document_title(DOCUMENT_URL) == "Found Title"


def test_get_document_subtitle_returns_value_when_helper_finds_it(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": None}

    class SubtitleGetter:
        def get_subtitle(self, document_url, xpath):
            return "Found Subtitle"

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "SubtitleGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: SubtitleGetter)

    assert server.get_document_subtitle(DOCUMENT_URL) == "Found Subtitle"


def test_get_document_subtitle_returns_empty_string_when_helpers_fail(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": None}

    class FailingSubtitleGetter:
        def get_subtitle(self, document_url, xpath):
            raise ValueError("missing subtitle")

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "FailingSubtitleGetter")
    monkeypatch.setattr(
        Kramerius5ServerType, "_get_class_from_name", lambda self, name: FailingSubtitleGetter
    )

    assert server.get_document_subtitle(DOCUMENT_URL) == ""


def test_get_document_title_uses_active_getter(monkeypatch):
    server = Kramerius5ServerType()

    class ActiveGetter:
        def get_title(self, document_url, xpath):
            return "Active Title"

    server.active_getter_instance = ActiveGetter()

    assert server.get_document_title(DOCUMENT_URL) == "Active Title"


def test_get_document_name_raises_when_no_helper_returns_name(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"dom_selenium": None}

    class EmptyNameGetter:
        def get_title(self, document_url, xpath):
            return ""

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "EmptyNameGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: EmptyNameGetter)

    assert server.get_document_title(DOCUMENT_URL) == ""


def test_get_document_title_discards_failed_active_getter_and_uses_next_helper(monkeypatch):
    server = Kramerius5ServerType()

    class ActiveGetter:
        def get_title(self, document_url, xpath):
            raise ValueError("stale title getter")

    class FallbackGetter:
        def get_title(self, document_url, xpath):
            return "Fallback Title"

    server.active_getter_instance = ActiveGetter()
    server.document_page_methods = {"dom_selenium": None}
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "FallbackGetter")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: FallbackGetter)

    assert server.get_document_title(DOCUMENT_URL) == "Fallback Title"
    assert server.active_getter_instance is None


def test_get_document_title_continues_on_value_error_and_uses_next_method(monkeypatch):
    server = Kramerius5ServerType()
    server.document_page_methods = {"one": None, "two": None}

    class RaisingGetter:
        def get_title(self, document_url, xpath):
            raise ValueError("fail")

    class SuccessGetter:
        def get_title(self, document_url, xpath):
            return "Recovered Title"

    classes = iter([RaisingGetter, SuccessGetter])

    def fake_get_class(self, class_name):
        return next(classes)

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "X")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class)

    assert server.get_document_title(DOCUMENT_URL) == "Recovered Title"
