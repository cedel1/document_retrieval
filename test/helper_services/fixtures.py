"""Shared fixtures for helper service tests."""

from __future__ import annotations

import re
import sys
import types
from unittest.mock import patch

import pytest

from src.helper_services.dom_selenium_getter import DomSeleniumGetterMethod
from src.helper_services.simple_dom_getter import SimpleDomGetterMethod


@pytest.fixture
def page_html():
    """Sample HTML content with page UUIDs for testing."""
    return """
<html>
  <body>
    <div id="page-id-uuid:11111111-1111-1111-1111-111111111111"></div>
    <div id="page-id-uuid:22222222-2222-2222-2222-222222222222"></div>
    <div id="non-page-id"></div>
  </body>
</html>
"""


@pytest.fixture
def page_search_pattern():
    """Search pattern for finding page UUIDs in HTML."""
    return {"name": "div", "id": re.compile(r"page-id-(uuid:[a-f0-9-]+)")}


@pytest.fixture
def api_payload():
    """Sample API payload for testing REST API getter."""
    return {
        "response": {
            "docs": [
                {"PID": "uuid:11111111-1111-1111-1111-111111111111", "rels_ext_index": [0]},
                {"PID": "uuid:22222222-2222-2222-2222-222222222222", "rels_ext_index": [1]},
            ]
        }
    }


@pytest.fixture
def document_url():
    """URL of the sample document used by the getter tests."""
    return "https://example.com/document"


class MethodStub:
    """Replacement for a getter method (not bound to the instance) that records calls and returns or raises a configured outcome."""

    def __init__(self):
        self.calls = []
        self.result = None
        self.error = None

    def __call__(self, *args):
        self.calls.append(args)
        if self.error is not None:
            raise self.error
        return self.result

    @property
    def args(self):
        """Return the arguments of the last call."""
        return self.calls[-1]


@pytest.fixture
def document_source_stub():
    """Fixture replacing ``get_document_source``; set ``.result`` or ``.error`` to change the outcome."""
    stub = MethodStub()
    with patch.object(SimpleDomGetterMethod, "get_document_source", stub):
        yield stub


@pytest.fixture
def extracted_uuids_stub():
    """Fixture replacing ``_extract_uuids_from_divs_with_id_pattern``; set ``.result`` to the UUIDs to return."""
    stub = MethodStub()
    with patch.object(SimpleDomGetterMethod, "_extract_uuids_from_divs_with_id_pattern", stub):
        yield stub


@pytest.fixture
def selenium_request_stub():
    """Fixture replacing ``_try_selenium_dom_request``; set ``.result`` to the HTML to return."""
    stub = MethodStub()
    with patch.object(DomSeleniumGetterMethod, "_try_selenium_dom_request", stub):
        yield stub


class FakeChromeOptions:
    """Chrome options stand-in recording the added arguments."""

    def __init__(self):
        self.args = []

    def add_argument(self, argument):
        """Record an argument."""
        self.args.append(argument)


class FakeSelenium:
    """Configurable stand-in for the selenium package.

    Set ``page_source``, ``chrome_error``, ``get_error`` or ``wait_error`` before running the code under test;
    ``driver_calls`` and ``options`` record what the code did.
    """

    def __init__(self):
        self.page_source = "<html><body>Rendered</body></html>"
        self.chrome_error = None
        self.get_error = None
        self.wait_error = None
        self.driver_calls = []
        self.options = None

    def create_driver(self, options=None):
        """Replacement for ``webdriver.Chrome``."""
        self.options = options
        if self.chrome_error is not None:
            raise self.chrome_error
        return _FakeDriver(self)

    def wait_until(self, _condition):
        """Replacement for ``WebDriverWait.until``."""
        if self.wait_error is not None:
            raise self.wait_error
        return True

    def build_modules(self):
        """Build the module tree that replaces ``selenium`` in ``sys.modules``."""
        names = [
            "selenium",
            "selenium.webdriver",
            "selenium.webdriver.chrome",
            "selenium.webdriver.chrome.options",
            "selenium.webdriver.common",
            "selenium.webdriver.common.by",
            "selenium.webdriver.support",
            "selenium.webdriver.support.ui",
            "selenium.webdriver.support.expected_conditions",
        ]
        modules = {name: types.ModuleType(name) for name in names}
        fake = self

        class FakeWebDriverWait:  # pylint: disable=too-few-public-methods
            """WebDriverWait stand-in delegating to the fake."""

            def __init__(self, _driver, *_args):
                pass

            def until(self, condition):
                """Delegate to the fake."""
                return fake.wait_until(condition)

        modules["selenium"].webdriver = modules["selenium.webdriver"]
        modules["selenium.webdriver"].Chrome = self.create_driver
        modules["selenium.webdriver"].chrome = modules["selenium.webdriver.chrome"]
        modules["selenium.webdriver"].common = modules["selenium.webdriver.common"]
        modules["selenium.webdriver"].support = modules["selenium.webdriver.support"]
        modules["selenium.webdriver.chrome"].options = modules["selenium.webdriver.chrome.options"]
        modules["selenium.webdriver.chrome.options"].Options = FakeChromeOptions
        modules["selenium.webdriver.common"].by = modules["selenium.webdriver.common.by"]
        modules["selenium.webdriver.common.by"].By = types.SimpleNamespace(CLASS_NAME="class name")
        modules["selenium.webdriver.support"].ui = modules["selenium.webdriver.support.ui"]
        modules["selenium.webdriver.support"].expected_conditions = modules[
            "selenium.webdriver.support.expected_conditions"
        ]
        modules["selenium.webdriver.support.ui"].WebDriverWait = FakeWebDriverWait
        modules["selenium.webdriver.support.expected_conditions"].presence_of_element_located = lambda locator: (
            "presence",
            locator,
        )
        return modules


class _FakeDriver:
    """Driver stand-in recording its calls on the owning ``FakeSelenium``."""

    def __init__(self, fake):
        self._fake = fake
        self.page_source = fake.page_source

    def set_page_load_timeout(self, timeout):
        """Record the timeout."""
        self._fake.driver_calls.append(("set_page_load_timeout", timeout))

    def get(self, url):
        """Record the URL or raise the configured error."""
        self._fake.driver_calls.append(("get", url))
        if self._fake.get_error is not None:
            raise self._fake.get_error

    def quit(self):
        """Record that the driver was closed."""
        self._fake.driver_calls.append(("quit",))


@pytest.fixture
def fake_selenium():
    """Fixture installing a fake ``selenium`` package into ``sys.modules`` and yielding its configuration."""
    fake = FakeSelenium()
    with patch.dict(sys.modules, fake.build_modules()):
        yield fake


@pytest.fixture
def selenium_unavailable():
    """Fixture making every ``selenium`` import fail with ImportError."""
    names = [
        "selenium",
        "selenium.webdriver",
        "selenium.webdriver.chrome.options",
        "selenium.webdriver.common.by",
        "selenium.webdriver.support",
        "selenium.webdriver.support.ui",
    ]
    with patch.dict(sys.modules, dict.fromkeys(names)):
        yield
