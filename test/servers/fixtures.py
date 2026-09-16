"""Shared fixtures for server tests."""

import re

import pytest


@pytest.fixture
def document_url():
    """Sample document URL for testing."""
    return (
        "https://www.digitalniknihovna.cz/dsmo/view/uuid:12345678-1234-1234-1234-123456789abc"
        "?page=uuid:87654321-4321-4321-4321-cba987654321"
    )


@pytest.fixture
def page_pattern():
    """Search pattern for finding page UUIDs."""
    return {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")}


@pytest.fixture
def example_server_type():
    """Fixture providing a concrete implementation of BaseServerType for testing."""
    from src.servers.base_server import BaseServerType

    class ExampleServerType(BaseServerType):
        server_type = "example"
        server_version = 3

        def get_document_pages(self, document_url: str) -> list[str]:
            return [document_url]

        def get_document_title(self, document_url: str) -> str:
            return "Example Document"

        def get_document_subtitle(self, document_url: str) -> str:
            return "Example Document Subtitle"

    return ExampleServerType


@pytest.fixture
def fake_getter():
    """Fixture providing a fake getter class for testing."""

    class FakeGetter:
        def __init__(self):
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            return ["uuid-1", "uuid-2"]

    return FakeGetter


@pytest.fixture
def failing_getter():
    """Fixture providing a failing getter class for testing."""

    class FailingGetter:
        def __init__(self):
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            raise ValueError("bad")

    return FailingGetter


@pytest.fixture
def success_after_failing_getter():
    """Fixture providing a getter that succeeds after failing for testing."""

    class SuccessAfterFailingGetter:
        def __init__(self):
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            return ["uuid-3"]

    return SuccessAfterFailingGetter
