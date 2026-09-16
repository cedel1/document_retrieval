"""Tests for BaseDocumentPage."""

from pathlib import Path

from src.library_models.base.base_document_page import BaseDocumentPage
from test.library_models.base.fixtures import dummy_page_class


def test_base_document_page_sets_metadata_and_output_base(dummy_page_class):
    page = dummy_page_class("abcd1234", "https://example.com/page", "https://example.com/detail", 4, "tmp")

    assert page.identifier == "abcd1234"
    assert page.page_url == "https://example.com/page"
    assert page.page_detail_url == "https://example.com/detail"
    assert page.output_dir == Path("tmp")
    assert page.output_base == Path("tmp/page_004_abcd1234")


def test_base_document_page_get_page_download_url_uses_pattern_template(dummy_page_class):
    BaseDocumentPage.page_properties_download_url = "https://example.com/download/{page_uuid}.xml"
    page = dummy_page_class("abcd1234", "https://example.com/page", "https://example.com/detail", 1)

    assert page.get_page_download_url("abcd1234") == "https://example.com/download/abcd1234.xml"
