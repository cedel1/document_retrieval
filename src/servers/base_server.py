"""Base server metadata definitions for supported document libraries."""

import importlib
import logging
import string
from abc import ABC, abstractmethod
from re import Pattern

logger = logging.getLogger(__name__)


class BaseServerType(ABC):
    """Abstract description of a document library backend.

    The server type captures the library identifier, version, and the page
    discovery methods supported by the hosting installation.
    """

    server_type = "base"
    server_version = 0
    base_getter_directory = "src.helper_services"
    # implementations should override this with a regex pattern to extract the document identifier from a URL
    document_identifier_url_pattern: Pattern
    document_page_methods: dict[str, str | dict] = {
        # examples:
        # "rest_api": "pages",
        # "simple_dom": {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")},
        # "dom_selenium": {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")},
    }
    document_properties_file: str = ""

    def __str__(self) -> str:
        """Return a readable identifier for the current server type.

        Args:
            None: This method does not accept positional arguments.

        Returns:
            str: A string containing the server type and version.
        """
        return f"{self.server_type}_{self.server_version}"

    @staticmethod
    def _get_class_name(method_key: str) -> str:
        """Get the class name for a given page discovery method.

        Args:
            method_key: The key representing the page discovery method.

        Returns:
            str: The class name corresponding to the provided method key.
        """
        return string.capwords(f"{method_key}_getter_method", sep="_").replace("_", "")

    def _get_class_from_name(self, class_name: str):
        """Dynamically import and return a class from the helper_services module.

        Args:
            class_name: The name of the class to import.

        Returns:
            type: The class object corresponding to the provided class name.
        """
        class_ = None
        try:
            module_ = importlib.import_module(self.base_getter_directory)
            try:
                class_ = getattr(module_, class_name)
            except AttributeError:
                logger.exception("Class %s does not exist", class_name)
        except ImportError:
            logger.exception("Module %s does not exist", self.base_getter_directory)
        return class_

    @abstractmethod
    def get_document_pages(self, document_url: str) -> list[str]:
        """Get the set of document pages available for the current server.

        Args:
            document_url: The URL of the document for which to retrieve pages.

        Returns:
            list[str]: A list of strings representing the available document pages.

        Raises:
            ValueError: If no valid document page methods are found for the current server.
        """
