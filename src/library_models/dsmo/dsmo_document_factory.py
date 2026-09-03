"""Concrete factory for document models."""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Sequence

from src.library_models.base.base_document import BaseDocument
from src.library_models.base.base_document_factory import BaseDocumentFactory
from src.library_models.base.base_library import BaseLibrary
from src.library_models.dsmo.dsmo_document import DSMODocument
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from src.library_models.dsmo.dsmo_document_page_factory import DSMODocumentPageFactory


class DSMODocumentFactory(BaseDocumentFactory):
    """Concrete factory to create document objects from UUIDs or URLs."""

    @staticmethod
    def _extract_uuids(url: str) -> Tuple[Optional[str], Optional[str]]:
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
    def _extract_document_uuid_from_url(source_url: str) -> str:
        """Return the document UUID from a source URL or raise if it is missing.

        Args:
            source_url: URL to parse for the document UUID.

        Returns:
            str: The extracted document UUID.

        Raises:
            ValueError: If the URL does not contain a document UUID.
        """
        document_uuid, _ = DSMODocumentFactory._extract_uuids(source_url)
        if not document_uuid:
            raise ValueError(f"Could not extract document UUID from URL: {source_url}")
        return document_uuid

    @staticmethod
    def from_uuid(
        document_uuid: str,
        source_url: str,
        page_detail_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> BaseDocument:
        """Construct a DSMODocument from a document UUID and optional page UUIDs.

        This builds page model objects for each page UUID and returns a
        fully initialized DSMODocument instance.

        Args:
            document_uuid: The UUID of the document to construct.
            source_url: The original document URL; used to generate per-page URLs.
            page_detail_url: The detail URL for the document.
            output_dir: Directory where the document and page outputs should be
                written.
            page_uuids: Optional iterable of page UUIDs to include. If omitted,
                an empty document (no pages) will be returned — discovery is
                performed by from_url when needed.

        Returns:
            A DSMODocument instance containing page model objects matching the
            provided page UUIDs.
        """
        document_output_dir = str(Path(output_dir + "/" + document_uuid)) if document_uuid else str(Path(output_dir))
        pages = []
        for index, page_uuid in enumerate(page_uuids or [], 1):
            pages.append(
                DSMODocumentPageFactory.from_uuid(
                    page_uuid,
                    DSMODocumentPage.get_page_url(page_uuid, source_url),
                    page_detail_url,
                    index,
                    document_output_dir,
                )
            )
        return DSMODocument(document_uuid, output_dir=output_dir, pages=pages)

    @staticmethod
    def from_url(
        library: BaseLibrary,
        source_url: str,
        page_detail_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> BaseDocument:
        """Create a DSMO document from a source URL, discovering pages if needed.

        This convenience method extracts the document UUID from the provided
        source URL and, unless page_uuids are supplied, uses the PageDiscovery
        service to load the list of page UUIDs. It then delegates to from_uuid
        to construct the DSMODocument instance.

        Args:
            library: The library instance that the document belongs to.
            source_url: The full URL that identifies the DSMO document.
            page_detail_url: The detail URL for the document.
            output_dir: Directory where outputs will be written.
            page_uuids: Optional sequence of page UUIDs to use instead of
                performing discovery.

        Returns:
            A DSMODocument instance built from the URL and its pages.
        """
        document_uuid = DSMODocumentFactory._extract_document_uuid_from_url(source_url)
        if page_uuids is None:
            page_uuids = library.server_type.get_document_pages(source_url)
        return DSMODocumentFactory.from_uuid(
            document_uuid,
            source_url,
            page_detail_url,
            output_dir=output_dir,
            page_uuids=page_uuids,
        )
