"""Tests for the Kramerius 5 server implementation."""

from unittest.mock import Mock, patch

import pytest

from src.helper_services.base_getter import CertificateValidationError
from src.helper_services.rest_api_getter import RestApiGetterMethod
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


def test_init_should_match_kramerius_5_configuration(kramerius_5_server):
    """Test that Kramerius 5 server metadata matches expected configuration."""
    server = Kramerius5ServerType()

    assert server.server_type == "kramerius"
    assert server.server_version == 5
    assert "dom_selenium" in server.document_info_methods
    assert server.document_info_methods["dom_selenium"]["page_search"]["id"].pattern == r"page-id-(uuid:[a-f0-9-]+)"


def test_get_document_pages_should_use_helper_class_and_return_values(
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


def test_get_document_pages_should_retry_with_next_method_on_failure(
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


def test_get_document_pages_should_raise_value_error_when_all_strategies_fail(
    monkeypatch, document_url, page_pattern, failing_getter, kramerius_5_server
):
    """Test that get_document_pages raises ValueError when all strategies fail."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"instance_params": {}, "page_search": page_pattern}}

    monkeypatch.setattr(Kramerius5ServerType, "_get_class_name", lambda self, page_method: "DomSeleniumGetterMethod")
    monkeypatch.setattr(Kramerius5ServerType, "_get_class_from_name", lambda self, name: failing_getter)

    with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
        kramerius_5_server.get_document_pages(document_url)


def test_get_document_pages_should_reuse_active_getter(document_url, kramerius_5_server):
    """Test that get_document_pages reuses the active getter instance."""
    kramerius_5_server.document_info_methods = {"dom_selenium": {"title_search": None, "page_search": None}}

    class DomSeleniumGetterMethod:
        def get_pages(self, document_url, xpath):
            return ["active-page"]

    kramerius_5_server.active_getter_instance = DomSeleniumGetterMethod()

    assert kramerius_5_server.get_document_pages(document_url) == ["active-page"]


def test_get_document_pages_should_discard_active_getter_on_failure(
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


def test_get_document_pages_should_raise_value_error_when_no_pages_returned(
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


def test_get_document_title_should_return_value_when_helper_finds_it(
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


def test_get_document_subtitle_should_return_empty_string_when_helper_fails(
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


def test_get_document_title_should_return_empty_string_when_no_helper_returns_title(
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


def test_get_document_title_should_discard_failed_active_getter_and_use_next_helper(
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


def test_get_document_pages_should_use_fallback_after_certificate_failure(document_url, kramerius_5_server):
    server = kramerius_5_server
    server.document_info_methods = {
        "one": {"instance_params": {}, "page_search": {}},
        "two": {"instance_params": {}, "page_search": {}},
    }
    server.active_getter_instance = Mock()
    error = CertificateValidationError("certificate failed")
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(server, "_get_document_partial_information", side_effect=[error, ["page"]]),
    ):
        result = server.get_document_pages(document_url)

    assert result == ["page"]


def test_get_document_pages_should_preserve_certificate_failure_when_fallback_is_empty(
    document_url, kramerius_5_server, caplog
):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"instance_params": {}, "page_search": {}}}
    server.active_getter_instance = Mock()
    error = CertificateValidationError("certificate failed")
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(server, "_get_document_partial_information", side_effect=[error, []]),
        pytest.raises(CertificateValidationError),
    ):
        server.get_document_pages(document_url)

    assert "Traceback" not in caplog.text


def test_get_document_title_should_not_try_fallback_when_active_getter_returns_empty(document_url, kramerius_5_server):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"title_search": {}}}
    server.active_getter_instance = Mock()
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name") as get_class,
        patch.object(server, "_get_document_partial_information", return_value=""),
    ):
        result = server.get_document_title(document_url)

    assert result == ""
    get_class.assert_not_called()


def test_get_document_title_should_continue_after_empty_fallback(document_url, kramerius_5_server):
    server = kramerius_5_server
    server.document_info_methods = {
        "one": {"instance_params": {}, "title_search": {}},
        "two": {"instance_params": {}, "title_search": {}},
    }
    server.active_getter_instance = Mock()
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(
            server, "_get_document_partial_information", side_effect=[ValueError("failed"), "", "fallback title"]
        ),
    ):
        result = server.get_document_title(document_url)

    assert result == "fallback title"


@pytest.mark.parametrize("cached_certificate_failure", [True, False])
def test_get_document_pages_should_keep_diagnostics_for_mixed_failures(
    document_url, kramerius_5_server, caplog, cached_certificate_failure
):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"instance_params": {}, "page_search": {}}}
    server.active_getter_instance = Mock()
    certificate_error = CertificateValidationError("certificate failed")
    other_error = ValueError("other failure")
    failures = [certificate_error, other_error] if cached_certificate_failure else [other_error, certificate_error]
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(server, "_get_document_partial_information", side_effect=failures),
    ):
        with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
            server.get_document_pages(document_url)

    assert "Could not find document information" in caplog.text
    assert "Traceback" in caplog.text


def test_get_document_pages_should_propagate_most_recent_certificate_failure(document_url, kramerius_5_server):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"instance_params": {}, "page_search": {}}}
    server.active_getter_instance = Mock()
    last_error = CertificateValidationError("fallback certificate failed")
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(
            server,
            "_get_document_partial_information",
            side_effect=[CertificateValidationError("cached certificate failed"), last_error],
        ),
    ):
        with pytest.raises(CertificateValidationError) as exc_info:
            server.get_document_pages(document_url)

    assert exc_info.value is last_error


def test_get_document_title_should_return_empty_on_certificate_only_failures(document_url, kramerius_5_server, caplog):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"instance_params": {}, "title_search": {}}}
    server.active_getter_instance = Mock()
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock()),
        patch.object(
            server, "_get_document_partial_information", side_effect=CertificateValidationError("certificate failed")
        ),
    ):
        result = server.get_document_title(document_url)

    assert result == ""
    assert "Traceback" not in caplog.text


def test_get_document_title_should_fall_back_on_invalid_rest_metadata(document_url, kramerius_5_server, caplog):
    server = kramerius_5_server
    server.document_info_methods = {
        "rest_api": {"instance_params": {}, "title_search": "title"},
        "fallback": {"instance_params": {}, "title_search": "//h1"},
    }
    server.active_getter_instance = RestApiGetterMethod(
        {
            "identifier_pattern": "x",
            "base_api_url": "https://example.com/",
            "document_api_url": "doc",
            "document_pages_api_url": "pages",
        }
    )
    server.active_getter_instance.document_json = {"title": ["unexpected"]}
    fallback = Mock()
    fallback.get_title.return_value = "Fallback title"
    with patch.object(server, "_get_class_from_name", side_effect=[None, Mock(return_value=fallback)]):
        result = server.get_document_title(document_url)

    assert result == "Fallback title"
    assert "Invalid REST metadata" in caplog.text


def test_get_document_pages_should_keep_diagnostics_when_fallback_constructor_fails(
    document_url, kramerius_5_server, caplog
):
    server = kramerius_5_server
    server.document_info_methods = {"one": {"instance_params": {}, "page_search": {}}}
    server.active_getter_instance = Mock()
    with (
        patch.object(server, "get_getter_name", return_value="one"),
        patch.object(server, "_get_class_from_name", return_value=Mock(side_effect=ValueError("constructor failed"))),
        patch.object(
            server, "_get_document_partial_information", side_effect=CertificateValidationError("certificate failed")
        ),
    ):
        with pytest.raises(ValueError, match="Could not find pages for Kramerius 5 server"):
            server.get_document_pages(document_url)

    assert "Could not find document information" in caplog.text
