"""Tests for the abstract base getter class."""

import pytest

from src.helper_services.base_getter import BaseGetterMethod


@pytest.fixture
def dummy_getter():
    """Fixture providing a concrete implementation of BaseGetterMethod for testing."""

    class DummyGetter(BaseGetterMethod):
        def get_document_source(self, document_url: str):
            return None

        def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
            return [document_url, str(search_parameter)]

        def get_title(self, document_url: str, xpath: str) -> str:
            return ""

        def get_subtitle(self, document_url: str, xpath: str) -> str:
            return ""

    return DummyGetter()


def test_base_getter_is_abstract():
    with pytest.raises(TypeError):
        BaseGetterMethod()


def test_concrete_subclass_can_implement_get_pages(dummy_getter):
    assert dummy_getter.get_pages("https://example.com", "pages") == [
        "https://example.com",
        "pages",
    ]


def test_abstract_base_getter_method_raises_not_implemented_when_called_directly():
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_pages(None, "https://example.com", "pages")


def test_abstract_get_document_source_should_raise_not_implemented():
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_document_source(None, "https://example.com")


def test_abstract_get_name_should_raise_not_implemented():

    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_title(None, "https://example.com", "//h1")


def test_abstract_get_subtitle_should_raise_not_implemented_when_called_directly():
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_subtitle(None, "https://example.com", "//h2")
