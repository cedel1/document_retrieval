"""Tests for BaseDocument behavior."""

from pathlib import Path

import pytest

from src.library_models.base.base_document import BaseDocument
from test.library_models.base.fixtures import dummy_page_class


def test_init_should_set_pages_and_output_directory(dummy_page_class):
    page_one = dummy_page_class("page-1", "https://example.com/page-1", "https://example.com/detail", 1, "tmp")
    page_two = dummy_page_class("page-2", "https://example.com/page-2", "https://example.com/detail", 2, "tmp")

    document = BaseDocument(
        "doc-123", source_url="https://example.com/doc", output_dir="tmp", pages=[page_one, page_two]
    )

    assert document.identifier == "doc-123"
    assert document.source_url == "https://example.com/doc"
    assert document.output_dir == Path("tmp")
    assert document.page_uuids == ["page-1", "page-2"]
    assert document.page_count == 2
    assert page_one.output_dir == document.output_dir


def test_add_page_should_update_directory_and_properties_path(tmp_path, dummy_page_class):
    page = dummy_page_class("page-1", "https://example.com/page-1", "https://example.com/detail", 1, str(tmp_path))
    document = BaseDocument("doc-123", output_dir=str(tmp_path / "doc-123"))

    document.add_page(page)

    assert document.properties_path == tmp_path / "doc-123" / "properties.txt"
    assert page.output_dir == document.output_dir


def test_create_properties_file_should_write_expected_content(tmp_path, dummy_page_class):
    doc_dir = tmp_path / "doc-123"
    page = dummy_page_class("page-1", "https://example.com/page-1", "https://example.com/detail", 1, str(doc_dir))
    document = BaseDocument("doc-123", output_dir=str(doc_dir), pages=[page])

    document.create_properties_file(
        dezoomify_path="/tool/dezoomify-rs", dezoomify_args=["--largest", "--max-width", "4000"]
    )

    content = (doc_dir / "properties.txt").read_text(encoding="utf-8")
    assert "Document_uuid: doc-123" in content
    assert "pages:" in content
    assert "    page-1" in content
    assert "Dezoomify-rs path: /tool/dezoomify-rs" in content
    assert "Dezoomify-rs args: --largest --max-width 4000" in content


@pytest.mark.parametrize("allow_insecure, expected", [(True, "true"), (False, "false")])
def test_create_properties_file_should_record_allow_insecure_separately(
    tmp_path, dummy_page_class, allow_insecure, expected
):
    doc_dir = tmp_path / "doc-123"
    document = BaseDocument("doc-123", output_dir=str(doc_dir), pages=[])

    document.create_properties_file(dezoomify_path="/tool", dezoomify_args=["--largest"], allow_insecure=allow_insecure)

    content = (doc_dir / "properties.txt").read_text(encoding="utf-8")
    assert f"Allow insecure: {expected}" in content
    assert "Dezoomify-rs args: --largest\n" in content


def test_create_properties_file_should_preserve_existing_directory(tmp_path):
    doc_dir = tmp_path / "doc-123"
    doc_dir.mkdir()
    properties = doc_dir / "properties.txt"
    properties.write_text("existing", encoding="utf-8")
    document = BaseDocument("doc-123", output_dir=str(doc_dir))

    with pytest.raises(FileExistsError):
        document.create_properties_file()

    assert properties.read_text(encoding="utf-8") == "existing"
