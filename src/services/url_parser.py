"""Utilities for parsing document and page UUIDs from source URLs."""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional, Tuple


class DocumentUrlParser:
    """Parse document URLs into the UUIDs they refer to."""

    @staticmethod
    def extract_uuids(url: str) -> Tuple[Optional[str], Optional[str]]:
        """Return both the document UUID and the page UUID present in a document URL.

        Args:
            url: URL to parse for document and page UUID values.

        Returns:
            Tuple[Optional[str], Optional[str]]: A pair containing the document UUID and page UUID.
        """
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        path_match = re.search(r"uuid:([a-f0-9-]+)", parsed.path)
        document_uuid = path_match.group(1) if path_match else None

        page_uuid = None
        if "page" in params:
            page_match = re.search(r"uuid:([a-f0-9-]+)", params["page"][0])
            page_uuid = page_match.group(1) if page_match else None

        return document_uuid, page_uuid

    @staticmethod
    def extract_document_uuid(url: str) -> str:
        """Return the document UUID and raise if the URL does not contain one.

        Args:
            url: URL to parse for the document UUID.

        Returns:
            str: The extracted document UUID.

        Raises:
            ValueError: If the URL does not contain a document UUID.
        """
        document_uuid, _ = DocumentUrlParser.extract_uuids(url)
        if not document_uuid:
            raise ValueError(f"Could not extract document UUID from URL: {url}")
        return document_uuid
