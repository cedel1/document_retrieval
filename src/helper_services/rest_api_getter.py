"""REST API document discovery helpers."""

import re
import urllib
from typing import Any

import requests
from requests import Response
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

        identifier_pattern = instance_params.get("identifier_pattern")
        if not identifier_pattern:
            raise ValueError("BaseGetterMethod instance params must include 'identifier_pattern'")

        base_api_url = instance_params.get("base_api_url")
        if not base_api_url:
            raise ValueError("RestApiGetterMethod instance params must include 'base_api_url'")

        self.identifier_pattern = identifier_pattern
        self.base_api_url = base_api_url

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

    def get_document_source(self, document_url: str) -> Response | None:
        """REST API getter does not retrieve HTML source.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            Response | None: The API response, or None if the request fails.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)
            target_url = (
                self.base_api_url
                + f'/search?fl=PID,dostupnost,fedora.model,dc.title,dnnt-labels,details,rels_ext_index,model_path&q="'
                f'"parent_pid:"{document_identifier}"&rows=4000&start=0'
            )
            response = requests.get(target_url, timeout=30, verify=False)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Error fetching pages from REST API: {e}")
            return None

    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the API response.
            document_url: URL of the document whose pages are requested.

        Returns:
            list[str]: A list of page identifiers returned by the API.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)
            target_url = (
                self.base_api_url
                + f"/search?fl=PID,dostupnost,fedora.model,dc.title,dnnt-labels,details,rels_ext_index,model_path&"
                f'q=parent_pid:"{document_identifier}"&rows=4000&start=0'
            )
            response = requests.get(target_url, timeout=30, verify=False)
            page_ids = response.json().get("response").get("docs", [])
            return page_ids
        except (requests.RequestException, ValueError, AttributeError) as e:
            print(f"Error fetching pages from REST API: {e}")
            return []

    def get_title(self, document_url: str, xpath: str) -> str:
        """Get the title of a document.

        Args:
            document_url: URL of the document whose title is requested.
            xpath: The XPath expression to locate the document title in the API response.

        Returns:
            str: The title of the document, or an empty string if not found.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)
            target_url = (
                self.base_api_url
                + f"/search?fl=PID,dostupnost,fedora.model,dc.title,datum_str,dc.creator,rels_ext_index,details,"
                f"dnnt-labels&q=PID:uuid\\:{document_identifier}&sort=datum_str asc,fedora.model asc,dc.title "
                "asc&rows=10000&start=0"
            )
            response = requests.get(target_url, timeout=30, verify=False)
            response.raise_for_status()
            return response.json()["response"]["doc"]["dc.title"]
        except (requests.RequestException, ValueError, AttributeError) as e:
            print(f"Error fetching document title from REST API: {e}")
            return ""

    def get_subtitle(self, document_url: str, xpath: str) -> str:
        """Get the subtitle of a document.

        Args:
            document_url: URL of the document whose subtitle is requested.
            xpath: The XPath expression to locate the document subtitle in the API response.

        Returns:
            str: The subtitle of the document, or an empty string if not found.
        """
        try:
            document_identifier = self._get_document_identifier(document_url)
            target_url = (
                self.base_api_url
                + f"/search?fl=PID,dostupnost,fedora.model,dc.title,datum_str,dc.creator,rels_ext_index,details,"
                f"dnnt-labels&q=PID:uuid\\:{document_identifier}&sort=datum_str asc,fedora.model asc,dc.title asc&"
                "rows=10000&start=0"
            )
            response = requests.get(target_url, timeout=30, verify=False)
            response.raise_for_status()
            return response.json()["response"]["doc"]["details"]
        except (requests.RequestException, ValueError, AttributeError) as e:
            print(f"Error fetching document subtitle from REST API: {e}")
            return ""
