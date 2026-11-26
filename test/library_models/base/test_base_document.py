"""Tests for BaseDocument behavior."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.library_models.base.base_document import BaseDocument
from test.library_models.base.fixtures import doc_dir, document, dummy_page_class, first_page, second_page


def test_init_should_set_pages_and_output_directory(first_page, second_page):
    document = BaseDocument(
        "doc-123", source_url="https://example.com/doc", output_dir="tmp", pages=[first_page, second_page]
    )

    assert document.identifier == "doc-123"
    assert document.source_url == "https://example.com/doc"
    assert document.output_dir == Path("tmp")
    assert document.page_uuids == ["page-1", "page-2"]
    assert document.page_count == 2
    assert first_page.output_dir == document.output_dir


def test_add_page_should_update_directory_and_properties_path(document, doc_dir, first_page):
    document.add_page(first_page)

    assert document.properties_path == doc_dir / "properties.txt"
    assert first_page.output_dir == document.output_dir


def test_create_properties_file_should_write_expected_content(document, doc_dir, first_page):
    document.add_page(first_page)

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
def test_create_properties_file_should_record_allow_insecure_separately(document, doc_dir, allow_insecure, expected):
    document.create_properties_file(dezoomify_path="/tool", dezoomify_args=["--largest"], allow_insecure=allow_insecure)

    content = (doc_dir / "properties.txt").read_text(encoding="utf-8")
    assert f"Allow insecure: {expected}" in content
    assert "Dezoomify-rs args: --largest\n" in content


def test_create_properties_file_should_preserve_existing_directory(document, doc_dir):
    doc_dir.mkdir()
    properties = doc_dir / "properties.txt"
    properties.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        document.create_properties_file()

    assert properties.read_text(encoding="utf-8") == "existing"


def test_create_properties_file_should_always_write_images_subfolder_line(document, doc_dir):
    document.create_properties_file()

    assert "Images subfolder: \n" in (doc_dir / "properties.txt").read_text(encoding="utf-8")


def test_create_properties_file_should_not_create_subfolder_when_not_set(document, doc_dir):
    document.create_properties_file()

    assert [path.name for path in doc_dir.iterdir()] == ["properties.txt"]


def test_create_properties_file_should_create_subfolder_and_keep_properties_in_document_folder(document, doc_dir):
    document.images_subfolder = "images"

    document.create_properties_file()

    assert (doc_dir / "images").is_dir()
    assert "Images subfolder: images\n" in (doc_dir / "properties.txt").read_text(encoding="utf-8")


def test_create_properties_file_should_raise_when_subfolder_exists(document, doc_dir):
    document.images_subfolder = "images"

    with patch.object(Path, "mkdir", side_effect=[None, FileExistsError("images")]):
        with pytest.raises(FileExistsError):
            document.create_properties_file()


def test_images_subfolder_should_apply_to_existing_and_added_pages(document, first_page, second_page):
    document.add_page(first_page)

    document.images_subfolder = "images"
    document.add_page(second_page)

    assert first_page.images_subfolder == "images"
    assert second_page.images_subfolder == "images"
