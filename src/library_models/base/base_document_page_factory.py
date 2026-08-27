"""Abstract factory for document page models."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.library_models.base.base_document_page import BaseDocumentPage


class BaseDocumentPageFactory(ABC):
    """Factory API for building page objects."""

    @staticmethod
    @abstractmethod
    def from_uuid(page_uuid: str, page_url: str, index: int, output_dir: str = "output") -> BaseDocumentPage:
        """Build a single page object from a page UUID.

        Args:
            page_uuid: Unique identifier of the page.
            page_url: URL used to access the page content.
            index: Order of the page within the parent document.
            output_dir: Directory used to store page artifacts.

        Returns:
            BaseDocumentPage: A page instance configured for the provided metadata.
        """
