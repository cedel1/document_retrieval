"""Shared fixtures for helper service tests."""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest

from src.helper_services.simple_dom_getter import SimpleDomGetterMethod


@pytest.fixture
def page_html():
    """Sample HTML content with page UUIDs for testing."""
    return """
<html>
  <body>
    <div id="page-id-uuid:11111111-1111-1111-1111-111111111111"></div>
    <div id="page-id-uuid:22222222-2222-2222-2222-222222222222"></div>
    <div id="non-page-id"></div>
  </body>
</html>
"""


@pytest.fixture
def page_search_pattern():
    """Search pattern for finding page UUIDs in HTML."""
    return {"name": "div", "id": re.compile(r"page-id-(uuid:[a-f0-9-]+)")}


@pytest.fixture
def api_payload():
    """Sample API payload for testing REST API getter."""
    return {
        "response": {
            "docs": [
                {"PID": "uuid:11111111-1111-1111-1111-111111111111", "rels_ext_index": [0]},
                {"PID": "uuid:22222222-2222-2222-2222-222222222222", "rels_ext_index": [1]},
            ]
        }
    }


@pytest.fixture
def document_url():
    """URL of the sample document used by the getter tests."""
    return "https://example.com/document"


class MethodStub:
    """Replacement for a getter method (not bound to the instance) that records calls and returns or raises a configured outcome."""

    def __init__(self):
        self.calls = []
        self.result = None
        self.error = None

    def __call__(self, *args):
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.result

    @property
    def args(self):
        """Return the arguments of the last call."""
        return self.calls[-1]


@pytest.fixture
def document_source_stub():
    """Fixture replacing ``get_document_source``; set ``.result`` or ``.error`` to change the outcome."""
    stub = MethodStub()
    with patch.object(SimpleDomGetterMethod, "get_document_source", stub):
        yield stub


@pytest.fixture
def extracted_uuids_stub():
    """Fixture replacing ``_extract_uuids_from_divs_with_id_pattern``; set ``.result`` to the UUIDs to return."""
    stub = MethodStub()
    with patch.object(SimpleDomGetterMethod, "_extract_uuids_from_divs_with_id_pattern", stub):
        yield stub
