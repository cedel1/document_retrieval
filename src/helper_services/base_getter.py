"""Abstract getter interfaces for document page discovery."""

from abc import ABC, abstractmethod


# pylint: disable-next=too-few-public-methods
class BaseGetterMethod(ABC):
    """Abstract base class for page-discovery getter implementations."""

    description: str = "Base document getter"

    def __init__(self):
        """Initialize the getter implementation.

        Args:
            None: This initializer takes no arguments.

        Returns:
            None: Subclasses must define their own initialization logic.
        """

    @abstractmethod
    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            document_url: URL of the document whose pages are requested.
            search_parameter: Parameter for searching document pages.

        Returns:
            list[str]: The discovered page identifiers.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")
