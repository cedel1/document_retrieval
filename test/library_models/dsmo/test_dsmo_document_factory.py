"""Tests for DSMODocumentFactory."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from src.library_models.dsmo.dsmo_document_factory import DSMODocumentFactory
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from src.servers.kramerius_5_server import Kramerius5ServerType
from test.library_models.dsmo.fixtures import document_url, dsmo_library_with_kramerius_5_server


def test_dsmo_document_factory_from_uuid_builds_document_with_page_objects(monkeypatch, document_url):
    captured = {}

    def fake_from_uuid(page_uuid, page_url, page_detail_url, index, output_dir):
        captured["args"] = (page_uuid, page_url, page_detail_url, index, output_dir)
        return DSMODocumentPage(page_uuid, page_url, page_detail_url, index, output_dir)

    monkeypatch.setattr(
        "src.library_models.dsmo.dsmo_document_factory.DSMODocumentPageFactory.from_uuid", fake_from_uuid
    )

    document = DSMODocumentFactory.from_identifier(
        "doc-123",
        document_url,
        "",
        "",
        "https://example.com/detail",
        output_dir="tmp",
        page_uuids=["page-1"],
    )

    assert document.identifier == "doc-123"
    assert len(document.pages) == 1
    assert document.pages[0].identifier == "page-1"
    assert captured["args"][2] == "https://example.com/detail"


def test_dsmo_document_factory_extract_document_uuid_from_url_returns_uuid_for_library_url(document_url):
    library = SimpleNamespace(server_type=Kramerius5ServerType())

    document_uuid = DSMODocumentFactory._extract_document_uuid_from_url(document_url, library)

    assert document_uuid == "11111111-1111-1111-1111-111111111111"


def test_dsmo_document_factory_extract_document_uuid_from_url_raises_when_missing_uuid():
    library = SimpleNamespace(server_type=Kramerius5ServerType())

    with pytest.raises(ValueError, match="Could not extract document UUID"):
        DSMODocumentFactory._extract_document_uuid_from_url("https://example.com/no-uuid-here", library)


def test_dsmo_document_factory_from_url_discovers_pages_when_not_provided(
    dsmo_library_with_kramerius_5_server, monkeypatch, document_url
):

    document = DSMODocumentFactory.from_url(
        dsmo_library_with_kramerius_5_server,
        Kramerius5ServerType(),
        document_url,
        page_detail_url="https://example.com/detail",
        output_dir="tmp",
    )

    assert [page.identifier for page in document.pages] == ["page-1", "page-2"]


def test_dsmo_document_factory_from_url_uses_explicit_page_detail_url(
    dsmo_library_with_kramerius_5_server, monkeypatch, document_url
):
    captured = {}

    def fake_from_uuid(page_uuid, page_url, page_detail_url, index, output_dir):
        captured["page_detail_url"] = page_detail_url
        return DSMODocumentPage(page_uuid, page_url, page_detail_url, index, output_dir)

    monkeypatch.setattr(
        "src.library_models.dsmo.dsmo_document_factory.DSMODocumentPageFactory.from_uuid", fake_from_uuid
    )

    DSMODocumentFactory.from_url(
        dsmo_library_with_kramerius_5_server,
        Kramerius5ServerType(),
        document_url,
        page_detail_url="https://explicit.example.com/detail",
        output_dir="tmp",
    )

    assert captured["page_detail_url"] == "https://explicit.example.com/detail"


def test_dsmo_document_factory_from_url_should_return_empty_string_when_document_title_raises_value_error(
    dsmo_library_with_kramerius_5_server, document_url
):
    """Tests that the document title is returned as an empty string when the underlying method raises a ValueError."""
    server_instance = Kramerius5ServerType()

    with patch.object(server_instance, "get_document_title", side_effect=ValueError):
        document = DSMODocumentFactory.from_url(
            dsmo_library_with_kramerius_5_server,
            server_instance,
            document_url,
            page_detail_url="https://example.com/detail",
            output_dir="tmp",
        )

        assert document.title == ""


def test_dsmo_document_factory_from_url_should_return_empty_string_when_document_subtitle_raises_value_error(
    dsmo_library_with_kramerius_5_server, document_url
):
    """Tests that the document subtitle is returned as an empty string when the underlying method raises a ValueError."""
    server_instance = Kramerius5ServerType()

    with patch.object(server_instance, "get_document_subtitle", side_effect=ValueError):
        document = DSMODocumentFactory.from_url(
            dsmo_library_with_kramerius_5_server,
            server_instance,
            document_url,
            page_detail_url="https://example.com/detail",
            output_dir="tmp",
        )
        assert document.subtitle == ""
