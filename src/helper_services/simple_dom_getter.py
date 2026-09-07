"""DOM-based page discovery helpers for library HTML pages."""

import logging
import re
from typing import List, Any

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests import HTTPError

from src.helper_services.base_getter import BaseGetterMethod

logger = logging.getLogger(__name__)


class SimpleDomGetterMethod(BaseGetterMethod):
    """Extract page identifiers from HTML markup using a simple DOM scan."""

    description: str = "Simple DOM getter"

    def get_document_source(self, document_url: str) -> BeautifulSoup | str | None:
        """Get the HTML source of a document page.

        Args:
            document_url: URL of the document page to fetch and parse.

        Returns:
            BeautifulSoup | None: The parsed HTML source of the document page, or None if not available.
        """
        try:
            response = requests.get(document_url, timeout=30, verify=False)
            response.raise_for_status()
            self.document_page_source = BeautifulSoup(response.content, "html.parser")
            return self.document_page_source
        except HTTPError as e:
            logger.debug("Basic request failed: %s", e)
            return None

    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the DOM.
            document_url: URL of the document page to fetch and parse.

        Returns:
            list[str]: Page UUIDs discovered in the DOM, or an empty list if none are found.
        """
        try:
            page_uuids = self._extract_uuids_from_divs_with_id_pattern(
                self.get_document_source(document_url), search_parameter
            )

            if page_uuids:
                logger.info("Found %d pages via basic request %s", len(page_uuids), page_uuids)
                return page_uuids
        except HTTPError as e:
            logger.exception("Basic request failed: %s", e)

        return []

    def get_name(self, document_url: str, xpath: str) -> str:
        """Get the name of a document.

        Args:
            document_url: URL of the document page to fetch and parse.
            xpath: The XPath expression to locate the document name in the DOM.

        Returns:
            str: The name of the document, or an empty string if not found.
        """
        try:
            dom = etree.HTML(str(self.get_document_source(document_url)))
            return dom.xpath(xpath)[0].text.strip()
        except (HTTPError, IndexError) as e:
            logger.exception("Failed to retrieve document name: %s", e)

        return ""

    def _extract_uuids_from_divs_with_id_pattern(self, soup, search_pattern: dict | str) -> List[str]:
        """Extract UUIDs from div elements with id matching a pattern.

        Args:
            soup: BeautifulSoup object containing the page markup.
            search_pattern: Pattern to search for in div ids.

        Returns:
            List[str]: Page UUIDs discovered in matching elements.
        """
        page_uuids = []
        if not soup:
            return page_uuids

        all_matching_divs = soup.find_all(**search_pattern)

        for div in all_matching_divs:
            page_uuids = self._get_uuid_from_match(page_uuids, div["id"], search_pattern["id"])

        return page_uuids

    @staticmethod
    def _get_uuid_from_match(page_uuids: List[str], div_id: str, pattern: Any) -> List[str]:
        """Check if the div id matches the pattern 'page-id-uuid:{uuid}' and extract the UUID.

        Args:
            page_uuids: List of page UUIDs to append to.
            div_id: The div id string to check.
            pattern: The pattern to match against.

        Returns:
            List[str]: Updated list of page UUIDs.
        """
        uuid_match = re.search(pattern, div_id)

        if uuid_match:
            page_uuid = uuid_match.group(1)
            if page_uuid not in page_uuids:  # Avoid duplicates (can't use set because order matters)
                page_uuids.append(page_uuid)
                print(f"Found page UUID: {page_uuid}")
        return page_uuids
