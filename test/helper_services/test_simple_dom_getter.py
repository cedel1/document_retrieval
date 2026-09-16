"""Tests for the simple DOM page-discovery helper."""

from requests import HTTPError

import pytest
import responses
from src.helper_services.simple_dom_getter import SimpleDomGetterMethod
from test.helper_services.fixtures import page_html, page_search_pattern


@pytest.fixture
def simple_dom_getter():
    """Fixture providing a SimpleDomGetterMethod instance."""
    return SimpleDomGetterMethod()


@responses.activate
def test_get_pages_calls_requests_with_expected_arguments_and_parses_response(
    monkeypatch, simple_dom_getter, page_html, page_search_pattern
):
    captured = {}

    def fake_extract(self, soup, search_pattern):
        captured["soup"] = soup
        captured["search_pattern"] = search_pattern
        return [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        ]

    responses.add(
        responses.GET,
        "https://example.com/document",
        body=page_html,
        status=200,
        content_type="text/html",
    )
    monkeypatch.setattr(SimpleDomGetterMethod, "_extract_uuids_from_divs_with_id_pattern", fake_extract)

    result = simple_dom_getter.get_pages("https://example.com/document", page_search_pattern)

    assert result == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    assert responses.calls[0].request.url == "https://example.com/document"
    assert captured["search_pattern"] == page_search_pattern
    assert captured["soup"] is not None


@responses.activate
def test_get_pages_returns_empty_list_on_http_error(simple_dom_getter, page_search_pattern):
    responses.add(
        responses.GET,
        "https://example.com/document",
        body=HTTPError("request failed"),
    )

    assert simple_dom_getter.get_pages("https://example.com/document", page_search_pattern) == []


def test_get_pages_handles_get_document_source_raising_http_error(monkeypatch, simple_dom_getter, page_search_pattern):
    def fake_get_document_source(self, document_url):
        raise HTTPError("failed")

    monkeypatch.setattr(SimpleDomGetterMethod, "get_document_source", fake_get_document_source)

    assert simple_dom_getter.get_pages("https://example.com/document", page_search_pattern) == []


def test_get_name_returns_empty_when_xpath_missing(monkeypatch, simple_dom_getter):
    # return HTML without the requested xpath
    monkeypatch.setattr(
        SimpleDomGetterMethod, "get_document_source", lambda self, url: "<html><body><div>no h1</div></body></html>"
    )

    assert simple_dom_getter.get_title("https://example.com/document", "//h1") == ""


def test_extract_uuids_from_divs_with_id_pattern_collects_unique_values(
    simple_dom_getter, page_html, page_search_pattern
):
    soup = __import__("bs4").BeautifulSoup(page_html, "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]


def test_get_uuid_from_match_ignores_duplicates_and_non_matches(simple_dom_getter):
    pattern = __import__("re").compile(r"page-id-uuid:([a-f0-9-]+)")

    result = simple_dom_getter._get_uuid_from_match([], "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern)
    assert result == ["33333333-3333-3333-3333-333333333333"]

    repeated = simple_dom_getter._get_uuid_from_match(
        result, "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern
    )
    assert repeated == ["33333333-3333-3333-3333-333333333333"]

    no_match = simple_dom_getter._get_uuid_from_match(result, "not-a-page-id", pattern)
    assert no_match == ["33333333-3333-3333-3333-333333333333"]


def test_extract_uuids_returns_empty_when_soup_none(simple_dom_getter, page_search_pattern):
    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(None, page_search_pattern)

    assert result == []


def test_extract_uuids_with_no_matches(simple_dom_getter, page_search_pattern):
    soup = __import__("bs4").BeautifulSoup('<html><body><div id="no-match"></div></body></html>', "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == []


def test_extract_uuids_handles_duplicates_preserving_order(simple_dom_getter, page_search_pattern):
    html = """
    <html>
      <body>
        <div id="page-id-uuid:aaa11111-1111-1111-1111-111111111111"></div>
        <div id="page-id-uuid:bbb22222-2222-2222-2222-222222222222"></div>
        <div id="page-id-uuid:aaa11111-1111-1111-1111-111111111111"></div>
      </body>
    </html>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == [
        "aaa11111-1111-1111-1111-111111111111",
        "bbb22222-2222-2222-2222-222222222222",
    ]
