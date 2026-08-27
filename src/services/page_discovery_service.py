"""Service for discovering pages belonging to a document."""

from __future__ import annotations

import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PageDiscoveryService:
    """Encapsulates page-discovery logic for Digital Library documents."""

    @staticmethod
    def _get_page_uuids_from_children_data(children: list, page_uuids: List[str]) -> List[str]:
        """Extract page UUIDs from raw child metadata returned by the API.

        Args:
            children: Raw child metadata entries from the library API.
            page_uuids: Accumulated list of page UUIDs to extend.

        Returns:
            List[str]: The updated list of page UUIDs.
        """
        for child in children:
            if "pid" in child:
                pid = child["pid"]
                uuid_match = re.search(r"uuid:([a-f0-9-]+)", pid)
                if uuid_match:
                    page_uuids.append(uuid_match.group(1))
                elif re.match(r"^[a-f0-9-]+$", pid):
                    page_uuids.append(pid)
        return page_uuids

    @staticmethod
    def get_document_pages(document_uuid: str) -> List[str]:
        """Discover all page UUIDs for a document from the API or fallback DOM parsing.

        Args:
            document_uuid: UUID of the document whose pages should be discovered.

        Returns:
            List[str]: Page UUIDs found for the document.
        """
        api_endpoints = [
            f"https://www.digitalniknihovna.cz/search/api/v5.0/item/uuid:{document_uuid}/children",
            f"https://www.digitalnistudovna.army.cz/search/api/v5.0/item/uuid:{document_uuid}/children",
            f"https://www.digitalniknihovna.cz/search/api/client/v7.0/items/uuid:{document_uuid}/info/structure",
        ]

        for api_url in api_endpoints:
            try:
                logger.debug("Trying API endpoint: %s", api_url)
                response = requests.get(api_url, timeout=30, verify=False)
                response.raise_for_status()
                data = response.json()
                page_uuids: List[str] = []

                if isinstance(data, list):
                    page_uuids = PageDiscoveryService._get_page_uuids_from_children_data(data, page_uuids)
                elif isinstance(data, dict) and "children" in data:
                    children = data["children"]
                    if isinstance(children, dict) and "own" in children:
                        children = children["own"]
                    page_uuids = PageDiscoveryService._get_page_uuids_from_children_data(children, page_uuids)

                if page_uuids:
                    logger.info("Found %d pages in document via API", len(page_uuids))
                    return page_uuids
            except requests.exceptions.RequestException as exc:
                logger.warning("Error with endpoint %s: %s", api_url, exc)
                continue
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Error parsing response from %s: %s", api_url, exc)
                continue

        logger.debug("All API endpoints failed, trying DOM parsing method...")
        return PageDiscoveryService.get_document_pages_from_dom(document_uuid)

    # @staticmethod
    # def _get_uuid_match(page_uuids, div_id) -> List[str]:
    #     """Extract a page UUID from a DOM element ID if it contains the expected pattern.
    #
    #     Args:
    #         page_uuids: Existing UUID list to extend.
    #         div_id: DOM element id to inspect.
    #
    #     Returns:
    #         List[str]: Updated list of page UUIDs.
    #     """
    #     uuid_match = re.search(r"page-id-uuid:([a-f0-9-]+)", div_id)
    #     if uuid_match:
    #         page_uuid = uuid_match.group(1)
    #         if page_uuid not in page_uuids:
    #             page_uuids.append(page_uuid)
    #             logger.debug("Found page UUID: %s", page_uuid)
    #     return page_uuids

    # @staticmethod
    # def _extract_uuids_from_divs_with_id_pattern(soup, pattern: str) -> List[str]:
    #     """Collect UUIDs from all div elements whose IDs match a given pattern.
    #
    #     Args:
    #         soup: BeautifulSoup object containing the rendered markup.
    #         pattern: Pattern used to match page ids.
    #
    #     Returns:
    #         List[str]: UUIDs extracted from matching div ids.
    #     """
    #     page_uuids: List[str] = []
    #     all_divs = soup.find_all("div", id=True)
    #     for div in all_divs:
    #         div_id = div["id"]
    #         if pattern in div_id:
    #             page_uuids = PageDiscoveryService._get_uuid_match(page_uuids, div_id)
    #     return page_uuids

    # @staticmethod
    # def _extract_uuids_from_navigation_items(soup) -> List[str]:
    #     """Collect page UUIDs from app-navigation-item elements in the rendered DOM.
    #
    #     Args:
    #         soup: BeautifulSoup object containing the page markup.
    #
    #     Returns:
    #         List[str]: Page UUIDs discovered in navigation item elements.
    #     """
    #     page_uuids: List[str] = []
    #     navigation_items = soup.find_all(class_="app-navigation-item")
    #     logger.debug("Found %d elements with class 'app-navigation-item'", len(navigation_items))
    #     for item in navigation_items:
    #         divs = item.find_all("div", id=True)
    #         for div in divs:
    #             div_id = div["id"]
    #             page_uuids = PageDiscoveryService._get_uuid_match(page_uuids, div_id)
    #     return page_uuids

    # @staticmethod
    # def _try_basic_dom_request(document_url: str) -> List[str]:
    #     """Try a lightweight DOM request to discover pages without Selenium.
    #
    #     Args:
    #         document_url: URL of the document page to inspect.
    #
    #     Returns:
    #         List[str]: Page UUIDs found in the static HTML, or an empty list.
    #     """
    #     try:
    #         response = requests.get(document_url, timeout=30, verify=False)
    #         response.raise_for_status()
    #         soup = BeautifulSoup(response.content, "html.parser")
    #         page_uuids = PageDiscoveryService._extract_uuids_from_divs_with_id_pattern(soup, "page-id-uuid:")
    #         if page_uuids:
    #             logger.info("Found %d pages via basic request (static content)", len(page_uuids))
    #             return page_uuids
    #     except Exception as exc:
    #         logger.debug("Basic request failed: %s", exc)
    #     return []

    # @staticmethod
    # def _setup_selenium_options():
    #     """Build the Chrome options used for JavaScript-rendered page discovery.
    #
    #     Args:
    #         None: This helper does not accept positional arguments.
    #
    #     Returns:
    #         Options: Selenium Chrome options configured for the automation flow.
    #     """
    #     try:
    #         from selenium.webdriver.chrome.options import Options
    #     except ImportError as exc:  # pragma: no cover - only when selenium missing
    #         raise RuntimeError("Selenium is required for DOM rendering fallback") from exc
    #
    #     chrome_options = Options()
    #     chrome_options.add_argument("--headless")
    #     chrome_options.add_argument("--no-sandbox")
    #     chrome_options.add_argument("--disable-dev-shm-usage")
    #     chrome_options.add_argument("--disable-gpu")
    #     chrome_options.add_argument("--ignore-certificate-errors")
    #     chrome_options.add_argument("--allow-running-insecure-content")
    #     return chrome_options

    # @staticmethod
    # def _try_selenium_dom_request(document_url: str) -> List[str]:
    #     """Use Selenium to render JavaScript and discover page UUIDs from the live DOM.
    #
    #     Args:
    #         document_url: URL of the page to render and inspect.
    #
    #     Returns:
    #         List[str]: Page UUIDs discovered in the rendered DOM, or an empty list.
    #     """
    #     try:
    #         from selenium import webdriver
    #         from selenium.webdriver.common.by import By
    #         from selenium.webdriver.support import expected_conditions as EC
    #         from selenium.webdriver.support.ui import WebDriverWait
    #     except ImportError:
    #         logger.debug("Selenium not available, cannot render JavaScript")
    #         return []
    #
    #     logger.debug("Trying with Selenium for JavaScript-rendered content...")
    #     chrome_options = PageDiscoveryService._setup_selenium_options()
    #
    #     try:
    #         driver = webdriver.Chrome(options=chrome_options)
    #         driver.set_page_load_timeout(30)
    #         try:
    #             logger.debug("Loading page with Selenium: %s", document_url)
    #             driver.get(document_url)
    #             try:
    #                 WebDriverWait(driver, 10).until(
    #                     EC.presence_of_element_located((By.CLASS_NAME, "app-navigation-item"))
    #                 )
    #             except Exception:
    #                 logger.debug("Timed out waiting for app-navigation-item, proceeding anyway")
    #             page_html = driver.page_source
    #             soup = BeautifulSoup(page_html, "html.parser")
    #             page_uuids = PageDiscoveryService._extract_uuids_from_navigation_items(soup)
    #             additional_uuids = PageDiscoveryService._extract_uuids_from_divs_with_id_pattern(soup, "page-id-uuid:")
    #             for uuid in additional_uuids:
    #                 if uuid not in page_uuids:
    #                     page_uuids.append(uuid)
    #                     logger.debug("Found page UUID from general search: %s", uuid)
    #             logger.info("Found %d pages in document via DOM parsing with Selenium", len(page_uuids))
    #             return page_uuids
    #         finally:
    #             driver.quit()
    #     except Exception as exc:  # pragma: no cover - environment dependent
    #         logger.warning("Error with Selenium DOM parsing: %s", exc)
    #         logger.debug("Selenium may not be installed or Chrome driver not available")
    #         return []

    @staticmethod
    def get_document_pages_from_dom(document_uuid: str) -> List[str]:
        """Try the static and JavaScript DOM discovery methods in sequence.

        Args:
            document_uuid: UUID of the document to inspect.

        Returns:
            List[str]: Page UUIDs discovered by the DOM fallback methods.
        """
        document_url = f"https://www.digitalniknihovna.cz/dsmo/view/uuid:{document_uuid}"
        page_uuids = PageDiscoveryService._try_basic_dom_request(document_url)
        if page_uuids:
            return page_uuids

        page_uuids = PageDiscoveryService._try_selenium_dom_request(document_url)
        if page_uuids:
            return page_uuids

        logger.warning("All DOM parsing methods failed")
        logger.warning("You may need to manually specify page UUIDs using --pages parameter")
        return []
