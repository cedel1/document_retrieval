"""Tests for the Selenium DOM page-discovery helper."""

import pytest
from src.helper_services.dom_selenium_getter import DomSeleniumGetterMethod
from test.helper_services.fixtures import (
    document_url,
    extracted_uuids_stub,
    fake_selenium,
    page_html,
    page_search_pattern,
    selenium_request_stub,
    selenium_unavailable,
)


@pytest.fixture
def dom_selenium_getter():
    """Fixture providing a DomSeleniumGetterMethod instance."""
    return DomSeleniumGetterMethod({})


def test_get_pages_should_use_selenium_html_and_pass_expected_attributes(
    dom_selenium_getter, selenium_request_stub, extracted_uuids_stub, document_url, page_html, page_search_pattern
):
    selenium_request_stub.result = page_html
    extracted_uuids_stub.result = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]

    result = dom_selenium_getter.get_pages(document_url, page_search_pattern)

    assert result == extracted_uuids_stub.result
    assert selenium_request_stub.args == (document_url,)
    soup, search_parameter = extracted_uuids_stub.args
    assert search_parameter == page_search_pattern
    assert soup is not None


def test_get_pages_should_return_empty_list_when_no_matching_ids(
    dom_selenium_getter, selenium_request_stub, document_url, page_search_pattern
):
    selenium_request_stub.result = "<html><body><div id='other'></div></body></html>"

    assert dom_selenium_getter.get_pages(document_url, page_search_pattern) == []


def test_try_selenium_dom_request_should_return_empty_string_on_import_failure(
    dom_selenium_getter, selenium_unavailable, document_url
):
    assert dom_selenium_getter._try_selenium_dom_request(document_url) == ""


def test_try_selenium_dom_request_should_return_empty_string_on_driver_failure(
    dom_selenium_getter, fake_selenium, document_url
):
    fake_selenium.chrome_error = RuntimeError("driver failed")

    assert dom_selenium_getter._try_selenium_dom_request(document_url) == ""


def test_setup_selenium_options_should_configure_headless_chrome(fake_selenium):
    options = DomSeleniumGetterMethod._setup_selenium_options()

    assert "--headless" in options.args
    assert "--no-sandbox" in options.args
    assert "--disable-dev-shm-usage" in options.args


def test_try_selenium_dom_request_should_create_driver_wait_and_quit(dom_selenium_getter, fake_selenium, document_url):
    result = dom_selenium_getter._try_selenium_dom_request(document_url)

    assert result == "<html><body>Rendered</body></html>"
    assert ("set_page_load_timeout", 30) in fake_selenium.driver_calls
    assert ("get", document_url) in fake_selenium.driver_calls
    assert ("quit",) in fake_selenium.driver_calls


def test_try_selenium_dom_request_should_handle_wait_timeout_and_return_page_source(
    dom_selenium_getter, fake_selenium, document_url
):
    """If WebDriverWait.until raises, method should proceed and return page source."""
    fake_selenium.wait_error = RuntimeError("wait timed out")

    result = dom_selenium_getter._try_selenium_dom_request(document_url)

    assert result == "<html><body>Rendered</body></html>"


def test_try_selenium_dom_request_should_return_empty_string_when_driver_get_raises(
    dom_selenium_getter, fake_selenium, document_url
):
    """If driver.get raises an exception, the method should catch and return empty string."""
    fake_selenium.get_error = RuntimeError("failed to load")

    assert dom_selenium_getter._try_selenium_dom_request(document_url) == ""

    assert ("quit",) in fake_selenium.driver_calls


def test_setup_selenium_options_should_return_options_or_raise_runtime_error():
    """If selenium is available, _setup_selenium_options should return an options object
    with add_argument method. If selenium is missing, it should raise RuntimeError.
    """
    try:
        opts = DomSeleniumGetterMethod._setup_selenium_options()
        # Options should support add_argument
        assert hasattr(opts, "add_argument")
    except RuntimeError:
        pytest.skip("Selenium not available in this environment")


@pytest.mark.parametrize("allow_insecure", [True, False])
def test_setup_selenium_options_should_ignore_certificate_errors_only_when_insecure(fake_selenium, allow_insecure):
    options = DomSeleniumGetterMethod._setup_selenium_options(allow_insecure)

    assert ("--ignore-certificate-errors" in options.args) is allow_insecure
    assert ("--allow-running-insecure-content" in options.args) is allow_insecure
