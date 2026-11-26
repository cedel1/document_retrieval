"""Tests for BaseDocumentPage."""

from pathlib import Path

from src.library_models.base.base_document_page import BaseDocumentPage
from test.library_models.base.fixtures import dummy_page_class, sample_page


def test_output_base_should_include_full_uuid_and_page_index(sample_page):
    assert sample_page.identifier == "abcd1234"
    assert sample_page.page_url == "https://example.com/page"
    assert sample_page.page_detail_url == "https://example.com/detail"
    assert sample_page.output_dir == Path("tmp")
    assert sample_page.output_base == Path("tmp/page_004_abcd1234")


def test_output_base_should_truncate_filename_to_64_chars(dummy_page_class):
    long_uuid = "a" * 100
    page = dummy_page_class(long_uuid, "https://example.com/page", "https://example.com/detail", 4, "tmp")

    assert page.output_base.name == "page_004_" + "a" * 55
    assert len(page.output_base.name) == 64


def test_output_base_should_use_full_uuid_when_under_limit(dummy_page_class):
    uuid = "550e8400-e29b-41d4-a716-446655440000"
    page = dummy_page_class(uuid, "https://example.com/page", "https://example.com/detail", 1, "tmp")

    assert page.output_base == Path("tmp/page_001_550e8400-e29b-41d4-a716-446655440000")


def test_output_base_should_keep_path_under_255_with_180_char_dir(dummy_page_class):
    long_dir = "d" * 180
    uuid = "550e8400-e29b-41d4-a716-446655440000"
    page = dummy_page_class(uuid, "https://example.com/page", "https://example.com/detail", 1, long_dir)

    full_path_str = str(page.output_base)
    assert len(page.output_base.name) <= 64
    assert len(full_path_str) < 255


def test_output_base_should_keep_filename_under_64_with_255_char_dir(dummy_page_class):
    long_dir = "e" * 255
    uuid = "550e8400-e29b-41d4-a716-446655440000"
    page = dummy_page_class(uuid, "https://example.com/page", "https://example.com/detail", 1, long_dir)

    assert len(page.output_base.name) <= 64
    assert page.output_base.name == "page_001_550e8400-e29b-41d4-a716-446655440000"


def test_get_page_download_url_should_substitute_page_uuid_in_template(dummy_page_class):
    BaseDocumentPage.page_properties_download_url = "https://example.com/download/{page_uuid}.xml"
    page = dummy_page_class("abcd1234", "https://example.com/page", "https://example.com/detail", 1)

    assert page.get_page_download_url("abcd1234") == "https://example.com/download/abcd1234.xml"


def test_output_base_should_not_include_subfolder_by_default(sample_page):
    assert sample_page.images_subfolder is None


def test_output_base_should_include_images_subfolder_when_set(sample_page):
    sample_page.images_subfolder = "images"

    assert sample_page.output_base == Path("tmp/images/page_004_abcd1234")
