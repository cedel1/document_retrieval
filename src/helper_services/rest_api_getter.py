"""REST API document discovery helpers."""

import requests
from requests import Response

from src.helper_services.base_getter import BaseGetterMethod


class RestApiGetterMethod(BaseGetterMethod):
    """Fetch page information from a document library's REST API."""

    description: str = "REST API getter"

    def __init__(self, api_url: str):
        """Initialize the REST API getter with a target endpoint.

        Args:
            api_url: Base URL used to query page metadata.

        Returns:
            None: The getter instance is created in memory.
        """
        super().__init__()
        self.api_url = api_url

    def get_document_source(self, document_url: str) -> Response | None:
        """REST API getter does not retrieve HTML source.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            Response | None: The API response, or None if the request fails.
        """
        try:
            response = requests.get(self.api_url, timeout=30, verify=False)
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
            return self.get_document_source(document_url).json().get(search_parameter, [])
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
            return self.get_document_source(document_url).json().get("title", "")
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
            return self.get_document_source(document_url).json().get("subtitle", "")
        except (requests.RequestException, ValueError, AttributeError) as e:
            print(f"Error fetching document subtitle from REST API: {e}")
            return ""
