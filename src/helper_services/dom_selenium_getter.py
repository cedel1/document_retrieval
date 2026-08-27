"""DOM-based page discovery helpers for library HTML pages."""

import logging

from bs4 import BeautifulSoup
from requests import HTTPError

from src.helper_services.simple_dom_getter import SimpleDomGetterMethod

logger = logging.getLogger(__name__)


class DomSeleniumGetterMethod(SimpleDomGetterMethod):
    """Extract page identifiers from HTML markup using a simple DOM scan."""

    description: str = "Selenium DOM getter"

    def get_pages(self, document_url: str, search_parameter: str | dict) -> list[str]:
        """Get the pages of a document.

        Args:
            search_parameter: The parameter to search for in the DOM.
            document_url: URL of the document page to fetch and parse.

        Returns:
            list[str]: Page UUIDs discovered in the DOM, or an empty list if none are found.
        """
        try:
            response = self._try_selenium_dom_request(document_url)
            soup = BeautifulSoup(response, "html.parser")

            page_uuids = self._extract_uuids_from_divs_with_id_pattern(soup, search_parameter)

            if page_uuids:
                logger.info("Found %d pages via basic request (static content)", len(page_uuids))
                return page_uuids
        except HTTPError as e:
            logger.debug("Basic request failed: %s", e)

        return []

    @staticmethod
    def _setup_selenium_options():
        """Build the Chrome options used for JavaScript-rendered page discovery.

        Args:
            None: This helper does not accept positional arguments.

        Returns:
            Options: Selenium Chrome options configured for the automation flow.
        """
        try:
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:  # pragma: no cover - only when selenium missing
            raise RuntimeError("Selenium is required for DOM rendering fallback") from exc

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        return chrome_options

    def _try_selenium_dom_request(self, document_url: str) -> str:
        """Use Selenium to render JavaScript and discover page UUIDs from the live DOM.

        Args:
            document_url: URL of the page to render and inspect.

        Returns:
            str: The HTML content of the rendered page, or an empty string.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
        except ImportError:
            logger.debug("Selenium not available, cannot render JavaScript")
            return ""

        logger.debug("Trying with Selenium for JavaScript-rendered content...")
        chrome_options = self._setup_selenium_options()

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            try:
                logger.debug("Loading page with Selenium: %s", document_url)
                driver.get(document_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "app-navigation-item"))
                    )
                except Exception:
                    logger.debug("Timed out waiting for app-navigation-item, proceeding anyway")
                return driver.page_source
            finally:
                driver.quit()
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Error with Selenium DOM parsing: %s", exc)
            logger.debug("Selenium may not be installed or Chrome driver not available")
            return ""
