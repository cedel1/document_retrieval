"""Tests for the abstract base document page factory."""

import pytest

from src.library_models.base.base_document_page_factory import BaseDocumentPageFactory


def test_init_should_raise_type_error_when_instantiated_directly():
    with pytest.raises(TypeError):
        BaseDocumentPageFactory()
