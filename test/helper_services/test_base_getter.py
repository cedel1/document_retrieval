"""Tests for the abstract base getter class."""

from typing import Any

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

        def get_title(self, document_url: str, search_parameter: str) -> str | Any:
            return ""

        def get_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
            return ""

        def get_part_title(self, document_url: str, search_parameter: str) -> str | Any:
            return ""

        def get_part_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
            return ""

    return DummyGetter("identifier_pattern")


def test_base_getter_should_be_abstract():
    """Test that the base getter class remains abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseGetterMethod("identifier_pattern")


def test_concrete_subclass_should_implement_get_pages(dummy_getter):
    """Test that a concrete subclass can implement get_pages without overriding the base contract."""
    assert dummy_getter.get_pages("https://example.com", "pages") == [
        "https://example.com",
        "pages",
    ]


def test_base_getter_get_pages_should_raise_not_implemented_when_called_directly():
    """Test that the abstract get_pages method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_pages(None, "https://example.com", "pages")


def test_base_getter_get_title_should_raise_not_implemented():
    """Test that the abstract get_title method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_title(None, "https://example.com", "//h1")


def test_base_getter_get_subtitle_should_raise_not_implemented_when_called_directly():
    """Test that the abstract get_subtitle method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_subtitle(None, "https://example.com", "//h2")
