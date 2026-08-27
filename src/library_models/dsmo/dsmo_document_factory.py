"""Concrete factory for document models."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from src.library_models.base.base_document import BaseDocument
from src.library_models.base.base_document_factory import BaseDocumentFactory
from src.library_models.base.base_library import BaseLibrary
from src.library_models.dsmo.dsmo_document import DSMODocument
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from src.library_models.dsmo.dsmo_document_page_factory import DSMODocumentPageFactory
from src.services.url_parser import DocumentUrlParser


class DSMODocumentFactory(BaseDocumentFactory):
    """Concrete factory to create document objects from UUIDs or URLs."""

    @staticmethod
    def _extract_document_uuid_from_url(source_url: str) -> str:
        """Extract the document UUID from a source URL.

        Args:
            source_url: The full document URL which is expected to contain a
                document UUID in its path or query parameters.

        Returns:
            The document UUID extracted from the source URL.

        Raises:
            ValueError: If no document UUID can be found in the provided URL.
        """
        return DocumentUrlParser.extract_document_uuid(source_url)

    @staticmethod
    def from_uuid(
        document_uuid: str,
        source_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> BaseDocument:
        """Construct a DSMODocument from a document UUID and optional page UUIDs.

        This builds page model objects for each page UUID and returns a
        fully initialized DSMODocument instance.

        Args:
            document_uuid: The UUID of the document to construct.
            source_url: The original document URL; used to generate per-page URLs.
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
                    page_uuid, DSMODocumentPage.get_page_url(page_uuid, source_url), index, document_output_dir
                )
            )
        return DSMODocument(document_uuid, output_dir=output_dir, pages=pages)

    @staticmethod
    def from_url(
        library: BaseLibrary, source_url: str, output_dir: str = "output", page_uuids: Optional[Sequence[str]] = None
    ) -> BaseDocument:
        """Create a DSMO document from a source URL, discovering pages if needed.

        This convenience method extracts the document UUID from the provided
        source URL and, unless page_uuids are supplied, uses the PageDiscovery
        service to load the list of page UUIDs. It then delegates to from_uuid
        to construct the DSMODocument instance.

        Args:
            library: The library instance that the document belongs to.
            source_url: The full URL that identifies the DSMO document.
            output_dir: Directory where outputs will be written.
            page_uuids: Optional sequence of page UUIDs to use instead of
                performing discovery.

        Returns:
            A DSMODocument instance built from the URL and its pages.
        """
        document_uuid = DSMODocumentFactory._extract_document_uuid_from_url(source_url)
        if page_uuids is None:
            page_uuids = library.server_type.get_document_pages(source_url)
        return DSMODocumentFactory.from_uuid(document_uuid, source_url, output_dir=output_dir, page_uuids=page_uuids)
