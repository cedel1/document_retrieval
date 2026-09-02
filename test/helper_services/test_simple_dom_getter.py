"""Tests for the simple DOM page-discovery helper."""

from requests import HTTPError

from src.helper_services.simple_dom_getter import SimpleDomGetterMethod
from test.helper_services.fixtures import PAGE_HTML, PAGE_SEARCH_PATTERN, FakeResponse


def test_get_pages_calls_requests_with_expected_arguments_and_parses_response(monkeypatch):
    getter = SimpleDomGetterMethod()
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse(content=PAGE_HTML.encode("utf-8"))

    def fake_extract(self, soup, search_pattern):
        captured["soup"] = soup
        captured["search_pattern"] = search_pattern
        return [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        ]

    monkeypatch.setattr("src.helper_services.simple_dom_getter.requests.get", fake_get)
    monkeypatch.setattr(SimpleDomGetterMethod, "_extract_uuids_from_divs_with_id_pattern", fake_extract)

    result = getter.get_pages("https://example.com/document", PAGE_SEARCH_PATTERN)

    assert result == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    assert captured["url"] == "https://example.com/document"
    assert captured["kwargs"]["timeout"] == 30
    assert captured["kwargs"]["verify"] is False
    assert captured["search_pattern"] == PAGE_SEARCH_PATTERN
    assert captured["soup"] is not None


def test_get_pages_returns_empty_list_on_http_error(monkeypatch):
    getter = SimpleDomGetterMethod()

    def fake_get(*args, **kwargs):
        raise HTTPError("request failed")

    monkeypatch.setattr("src.helper_services.simple_dom_getter.requests.get", fake_get)

    assert getter.get_pages("https://example.com/document", PAGE_SEARCH_PATTERN) == []


def test_extract_uuids_from_divs_with_id_pattern_collects_unique_values():
    getter = SimpleDomGetterMethod()
    soup = __import__("bs4").BeautifulSoup(PAGE_HTML, "html.parser")

    result = getter._extract_uuids_from_divs_with_id_pattern(soup, PAGE_SEARCH_PATTERN)

    assert result == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]


def test_get_uuid_from_match_ignores_duplicates_and_non_matches():
    getter = SimpleDomGetterMethod()
    pattern = __import__("re").compile(r"page-id-uuid:([a-f0-9-]+)")

    result = getter._get_uuid_from_match([], "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern)
    assert result == ["33333333-3333-3333-3333-333333333333"]

    repeated = getter._get_uuid_from_match(result, "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern)
    assert repeated == ["33333333-3333-3333-3333-333333333333"]

    no_match = getter._get_uuid_from_match(result, "not-a-page-id", pattern)
    assert no_match == ["33333333-3333-3333-3333-333333333333"]
