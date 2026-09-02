"""Abstract factory for document models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.library_models.base.base_document import BaseDocument
from src.library_models.base.base_library import BaseLibrary


class BaseDocumentFactory(ABC):
    """Factory API for building document instances from raw inputs."""

    @staticmethod
    @abstractmethod
    def from_uuid(
        document_uuid: str,
        source_url: str,
        page_detail_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> BaseDocument:
        """Build a document from its UUID and optional page IDs.

        Args:
            document_uuid: UUID of the document to create.
            source_url: URL used to identify the source document.
            page_detail_url: The detail URL for the document.
            output_dir: Directory used to store generated document artifacts.
            page_uuids: Optional page identifiers to attach immediately.

        Returns:
            BaseDocument: A populated document instance.
        """

    @staticmethod
    @abstractmethod
    def from_url(
        library: BaseLibrary,
        source_url: str,
        page_detail_url: str,
        output_dir: str = "output",
        page_uuids: Optional[Sequence[str]] = None,
    ) -> BaseDocument:
        """Build a document from a source URL.

        Args:
            library: The library instance that the document belongs to.
            source_url: URL that identifies the document.
            page_detail_url: The detail URL for the document.
            output_dir: Directory used to store generated document artifacts.
            page_uuids: Optional page identifiers to attach immediately.

        Returns:
            BaseDocument: A document instance resolved from the source URL.
        """
