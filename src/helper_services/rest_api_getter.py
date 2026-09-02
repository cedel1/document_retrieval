"""REST API document discovery helpers."""

import requests

from src.helper_services.base_getter import BaseGetterMethod


# pylint: disable-next=too-few-public-methods
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
        self.api_url = api_url

    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the API response.
            document_url: URL of the document whose pages are requested.

        Returns:
            list[str]: A list of page identifiers returned by the API.
        """
        try:
            response = requests.get(self.api_url, timeout=30, verify=False)
            response.raise_for_status()
            return response.json().get(search_parameter, [])
        except requests.RequestException as e:
            print(f"Error fetching pages from REST API: {e}")
            return []
