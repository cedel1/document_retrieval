"""Concrete document model."""

from __future__ import annotations

from typing import List, Optional
from typing import Sequence

from src.library_models.base.base_document import BaseDocument
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage
from src.services.download_service import DownloadService
from src.services.url_parser import DocumentUrlParser


class DSMODocument(BaseDocument):
    """Concrete document implementation used by the retrieval pipeline."""

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

    def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args: Optional[List[str]] = None) -> bool:
        """Download all pages for this DSMO document.

        Args:
            dezoomify_path: Path or command name of the dezoomify executable.
            dezoomify_args: Optional additional command-line arguments.

        Returns:
            bool: True when the document download succeeds, otherwise False.
        """
        if not self.pages:
            return False

        service = DownloadService()
        return service.download_document(self, dezoomify_path, dezoomify_args)

    def from_url(self, source_url: str, output_dir: str = "output") -> DSMODocument:
        """Create a DSMODocument instance from a source URL.

        Args:
            source_url: The URL of the document to create.
            output_dir: Directory used to store generated document artifacts.

        Returns:
            DSMODocument: A populated document instance.
        """
        document_uuid = DSMODocument._extract_document_uuid_from_url(source_url)
        return self.from_uuid(document_uuid, source_url, output_dir)

    def from_uuid(
        self,
        document_uuid: str,
        source_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> DSMODocument:
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
        pages = []
        for index, page_uuid in enumerate(page_uuids or [], 1):
            pages.append(
                DSMODocumentPage(page_uuid, DSMODocumentPage.get_page_url(page_uuid, source_url), index, output_dir)
            )
        return DSMODocument(document_uuid, output_dir=output_dir, pages=pages)
