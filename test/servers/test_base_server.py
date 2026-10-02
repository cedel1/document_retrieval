"""Tests for the abstract server base type."""

import importlib

import pytest

from src.helper_services.rest_api_getter import RestApiGetterMethod
from src.helper_services.simple_dom_getter import SimpleDomGetterMethod
from src.servers.base_server import BaseServerType
from test.servers.fixtures import example_server_type, document_url


def test_base_server_str_includes_server_type_and_version(example_server_type):
    """Test that the server string representation includes both type and version."""
    assert str(example_server_type()) == "example_3"


def test_get_class_name_formats_registry_names():
    """Test that getter method names are converted to the expected class names."""
    assert BaseServerType._get_class_name("dom_selenium") == "DomSeleniumGetterMethod"
    assert BaseServerType._get_class_name("simple_dom") == "SimpleDomGetterMethod"
    assert BaseServerType._get_class_name("rest_api") == "RestApiGetterMethod"


def test_get_class_from_name_imports_helper_class(monkeypatch, example_server_type):
    """Test that the helper class is imported from the helper services module."""

    class FakeGetter:
        pass

    fake_module = type("FakeModule", (), {"SimpleDomGetterMethod": FakeGetter})

    def fake_import(name):
        assert name == "src.helper_services"
        return fake_module

    monkeypatch.setattr(importlib, "import_module", fake_import)

    result = example_server_type()._get_class_from_name("SimpleDomGetterMethod")

    assert result is FakeGetter


def test_get_class_from_name_returns_none_for_missing_helper(monkeypatch, example_server_type):
    """Test that unknown helper names resolve to None instead of raising."""
    fake_module = type("FakeModule", (), {})

    monkeypatch.setattr(importlib, "import_module", lambda module_name: fake_module)

    assert example_server_type()._get_class_from_name("DoesNotExist") is None


def test_get_class_from_name_returns_none_when_module_import_fails(monkeypatch, example_server_type):
    """Test that missing import modules are handled gracefully."""

    def fake_import(name):
        raise ImportError("missing module")

    monkeypatch.setattr(importlib, "import_module", fake_import)

    assert example_server_type()._get_class_from_name("SimpleDomGetterMethod") is None


def test_get_getter_name_should_return_active_getter_name(example_server_type):
    """Test that get_getter_name returns the normalized active getter identifier."""
    server = example_server_type()
    server.active_getter_instance = SimpleDomGetterMethod({})

    assert server.get_getter_name() == "simple_dom"


def test_set_next_getter_should_switch_to_next_method(example_server_type):
    """Test that set_next_getter advances to the next configured getter instance."""
    server = example_server_type()
    server.document_info_methods = {
        "simple_dom": {"instance_params": {}},
        "rest_api": {
            "instance_params": {
                "identifier_pattern": "x",
                "base_api_url": "https://example.com",
                "document_api_url": "doc",
                "document_pages_api_url": "pages",
            }
        },
    }
    server.active_getter_instance = SimpleDomGetterMethod({})

    server.set_next_getter()

    assert isinstance(server.active_getter_instance, RestApiGetterMethod)


def test_set_next_getter_should_raise_value_error_when_no_more_getters_exist(example_server_type):
    """Test that set_next_getter raises when the current getter is the last configured option."""
    server = example_server_type()
    server.document_info_methods = {
        "rest_api": {
            "instance_params": {
                "identifier_pattern": "x",
                "base_api_url": "https://example.com",
                "document_api_url": "doc",
                "document_pages_api_url": "pages",
            }
        }
    }
    server.active_getter_instance = RestApiGetterMethod(
        {
            "identifier_pattern": "x",
            "base_api_url": "https://example.com",
            "document_api_url": "doc",
            "document_pages_api_url": "pages",
        }
    )

    with pytest.raises(ValueError, match="No more getters to try"):
        server.set_next_getter()


def test___exit__should_clear_active_getter(example_server_type):
    """Test that leaving the server context clears any cached active getter instance."""
    server = example_server_type()
    server.active_getter_instance = SimpleDomGetterMethod({})

    with server:
        assert server.active_getter_instance is not None

    assert server.active_getter_instance is None
