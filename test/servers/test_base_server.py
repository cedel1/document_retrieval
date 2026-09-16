"""Tests for the abstract server base type."""

import importlib

from src.servers.base_server import BaseServerType
from test.servers.fixtures import example_server_type


def test_base_server_str_includes_server_type_and_version(example_server_type):
    assert str(example_server_type()) == "example_3"


def test_get_class_name_formats_registry_names():
    assert BaseServerType._get_class_name("dom_selenium") == "DomSeleniumGetterMethod"
    assert BaseServerType._get_class_name("simple_dom") == "SimpleDomGetterMethod"
    assert BaseServerType._get_class_name("rest_api") == "RestApiGetterMethod"


def test_get_class_from_name_imports_helper_class(monkeypatch, example_server_type):
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
    fake_module = type("FakeModule", (), {})

    monkeypatch.setattr(importlib, "import_module", lambda module_name: fake_module)

    assert example_server_type()._get_class_from_name("DoesNotExist") is None


def test_get_class_from_name_returns_none_when_module_import_fails(monkeypatch, example_server_type):
    def fake_import(name):
        raise ImportError("missing module")

    monkeypatch.setattr(importlib, "import_module", fake_import)

    assert example_server_type()._get_class_from_name("SimpleDomGetterMethod") is None
