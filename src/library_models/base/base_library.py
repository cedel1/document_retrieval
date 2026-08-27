"""Abstract library model."""

from __future__ import annotations

from abc import ABC, abstractmethod, ABCMeta
from typing import Optional, Sequence

from src.helpers.singleton import Singleton, SingletonMeta
from src.library_models.base.base_document import BaseDocument

# from src.library_models.base.base_document_factory import BaseDocumentFactory
from src.servers.base_server import BaseServerType


class BaseMetaClass(ABCMeta, SingletonMeta):
    """Metaclass for defining Abstract Base Classes (ABCs) with Singleton behavior."""


class BaseLibrary(ABC, Singleton, metaclass=BaseMetaClass):
    """Abstract base library/server that a specific document is hosted on."""

    server_urls: list[str] = []
    server_type: Optional[BaseServerType] = None
    library_name = "Library_Base"

    def __init__(self, document_url: Optional[str] = "") -> None:
        """Initialize a library definition with its URL and contained documents.

        Args:
            library_url: Base URL for the document library.
            documents: Optional list of documents already associated with the library.

        Returns:
            None: The library instance is created in memory.
        """
        self.library_url = [url for url in self.server_urls if document_url.startswith(url)][0] if document_url else ""
        self.documents = []  # List of BaseDocument instances associated with this library

    @classmethod
    def is_document_in_library(cls, document_url: str) -> bool:
        """Check if a document is hosted on this library.

        Args:
            document_url: URL of the document being checked.

        Returns:
            bool: True when the URL belongs to the library; otherwise False.
        """
        return any(document_url.startswith(url) for url in cls.server_urls)

    @abstractmethod
    def preprocess_document_from_url(
        self, document_url: str, output_dir: str = "output", page_uuids: Optional[Sequence[str]] = None
    ) -> BaseDocument:
        """Preprocess a document before processing.

        Args:
            document_url: URL of the document to preprocess.
            output_dir: Directory used to store generated document artifacts.
            page_uuids: Optional page identifiers to attach immediately.

        Returns:
            BaseDocument: The preprocessed document.
        """
        # return BaseDocumentFactory.from_url(
        #     library=self, source_url=document_url, output_dir=output_dir, page_uuids=page_uuids
        # )

    def append_preprocessed_document(self, document: BaseDocument) -> None:
        """Append a preprocessed document to the library's document list.

        Args:
            document: The preprocessed document to append.

        Returns:
            None: The document is appended to the library's document list.
        """
        self.documents.append(document)

    def __str__(self):
        """Return a string representation of the library."""
        return f"{self.__class__.__name__}"

    def process_document(self, document: BaseDocument, additional_args: dict[str, list], output_dir: str) -> None:
        """Process a document hosted on this library.

        Args:
            document: The document to process.
            additional_args: Additional arguments for processing.
            output_dir: Directory to store processed outputs.

        Returns:
            None: The document is processed and stored in the specified output directory.
        """
        # Placeholder for actual processing logic
        print(f"Processing document {document} from library {self} with args {additional_args} into {output_dir}")
        print(f"additional_args: {additional_args}")
        document.create_properties_file(
            dezoomify_path=additional_args["dezoomify-path"], dezoomify_args=additional_args["dezoomify-args"]
        )
        for page in document.pages:
            print(f"Processing page {page} of document {document}")
            page.download(
                dezoomify_path=additional_args["dezoomify-path"], dezoomify_args=additional_args["dezoomify-args"]
            )
