"""Factory helpers for choosing the correct library implementation from a URL."""

from src.library_models.base.base_library import BaseLibrary
from src.library_models.dsmo.dsmo_library import DSMOLibrary


# pylint: disable-next=too-few-public-methods
class LibraryFactory:
    """Construct the correct library model for an incoming document URL."""

    library_classes = [
        DSMOLibrary,
    ]

    @staticmethod
    def from_url(document_url: str) -> BaseLibrary:
        """Resolve a document URL to its matching library implementation.

        Args:
            document_url: URL of the document to resolve.

        Returns:
            BaseLibrary: The matching library instance.

        Raises:
            ValueError: If the URL does not belong to a supported library.
        """
        # Logic to determine the appropriate library class based on the URL
        for library_class in LibraryFactory.library_classes:
            if library_class.is_document_in_library(document_url):
                return library_class()

        raise ValueError(f"Unsupported library URL: {document_url}")
