"""Shared fixtures for helper service tests."""

from __future__ import annotations

import re

PAGE_HTML = """
<html>
  <body>
    <div id="page-id-uuid:11111111-1111-1111-1111-111111111111"></div>
    <div id="page-id-uuid:22222222-2222-2222-2222-222222222222"></div>
    <div id="non-page-id"></div>
  </body>
</html>
"""

PAGE_SEARCH_PATTERN = {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")}

API_PAYLOAD = {"pages": ["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"]}


class FakeResponse:
    """Minimal response stub for request-based helper tests."""

    def __init__(self, *, content: bytes | str = b"", json_data: dict | None = None, exc: Exception | None = None):
        self.content = content
        self._json_data = json_data or {}
        self._exc = exc

    def raise_for_status(self):
        if self._exc is not None:
            raise self._exc

    def json(self):
        return self._json_data
