"""Tests for BaseDocumentPage."""

from pathlib import Path

from src.library_models.base.base_document_page import BaseDocumentPage


class DummyPage(BaseDocumentPage):
    def __init__(self, identifier: str, page_url: str, page_detail_url: str, index: int, output_dir: str = "output"):
        super().__init__(identifier, page_url, page_detail_url, index, output_dir)

    def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args=None) -> bool:
        return True


def test_base_document_page_sets_metadata_and_output_base():
    page = DummyPage("abcd1234", "https://example.com/page", "https://example.com/detail", 4, "tmp")

    assert page.identifier == "abcd1234"
    assert page.page_url == "https://example.com/page"
    assert page.page_detail_url == "https://example.com/detail"
    assert page.output_dir == Path("tmp")
    assert page.output_base == Path("tmp/page_004_abcd1234")


def test_base_document_page_get_page_download_url_uses_pattern_template():
    BaseDocumentPage.page_properties_download_url = "https://example.com/download/{page_uuid}.xml"
    page = DummyPage("abcd1234", "https://example.com/page", "https://example.com/detail", 1)

    assert page.get_page_download_url("abcd1234") == "https://example.com/download/abcd1234.xml"
