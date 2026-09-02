"""Tests for the abstract base getter class."""

import pytest

from src.helper_services.base_getter import BaseGetterMethod


def test_base_getter_is_abstract():
    with pytest.raises(TypeError):
        BaseGetterMethod()


def test_concrete_subclass_can_implement_get_pages():
    class DummyGetter(BaseGetterMethod):
        def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
            return [document_url, str(search_parameter)]

    instance = DummyGetter()

    assert instance.get_pages("https://example.com", "pages") == [
        "https://example.com",
        "pages",
    ]


def test_abstract_base_getter_method_raises_not_implemented_when_called_directly():
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_pages(None, "https://example.com", "pages")
