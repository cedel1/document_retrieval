"""Concrete factory for document page models."""

from __future__ import annotations

from src.library_models.base.base_document_page import BaseDocumentPage
from src.library_models.base.base_document_page_factory import BaseDocumentPageFactory
from src.library_models.dsmo.dsmo_document_page import DSMODocumentPage


class DSMODocumentPageFactory(BaseDocumentPageFactory):
    """Concrete factory for page objects."""

    @staticmethod
    def from_uuid(
        page_uuid: str, page_url: str, page_detail_url: str, index: int, output_dir: str = "output"
    ) -> BaseDocumentPage:
        """Create a DSMO document page from its UUID and metadata.

        Args:
            page_uuid: Unique identifier of the page.
            page_url: URL used to access the page.
            page_detail_url: The detail URL for the page.
            index: Zero-based position of the page within the document.
            output_dir: Target directory for the downloaded page output.

        Returns:
            BaseDocumentPage: A configured DSMO page instance.
        """
        return DSMODocumentPage(page_uuid, page_url, page_detail_url, index, output_dir)
