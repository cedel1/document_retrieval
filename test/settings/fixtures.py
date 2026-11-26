"""Shared fixtures for settings tests."""

from argparse import Namespace

import pytest

LIBRARY_NAME = "Library_DSMO"


@pytest.fixture
def known_libraries():
    """Fixture providing the library names accepted in the config file."""
    return [LIBRARY_NAME]


@pytest.fixture
def write_config(tmp_path):
    """Fixture providing a factory that writes TOML text into a config file and returns its path."""

    def _write(content: str, name: str = "document_retrieval.toml"):
        config_path = tmp_path / name
        config_path.write_text(content, encoding="UTF-8")
        return config_path

    return _write


@pytest.fixture
def cli_args():
    """Fixture providing a factory for parsed CLI options where every option defaults to "not given"."""

    def _make(**values):
        defaults = {
            "documents_file": None,
            "output": None,
            "processes": None,
            "verbose": None,
            "pages": None,
            "dezoomify_path": None,
            "dezoomify_args": None,
            "allow_insecure": None,
            "images_subfolder": None,
        }
        defaults.update(values)
        return Namespace(**defaults)

    return _make
