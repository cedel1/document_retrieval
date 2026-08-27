"""Concrete document page model."""

from __future__ import annotations

from typing import List, Optional

from src.library_models.base.base_document_page import BaseDocumentPage
from src.services.download_service import DownloadService


class DSMODocumentPage(BaseDocumentPage):
    """Concrete page object containing page metadata and output configuration."""

    @staticmethod
    def get_page_url(page_id: str, document_url: str) -> str:
        """Return a page-specific URL for a given page UUID and document base URL.

        Args:
            page_id: UUID of the page to be opened.
            document_url: Base URL of the document.

        Returns:
            str: A page-specific URL with the page UUID included as a query parameter.
        """
        return f"{document_url}?page=uuid:{page_id}"

    def download(self, dezoomify_path: str = "dezoomify-rs", dezoomify_args: Optional[List[str]] = None) -> bool:
        """Download the current page using the dezoomify image pipeline.

        Args:
            dezoomify_path: Path or command name of the dezoomify executable.
            dezoomify_args: Optional additional command-line arguments.

        Returns:
            bool: True when the page download succeeds, otherwise False.
        """
        return bool(
            DownloadService.retrieve_dezoomified_image(
                self.identifier,
                str(self.output_base),
                dezoomify_path,
                dezoomify_args or [],
            )
        )
