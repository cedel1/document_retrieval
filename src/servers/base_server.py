"""Base server metadata definitions for supported document libraries."""

import importlib
import logging
import re
import string
from abc import ABC, abstractmethod
from re import Pattern

IMPLEMENT_IN_SUBCLASSES = "This method must be implemented in a subclass."

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
    document_info_methods: dict[str, dict]
    # sample document_info_methods
    # document_info_methods: dict[str, dict|str] = {
    #     "dom_selenium": {
    #         "instance_params": {},
    #         "page_search": {"name": "div", "id": re.compile(r"page-id-uuid:([a-f0-9-]+)")},
    #         "title_search": (
    #             "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, "
    #             "'app-book-wrapper')]/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, "
    #             "'app-metadata-content')]/h1"
    #         ),
    #         "subtitle_search": (
    #             "//html/body/app-root/main[contains(@class, 'app-wrapper')]/app-book/div[contains(@class, "
    #             "'app-book-wrapper')]/app-metadata[contains(@class, 'app-book-metadata')]/div/div[contains(@class, "
    #             "'app-metadata-content')]/h2"
    #         ),
    #     },
    # }

    def __init__(self):
        """Initialize the server with no cached getter.

        ``active_getter_instance`` caches the getter selected during the
        current context-manager lifetime. It starts as ``None`` and is
        cleared by ``__exit__``; callers must not rely on it after leaving a
        ``with`` block.
        """
        self.active_getter_instance = None  # we always start with empty getter

    def __enter__(self):
        """Enter the context manager for the server.

        Returns:
            BaseServerType: The server instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and clear the cached getter.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Returns:
            None: Context manager exit does not suppress exceptions.
        """
        self.active_getter_instance = None

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

    def get_getter_name(self) -> str | None:
        """Get the name of the active getter instance.

        Args:
            None: This method does not accept positional arguments.

        Returns:
            str | None: The name of the active getter instance, or None if no active getter is available.
        """
        if self.active_getter_instance:
            return (
                "_".join(re.findall("[a-zA-Z][^A-Z]*", self.active_getter_instance.__class__.__name__)).lower()
            ).split("_getter_method", maxsplit=1)[0]
        return None

    def set_next_getter(self):
        """Get and set the next available getter method.

        This method advances to the next getter method in the configured methods list.
        If an active getter exists, it moves to the next one; otherwise, it starts
        from the first available method.

        Returns:
            None: The active_getter_instance is set as a side effect.

        Raises:
            ValueError: If there are no more getters to try after the current one.
        """
        methods_list = list(self.document_info_methods.keys())

        if self.active_getter_instance:
            current_name = self.get_getter_name()
            if current_name and current_name in methods_list:
                try:
                    method_name = methods_list[methods_list.index(current_name) + 1]
                except IndexError as e:
                    raise ValueError("No more getters to try...") from e
            else:
                method_name = methods_list[0]
        else:
            method_name = methods_list[0]

        getter_class_name = self._get_class_name(method_name)
        self.active_getter_instance = self._get_class_from_name(getter_class_name)(
            self.document_info_methods[method_name]["instance_params"]
        )

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
    def get_document_pages(self, document_url: str) -> str | list[str] | None:
        """Get the set of document pages available for the current server.

        Args:
            document_url: The URL of the document for which to retrieve pages.

        Returns:
            list[str]: A list of strings representing the available document pages.

        Raises:
            ValueError: If no valid document page methods are found for the current server.
        """

    @abstractmethod
    def get_document_title(self, document_url: str) -> str:
        """Get the document title for the current server."""

    @abstractmethod
    def get_document_subtitle(self, document_url: str) -> str:
        """Get the document subtitle for the current server."""

    @abstractmethod
    def get_document_part_title(self, document_url: str) -> str:
        """Get the document part title for the current server."""

    @abstractmethod
    def get_document_part_subtitle(self, document_url: str) -> str:
        """Get the document part subtitle for the current server."""
