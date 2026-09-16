"""Shared fixtures for library model base tests."""

import pytest

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
