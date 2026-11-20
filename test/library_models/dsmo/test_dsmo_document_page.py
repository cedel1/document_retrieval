"""Tests for DSMODocumentPage."""

from unittest.mock import patch

import pytest

from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage


@pytest.fixture
def dsmo_document_page():
    """Fixture providing a DSMODocumentPage instance for testing."""
    return DSMODocumentPage(
        "page-uuid",
        "https://example.com/document?page=uuid:page-uuid",
        "https://example.com/detail/",
        2,
        "tmp",
    )


def test_get_page_url_should_build_correct_url_and_download_url(dsmo_document_page):
    assert (
        DSMODocumentPage.get_page_url("page-uuid", "https://example.com/document")
        == "https://example.com/document?page=page-uuid"
    )
    assert (
        dsmo_document_page.get_page_download_url("page-uuid")
        == "https://example.com/detail/search/zoomify/page-uuid/ImageProperties.xml"
    )


def test_download_should_delegate_to_download_service(dsmo_document_page):
    with patch("src.library_models.dsmo.dsmo_document_page.DownloadService.retrieve_dezoomified_image") as retrieve:
        retrieve.return_value = True
        result = dsmo_document_page.download(
            dezoomify_path="/tool/dezoomify-rs", dezoomify_args=["--largest"], allow_insecure=True
        )

    assert result is True
    retrieve.assert_called_once_with(
        "https://example.com/detail/search/zoomify/page-uuid/ImageProperties.xml",
        str(dsmo_document_page.output_base),
        "/tool/dezoomify-rs",
        ["--largest"],
        True,
        document_url=dsmo_document_page.page_url,
    )
