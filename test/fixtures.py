"""Shared pytest fixtures for document_retrieval tests."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def run_cli(tmp_path):
    """Run the document retrieval CLI with temporary input and configuration files."""
    documents_file = tmp_path / "documents.txt"
    config = tmp_path / "config.toml"
    config.write_text("", encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "document_retrieval.py"

    def run(contents):
        documents_file.write_text(contents, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(script),
                "--config",
                str(config),
                "--documents_file",
                str(documents_file),
                "--output",
                str(tmp_path / "output"),
                "--processes",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    return run


@pytest.fixture
def mock_library():
    """Fixture providing a mock library instance."""
    library = Mock()
    library.__class__ = Mock
    library.__str__ = Mock(return_value="MockLibrary")
    library.page_detail_url = "https://example.com/page"
    library.preprocess_document_from_url = Mock()
    library.append_preprocessed_document = Mock()
    return library


@pytest.fixture
def mock_document():
    """Fixture providing a mock document instance."""
    document = Mock()
    document.title = "Test Document"
    document.identifier = "test-uuid"
    document.source_url = "https://example.com/doc"
    return document


@pytest.fixture
def temp_documents_file(tmp_path):
    """Fixture providing a temporary documents file with test URLs."""
    documents_file = tmp_path / "documents.txt"
    documents_file.write_text(
        "https://example.com/doc1\n"
        "# This is a comment\n"
        "https://example.com/doc2\n"
        "   https://example.com/doc3   \n"
        "# Another comment\n"
        "https://example.com/doc4\n"
    )
    return documents_file


@pytest.fixture
def main_env(tmp_path):
    """Fixture isolating main(): processing is mocked and the script directory is a temporary directory."""
    library = Mock()
    library.library_name = "Library_DSMO"
    library.documents = []

    def write_config(content: str, name: str = "document_retrieval.toml") -> Path:
        config_path = tmp_path / name
        config_path.write_text(content, encoding="UTF-8")
        return config_path

    with (
        patch("document_retrieval.SCRIPT_DIR", tmp_path),
        patch("document_retrieval.preprocess_documents", return_value=({"lib": library}, [], 1)) as preprocess,
        patch("document_retrieval.process_library_documents", return_value=[]) as process,
    ):
        yield SimpleNamespace(tmp_path=tmp_path, preprocess=preprocess, process=process, write_config=write_config)
