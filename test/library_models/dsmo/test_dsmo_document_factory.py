"""Tests for DSMODocumentFactory."""

from types import SimpleNamespace

from src.library_models.dsmo.dsmo_document_factory import DSMODocumentFactory
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from test.library_models.fixtures import DOCUMENT_URL


def test_dsmo_document_factory_from_uuid_builds_document_with_page_objects(monkeypatch):
    captured = {}

    def fake_from_uuid(page_uuid, page_url, page_detail_url, index, output_dir):
        captured["args"] = (page_uuid, page_url, page_detail_url, index, output_dir)
        return DSMODocumentPage(page_uuid, page_url, page_detail_url, index, output_dir)

    monkeypatch.setattr("src.library_models.dsmo.dsmo_document_factory.DSMODocumentPageFactory.from_uuid", fake_from_uuid)

    document = DSMODocumentFactory.from_uuid(
        "doc-123",
        DOCUMENT_URL,
        "https://example.com/detail",
        output_dir="tmp",
        page_uuids=["page-1"],
    )

    assert document.identifier == "doc-123"
    assert len(document.pages) == 1
    assert document.pages[0].identifier == "page-1"
    assert captured["args"][2] == "https://example.com/detail"


def test_dsmo_document_factory_from_url_discovers_pages_when_not_provided(monkeypatch):
    library = SimpleNamespace()
    library.server_type = SimpleNamespace()
    library.server_type.get_document_pages = lambda url: ["page-1", "page-2"]
    library.page_detail_url = "https://example.com/detail"

    document = DSMODocumentFactory.from_url(
        library,
        DOCUMENT_URL,
        page_detail_url="https://example.com/detail",
        output_dir="tmp",
    )

    assert [page.identifier for page in document.pages] == ["page-1", "page-2"]
