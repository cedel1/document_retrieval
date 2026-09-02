"""Tests for DSMODocumentPage."""

from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage


def test_get_page_url_and_download_url_are_built_correctly():
    page = DSMODocumentPage(
        "page-uuid",
        "https://example.com/document?page=uuid:page-uuid",
        "https://example.com/detail/",
        2,
        "tmp",
    )

    assert DSMODocumentPage.get_page_url("page-uuid", "https://example.com/document") == "https://example.com/document?page=uuid:page-uuid"
    assert page.get_page_download_url("page-uuid") == "https://example.com/detail/search/zoomify/uuid:page-uuid/ImageProperties.xml"


def test_download_delegates_to_download_service(monkeypatch):
    captured = {}

    def fake_retrieve(properties_download_url, output_base, dezoomify_path, dezoomify_args):
        captured["properties_download_url"] = properties_download_url
        captured["output_base"] = output_base
        captured["dezoomify_path"] = dezoomify_path
        captured["dezoomify_args"] = dezoomify_args
        return True

    monkeypatch.setattr("src.library_models.dsmo.dsmo_document_page.DownloadService.retrieve_dezoomified_image", fake_retrieve)

    page = DSMODocumentPage("page-uuid", "https://example.com/page", "https://example.com/detail/", 1, "tmp")
    result = page.download(dezoomify_path="/tool/dezoomify-rs", dezoomify_args=["--largest"])

    assert result is True
    assert captured["properties_download_url"] == "https://example.com/detail/search/zoomify/uuid:page-uuid/ImageProperties.xml"
    assert captured["output_base"] == str(page.output_base)
    assert captured["dezoomify_path"] == "/tool/dezoomify-rs"
    assert captured["dezoomify_args"] == ["--largest"]
