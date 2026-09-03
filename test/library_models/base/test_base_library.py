"""Tests for the abstract base library implementation."""

import pytest

from src.library_models.base.base_library import BaseLibrary


class ConcreteLibrary(BaseLibrary):
    server_urls = ["https://example.com/"]

    def preprocess_document_from_url(self, document_url: str, page_detail_url: str, output_dir: str = "output", page_uuids=None):
        return {"source_url": document_url, "output_dir": output_dir, "page_uuids": page_uuids}


def test_base_library_resolves_library_url_and_document_membership():
    library = ConcreteLibrary("https://example.com/documents/123")

    assert library.library_url == "https://example.com/"
    assert BaseLibrary.is_document_in_library("https://example.com/documents/123") is False
    assert ConcreteLibrary.is_document_in_library("https://example.com/documents/123") is True
    assert ConcreteLibrary.get_document_base_server_url("https://example.com/documents/123") == "https://example.com/"


def test_base_library_append_and_stringify():
    library = ConcreteLibrary("https://example.com/")
    marker = object()

    library.append_preprocessed_document(marker)

    assert library.documents == [marker]
    assert str(library) == "ConcreteLibrary"


def test_base_library_process_document_uses_document_create_properties_file_and_page_download(monkeypatch):
    library = ConcreteLibrary("https://example.com/")

    class DummyPage:
        def __init__(self):
            self.called = []

        def download(self, dezoomify_path, dezoomify_args):
            self.called.append((dezoomify_path, dezoomify_args))

    class DummyDocument:
        def __init__(self):
            self.source_url = "https://example.com/doc"
            self.pages = [DummyPage()]

        def create_properties_file(self, dezoomify_path, dezoomify_args):
            return {"dezoomify_path": dezoomify_path, "dezoomify_args": dezoomify_args}

    document = DummyDocument()
    captured = {}

    calls = []

    def fake_print(*args, **kwargs):
        calls.append(args)

    monkeypatch.setattr("builtins.print", fake_print)

    library.process_document(document, {"dezoomify-path": "/tool", "dezoomify-args": ["--largest"]}, "/tmp/out")

    assert document.pages[0].called == [("/tool", ["--largest"])]
    assert any("Processing document" in str(part) for call in calls for part in call)


def test_base_library_get_document_base_server_url_raises_for_non_matching_url():
    with pytest.raises(ValueError, match="does not belong to library"):
        ConcreteLibrary.get_document_base_server_url("https://other.example/document")
