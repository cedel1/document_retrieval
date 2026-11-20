"""Server metadata for Kramerius 5 document repositories."""

import logging
import re
from typing import Any, Literal, overload

from src.helper_services.base_getter import CertificateValidationError, MetadataSearch, PageSearch
from .base_server import BaseServerType

MSG_ERROR_IN_METHOD = "Error in %s method: %s"
MSG_SWITCHING_TO_NEXT_METHOD = "Switching to next method"

logger = logging.getLogger(__name__)


# pylint: disable-next=too-few-public-methods
class Kramerius5ServerType(BaseServerType):
    """Concrete server configuration for Kramerius 5 instances."""

    server_type = "kramerius"
    server_version = 5
    document_identifier_url_pattern = re.compile(r"(uuid:[a-f0-9-]+)")

    document_info_methods: dict[str, dict[str, Any]] = {
        # The rest_api makes assumptions about a concrete Kramerius server - revisit when more libraries/servers
        # are added.
        "rest_api": {
            "instance_params": {
                "identifier_pattern": document_identifier_url_pattern,
                "base_api_url": "https://digitalnistudovna.mo.gov.cz/search/api/v5.0/",
                "document_api_url": (
                    "search?fl=PID,dostupnost,fedora.model,dc.title,datum_str,dc.creator,rels_ext_index,details,"
                    "dnnt-labels&q=PID:{}&sort=datum_str asc,fedora.model asc,dc.title "
                    "asc&rows=10000&start=0"
                ),
                "document_pages_api_url": (
                    "search?fl=PID,dostupnost,fedora.model,dc.title,dnnt-labels,details,rels_ext_index,model_path&"
                    'q=parent_pid:"{}"&rows=4000&start=0'
                ),
            },
            "page_search": {
                "page_object": ("response", "docs"),
                "page_id": ("PID",),
                "page_number": ("rels_ext_index", [0]),
            },
            "title_search": ["response", "docs", [0], "dc.title"],
            "subtitle_search": ["response", "docs", [0], "details", [0]],
            "part_title_search": ["response", "docs", [0], "dc.title"],
            "part_subtitle_search": ["response", "docs", [0], "details", [0]],
        },
        "dom_selenium": {
            "instance_params": {},
            "page_search": {"name": "div", "id": re.compile(r"page-id-(uuid:[a-f0-9-]+)")},
            "title_search": (
                "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, "
                "'app-book-wrapper')]/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, "
                "'app-metadata-content')]/h1//text()"
            ),
            "subtitle_search": (
                "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, "
                "'app-book-wrapper')]/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, "
                "'app-metadata-content')]/h2//text()"
            ),
            "part_title_search": (
                "/html/body/app-root/main/app-book/div/app-metadata/div/div[2]/div[2]/div[1]/app-metadata/div/div"
                "/h1//text()"
            ),
            "part_subtitle_search": (
                "/html/body/app-root/main/app-book/div/app-metadata/div/div[2]/div[2]/div[1]/app-metadata/div/div"
                "/h2//text()"
            ),
        },
    }

    def get_document_pages(self, document_url: str) -> str | list[str] | None:
        """Get the set of document pages available for Kramerius 5 servers.

        Args:
            document_url: The URL of the document for which to retrieve pages.

        Returns:
            str | list[str] | None: A list of strings representing the available document pages,
                                or None if no pages are found.

        Raises:
            ValueError: If no pages can be found using any available method.
        """
        if self.active_getter_instance is None:
            self.set_next_getter()

        result = self._get_partial_information(
            document_url, "get_pages", "page_search", "Error occurred while fetching document pages for %s: %s"
        )

        # Raise ValueError if result is empty list (no pages found) or empty string (all methods failed)
        if (isinstance(result, list) and not result) or result == "":
            raise ValueError("Could not find pages for Kramerius 5 server")

        return result or None

    def get_document_title(self, document_url: str) -> str:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        return self._get_partial_information(
            document_url, "get_title", "title_search", "Error occurred while fetching document title for %s: %s"
        )

    def get_document_subtitle(self, document_url: str) -> str:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        return self._get_partial_information(
            document_url,
            "get_subtitle",
            "subtitle_search",
            "Error occurred while fetching document subtitle for %s: %s",
        )

    def get_document_part_title(self, document_url: str) -> str:
        """Get the title of a document part.

        Args:
            document_url: URL of the document whose title is requested.

        Returns:
            str: The title of the document part, or an empty string if not found.
        """
        return self._get_partial_information(
            document_url,
            "get_part_title",
            "part_title_search",
            "Error occurred while fetching document part title for %s: %s",
        )

    def get_document_part_subtitle(self, document_url: str) -> str:
        """Get the subtitle of a document part.

        Args:
            document_url: URL of the document whose subtitle is requested.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        return self._get_partial_information(
            document_url,
            "get_part_subtitle",
            "part_subtitle_search",
            "Error occurred while fetching document part subtitle for %s: %s",
        )

    # These type-checking overloads distinguish page lists (or an empty string on failure) from metadata strings.
    # The implementation below handles both cases at runtime.
    @overload
    def _get_partial_information(
        self,
        document_url: str,
        getter_method_name: Literal["get_pages"],
        getter_method_parameters_key: str,
        exception_text: str,
    ) -> str | list[str]: ...

    @overload
    def _get_partial_information(
        self,
        document_url: str,
        getter_method_name: Literal["get_title", "get_subtitle", "get_part_title", "get_part_subtitle"],
        getter_method_parameters_key: str,
        exception_text: str,
    ) -> str: ...

    def _get_partial_information(
        self, document_url: str, getter_method_name: str, getter_method_parameters_key: str, exception_text: str
    ) -> str | list[str]:
        """Get partial document information, reusing the active getter when possible.

        Args:
            document_url: URL of the document whose information is requested.
            getter_method_name: The name of the method to use for retrieving the information.

        Returns:
            str | list[str]: The requested information from the document, or an empty string if not found.

        Notes:
            ``active_getter_instance`` is a per-context cache. The cached
            getter is tried first; if it raises ``ValueError``, it is
            discarded and the configured getter methods are tried in order.
            The cache is valid only within the server's context-manager
            lifetime and is reset by ``BaseServerType.__exit__``.
        """
        failures: tuple[CertificateValidationError | None, bool] = (None, False)
        try:
            if self.active_getter_instance:
                try:
                    getter_name = self.get_getter_name()
                    if getter_name is None:
                        raise ValueError("Active getter has no name")
                    getter_method_parameters = self.document_info_methods[getter_name][getter_method_parameters_key]
                    return self._get_document_partial_information(
                        document_url, getter_method_name, getter_method_parameters
                    )
                except ValueError as error:
                    failures = self._record_getter_failure(error, failures)

            return self._get_configured_information(
                document_url, getter_method_name, getter_method_parameters_key, failures
            )
        except CertificateValidationError:
            if getter_method_name == "get_pages":
                raise
            return ""
        except ValueError as e:
            logger.exception(exception_text, document_url, e)
        return ""

    def _get_configured_information(
        self,
        document_url: str,
        getter_method_name: str,
        getter_method_parameters_key: str,
        failures: tuple[CertificateValidationError | None, bool],
    ) -> str | list[str]:
        """Try configured getters in order, preserving failures from the active getter."""
        methods_list = list(self.document_info_methods.keys())
        for method_name in methods_list:
            try:
                getter_class_name = self._get_class_name(method_name)
                getter_class = self._get_class_from_name(getter_class_name)
                if getter_class is None:
                    continue

                self.active_getter_instance = getter_class(self._getter_params(method_name))
                getter_method_parameters = self.document_info_methods[method_name][getter_method_parameters_key]
                if result := self._get_document_partial_information(
                    document_url, getter_method_name, getter_method_parameters
                ):
                    return result
            except ValueError as error:
                failures = self._record_getter_failure(error, failures)

        certificate_error, other_failure = failures
        if certificate_error and not other_failure:
            raise certificate_error
        raise ValueError(
            f"Could not find document information for Kramerius 5 server using method {getter_method_name}."
        )

    def _record_getter_failure(
        self, error: ValueError, failures: tuple[CertificateValidationError | None, bool]
    ) -> tuple[CertificateValidationError | None, bool]:
        """Discard the failed getter and retain certificate and other failures separately."""
        self.active_getter_instance = None
        certificate_error, other_failure = failures
        if isinstance(error, CertificateValidationError):
            certificate_error = error
        else:
            other_failure = True
        return certificate_error, other_failure

    def _get_document_partial_information(
        self, document_url: str, getter_method_name: str, getter_method_parameters: PageSearch | MetadataSearch
    ) -> str | list[str]:
        try:
            if self.active_getter_instance is None:
                raise ValueError("No active getter is available")
            return getattr(self.active_getter_instance, getter_method_name)(document_url, getter_method_parameters)
        except CertificateValidationError:
            self.active_getter_instance = None
            raise
        except ValueError as e:
            logger.exception("Saved active getter did not return information for %s: %s", document_url, e)
            logger.debug(MSG_SWITCHING_TO_NEXT_METHOD)
            self.active_getter_instance = None
            raise
