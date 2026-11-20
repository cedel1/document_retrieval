"""Abstract getter interfaces for document page discovery."""

import logging
from typing import Any

import urllib3
from abcmeta import ABC, abstractmethod

IMPLEMENT_IN_SUBCLASSES = "This method should be implemented in subclasses."

logger = logging.getLogger(__name__)

SSL_ERROR_HINT = (
    "Certificate validation failed for %s: %s. If you trust this site, disable validation with --allow-insecure "
    "or allow_insecure = true (top level or in [library.<library_name>]) in the config file."
)


# pylint: disable-next=too-few-public-methods
class BaseGetterMethod(ABC):
    """Abstract base class for page-discovery getter implementations."""

    description: str = "Base document getter"

    def __init__(self, instance_params: dict[str, Any]) -> None:
        """Initialize the getter with instance parameters.

        Args:
            instance_params: Dictionary containing configuration parameters for the getter.
                             Must include 'identifier_pattern' for document identifier extraction.
                             An optional 'allow_insecure' (default False) disables certificate validation.
        """
        self.allow_insecure: bool = isinstance(instance_params, dict) and bool(
            instance_params.get("allow_insecure", False)
        )
        if self.allow_insecure:
            # The user opted in explicitly and is warned once when the settings are resolved
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
