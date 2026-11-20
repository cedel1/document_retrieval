"""Tests for the simple DOM page-discovery helper."""

import re
import pytest
import responses
from bs4 import BeautifulSoup
from requests import HTTPError
from requests.exceptions import SSLError
from src.helper_services.simple_dom_getter import SimpleDomGetterMethod
from test.helper_services.fixtures import (
    document_url,
    page_html,
    page_search_pattern,
    extracted_uuids_stub,
    document_source_stub,
)


@pytest.fixture
def simple_dom_getter():
    """Fixture providing a SimpleDomGetterMethod instance."""
    return SimpleDomGetterMethod({})


@responses.activate
def test_get_pages_should_call_requests_and_parse_response(
    simple_dom_getter, extracted_uuids_stub, document_url, page_html, page_search_pattern
):
    extracted_uuids_stub.result = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]

    responses.add(
        responses.GET,
        document_url,
        body=page_html,
        status=200,
        content_type="text/html",
    )
    result = simple_dom_getter.get_pages(document_url, page_search_pattern)

    assert result == extracted_uuids_stub.result
    assert responses.calls[0].request.url == document_url
    soup, search_pattern = extracted_uuids_stub.args
    assert search_pattern == page_search_pattern
    assert soup is not None


@responses.activate
def test_get_pages_should_return_empty_list_on_http_error(simple_dom_getter, document_url, page_search_pattern):
    responses.add(responses.GET, document_url, body=HTTPError("request failed"))

    assert simple_dom_getter.get_pages(document_url, page_search_pattern) == []


def test_get_pages_should_handle_http_error_from_get_document_source(
    simple_dom_getter, document_source_stub, document_url, page_search_pattern
):
    document_source_stub.error = HTTPError("failed")

    assert simple_dom_getter.get_pages(document_url, page_search_pattern) == []


def test_get_title_should_return_empty_when_xpath_missing(simple_dom_getter, document_source_stub, document_url):
    document_source_stub.result = "<html><body><div>no h1</div></body></html>"

    assert simple_dom_getter.get_title(document_url, "//h1") == ""


def test_extract_uuids_from_divs_with_id_pattern_should_collect_unique_values(
    simple_dom_getter, page_html, page_search_pattern
):
    soup = BeautifulSoup(page_html, "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == [
        "uuid:11111111-1111-1111-1111-111111111111",
        "uuid:22222222-2222-2222-2222-222222222222",
    ]


def test_get_uuid_from_match_should_ignore_duplicates_and_non_matches(simple_dom_getter):
    pattern = re.compile(r"page-id-(uuid:[a-f0-9-]+)")

    result = simple_dom_getter._get_uuid_from_match([], "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern)
    assert result == ["uuid:33333333-3333-3333-3333-333333333333"]

    repeated = simple_dom_getter._get_uuid_from_match(
        result, "page-id-uuid:33333333-3333-3333-3333-333333333333", pattern
    )
    assert repeated == ["uuid:33333333-3333-3333-3333-333333333333"]

    no_match = simple_dom_getter._get_uuid_from_match(result, "not-a-page-id", pattern)
    assert no_match == ["uuid:33333333-3333-3333-3333-333333333333"]


def test_extract_uuids_from_divs_with_id_pattern_should_return_empty_when_soup_none(
    simple_dom_getter, page_search_pattern
):
    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(None, page_search_pattern)

    assert result == []


def test_extract_uuids_from_divs_with_id_pattern_should_return_empty_on_no_matches(
    simple_dom_getter, page_search_pattern
):
    soup = BeautifulSoup('<html><body><div id="no-match"></div></body></html>', "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == []


def test_extract_uuids_from_divs_with_id_pattern_should_preserve_order_and_deduplicate(
    simple_dom_getter, page_search_pattern
):
    html = """
    <html>
      <body>
        <div id="page-id-uuid:aaa11111-1111-1111-1111-111111111111"></div>
        <div id="page-id-uuid:bbb22222-2222-2222-2222-222222222222"></div>
        <div id="page-id-uuid:aaa11111-1111-1111-1111-111111111111"></div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    result = simple_dom_getter._extract_uuids_from_divs_with_id_pattern(soup, page_search_pattern)

    assert result == [
        "uuid:aaa11111-1111-1111-1111-111111111111",
        "uuid:bbb22222-2222-2222-2222-222222222222",
    ]


@responses.activate
@pytest.mark.parametrize("allow_insecure, expected_verify", [(False, True), (True, False)])
def test_get_document_source_should_pass_verify_according_to_allow_insecure(
    document_url, allow_insecure, expected_verify
):
    responses.add(responses.GET, document_url, body="<html></html>")

    SimpleDomGetterMethod({"allow_insecure": allow_insecure}).get_document_source(document_url)

    assert responses.calls[0].request.req_kwargs["verify"] is expected_verify


def test_getter_should_validate_certificates_by_default():
    assert SimpleDomGetterMethod({}).allow_insecure is False


@responses.activate
def test_get_document_source_should_log_hint_and_raise_on_ssl_error(document_url, caplog):
    responses.add(responses.GET, document_url, body=SSLError("bad certificate"))

    getter = SimpleDomGetterMethod({})

    with caplog.at_level("ERROR"), pytest.raises(ValueError, match="Certificate validation failed") as exc_info:
        getter.get_document_source(document_url)

    assert document_url in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, SSLError)
    assert "--allow-insecure" in caplog.text
    assert document_url in caplog.text
