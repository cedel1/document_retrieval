"""Tests for the REST API getter helper."""

import re

import pytest
import requests
import responses

from src.helper_services.rest_api_getter import RestApiGetterMethod
from test.helper_services.fixtures import api_payload


@pytest.fixture
def mocked_requests():
    """Provide an isolated mock HTTP session for REST API calls."""
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def document_url():
    """Return a sample document URL."""
    return "https://example.com/view/uuid:11111111-1111-1111-1111-111111111111"


@pytest.fixture
def rest_api_getter(document_url):
    """Create a configured REST API getter."""
    return RestApiGetterMethod(
        {
            "identifier_pattern": r"(uuid:[a-f0-9-]+)",
            "base_api_url": "https://example.com/api/",
            "document_api_url": "search?fl=PID,dostupnost,fedora.model,dc.title&q=PID:{}&rows=10000&start=0",
            "document_pages_api_url": 'search?fl=PID,dostupnost&q=parent_pid:"{}"&rows=4000&start=0',
        }
    )


@pytest.fixture
def document_source_getter(rest_api_getter, api_payload):
    """Return a getter stub that supplies document and page payloads."""

    class StubRestApiGetter(RestApiGetterMethod):
        def get_document_source(self, document_url):
            self.document_json = {"response": {"docs": []}}
            self.document_pages_json = api_payload
            return self.document_json, self.document_pages_json

    return StubRestApiGetter(rest_api_getter.instance_params)


@pytest.fixture
def populated_document_getter(rest_api_getter):
    """Return a getter seeded with document metadata for JSON value lookups."""
    rest_api_getter.document_json = {
        "response": {"docs": [{"dc.title": "Sample title", "details": ["Sample subtitle"]}]}
    }
    return rest_api_getter


@pytest.fixture
def empty_document_source_getter(rest_api_getter):
    """Return a getter stub that provides no page data."""

    class StubRestApiGetter(RestApiGetterMethod):
        def get_document_source(self, document_url):
            self.document_json = {"response": {"docs": []}}
            self.document_pages_json = {"response": {"docs": []}}
            return self.document_json, self.document_pages_json

    return StubRestApiGetter(rest_api_getter.instance_params)


def test___init__should_raise_value_error_when_required_identifier_pattern_is_missing():
    """Test that initialization fails when the document identifier regex is missing."""
    with pytest.raises(ValueError, match="identifier_pattern"):
        RestApiGetterMethod(
            {"base_api_url": "https://example.com/api", "document_api_url": "doc", "document_pages_api_url": "pages"}
        )


def test___init__should_raise_value_error_when_required_api_urls_are_missing():
    """Test that initialization fails when any required API URL configuration is missing."""
    with pytest.raises(ValueError, match="base_api_url"):
        RestApiGetterMethod({"identifier_pattern": "x", "document_api_url": "doc", "document_pages_api_url": "pages"})

    with pytest.raises(ValueError, match="document_api_url"):
        RestApiGetterMethod(
            {"identifier_pattern": "x", "base_api_url": "https://example.com/api", "document_pages_api_url": "pages"}
        )

    with pytest.raises(ValueError, match="document_pages_api_url"):
        RestApiGetterMethod(
            {"identifier_pattern": "x", "base_api_url": "https://example.com/api", "document_api_url": "doc"}
        )


def test__recursive_get_should_return_nested_values_from_list_paths(rest_api_getter):
    """Test that nested JSON values can be retrieved using list-based traversal paths."""
    payload = {"response": {"docs": [{"PID": "uuid:abc", "rels_ext_index": [1]}]}}

    assert rest_api_getter._recursive_get(payload, "response", "docs", [0], "PID") == "uuid:abc"
    assert rest_api_getter._recursive_get(payload, "response", "missing") is None


def test__get_full_api_url_should_build_complete_url_from_template(rest_api_getter):
    """Test that a URL template is combined with the configured base API URL."""
    url = rest_api_getter._get_full_api_url("search?q={}&rows=10", ["uuid:abc"])

    assert url == "https://example.com/api/search?q=uuid:abc&rows=10"


def test__get_document_identifier_should_return_none_when_url_has_no_matching_identifier(rest_api_getter):
    """Test that identifier extraction returns None when the URL path does not match the configured pattern."""
    assert rest_api_getter._get_document_identifier("https://example.com/view/no-id") is None


def test_get_pages_should_return_page_uuids_for_document_source(document_source_getter, document_url):
    """Test that get_pages extracts page UUIDs from the document source payload."""
    result = document_source_getter.get_pages(
        document_url,
        {
            "page_object": ("response", "docs"),
            "page_id": ("PID",),
            "page_number": ("rels_ext_index", [0]),
        },
    )

    assert result == ["uuid:11111111-1111-1111-1111-111111111111", "uuid:22222222-2222-2222-2222-222222222222"]


def test_get_pages_should_return_empty_list_when_document_source_is_missing(empty_document_source_getter, document_url):
    """Test that get_pages returns an empty list when the document source is missing."""
    assert empty_document_source_getter.get_pages(document_url, {"page_object": ("response", "docs")}) == []


def test_get_document_source_should_store_both_json_responses(
    mocked_requests, rest_api_getter, document_url, api_payload
):
    """Test that document source retrieval stores and returns the document and page JSON responses."""
    endpoint = re.compile(r"https://example\.com/api/search\?.*")
    document_payload = {"response": {"docs": [{"dc.title": "Sample title"}]}}
    mocked_requests.add(responses.GET, endpoint, json=document_payload)
    mocked_requests.add(responses.GET, endpoint, json=api_payload)

    result = rest_api_getter.get_document_source(document_url)

    assert result == (document_payload, api_payload)
    assert rest_api_getter.document_json == document_payload
    assert rest_api_getter.document_pages_json == api_payload
    assert len(mocked_requests.calls) == 2
    assert "uuid%5C:11111111-1111-1111-1111-111111111111" in mocked_requests.calls[0].request.url
    assert "uuid:11111111-1111-1111-1111-111111111111" in mocked_requests.calls[1].request.url


def test_get_document_source_should_return_none_on_request_exception(mocked_requests, rest_api_getter, document_url):
    """Test that get_document_source returns None when the request raises a RequestException."""
    endpoint = re.compile(r"https://example\.com/api/search\?.*")
    mocked_requests.add(responses.GET, endpoint, body=requests.ConnectionError("network"))

    assert rest_api_getter.get_document_source(document_url) is None


def test_get_document_source_should_return_none_on_non_200_response(mocked_requests, rest_api_getter, document_url):
    """Test that get_document_source returns None when the API responds with an error status."""
    endpoint = re.compile(r"https://example\.com/api/search\?.*")
    mocked_requests.add(responses.GET, endpoint, json={}, status=200)
    mocked_requests.add(responses.GET, endpoint, json={}, status=500)

    assert rest_api_getter.get_document_source(document_url) is None


def test_get_json_value_should_return_values_for_string_and_list_paths(populated_document_getter):
    """Test that JSON values can be retrieved using direct keys and nested list paths."""
    assert populated_document_getter._get_json_value("missing") == ""
    assert populated_document_getter._get_json_value(["response", "docs", [0], "dc.title"]) == "Sample title"
    assert populated_document_getter.get_title("", ["response", "docs", [0], "dc.title"]) == "Sample title"
    assert populated_document_getter.get_subtitle("", ["response", "docs", [0], "details", [0]]) == "Sample subtitle"


def test_get_json_value_should_return_empty_string_when_document_json_is_not_loaded(rest_api_getter):
    """Test that JSON metadata accessors return an empty string before a document response is loaded."""
    assert rest_api_getter.get_title("", "dc.title") == ""
    assert rest_api_getter.get_part_title("", "dc.title") == ""
    assert rest_api_getter.get_part_subtitle("", ["response", "docs", [0], "details", [0]]) == ""
