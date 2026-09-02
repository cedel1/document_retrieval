"""Tests for the abstract server base type."""

import importlib

from src.servers.base_server import BaseServerType


class ExampleServerType(BaseServerType):
    server_type = "example"
    server_version = 3

    def get_document_pages(self, document_url: str) -> list[str]:
        return [document_url]


def test_base_server_str_includes_server_type_and_version():
    assert str(ExampleServerType()) == "example_3"


def test_get_class_name_formats_registry_names():
    assert BaseServerType._get_class_name("dom_selenium") == "DomSeleniumGetterMethod"
    assert BaseServerType._get_class_name("simple_dom") == "SimpleDomGetterMethod"
    assert BaseServerType._get_class_name("rest_api") == "RestApiGetterMethod"


def test_get_class_from_name_imports_helper_class(monkeypatch):
    class FakeGetter:
        pass

    fake_module = type("FakeModule", (), {"SimpleDomGetterMethod": FakeGetter})

    def fake_import(name):
        assert name == "src.helper_services"
        return fake_module

    monkeypatch.setattr(importlib, "import_module", fake_import)

    result = ExampleServerType()._get_class_from_name("SimpleDomGetterMethod")

    assert result is FakeGetter


def test_get_class_from_name_returns_none_for_missing_helper(monkeypatch):
    fake_module = type("FakeModule", (), {})

    monkeypatch.setattr(importlib, "import_module", lambda module_name: fake_module)

    assert ExampleServerType()._get_class_from_name("DoesNotExist") is None
