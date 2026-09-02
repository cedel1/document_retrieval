"""Concrete document page model."""

from __future__ import annotations

import logging
from typing import List, Optional

from src.library_models.base.base_document_page import BaseDocumentPage
from src.services.download_service import DownloadService

logger = logging.getLogger(__name__)


class DSMODocumentPage(BaseDocumentPage):
    """Concrete page object containing page metadata and output configuration."""

    page_properties_download_url = "{page_detail_url}search/zoomify/uuid:{page_uuid}/ImageProperties.xml"

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

    def get_page_download_url(self, page_id: str) -> str:
        """Return the download URL for a given page UUID.

        Args:
            page_id: UUID of the page to be downloaded.

        Returns:
            str: The download URL for the specified page.
        """
        result = DSMODocumentPage.page_properties_download_url.format(
            page_detail_url=self.page_detail_url, page_uuid=page_id
        )
        logger.debug("Download URL for page %s: %s", page_id, result)
        return result

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
                self.get_page_download_url(self.identifier), str(self.output_base), dezoomify_path, dezoomify_args or []
            )
        )
