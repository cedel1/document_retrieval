"""Tests for LibraryFactory."""

import pytest

from src.library_models.dsmo.dsmo_library import DSMOLibrary
from src.library_models.factories.library_factory import LibraryFactory


def test_library_factory_returns_matching_library_for_supported_url():
    library = LibraryFactory.from_url("https://www.digitalniknihovna.cz/dsmo/view/uuid:11111111-1111-1111-1111-111111111111")

    assert isinstance(library, DSMOLibrary)


def test_library_factory_raises_for_unsupported_url():
    with pytest.raises(ValueError, match="Unsupported library URL"):
        LibraryFactory.from_url("https://example.com/unsupported")
