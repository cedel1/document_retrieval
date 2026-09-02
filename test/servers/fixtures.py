"""Shared fixtures for server tests."""

import re

DOCUMENT_URL = (
    "https://www.digitalniknihovna.cz/dsmo/view/uuid:12345678-1234-1234-1234-123456789abc"
    "?page=uuid:87654321-4321-4321-4321-cba987654321"
)
PAGE_PATTERN = {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")}
