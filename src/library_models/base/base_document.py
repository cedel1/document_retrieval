"""Abstract document model."""

from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

from src.library_models.base.base_document_page import BaseDocumentPage

logger = logging.getLogger(__name__)


class BaseDocument(ABC):
    """Abstract base document owning all pages for a given source document."""

    def __init__(
        self,
        identifier: str = "",
        source_url: Optional[str] = None,
        output_dir: str = "output",
        pages: Optional[Sequence[BaseDocumentPage]] = None,
    ) -> None:
        """Initialize the document and optionally attach initial pages.

        Args:
            identifier: Unique identifier for the document.
            source_url: Optional URL pointing to the source document.
            output_dir: Directory used to store generated metadata and page files.
            pages: Optional sequence of pages to attach immediately.

        Returns:
            None: The document instance is created in memory.
        """
        self.identifier = identifier
        self.source_url = source_url
        self.output_dir = Path(output_dir + "/" + self.identifier) if identifier else Path(output_dir)
        self.pages: List[BaseDocumentPage] = []

        if pages:
            for page in pages:
                self.add_page(page)

    @property
    def page_uuids(self) -> List[str]:
        """Return the UUIDs of all pages currently attached to this document.

        Args:
            None: This property does not accept arguments.

        Returns:
            List[str]: The UUIDs of every attached page.
        """
        return [page.identifier for page in self.pages]

    @property
    def page_count(self) -> int:
        """Return the number of pages in the document.

        Args:
            None: This property does not accept arguments.

        Returns:
            int: The number of attached pages.
        """
        return len(self.pages)

    def add_page(self, page: BaseDocumentPage) -> None:
        """Attach a page to the document and align the page output directory.

        Args:
            page: Page instance to add to the document.

        Returns:
            None: The page is attached in-place to the document.
        """
        if page.output_dir != self.output_dir:
            page.output_dir = self.output_dir
        self.pages.append(page)

    @property
    def properties_path(self) -> Path:
        """Return the path to the generated metadata file for this document.

        Args:
            None: This property does not accept arguments.

        Returns:
            Path: The destination path for the document metadata file.
        """
        return self.output_dir / "properties.txt"

    def create_properties_file(
        self, dezoomify_path: Optional[str] = None, dezoomify_args: Optional[List[str]] = None
    ) -> None:
        """Write a download-style properties file using the document's fields.

        This mirrors the standalone DownloadService.create_download_properties_file
        implementation but is bound to the document instance, so callers do not
        need to pass document_uuid or page lists explicitly.

        Args:
            dezoomify_path: Optional path to the dezoomify executable.
            dezoomify_args: Optional list of dezoomify command-line arguments.

        Returns:
            None: The metadata file is written to the document's output directory.
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=False)
            with self.properties_path.open("w", encoding="utf-8") as properties_file:
                properties_file.write(f"Document_uuid: {self.identifier}\n")
                properties_file.write("pages:\n")
                for page_uuid in self.page_uuids:
                    properties_file.write(f"    {page_uuid}\n")
                properties_file.write(f"Page count: {len(self.page_uuids)}\n")
                properties_file.write(f"Dezoomify-rs path: {dezoomify_path}\n")
                properties_file.write(f"Dezoomify-rs args: {' '.join(dezoomify_args or [])}\n")
                properties_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            logger.debug("Created properties file at %s", self.properties_path)
        except Exception as exc:  # pragma: no cover - filesystem dependent
            logger.exception("Error creating properties file: %s", exc)
