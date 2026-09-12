"""Server metadata for Kramerius 5 document repositories."""

import logging
import re
from typing import Any

from .base_server import BaseServerType

MSG_ERROR_IN_METHOD = "Error in %s method: %s"
MSD_SWITCHING_TO_NEXT_METHOD = "Switching to next method"

logger = logging.getLogger(__name__)


# pylint: disable-next=too-few-public-methods
class Kramerius5ServerType(BaseServerType):
    """Concrete server configuration for Kramerius 5 instances."""

    server_type = "kramerius"
    server_version = 5
    document_identifier_url_pattern = re.compile(r"uuid:([a-f0-9-]+)")
    document_page_methods: dict[str, str | dict] = {
        "dom_selenium": {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")},
    }
    document_title_xpath: str = (
        "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, 'app-book-wrapper')]"
        "/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, 'app-metadata-content')]/h1"
    )
    document_subtitle_xpath: str = (
        "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, 'app-book-wrapper')]"
        "/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, 'app-metadata-content')]/h2"
    )

    def get_document_pages(self, document_url: str) -> list[str]:
        """Get the set of document pages available for Kramerius 5 servers.

        Args:
            document_url: The URL of the document for which to retrieve pages.

        Returns:
            list[str]: A list of strings representing the available document pages.

        Returns:
            list[str]: A list of strings representing the available document pages.
        """
        if self.active_getter_instance:
            try:
                return self.active_getter_instance.get_pages(document_url, self.document_title_xpath)
            except ValueError as e:
                logger.exception("Saved active logger did not find pages for %s: %s", document_url, e)
                logger.debug(MSD_SWITCHING_TO_NEXT_METHOD)
                self.active_getter_instance = None

        page_urls = None
        for page_method, search_attribute in self.document_page_methods.items():
            logger.info("Trying page method: %s with search attribute: %s", page_method, search_attribute)
            # create a class from the page method key
            class_ = self._get_class_from_name(self._get_class_name(page_method))
            logger.debug("Class for page method %s: %s", page_method, class_)
            # call the class with the provided document_page_methods[key] value as an argument
            try:
                logger.debug(
                    "Calling class %s with document_url: %s and search_attribute: %s",
                    class_,
                    document_url,
                    search_attribute,
                )
                self.active_getter_instance = class_()
                page_urls = self.active_getter_instance.get_pages(document_url, search_attribute)
                # pylint: disable-next=logging-not-lazy,consider-using-f-string
                logger.debug("Page URLs found: %s" % page_urls)
            except ValueError as e:
                # if the class raises a ValueError, log the error and continue to the next method
                # pylint: disable-next=logging-not-lazy,consider-using-f-string
                logger.exception(MSG_ERROR_IN_METHOD % (page_method, e))
                self.active_getter_instance = None  # clear it out so it is not reused later
                continue
            # if the class returns a valid list of document pages, return that list and stop iterating through the keys
            if page_urls:
                return page_urls

        # if no valid document page methods were found, raise an error
        raise ValueError("Could not find pages for Kramerius 5 server.")

    def get_document_title(self, document_url: str) -> str:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        try:
            return self._get_document_partial_information(document_url, "get_title", [self.document_title_xpath])
        except ValueError as e:
            logger.exception("Error occurred while fetching document title for %s: %s", document_url, e)
        return ""

    def get_document_subtitle(self, document_url: str) -> str:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        try:
            return self._get_document_partial_information(document_url, "get_subtitle", [self.document_subtitle_xpath])
        except ValueError as e:
            logger.exception("Error occurred while fetching document subtitle for %s: %s", document_url, e)
        return ""

    def _get_document_partial_information(
        self, document_url: str, getter_method_name: str, getter_method_parameters: list[Any]
    ) -> str:
        """Get partial document information, reusing the active getter when possible.

        Args:
            document_url: URL of the document whose information is requested.
            getter_method_name: The name of the method to use for retrieving the information.

        Returns:
            str: The requested information from the document, or an empty string if not found.

        Notes:
            ``active_getter_instance`` is a per-context cache. The cached
            getter is tried first; if it raises ``ValueError``, it is
            discarded and the configured getter methods are tried in order.
            The cache is valid only within the server's context-manager
            lifetime and is reset by ``BaseServerType.__exit__``.
        """
        if self.active_getter_instance:
            try:
                if method_to_use := getattr(self.active_getter_instance, getter_method_name):
                    return method_to_use(document_url, *getter_method_parameters)
            except ValueError as e:
                logger.exception("Saved active logger did not find subtitle for %s: %s", document_url, e)
                logger.debug(MSD_SWITCHING_TO_NEXT_METHOD)
                self.active_getter_instance = None
                # We could remove the failed getter from the list of getters to try here, but to be on the safe side,
                # don't do that.

        for page_method in self.document_page_methods:
            # create a class from the page method key
            getter_class = self._get_class_from_name(self._get_class_name(page_method))
            method_to_use = getattr(getter_class(), getter_method_name)
            logger.debug("Class for name method %s: %s", page_method, getter_class)
            try:
                method_result = method_to_use(document_url, *getter_method_parameters)
            except ValueError as e:
                logger.exception(MSG_ERROR_IN_METHOD, page_method, e)
                continue
            if method_result:
                return method_result

        raise ValueError(
            f"Could not find document information for Kramerius 5 server using method {getter_method_name}."
        )
