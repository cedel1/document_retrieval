"""REST API document discovery helpers."""

import re
import urllib
from typing import Any, override

import requests
from document_retrieval import logger
from src.helper_services.base_getter import BaseGetterMethod


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

        self.identifier_pattern = instance_params.get("identifier_pattern")
        if not self.identifier_pattern:
            raise ValueError("BaseGetterMethod instance params must include 'identifier_pattern'")

        self.base_api_url = instance_params.get("base_api_url")
        if not self.base_api_url:
            raise ValueError("RestApiGetterMethod instance params must include 'base_api_url'")

        self.document_api_url = instance_params.get("document_api_url")
        if not self.document_api_url:
            raise ValueError("RestApiGetterMethod instance params must include 'document_api_url'")

        self.document_pages_api_url = instance_params.get("document_pages_api_url")
        if not self.document_pages_api_url:
            raise ValueError("RestApiGetterMethod instance params must include 'document_pages_api_url'")

    def _get_document_identifier(self, document_url: str) -> str:
        """Extract the document identifier from the document URL.

        Args:
            document_url: The URL of the document.

        Returns:
            str: The extracted document identifier, or None if not found.
        """
        path_match = re.search(self.identifier_pattern, urllib.parse.urlparse(document_url).path)
        document_uuid = path_match.group(1) if path_match else None
        return document_uuid

    def _get_full_api_url(self, url_pattern, replacement_strings: list[str]):
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
            except KeyError:
                return None
        return source_dictionary

    def get_document_source(self, document_url: str) -> tuple[str, str] | None:
        """REST API getter does not retrieve HTML source.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            Response | None: The API response, or None if the request fails.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)

            try:
                document_info_response = requests.get(
                    self._get_full_api_url(
                        self.document_api_url,
                        [
                            document_identifier.replace(":", "\\:"),
                        ],
                    ),
                    headers={"Accept": "application/json"},
                    timeout=30,
                    verify=False,
                )
                logger.debug(document_info_response)
                document_info_response.raise_for_status()
                document_pages_response = requests.get(
                    self._get_full_api_url(
                        self.document_pages_api_url,
                        [
                            document_identifier,
                        ],
                    ),
                    headers={"Accept": "application/json"},
                    timeout=30,
                    verify=False,
                )
                logger.debug(document_pages_response)
                document_pages_response.raise_for_status()
            except requests.RequestException as e:
                logger.exception("Error fetching document info from REST API: %s", e)
                return None

            self.document_json = document_info_response.json()
            self.document_pages_json = document_pages_response.json()
            return self.document_json, self.document_pages_json
        except requests.RequestException as e:
            logger.exception("Error fetching pages from REST API: %s", e)
            return None

    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the API response.
            document_url: URL of the document whose pages are requested.

        Returns:
            list[str]: A list of page identifiers returned by the API.
        """
        page_objects = {}

        try:
            _, _ = self.get_document_source(document_url)
            for page_object in self._recursive_get(self.document_pages_json, *search_parameter.get("page_object")):
                page_objects[self._recursive_get(page_object, *search_parameter.get("page_number"))] = (
                    self._recursive_get(page_object, *search_parameter.get("page_id"))
                )
            page_uuids = [page_objects[key] for key in sorted(page_objects)]
            return page_uuids

        except KeyError as e:
            logger.exception("Error fetching pages from REST API: %s", e)

        return []

    def _get_json_value(self, search_parameter: dict | list | str) -> str | Any:
        if self.document_json:
            if isinstance(search_parameter, list):
                return self._recursive_get(self.document_json, *search_parameter)
            return self.document_json.get(search_parameter, "")
        return ""

    @override
    def get_title(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_part_title(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the part title of a document.

        Args:
            document_url: URL of the document whose part title is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The part title of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)

    @override
    def get_part_subtitle(self, document_url: str, search_parameter: str) -> str | Any:
        """Get the part subtitle of a document.

        Args:
            document_url: URL of the document whose part subtitle is requested.
            search_parameter: The parameter to search for in the API response.

        Returns:
            str: The part subtitle of the document, or an empty string if not found.
        """
        return self._get_json_value(search_parameter)
