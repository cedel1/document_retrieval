"""Tests for the abstract base document factory."""

import pytest

from src.library_models.base.base_document_factory import BaseDocumentFactory


def test_base_document_factory_is_abstract():
    with pytest.raises(TypeError):
        BaseDocumentFactory()
