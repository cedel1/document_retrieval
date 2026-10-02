"""Shared fixtures for server tests."""

import re

import pytest
from src.servers.kramerius_5_server import Kramerius5ServerType


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
    return {"name": "div", "id": re.compile(r"page-id-(uuid:[a-f0-9-]+)")}


@pytest.fixture
def getter_params(page_pattern):
    """Instance params fot the getters"""
    return {
        "instance_params": {},
        "document_identifier_pattern": page_pattern,
        "title_search": "some_title_xpath",
        "subtitle_search": None,
        "page_search": None,
    }


@pytest.fixture
def document_info_methods_mock(getter_params):
    """Instance params fot the getters"""
    return {
        "dom_selenium": getter_params,
        "stale": getter_params,
    }


@pytest.fixture
def kramerius_5_server(document_info_methods_mock):
    server = Kramerius5ServerType()
    server.document_info_methods = document_info_methods_mock

    return server


@pytest.fixture
def example_server_type(document_url):
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

        def get_document_part_title(self, document_url: str) -> str:
            return "Example Document Part Title"

        def get_document_part_subtitle(self, document_url: str) -> str:
            return "Example Document Part Subtitle"

    return ExampleServerType


@pytest.fixture
def fake_getter(getter_params, document_info_methods_mock, document_url):
    """Fixture providing a fake getter class for testing."""

    class DomSeleniumGetterMethod:
        def __init__(self, getter_params):
            self.document_page_identifier = (
                ""  # document_info_methods_mock["instance_params"]["document_identifier_pattern"]
            )
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            return ["uuid-1", "uuid-2"]

    return DomSeleniumGetterMethod


@pytest.fixture
def failing_getter(document_url, getter_params):
    """Fixture providing a failing getter class for testing."""

    class DomSeleniumGetterMethod:

        def __init__(self, getter_params):
            self.document_page_identifier = ""
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            raise ValueError("bad")

    return DomSeleniumGetterMethod


@pytest.fixture
def success_after_failing_getter(getter_params, document_info_methods_mock, document_url):
    """Fixture providing a getter that succeeds after failing for testing."""

    class SimpleDomGetterMethod:

        def __init__(self, getter_params):
            self.document_page_identifier = (
                ""  # document_info_methods_mock["instance_params"]["document_identifier_pattern"]
            )
            self.calls = []

        def get_pages(self, document_url: str, search_attribute: str | dict):
            self.calls.append((document_url, search_attribute))
            return ["uuid-3"]

    return SimpleDomGetterMethod
