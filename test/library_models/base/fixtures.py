"""Shared fixtures for library model base tests."""

from unittest.mock import patch

import pytest

from src.library_models.base.base_document import BaseDocument
from src.library_models.base.base_document_page import BaseDocumentPage


@pytest.fixture
def dummy_page_class():
    """Fixture providing a concrete implementation of BaseDocumentPage for testing."""

    class DummyPage(BaseDocumentPage):
        def __init__(
            self, identifier: str, page_url: str, page_detail_url: str, index: int, output_dir: str = "output"
        ):
            super().__init__(identifier, page_url, page_detail_url, index, output_dir)

        def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args=None) -> bool:
            return True

    return DummyPage


@pytest.fixture
def sample_page(dummy_page_class):
    """Fixture providing a page with identifier ``abcd1234`` and index 4 in the ``tmp`` directory."""
    return dummy_page_class("abcd1234", "https://example.com/page", "https://example.com/detail", 4, "tmp")


@pytest.fixture
def first_page(dummy_page_class):
    """Fixture providing the first page (``page-1``) of a document."""
    return dummy_page_class("page-1", "https://example.com/page-1", "https://example.com/detail", 1, "tmp")


@pytest.fixture
def second_page(dummy_page_class):
    """Fixture providing the second page (``page-2``) of a document."""
    return dummy_page_class("page-2", "https://example.com/page-2", "https://example.com/detail", 2, "tmp")


@pytest.fixture
def doc_dir(tmp_path):
    """Fixture providing the (not yet created) output directory of the ``doc-123`` document."""
    return tmp_path / "doc-123"


@pytest.fixture
def document(doc_dir):
    """Fixture providing an empty ``doc-123`` document writing into ``doc_dir``."""
    return BaseDocument("doc-123", output_dir=str(doc_dir))


@pytest.fixture
def print_mock():
    """Fixture replacing ``builtins.print`` with a mock that keeps the test output clean."""
    with patch("builtins.print") as mocked_print:
        yield mocked_print
