"""Tests for the Selenium DOM page-discovery helper."""

import sys
import types

from src.helper_services.dom_selenium_getter import DomSeleniumGetterMethod
from test.helper_services.fixtures import PAGE_HTML, PAGE_SEARCH_PATTERN


def test_get_pages_uses_selenium_html_and_passes_expected_attributes(monkeypatch):
    getter = DomSeleniumGetterMethod()
    captured = {}

    def fake_request(document_url):
        captured["document_url"] = document_url
        return PAGE_HTML

    def fake_extract(self, soup, search_parameter):
        captured["soup"] = soup
        captured["search_parameter"] = search_parameter
        return [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        ]

    monkeypatch.setattr(getter, "_try_selenium_dom_request", fake_request)
    monkeypatch.setattr(DomSeleniumGetterMethod, "_extract_uuids_from_divs_with_id_pattern", fake_extract)

    result = getter.get_pages("https://example.com/document", PAGE_SEARCH_PATTERN)

    assert result == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    assert captured["document_url"] == "https://example.com/document"
    assert captured["search_parameter"] == PAGE_SEARCH_PATTERN
    assert captured["soup"] is not None


def test_get_pages_returns_empty_list_when_no_matching_ids_are_present(monkeypatch):
    getter = DomSeleniumGetterMethod()
    monkeypatch.setattr(getter, "_try_selenium_dom_request", lambda document_url: "<html><body><div id='other'></div></body></html>")

    assert getter.get_pages("https://example.com/document", PAGE_SEARCH_PATTERN) == []


def test_setup_selenium_options_configures_headless_chrome(monkeypatch):
    class FakeOptions:
        def __init__(self):
            self.args = []

        def add_argument(self, argument):
            self.args.append(argument)

    selenium_module = types.ModuleType("selenium")
    webdriver_module = types.ModuleType("selenium.webdriver")
    chrome_module = types.ModuleType("selenium.webdriver.chrome")
    chrome_options_module = types.ModuleType("selenium.webdriver.chrome.options")
    chrome_options_module.Options = FakeOptions
    chrome_module.options = chrome_options_module
    webdriver_module.chrome = chrome_module
    selenium_module.webdriver = webdriver_module

    monkeypatch.setitem(sys.modules, "selenium", selenium_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver", webdriver_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.chrome", chrome_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.chrome.options", chrome_options_module)

    options = DomSeleniumGetterMethod._setup_selenium_options()

    assert isinstance(options, FakeOptions)
    assert "--headless" in options.args
    assert "--no-sandbox" in options.args
    assert "--disable-dev-shm-usage" in options.args


def test_try_selenium_dom_request_creates_driver_waits_and_quits(monkeypatch):
    class FakeDriver:
        def __init__(self):
            self.page_source = "<html><body>Rendered</body></html>"
            self.calls = []

        def set_page_load_timeout(self, timeout):
            self.calls.append(("set_page_load_timeout", timeout))

        def get(self, url):
            self.calls.append(("get", url))

        def quit(self):
            self.calls.append(("quit",))

    class FakeOptions:
        def __init__(self):
            self.args = []

        def add_argument(self, argument):
            self.args.append(argument)

    class FakeWebDriverWait:
        def __init__(self, driver, timeout):
            self.driver = driver
            self.timeout = timeout
            self.called = []

        def until(self, condition):
            self.called.append(condition)
            return True

    class FakeEC:
        @staticmethod
        def presence_of_element_located(locator):
            return ("presence", locator)

    class FakeBy:
        CLASS_NAME = "class name"

    fake_driver = FakeDriver()

    def fake_chrome(options=None):
        assert options is not None
        fake_driver.options = options
        return fake_driver

    selenium_module = types.ModuleType("selenium")
    webdriver_module = types.ModuleType("selenium.webdriver")
    chrome_module = types.ModuleType("selenium.webdriver.chrome")
    chrome_options_module = types.ModuleType("selenium.webdriver.chrome.options")
    support_module = types.ModuleType("selenium.webdriver.support")
    ui_module = types.ModuleType("selenium.webdriver.support.ui")
    by_module = types.ModuleType("selenium.webdriver.common.by")
    expected_module = types.ModuleType("selenium.webdriver.support.expected_conditions")

    chrome_options_module.Options = FakeOptions
    chrome_module.options = chrome_options_module
    webdriver_module.chrome = chrome_module
    webdriver_module.common = types.SimpleNamespace(by=by_module)
    support_module.ui = ui_module
    support_module.expected_conditions = expected_module
    ui_module.WebDriverWait = FakeWebDriverWait
    by_module.By = FakeBy
    expected_module.presence_of_element_located = FakeEC.presence_of_element_located
    selenium_module.webdriver = webdriver_module
    webdriver_module.Chrome = fake_chrome

    monkeypatch.setitem(sys.modules, "selenium", selenium_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver", webdriver_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.chrome", chrome_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.chrome.options", chrome_options_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.support", support_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.support.ui", ui_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.support.expected_conditions", expected_module)
    monkeypatch.setitem(sys.modules, "selenium.webdriver.common", types.ModuleType("selenium.webdriver.common"))
    monkeypatch.setitem(sys.modules, "selenium.webdriver.common.by", by_module)

    result = DomSeleniumGetterMethod()._try_selenium_dom_request("https://example.com/document")

    assert result == "<html><body>Rendered</body></html>"
    assert ("set_page_load_timeout", 30) in fake_driver.calls
    assert ("get", "https://example.com/document") in fake_driver.calls
    assert ("quit",) in fake_driver.calls
