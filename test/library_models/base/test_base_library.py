"""Tests for the abstract base library implementation."""

from unittest.mock import Mock

import pytest

from src.library_models.base.base_library import BaseLibrary, PageDownloadResult
from test.library_models.base.fixtures import print_mock


@pytest.fixture
def concrete_library():
    """Fixture providing a concrete implementation of BaseLibrary for testing."""

    class ConcreteLibrary(BaseLibrary):
        server_urls = ["https://example.com/"]

        def preprocess_document_from_url(
            self, document_url: str, page_detail_url: str, output_dir: str = "output", page_uuids=None
        ):
            return {"source_url": document_url, "output_dir": output_dir, "page_uuids": page_uuids}

    return ConcreteLibrary


@pytest.fixture
def dummy_page():
    """Fixture providing a dummy page for testing."""

    class DummyPage:
        def __init__(self):
            self.called = []

        def download(self, dezoomify_path, dezoomify_args, allow_insecure=False):
            self.called.append((dezoomify_path, dezoomify_args, allow_insecure))
            return True

    return DummyPage


@pytest.fixture
def dummy_document(dummy_page):
    """Fixture providing a dummy document for testing."""

    class DummyDocument:
        def __init__(self):
            self.source_url = "https://example.com/doc"
            self.pages = [dummy_page()]
            self.images_subfolder = None

        def create_properties_file(self, dezoomify_path, dezoomify_args, allow_insecure=False):
            return {
                "dezoomify_path": dezoomify_path,
                "dezoomify_args": dezoomify_args,
                "allow_insecure": allow_insecure,
            }

    return DummyDocument


@pytest.fixture
def concrete_library_with_dummy_document(concrete_library, dummy_document):
    """Fixture providing a ``(library, document)`` pair of a concrete library and a dummy document."""
    return concrete_library("https://example.com/"), dummy_document()


def test_library_url_should_resolve_and_check_document_membership(concrete_library):
    library = concrete_library("https://example.com/documents/123")

    assert library.library_url == "https://example.com/"
    assert BaseLibrary.is_document_in_library("https://example.com/documents/123") is False
    assert concrete_library.is_document_in_library("https://example.com/documents/123") is True
    assert concrete_library.get_document_base_server_url("https://example.com/documents/123") == "https://example.com/"


def test_append_preprocessed_document_should_add_to_documents_list(concrete_library):
    library = concrete_library("https://example.com/")
    marker = object()

    library.append_preprocessed_document(marker)

    assert library.documents == [marker]
    assert str(library) == "ConcreteLibrary"


def test_process_document_should_call_create_properties_file_and_page_download(
    concrete_library_with_dummy_document, print_mock
):
    library, document = concrete_library_with_dummy_document

    library.process_document(document, {"dezoomify-path": "/tool", "dezoomify-args": ["--largest"]}, "/tmp/out")

    assert document.pages[0].called == [("/tool", ["--largest"], False)]
    assert any("Processing document" in str(part) for call in print_mock.call_args_list for part in call.args)


def test_process_document_should_pass_allow_insecure_to_pages(concrete_library_with_dummy_document, print_mock):
    library, document = concrete_library_with_dummy_document

    library.process_document(
        document, {"dezoomify-path": "/tool", "dezoomify-args": [], "allow-insecure": True}, "/tmp/out"
    )

    assert document.pages[0].called == [("/tool", [], True)]


def test_get_document_base_server_url_should_raise_for_non_matching_url(concrete_library):
    with pytest.raises(ValueError, match="does not belong to library"):
        concrete_library.get_document_base_server_url("https://other.example/document")


def test_init_should_set_empty_library_url_for_unmatched_url(concrete_library):
    """Test that constructing with a non-matching URL sets library_url to an empty string."""
    library = concrete_library("https://other.example/document")

    assert library.library_url == ""


def test_process_document_should_continue_after_failed_page(concrete_library_with_dummy_document):
    library, document = concrete_library_with_dummy_document
    document.pages = [Mock(identifier="p1"), Mock(identifier="p2"), Mock(identifier="p3")]
    document.pages[0].download.return_value = True
    document.pages[1].download.return_value = False
    document.pages[2].download.return_value = True

    result = library.process_document(document, {"dezoomify-path": "/tool", "dezoomify-args": []}, "out")

    assert result == PageDownloadResult(2, 1, 0)
    document.pages[2].download.assert_called_once()


def test_process_document_should_stop_after_unexpected_page_exception(concrete_library_with_dummy_document, caplog):
    library, document = concrete_library_with_dummy_document
    document.pages = [Mock(identifier="p1"), Mock(identifier="p2"), Mock(identifier="p3")]
    document.pages[0].download.return_value = True
    document.pages[1].download.side_effect = RuntimeError("unexpected")

    result = library.process_document(document, {"dezoomify-path": "/tool", "dezoomify-args": []}, "out")

    assert result == PageDownloadResult(1, 1, 1)
    document.pages[2].download.assert_not_called()
    assert "Traceback" in caplog.text


def test_process_document_should_not_download_pages_when_properties_fail(concrete_library_with_dummy_document):
    library, document = concrete_library_with_dummy_document
    document.create_properties_file = Mock(side_effect=OSError("cannot write"))
    document.pages = [Mock(identifier="p1")]

    with pytest.raises(OSError, match="cannot write"):
        library.process_document(document, {"dezoomify-path": "/tool", "dezoomify-args": []}, "out")

    document.pages[0].download.assert_not_called()


@pytest.mark.parametrize("value, expected", [("images", "images"), (None, None)])
def test_process_document_should_set_images_subfolder_on_document(
    concrete_library_with_dummy_document, print_mock, value, expected
):
    library, document = concrete_library_with_dummy_document

    library.process_document(
        document, {"dezoomify-path": "/tool", "dezoomify-args": [], "images-subfolder": value}, "/tmp/out"
    )

    assert document.images_subfolder == expected


def test_process_document_should_not_download_pages_when_subfolder_exists(concrete_library_with_dummy_document):
    library, document = concrete_library_with_dummy_document
    document.create_properties_file = Mock(side_effect=FileExistsError("images"))
    document.pages = [Mock(identifier="p1")]

    with pytest.raises(FileExistsError):
        library.process_document(
            document, {"dezoomify-path": "/tool", "dezoomify-args": [], "images-subfolder": "images"}, "out"
        )

    document.pages[0].download.assert_not_called()
