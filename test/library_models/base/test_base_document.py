"""Tests for BaseDocument behavior."""

from pathlib import Path

from src.library_models.base.base_document import BaseDocument
from src.library_models.base.base_document_page import BaseDocumentPage


class DummyPage(BaseDocumentPage):
    def __init__(self, identifier: str, page_url: str, page_detail_url: str, index: int, output_dir: str):
        super().__init__(identifier, page_url, page_detail_url, index, output_dir)

    def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args=None) -> bool:
        return True


def test_base_document_initializes_pages_and_output_directory():
    page_one = DummyPage("page-1", "https://example.com/page-1", "https://example.com/detail", 1, "tmp")
    page_two = DummyPage("page-2", "https://example.com/page-2", "https://example.com/detail", 2, "tmp")

    document = BaseDocument("doc-123", source_url="https://example.com/doc", output_dir="tmp", pages=[page_one, page_two])

    assert document.identifier == "doc-123"
    assert document.source_url == "https://example.com/doc"
    assert document.output_dir == Path("tmp/doc-123")
    assert document.page_uuids == ["page-1", "page-2"]
    assert document.page_count == 2
    assert page_one.output_dir == document.output_dir


def test_base_document_add_page_updates_directory_and_properties_path(tmp_path):
    page = DummyPage("page-1", "https://example.com/page-1", "https://example.com/detail", 1, str(tmp_path))
    document = BaseDocument("doc-123", output_dir=str(tmp_path))

    document.add_page(page)

    assert document.properties_path == tmp_path / "doc-123" / "properties.txt"
    assert page.output_dir == document.output_dir


def test_base_document_create_properties_file_writes_expected_content(tmp_path):
    page = DummyPage("page-1", "https://example.com/page-1", "https://example.com/detail", 1, str(tmp_path))
    document = BaseDocument("doc-123", output_dir=str(tmp_path), pages=[page])

    document.create_properties_file(dezoomify_path="/tool/dezoomify-rs", dezoomify_args=["--largest", "--max-width", "4000"])

    content = (tmp_path / "doc-123" / "properties.txt").read_text(encoding="utf-8")
    assert "Document_uuid: doc-123" in content
    assert "pages:" in content
    assert "    page-1" in content
    assert "Dezoomify-rs path: /tool/dezoomify-rs" in content
    assert "Dezoomify-rs args: --largest --max-width 4000" in content
