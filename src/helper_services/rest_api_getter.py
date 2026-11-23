"""REST API document discovery helpers."""

import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests
from typing_extensions import override

from src.helper_services.base_getter import (
    BaseGetterMethod,
    MetadataSearch,
    PageSearch,
    is_certificate_verification_error,
    report_certificate_failure,
)

logger = logging.getLogger(__name__)


class RestApiGetterMethod(BaseGetterMethod):
    """Fetch page information from a document library's REST API."""

    description: str = "REST API getter"

    def __init__(self, instance_params: dict[str, Any]):
        """Initialize the REST API getter with a target endpoint.

        Args:
            instance_params: Dictionary containing configuration parameters for the getter.
                             Must include 'identifier_pattern' for document identifier extraction
                             and 'base_api_url' for the REST API endpoint.

        Returns:
            None: The getter instance is created in memory.

        Raises:
            ValueError: If required parameters are missing from instance_params.
        """
        super().__init__(instance_params)

        self.instance_params = instance_params

        self.document_json = None
        self.document_pages_json = None

        identifier_pattern = instance_params.get("identifier_pattern")
        if not identifier_pattern or not (
            isinstance(identifier_pattern, str)
            or (isinstance(identifier_pattern, re.Pattern) and isinstance(identifier_pattern.pattern, str))
        ):
            raise ValueError("BaseGetterMethod instance params must include a text 'identifier_pattern'")
        self.identifier_pattern = identifier_pattern

        self.base_api_url = self._check_value_is_non_empty_string(instance_params, "base_api_url")
        self.document_api_url = self._check_value_is_non_empty_string(instance_params, "document_api_url")
        self.document_pages_api_url = self._check_value_is_non_empty_string(instance_params, "document_pages_api_url")

    @staticmethod
    def _check_value_is_non_empty_string(instance_params: dict[str, Any], parameter_name: str) -> str:
        """Return a required string parameter or raise if it is missing or invalid."""
        value = instance_params.get(parameter_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"RestApiGetterMethod instance params must include '{parameter_name}'")
        return value

    def _get_document_identifier(self, document_url: str) -> str | None:
        """Extract the document identifier from the document URL.

        Args:
            document_url: The URL of the document.

        Returns:
            str: The extracted document identifier, or None if not found.
        """
        path_match = re.search(self.identifier_pattern, urlparse(document_url).path)
        return path_match.group(1) if path_match else None

    def _get_full_api_url(self, url_pattern: str, replacement_strings: list[str]) -> str:
        """
        Args:
            url_pattern:
            replacement_strings:

        Returns:
        """

        return "".join([self.base_api_url, url_pattern.format(*replacement_strings)])

    def _recursive_get(self, source_dictionary, *keys):
        """Helper to get nested json values using a list of keys"""
        for key in keys:
            try:
                if isinstance(key, list):
                    source_dictionary = source_dictionary[key[0]]
                else:
                    source_dictionary = source_dictionary[key]
            except (KeyError, IndexError, TypeError):
                return None
        return source_dictionary

    def get_document_source(self, document_url: str) -> tuple[Any, Any] | None:
        """REST API getter does not retrieve HTML source.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            tuple[Any, Any] | None: The document and page JSON responses, or None if the request fails.

        Raises:
            ValueError: If the server certificate validation fails.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)
            if document_identifier is None:
                raise ValueError(f"No document identifier found in {document_url}")
            request_url = self._get_full_api_url(self.document_api_url, [document_identifier.replace(":", "\\:")])

            try:
                document_info_response = requests.get(
                    request_url,
                    headers={"Accept": "application/json"},
                    timeout=30,
                    verify=not self.allow_insecure,
                )
                logger.debug(document_info_response)
                document_info_response.raise_for_status()
                request_url = self._get_full_api_url(self.document_pages_api_url, [document_identifier])
                document_pages_response = requests.get(
                    request_url,
                    headers={"Accept": "application/json"},
                    timeout=30,
                    verify=not self.allow_insecure,
                )
                logger.debug(document_pages_response)
                document_pages_response.raise_for_status()
            except requests.exceptions.SSLError as e:
                if is_certificate_verification_error(e):
                    raise report_certificate_failure(document_url, request_url) from e
                logger.exception("SSL error fetching document info from REST API: %s", e)
                raise ValueError(f"SSL error fetching document info from REST API: {e}") from e
            except requests.RequestException as e:
                logger.exception("Error fetching document info from REST API: %s", e)
                return None

            self.document_json = document_info_response.json()
            self.document_pages_json = document_pages_response.json()
            return self.document_json, self.document_pages_json
        except requests.RequestException as e:
            logger.exception("Error fetching pages from REST API: %s", e)
            return None

    def get_pages(self, document_url: str, search_parameter: PageSearch) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the API response.
            document_url: URL of the document whose pages are requested.

        Returns:
            list[str]: A list of page identifiers returned by the API.
        """
        page_objects = {}

        try:
            if self.get_document_source(document_url) is None:
                raise ValueError(f"Could not retrieve REST document source for {document_url}")
            page_entries = self._recursive_get(self.document_pages_json, *search_parameter["page_object"])
            if not isinstance(page_entries, list):
                raise ValueError(f"Invalid REST page data for {document_url}: expected a list")
            for page_object in page_entries:
                page_id = self._recursive_get(page_object, *search_parameter["page_id"])
                if not isinstance(page_id, str):
                    raise ValueError(f"Invalid REST page identifier for {document_url}: expected a string")
                page_objects[self._recursive_get(page_object, *search_parameter["page_number"])] = page_id
            return [page_objects[key] for key in sorted(page_objects)]

        except KeyError as e:
            logger.exception("Error fetching pages from REST API: %s", e)

        return []

    def _get_json_value(self, search_parameter: MetadataSearch) -> str:
        if self.document_json is None:
            return ""
        if not isinstance(self.document_json, dict):
            raise ValueError("Invalid REST document metadata: expected a JSON object")
        if isinstance(search_parameter, list):
            value = self._recursive_get(self.document_json, *search_parameter)
        else:
            value = self.document_json.get(search_parameter)
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"Invalid REST metadata for {search_parameter!r}: expected a string")
        return value

    @override
    def get_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_part_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the part title of a document.

        Args:
            document_url: URL of the document whose part title is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The part title of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_part_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
        """Get the part subtitle of a document.

        Args:
            document_url: URL of the document whose part subtitle is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The part subtitle of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)
