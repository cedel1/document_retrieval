"""Tests for DSMODocumentPageFactory."""

from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from src.library_models.dsmo.dsmo_document_page_factory import DSMODocumentPageFactory


def test_dsmo_document_page_factory_returns_correct_page_instance():
    page = DSMODocumentPageFactory.from_uuid(
        "page-uuid",
        "https://example.com/page",
        "https://example.com/detail",
        3,
        "tmp",
    )

    assert isinstance(page, DSMODocumentPage)
    assert page.identifier == "page-uuid"
    assert page.page_url == "https://example.com/page"
    assert page.page_detail_url == "https://example.com/detail"
    assert page.index == 3
