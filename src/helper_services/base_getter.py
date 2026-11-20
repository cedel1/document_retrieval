"""Abstract getter interfaces for document page discovery."""

import logging
import ssl
from typing import Any
from urllib.parse import urlparse

import urllib3
from abcmeta import ABC, abstractmethod

PageSearch = dict[str, Any]
MetadataSearch = str | list[str] | list[str | list[int]]

IMPLEMENT_IN_SUBCLASSES = "This method should be implemented in subclasses."

logger = logging.getLogger(__name__)

SSL_ERROR_HINT = (
    "Certificate validation failed for server %s (document: %s). If you trust this server, --allow-insecure "
    "disables validation, which permits interception or spoofing. Alternatively, contact the server owner "
    "to fix the certificate."
)


class CertificateValidationError(ValueError):
    """A certificate verification failure already reported to the user."""


def is_certificate_verification_error(error: BaseException) -> bool:
    """Find a certificate verification error through requests and urllib3 exception wrappers."""
    pending = [error]
    seen = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, ssl.SSLCertVerificationError):
            return True
        for candidate in (*current.args, current.__cause__, current.__context__, getattr(current, "reason", None)):
            if isinstance(candidate, BaseException):
                pending.append(candidate)
    return False


def report_certificate_failure(document_url: str, request_url: str) -> CertificateValidationError:
    """Report one failed request and retain its full traceback at debug level."""
    logger.warning(SSL_ERROR_HINT, urlparse(request_url).hostname, document_url)
    logger.debug("Certificate verification failure details", exc_info=True)
    return CertificateValidationError(f"Certificate validation failed for {document_url}")


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
    def get_pages(self, document_url: str, search_parameter: PageSearch) -> list[str]:
        """Get the pages of a document.

        Args:
            document_url: URL of the document whose pages are requested.
            search_parameter: Parameter for searching document pages.

        Returns:
            list[str]: The discovered page identifiers.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.
            search_parameter: An XPath expression or a REST API metadata path.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.
            search_parameter: An XPath expression or a REST API metadata path.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_part_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the part title of a document.

        Args:
            document_url: URL of the document whose part title is requested.
            search_parameter: An XPath expression or a REST API metadata path.

        Returns:
            str: The part title of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)

    @abstractmethod
    def get_part_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the part subtitle of a document.

        Args:
            document_url: URL of the document whose part subtitle is requested.
            search_parameter: An XPath expression or a REST API metadata path.

        Returns:
            str: The part subtitle of the document, or an empty string if not found.
        """
        raise NotImplementedError(IMPLEMENT_IN_SUBCLASSES)
