"""Tests for document_retrieval.py methods."""

import os
import sys
from multiprocessing.pool import AsyncResult
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the functions to test
from document_retrieval import get_document_urls, get_library_document, preprocess_documents, process_library_documents
from .fixtures import mock_library, mock_document, temp_documents_file


def test_get_document_urls_should_ignore_comments_and_whitespace(temp_documents_file):
    """Test that get_document_urls ignores comments and strips whitespace."""
    urls = list(get_document_urls(temp_documents_file))

    assert len(urls) == 4
    assert urls == [
        "https://example.com/doc1",
        "https://example.com/doc2",
        "https://example.com/doc3",
        "https://example.com/doc4",
    ]


def test_get_document_urls_should_handle_empty_file(tmp_path):
    """Test that get_document_urls handles empty files."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    urls = list(get_document_urls(empty_file))
    assert urls == []


def test_get_document_urls_should_handle_only_comments(tmp_path):
    """Test that get_document_urls handles files with only comments."""
    comments_file = tmp_path / "comments.txt"
    comments_file.write_text("# comment 1\n# comment 2\n")

    urls = list(get_document_urls(comments_file))
    assert urls == []


def test_get_document_urls_should_ignore_empty_lines(tmp_path):
    """Test that get_document_urls ignores empty lines."""
    comments_file = tmp_path / "comments.txt"
    comments_file.write_text("url 1\n\n# comment 2\n")

    urls = list(get_document_urls(comments_file))
    assert urls == ["url 1"]


def test_get_library_document_should_preprocess_document_successfully(mock_library, mock_document):
    """Test that get_library_document successfully preprocesses a document."""
    # Create a mock library class that returns our mock instance when instantiated
    mock_library_class = Mock()
    mock_library_instance = mock_library
    mock_library_instance.preprocess_document_from_url.return_value = mock_document
    mock_library_instance.__str__ = Mock(return_value="MockLibrary")
    mock_library_class.return_value = mock_library_instance

    document, library_name = get_library_document("https://example.com/doc", "output", None, mock_library_class)

    assert document == mock_document
    assert library_name == "MockLibrary"
    mock_library_instance.preprocess_document_from_url.assert_called_once_with(
        "https://example.com/doc",
        page_detail_url=mock_library_instance.page_detail_url,
        output_dir="output",
        page_uuids=None,
    )


def test_get_library_document_should_raise_value_error_on_preprocessing_failure():
    """Test that get_library_document raises ValueError on preprocessing failure."""
    # Create a mock library class that raises ValueError when preprocess_document_from_url is called
    mock_library_class = Mock()
    mock_library_instance = Mock()
    mock_library_instance.preprocess_document_from_url.side_effect = ValueError("Network error")
    mock_library_instance.page_detail_url = "https://example.com/page"
    mock_library_class.return_value = mock_library_instance

    with pytest.raises(ValueError, match="Network error"):
        get_library_document("https://example.com/doc", "output", None, mock_library_class)


def test_preprocess_documents_should_use_multiprocessing_to_process_documents(
    temp_documents_file, mock_library, mock_document
):
    """Test that preprocess_documents uses multiprocessing to process documents."""
    mock_library.preprocess_document_from_url.return_value = mock_document
    mock_library.__str__ = Mock(return_value="MockLibrary")

    with patch("document_retrieval.LibraryFactory") as mock_factory:
        mock_factory.from_url.return_value = mock_library

        with patch("document_retrieval.Pool") as mock_pool:
            # Setup mock pool behavior
            mock_pool_instance = MagicMock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance

            # Mock the async results - we need 4 results for 4 URLs
            mock_results = []
            for _ in range(4):  # 4 URLs in the test file
                mock_result = MagicMock(spec=AsyncResult)
                mock_result.get.return_value = (mock_document, "MockLibrary")
                mock_results.append(mock_result)

            mock_pool_instance.apply_async.side_effect = mock_results

            libraries = preprocess_documents(temp_documents_file, "output", None)

            assert "MockLibrary" in libraries
            assert libraries["MockLibrary"] == mock_library
            # Should be called 4 times for 4 documents
            assert mock_library.append_preprocessed_document.call_count == 4


@pytest.mark.parametrize(
    "exception_type, exception_message",
    [
        (TimeoutError, "Result retrieval timed out"),
        (ValueError, "Invalid result format"),
    ],
)
def test_preprocess_documents_should_handle_caught_exceptions_gracefully(
    temp_documents_file, mock_library, exception_type, exception_message
):
    """Test that preprocess_documents handles caught exceptions from result.get() gracefully."""
    mock_library.__str__ = Mock(return_value="MockLibrary")

    with patch("document_retrieval.LibraryFactory") as mock_factory:
        mock_factory.from_url.return_value = mock_library

        with patch("document_retrieval.Pool") as mock_pool:
            with patch("document_retrieval.logger") as mock_logger:
                # Setup mock pool behavior
                mock_pool_instance = MagicMock()
                mock_pool.return_value.__enter__.return_value = mock_pool_instance

                # Mock results that raise the specified exception when get() is called
                # We need 4 results for 4 URLs in the test file
                mock_results = []
                for _ in range(4):
                    mock_result = MagicMock(spec=AsyncResult)
                    mock_result.get.side_effect = exception_type(exception_message)
                    mock_results.append(mock_result)

                mock_pool_instance.apply_async.side_effect = mock_results

                # Should not raise an exception, but handle it gracefully
                libraries = preprocess_documents(temp_documents_file, "output", None)

                # Library should still be created but document should not be appended
                assert "MockLibrary" in libraries
                assert libraries["MockLibrary"] == mock_library
                # Should not be called due to the exceptions
                assert mock_library.append_preprocessed_document.call_count == 0
                # Should log the exception for each of the 4 failed results
                assert mock_logger.exception.call_count == 4
                # Verify the log message format
                for call in mock_logger.exception.call_args_list:
                    assert "Failed to retrieve result:" in str(call[0][0])


def test_preprocess_documents_should_propagate_uncaught_exceptions(temp_documents_file, mock_library):
    """Test that preprocess_documents propagates exceptions that are not TimeoutError or ValueError."""
    mock_library.__str__ = Mock(return_value="MockLibrary")

    with patch("document_retrieval.LibraryFactory") as mock_factory:
        mock_factory.from_url.return_value = mock_library

        with patch("document_retrieval.Pool") as mock_pool:
            # Setup mock pool behavior
            mock_pool_instance = MagicMock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance

            # Mock a result that raises a different exception when get() is called
            mock_result = MagicMock(spec=AsyncResult)
            mock_result.get.side_effect = RuntimeError("Unexpected error")
            mock_pool_instance.apply_async.return_value = mock_result

            # Should raise the exception since it's not caught
            with pytest.raises(RuntimeError, match="Unexpected error"):
                preprocess_documents(temp_documents_file, "output", None)


def test_preprocess_documents_should_handle_library_creation_failure_gracefully(temp_documents_file):
    """Test that preprocess_documents handles library creation failures gracefully."""
    with patch("document_retrieval.LibraryFactory") as mock_factory:
        mock_factory.from_url.side_effect = ValueError("Invalid URL")

        with patch("document_retrieval.Pool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value.__enter__.return_value = mock_pool_instance

            libraries = preprocess_documents(temp_documents_file, "output", None)

            assert libraries == {}


def test_process_library_documents_should_return_true_when_all_documents_succeed(mock_library, mock_document):
    """Test that process_library_documents returns True when all documents succeed."""
    mock_library.documents = [mock_document]
    mock_library.process_document = Mock()

    result = process_library_documents(mock_library, {}, "output")

    assert result is True
    mock_library.process_document.assert_called_once_with(mock_document, {}, "output")


def test_process_library_documents_should_return_false_when_document_fails(mock_library, mock_document):
    """Test that process_library_documents returns False when a document fails."""
    mock_library.documents = [mock_document]
    mock_library.process_document.side_effect = Exception("Processing error")

    result = process_library_documents(mock_library, {}, "output")

    assert result is False


def test_process_library_documents_should_return_false_when_some_documents_fail(mock_library):
    """Test that process_library_documents returns False when some documents fail."""
    doc1 = Mock()
    doc2 = Mock()
    mock_library.documents = [doc1, doc2]

    def process_side_effect(document, args, output_dir):
        if document == doc2:
            raise Exception("doc2 failed")

    mock_library.process_document.side_effect = process_side_effect

    result = process_library_documents(mock_library, {}, "output")

    assert result is False


def test_process_library_documents_should_return_true_for_empty_library(mock_library):
    """Test that process_library_documents returns True for empty library."""
    mock_library.documents = []

    result = process_library_documents(mock_library, {}, "output")

    assert result is True


def test_process_library_documents_should_pass_additional_args_correctly(mock_library, mock_document):
    """Test that process_library_documents passes additional args correctly."""
    mock_library.documents = [mock_document]
    mock_library.process_document = Mock()

    additional_args = {"--pages": ["page1", "page2"], "dezoomify-path": "/custom/path"}

    result = process_library_documents(mock_library, additional_args, "output")

    assert result is True
    mock_library.process_document.assert_called_once_with(mock_document, additional_args, "output")
