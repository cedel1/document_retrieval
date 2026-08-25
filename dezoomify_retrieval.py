#!/usr/bin/env python3
"""
Dezoomify Retrieval Script

This script takes a digital library webpage URL, extracts the document and page UUIDs,
and retrieves all pages of the document using the dezoomify-rs command-line tool.
"""

import argparse
import os
import random
import re
import subprocess
import time
from typing import List, Optional, Tuple
import urllib.parse

from bs4 import BeautifulSoup
import requests
import urllib3

# Try to import selenium, but make it optional
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available, JavaScript rendering will be limited")

# Suppress SSL warnings for problematic certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def extract_uuids_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract both the document UUID and page UUID from the URL.

    Args:
        url: The source webpage URL

    Returns:
        Tuple of (document_uuid, page_uuid) or (None, None) if not found
    """
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # Extract document UUID from the path
    path_match = re.search(r"uuid:([a-f0-9-]+)", parsed.path)
    document_uuid = path_match.group(1) if path_match else None

    # Extract page UUID from the page parameter
    page_uuid = None
    if "page" in params:
        page_match = re.search(r"uuid:([a-f0-9-]+)", params["page"][0])
        page_uuid = page_match.group(1) if page_match else None

    return document_uuid, page_uuid


def _get_page_uuids_from_children_data(children: dict, page_uuids: List[str]) -> List[str]:
    """
    Get and possibly append page UUID from data dictionary.

    Args:
        children: The children dictionary
        page_uuids: The list of page UUIDs to append to

    Returns:
        The updated list of page UUIDs
    """
    for child in children:
        if "pid" in child:
            pid = children["pid"]
            uuid_match = re.search(r"uuid:([a-f0-9-]+)", pid)
            if uuid_match:
                page_uuids.append(uuid_match.group(1))
            elif re.match(r"^[a-f0-9-]+$", pid):
                page_uuids.append(pid)

    return page_uuids


def get_document_pages(document_uuid: str) -> List[str]:
    """
    Get list of all page UUIDs for a document using the Kramerius API or DOM parsing.

    Args:
        document_uuid: The document UUID

    Returns:
        List of page UUIDs
    """
    # Try different Kramerius API endpoints
    api_endpoints = [
        f"https://www.digitalniknihovna.cz/search/api/v5.0/item/uuid:{document_uuid}/children",
        f"https://www.digitalnistudovna.army.cz/search/api/v5.0/item/uuid:{document_uuid}/children",
        f"https://www.digitalniknihovna.cz/search/api/client/v7.0/items/uuid:{document_uuid}/info/structure",
    ]

    for api_url in api_endpoints:
        try:
            print(f"Trying API endpoint: {api_url}")
            # Fetch the document's children via API
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()

            data = response.json()
            page_uuids = []

            # Handle different response formats
            if isinstance(data, list):
                # Direct list of children
                page_uuids = _get_page_uuids_from_children_data(data, page_uuids)
            elif isinstance(data, dict):
                # Nested structure
                if "children" in data:
                    children = data["children"]
                    if isinstance(children, dict) and "own" in children:
                        children = children["own"]
                    page_uuids = _get_page_uuids_from_children_data(children, page_uuids)

            if page_uuids:
                print(f"Found {len(page_uuids)} pages in document via API")
                return page_uuids

        except requests.exceptions.RequestException as e:
            print(f"Error with endpoint {api_url}: {e}")
            continue
        except Exception as e:
            print(f"Error parsing response from {api_url}: {e}")
            continue

    print("All API endpoints failed, trying DOM parsing method...")
    # Fallback: Try to extract pages from DOM
    return get_document_pages_from_dom(document_uuid)


def _extract_uuids_from_divs_with_id_pattern(soup, pattern: str) -> List[str]:
    """
    Extract UUIDs from div elements with id matching a pattern.

    Args:
        soup: BeautifulSoup object
        pattern: Pattern to search for in div ids

    Returns:
        List of page UUIDs
    """
    page_uuids = []
    all_divs = soup.find_all("div", id=True)

    for div in all_divs:
        div_id = div["id"]
        if pattern in div_id:
            uuid_match = re.search(r"page-id-uuid:([a-f0-9-]+)", div_id)
            if uuid_match:
                page_uuid = uuid_match.group(1)
                if page_uuid not in page_uuids:
                    page_uuids.append(page_uuid)

    return page_uuids


def _extract_uuids_from_navigation_items(soup) -> List[str]:
    """
    Extract UUIDs from app-navigation-item elements.

    Args:
        soup: BeautifulSoup object

    Returns:
        List of page UUIDs
    """
    page_uuids = []

    # Find all elements with class 'app-navigation-item'
    navigation_items = soup.find_all(class_="app-navigation-item")
    print(f"Found {len(navigation_items)} elements with class 'app-navigation-item'")

    for item in navigation_items:
        # Look for div elements with id in format 'page-id-uuid:{uuid}'
        divs = item.find_all("div", id=True)
        for div in divs:
            div_id = div["id"]
            # Check if the id matches the pattern 'page-id-uuid:{uuid}'
            uuid_match = re.search(r"page-id-uuid:([a-f0-9-]+)", div_id)
            if uuid_match:
                page_uuid = uuid_match.group(1)
                if page_uuid not in page_uuids:  # Avoid duplicates
                    page_uuids.append(page_uuid)
                    print(f"Found page UUID: {page_uuid}")

    return page_uuids


def _try_basic_dom_request(document_url: str) -> List[str]:
    """
    Try to extract page UUIDs using a basic HTTP request.

    Args:
        document_url: URL of the document page

    Returns:
        List of page UUIDs
    """
    try:
        response = requests.get(document_url, timeout=30, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        page_uuids = _extract_uuids_from_divs_with_id_pattern(soup, "page-id-uuid:")

        if page_uuids:
            print(f"Found {len(page_uuids)} pages via basic request (static content)")
            return page_uuids
    except Exception as e:
        print(f"Basic request failed: {e}")

    return []


def _setup_selenium_options() -> Options:
    """
    Setup Chrome options for headless browsing.

    Returns:
        Chrome Options object
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    return chrome_options


def _try_selenium_dom_request(document_url: str) -> List[str]:
    """
    Try to extract page UUIDs using Selenium for JavaScript rendering.

    Args:
        document_url: URL of the document page

    Returns:
        List of page UUIDs
    """
    if not SELENIUM_AVAILABLE:
        print("Selenium not available, cannot render JavaScript")
        return []

    print("Trying with Selenium for JavaScript-rendered content...")

    chrome_options = _setup_selenium_options()

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        try:
            print(f"Loading page with Selenium: {document_url}")
            driver.get(document_url)

            # Wait for the page to load and navigation items to appear
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "app-navigation-item")))
            except Exception:
                print("Timed out waiting for app-navigation-item, proceeding anyway")

            # Get the page HTML after JavaScript execution
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, "html.parser")

            # Extract UUIDs from navigation items
            page_uuids = _extract_uuids_from_navigation_items(soup)

            # Also try to find any div with id containing 'page-id-uuid:' in the entire page
            additional_uuids = _extract_uuids_from_divs_with_id_pattern(soup, "page-id-uuid:")
            for uuid in additional_uuids:
                if uuid not in page_uuids:
                    page_uuids.append(uuid)
                    print(f"Found page UUID from general search: {uuid}")

            print(f"Found {len(page_uuids)} pages in document via DOM parsing with Selenium")
            return page_uuids

        finally:
            driver.quit()

    except Exception as e:
        print(f"Error with Selenium DOM parsing: {e}")
        print("Selenium may not be installed or Chrome driver not available")
        return []


def get_document_pages_from_dom(document_uuid: str) -> List[str]:
    """
    Extract page UUIDs from the DOM using multiple methods.
    Tries basic request first, then Selenium for JavaScript-rendered content.
    Finds app-navigation-item elements and extracts UUIDs from div elements
    with id format 'page-id-uuid:{uuid}'.

    Args:
        document_uuid: The document UUID

    Returns:
        List of page UUIDs
    """
    document_url = f"https://www.digitalniknihovna.cz/dsmo/view/uuid:{document_uuid}"

    # First try basic request to see if page has static content
    page_uuids = _try_basic_dom_request(document_url)
    if page_uuids:
        return page_uuids

    # If basic request didn't find pages, try with Selenium
    page_uuids = _try_selenium_dom_request(document_url)
    if page_uuids:
        return page_uuids

    # If all methods failed
    print("All DOM parsing methods failed")
    print("You may need to manually specify page UUIDs using --pages parameter")
    return []


def check_dezoomify_rs(dezoomify_path: str = "dezoomify-rs") -> bool:
    """
    Check if dezoomify-rs is available at the specified path.

    Args:
        dezoomify_path: Path to dezoomify-rs executable

    Returns:
        True if dezoomify-rs is available, False otherwise
    """
    try:
        result = subprocess.run([dezoomify_path, "--help"], capture_output=True, text=True, timeout=5, check=True)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def random_delay(min_seconds: float = 1.0, max_seconds: float = 20.0):
    """
    Sleep for a random amount of time between min and max seconds.

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting {delay:.2f} seconds before next download...")
    time.sleep(delay)


def retrieve_dezoomified_image(
    uuid: str, output_base: str = "output", dezoomify_path: str = "dezoomify-rs", dezoomify_args: List[str] = None
) -> bool:
    """
    Retrieve the dezoomified image using dezoomify-rs.

    Args:
        uuid: The image UUID
        output_base: Base path for the output image (without extension)
        dezoomify_path: Path to dezoomify-rs executable

    Returns:
        Boolean indication success or failure
    """
    # Check if dezoomify-rs is available
    if not check_dezoomify_rs(dezoomify_path):
        print(f"Error: dezoomify-rs not found at '{dezoomify_path}'.")
        print("Please install it using: brew install dezoomify-rs")
        print("Or specify the correct path using --dezoomify-path")
        print("Or download from: https://github.com/lovasoa/dezoomify-rs/releases")
        return False

    # Handle default value for dezoomify_args
    if dezoomify_args is None:
        dezoomify_args = []

    # Construct the ImageProperties.xml URL
    image_properties_url = f"https://digitalnistudovna.army.cz/search/zoomify/uuid:{uuid}/ImageProperties.xml"

    print(f"Using dezoomify-rs to download image from: {image_properties_url}")

    try:
        # Run dezoomify-rs without specifying output format
        # dezoomify-rs will determine the appropriate format
        print(f"Dezoomify-args: {dezoomify_args}")

        result = subprocess.run(
            [dezoomify_path, *dezoomify_args, image_properties_url, output_base],
            capture_output=True,
            text=True,
            check=True,
            timeout=5 * 60,  # 5 minute timeout for large images
        )

        if result.returncode == 0:
            # Determine what file was actually created
            # dezoomify-rs might add .jpg, .png or other image extension

            print(f"Image with output base {output_base} downloaded successfully.")
            return True

        print(f"Error running dezoomify-rs: {result.stderr}")
        return False

    except subprocess.TimeoutExpired as e:
        print("Error: dezoomify-rs timed out")
        print(e)
        return False
    except subprocess.SubprocessError as e:
        print(f"Error running dezoomify-rs: {e}")
        print(e)
        return False


def download_specific_pages(
    page_uuids: List[str],
    output_dir: str = "output",
    dezoomify_path: str = "dezoomify-rs",
    dezoomify_args: List[str] = None,
) -> bool:
    """
    Download specific pages given their UUIDs.

    Args:
        page_uuids: List of page UUIDs to download
        output_dir: Directory to save the output images
        dezoomify_path: Path to dezoomify-rs executable

    Returns:
        True if all downloads successful, False otherwise
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Handle default value for dezoomify_args
    if dezoomify_args is None:
        dezoomify_args = []

    print(f"Starting download of {len(page_uuids)} specific pages...")

    # Download each page
    successful_downloads = 0
    failed_downloads = 0

    for i, page_uuid in enumerate(page_uuids, 1):
        output_base = os.path.join(output_dir, f"page_{i:03d}_{page_uuid[:8]}")

        print(f"Downloading page {i}/{len(page_uuids)}: {page_uuid}")

        # Don't add delay before the first download
        if i > 1:
            random_delay()
        actual_output = retrieve_dezoomified_image(page_uuid, output_base, dezoomify_path, dezoomify_args)

        if actual_output:
            successful_downloads += 1
        else:
            failed_downloads += 1

    print(f"\nDownload complete: {successful_downloads} successful, {failed_downloads} failed")
    return failed_downloads == 0


def retrieve_document(
    document_uuid: str,
    output_dir: str = "output",
    dezoomify_path: str = "dezoomify-rs",
    dezoomify_args: List[str] = None,
) -> bool:
    """
    Retrieve all pages of a document.

    Args:
        document_uuid: The document UUID
        output_dir: Directory to save the output images
        dezoomify_path: Path to dezoomify-rs executable

    Returns:
        True if successful, False otherwise
    """
    # Get list of all pages
    page_uuids = get_document_pages(document_uuid)
    if not page_uuids:
        print("No pages found in document")
        return False

    # Use the common download function
    return download_specific_pages(page_uuids, output_dir, dezoomify_path, dezoomify_args)


def main():
    """Main function to process a URL and retrieve the dezoomified image."""
    parser = argparse.ArgumentParser(description="Retrieve dezoomified images from digital library documents")
    parser.add_argument("url", help="URL of the document page (required)")
    parser.add_argument("--pages", nargs="+", help="List of page UUIDs to download (overrides automatic discovery)")
    parser.add_argument("--output", default="output", help="Output directory for downloaded images")
    parser.add_argument(
        "--dezoomify-path", default="dezoomify-rs", help="Path to dezoomify-rs executable (default: dezoomify-rs)"
    )
    parser.add_argument(
        "--dezoomify-args", nargs="?", action="append", help="Additional arguments to pass to dezoomify-rs"
    )

    args = parser.parse_args()

    # URL is now required
    source_url = args.url
    dezoomify_path = args.dezoomify_path
    dezoomify_args = args.dezoomify_args if args.dezoomify_args else []

    # Extract both UUIDs
    document_uuid, page_uuid = extract_uuids_from_url(source_url)
    if not document_uuid:
        print("Could not extract document UUID from URL")
        return

    print(f"Extracted document UUID: {document_uuid}")
    if page_uuid:
        print(f"Extracted page UUID: {page_uuid}")

    print(f"Using dezoomify-rs at: {dezoomify_path}")

    # If pages are manually specified, use them
    if args.pages:
        print(f"Using manually specified {len(args.pages)} pages")
        page_uuids = args.pages
        print(f"dezoomify-args in main {dezoomify_args}")
        success = download_specific_pages(page_uuids, args.output, dezoomify_path, dezoomify_args)
    else:
        # Try automatic discovery
        success = retrieve_document(document_uuid, args.output, dezoomify_path, dezoomify_args)

    if success:
        print("Document retrieval completed successfully")
    else:
        print("Document retrieval completed with some failures")


if __name__ == "__main__":
    main()
