"""Shared fixtures for DSMO library model tests."""

from types import SimpleNamespace

import pytest
from src.servers.kramerius_5_server import Kramerius5ServerType
from test.library_models.fixtures import DOCUMENT_URL


@pytest.fixture
def document_url():
    """Fixture providing a sample document URL for testing."""
    return DOCUMENT_URL


@pytest.fixture
def dsmo_library_with_kramerius_5_server(monkeypatch, document_url):
    """Fixture providing a library instance with a Kramerius 5 server for testing."""
    library = SimpleNamespace()
    library.server_type = Kramerius5ServerType
    monkeypatch.setattr(Kramerius5ServerType, "get_document_pages", lambda self, url: ["page-1", "page-2"])
    monkeypatch.setattr(Kramerius5ServerType, "get_document_title", lambda self, url: "")
    monkeypatch.setattr(Kramerius5ServerType, "get_document_subtitle", lambda self, url: "")
    library.page_detail_url = "https://library.example.com/detail"

    return library
