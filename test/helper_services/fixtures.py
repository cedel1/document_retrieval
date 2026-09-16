"""Shared fixtures for helper service tests."""

from __future__ import annotations

import re

import pytest


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
    return {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")}


@pytest.fixture
def api_payload():
    """Sample API payload for testing REST API getter."""
    return {"pages": ["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"]}
