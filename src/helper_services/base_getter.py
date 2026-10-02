"""Abstract getter interfaces for document page discovery."""

from typing import Any

from abcmeta import ABC, abstractmethod

IMPLEMENT_IN_SUBCLASSES = "This method should be implemented in subclasses."


# pylint: disable-next=too-few-public-methods
class BaseGetterMethod(ABC):
    """Abstract base class for page-discovery getter implementations."""

    description: str = "Base document getter"

    def __init__(self, instance_params: dict[str, Any]) -> None:
        """Initialize the getter with instance parameters.

        Args:
            instance_params: Dictionary containing configuration parameters for the getter.
                             Must include 'identifier_pattern' for document identifier extraction.
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
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_title(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.
            search_parameter: The XPath expression to locate the document title in the DOM.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.
            search_parameter: The XPath expression to locate the document subtitle in the DOM.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_part_title(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the part title of a document.

        Args:
            document_url: URL of the document whose part title is requested.
            search_parameter: The XPath expression to locate the document part title in the DOM.

        Returns:
            str: The part title of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_part_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the part subtitle of a document.

        Args:
            document_url: URL of the document whose part subtitle is requested.
            search_parameter: The XPath expression to locate the document part subtitle in the DOM.

        Returns:
            str: The part subtitle of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)
