"""Server metadata for Kramerius 5 document repositories."""

import logging
import re

from .base_server import BaseServerType

logger = logging.getLogger(__name__)


class Kramerius5ServerType(BaseServerType):
    """Concrete server configuration for Kramerius 5 instances."""

    server_type = "kramerius"
    server_version = 5
    document_page_methods: dict[str, str | dict] = {
        "dom_selenium": {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")},
    }

    def get_document_pages(self, document_url: str) -> list[str]:
        """Get the set of document pages available for Kramerius 5 servers.

        Args:
            document_url: The URL of the document for which to retrieve pages.

        Returns:
            list[str]: A list of strings representing the available document pages.

        Returns:
            list[str]: A list of strings representing the available document pages.
        """
        page_urls = None
        for page_method, search_attribute in self.document_page_methods.items():
            logger.info("Trying page method: %s with search attribute: %s", page_method, search_attribute)
            print(f"Trying page method: {page_method} with search attribute: {search_attribute}")
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
                page_urls = class_().get_pages(document_url, search_attribute)
                logger.debug("Page URLs found: %s" % page_urls)
            except ValueError as e:
                # if the class raises a ValueError, log the error and continue to the next method
                logger.exception("Error in %s method: %s" % (page_method, e))
                continue
            # if the class returns a valid list of document pages, return that list and stop iterating through the keys
            if page_urls:
                return page_urls

        # if no valid document page methods were found, raise an error
        raise ValueError("Could not find pages for Kramerius 5 server.")
