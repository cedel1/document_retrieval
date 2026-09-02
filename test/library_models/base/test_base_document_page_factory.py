"""Tests for the abstract base document page factory."""

import pytest

from src.library_models.base.base_document_page_factory import BaseDocumentPageFactory


def test_base_document_page_factory_is_abstract():
    with pytest.raises(TypeError):
        BaseDocumentPageFactory()
