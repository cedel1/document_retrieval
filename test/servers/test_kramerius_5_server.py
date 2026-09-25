"""Tests for the Kramerius 5 server implementation."""

import pytest

from src.servers.kramerius_5_server import Kramerius5ServerType
from test.servers.fixtures import (
    document_url,
    page_pattern,
    fake_getter,
    failing_getter,
    success_after_failing_getter,
    getter_params,
    document_info_methods_mock,
    kramerius_5_server,
)


def test_server_metadata_should_match_kramerius_5_configuration(kramerius_5_server):
    """Test that Kramerius 5 server metadata matches expected configuration."""
    server = Kramerius5ServerType()

    assert server.server_type == "kramerius"
    assert server.server_version == 5
    assert "dom_selenium" in server.document_info_methods
    assert server.document_info_methods["dom_selenium"]["page_search"]["id"].pattern == r"page-id-uuid:([a-f0-9-]+)"


def test_get_document_pages_should_use_helper_class_and_returned_values(
    monkeypatch, document_url, fake_getter, kramerius_5_server
):
    """Test that get_document_pages uses the helper class and returns its values."""
    captured = {}

    def fake_get_class_from_name(self, name):
        captured["name"] = name
        return fake_getter

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class_from_name)

    result = kramerius_5_server.get_document_pages(document_url)

    assert result == ["uuid-1", "uuid-2"]
    assert captured["name"] == "DomSeleniumGetterMethod"


def test_get_document_pages_should_retry_with_next_method_when_first_fails(
    monkeypatch, document_url, page_pattern, failing_getter, success_after_failing_getter, kramerius_5_server
):
    """Test that get_document_pages retries the next method when the first fails."""
    kramerius_5_server.document_info_methods = {
        "dom_selenium": {"instance_params": {}, "page_search": page_pattern},
        "simple_dom": {"instance_params": {}, "page_search": page_pattern},
    }

    defs = {
        "DomSeleniumGetterMethod": failing_getter,
        "SimpleDomGetterMethod": success_after_failing_getter,
    }

    def fake_get_class_name(self, page_method):
        mapping = {
            "dom_selenium": "DomSeleniumGetterMethod",
            "simple_dom": "SimpleDomGetterMethod",
        }
        return mapping[page_method]

    def fake_get_class_from_name(self, name):
        return defs[name]

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", fake_get_class_name)
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class_from_name)

    result = kramerius_5_server.get_document_pages(document_url)

    assert result == ["uuid-3"]


def test_get_document_pages_should_raise_value_error_when_every_strategy_fails(
    monkeypatch, document_url, page_pattern, failing_getter, kramerius_5_server
):
    """Test that get_document_pages raises ValueError when all strategies fail."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"instance_params": {}, "page_search": page_pattern}}

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: failing_getter)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        kramerius_5_server.get_document_pages(document_url)


def test_get_document_pages_should_reuses_active_getter(document_url, kramerius_5_server):
    """Test that get_document_pages reuses the active getter instance."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"title_search": None, "page_search": None}}

    class DomSeleniumGetterMethod:
        def get_pages(self, document_url, xpath):
            return ["active-page"]

    kramerius_5_server.active_getter_instance = DomSeleniumGetterMethod()

    assert kramerius_5_server.get_document_pages(document_url) == ["active-page"]


def test_get_document_pages_should_discard_active_getter_after_failure(
    monkeypatch, document_url, fake_getter, getter_params, page_pattern, kramerius_5_server
):
    """Test that get_document_pages discards a failed active getter and tries the next method."""
    kramerius_5_server.document_info_methods = {
        "dom_selenium": {"instance_params": {}, "title_search": None, "page_search": None}
    }

    class StaleDomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_pages(self, document_url, xpath):
            raise ValueError("stale getter")

    kramerius_5_server.active_getter_instance = StaleDomSeleniumGetterMethod(getter_params)
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: fake_getter)

    # Mock get_getter_name to return dom_selenium for the stale getter
    def fake_get_getter_name(self):
        if (
            self.active_getter_instance
            and self.active_getter_instance.__class__.__name__ == "StaleDomSeleniumGetterMethod"
        ):
            return "dom_selenium"
        return "dom_selenium"

    monkeypatch.setattr(Kramerius5ServerType, "get_getter_name", fake_get_getter_name)

    assert kramerius_5_server.get_document_pages(document_url) == ["uuid-1", "uuid-2"]
    # The implementation will try the next method after discarding the stale one
    assert isinstance(kramerius_5_server.active_getter_instance, fake_getter)


def test_get_document_pages_should_raise_value_error_when_getter_returns_no_pages(
    monkeypatch, document_url, page_pattern, getter_params, kramerius_5_server
):
    """Test that get_document_pages raises ValueError when getter returns empty page list."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"instance_params": {}, "page_search": page_pattern}}

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_pages(self, document_url, page_pattern):
            return []

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        kramerius_5_server.get_document_pages(document_url)


def test_get_document_name_should_return_value_when_helper_finds_it(
    monkeypatch, document_url, getter_params, kramerius_5_server
):
    """Test that get_document_title returns the value when the helper finds it."""

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_title(self, document_url, xpath):
            return "Found Title"

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    assert kramerius_5_server.get_document_title(document_url) == "Found Title"


def test_get_document_subtitle_should_return_value_when_helper_finds_it(monkeypatch, document_url, kramerius_5_server):
    """Tests that document_subtitle returns the value when the helper finds it."""

    class DomSeleniumGetterMethod:
        def __init__(self, document_page_identifier):
            self.document_page_identifier = {}

        def get_subtitle(self, document_url, xpath):
            return "Found Subtitle"

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    assert kramerius_5_server.get_document_subtitle(document_url) == "Found Subtitle"


def test_get_document_subtitle_should_return_empty_string_when_helpers_fails(
    monkeypatch, document_url, getter_params, kramerius_5_server
):
    """Tests that get_document_subtitle returns empty string when helpers fails."""

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_subtitle(self, document_url, xpath):
            raise ValueError("missing subtitle")

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    assert kramerius_5_server.get_document_subtitle(document_url) == ""


def test_get_document_title_should_use_active_getter(document_url, kramerius_5_server):
    """Tests that get_document_title uses active getter."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"title_search": None}}

    class DomSeleniumGetterMethod:
        def get_title(self, document_url, xpath):
            return "Active Title"

    kramerius_5_server.active_getter_instance = DomSeleniumGetterMethod()

    assert kramerius_5_server.get_document_title(document_url) == "Active Title"


def test_get_document_title_should_return_empty_titles_when_no_helper_returns_title(
    monkeypatch, document_url, getter_params, kramerius_5_server
):
    """Tests that get_document_title returns empty string when no helper returns a title."""

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_title(self, document_url, xpath):
            return ""

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    assert kramerius_5_server.get_document_title(document_url) == ""


def test_get_document_title_should_discard_failed_active_getter_and_uses_next_helper(
    monkeypatch, document_url, getter_params, kramerius_5_server
):
    """Tests that get_document_title discards failed active getter and uses next helper."""

    class StaleGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_title(self, document_url, xpath):
            raise ValueError("stale title getter")

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = {}

        def get_title(self, document_url, xpath):
            return "Fallback Title"

    kramerius_5_server.active_getter_instance = StaleGetterMethod(getter_params)
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: DomSeleniumGetterMethod)

    # Mock get_getter_name to handle the stale getter
    def fake_get_getter_name(self):
        if self.active_getter_instance and self.active_getter_instance.__class__.__name__ == "StaleGetterMethod":
            return "dom_selenium"
        return "dom_selenium"

    monkeypatch.setattr(Kramerius5ServerType, "get_getter_name", fake_get_getter_name)

    assert kramerius_5_server.get_document_title(document_url) == "Fallback Title"
    # The successful fallback getter should now be the active getter
    assert isinstance(kramerius_5_server.active_getter_instance, DomSeleniumGetterMethod)


def test_get_document_title_should_continue_on_value_error_and_use_next_method(
    monkeypatch, document_url, kramerius_5_server
):
    """Tests that get_document_title continues on value error and uses next method."""
    kramerius_5_server.document_info_methods = {
        "one": {"instance_params": {}, "title_search": None},
        "two": {"instance_params": {}, "title_search": None},
    }

    class OneGetterMethod:
        def __init__(self, document_page_identifier):
            self.document_page_identifier = document_page_identifier

        def get_title(self, document_url, xpath):
            raise ValueError("fail")

    class TwoGetterMethod:
        def __init__(self, document_page_identifier):
            self.document_page_identifier = document_page_identifier

        def get_title(self, document_url, xpath):
            return "Recovered Title"

    getters = {
        "OneGetterMethod": OneGetterMethod,
        "TwoGetterMethod": TwoGetterMethod,
    }

    def fake_get_class_name(self, page_method):
        mapping = {
            "one": "OneGetterMethod",
            "two": "TwoGetterMethod",
        }
        return mapping[page_method]

    def fake_get_class_from_name(self, name):
        return getters[name]

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", fake_get_class_name)
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", fake_get_class_from_name)

    assert kramerius_5_server.get_document_title(document_url) == "Recovered Title"
