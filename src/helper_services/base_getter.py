"""Abstract getter interfaces for document page discovery."""

from abc import ABC, abstractmethod
from typing import Optional

from bs4 import BeautifulSoup
from requests import Response

IMPLEMENT_IN_SUBCLASSES = "This method should be implemented in subclasses."


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
        self.document_page_source: Optional[BeautifulSoup | str] = None

    @abstractmethod
    def get_document_source(self, document_url: str) -> BeautifulSoup | Response | None:
        """Get the HTML source of a document page.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            BeautifulSoup | Response | None: The parsed HTML source of the document page, or None if not available.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

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
    def get_name(self, document_url: str, xpath: str) -> str:
        """Get the name of a document.

        Args:
            document_url: URL of the document whose name is requested.
            xpath: The XPath expression to locate the document name in the DOM.

        Returns:
            str: The name of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)
