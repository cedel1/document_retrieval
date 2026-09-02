"""Tests for URL UUID parsing helpers."""

import pytest

from src.services.url_parser import DocumentUrlParser
from test.services.fixtures import DOCUMENT_URL, PAGE_URL


def test_extract_uuids_returns_document_and_page_uuid():
    document_uuid, page_uuid = DocumentUrlParser.extract_uuids(DOCUMENT_URL)

    assert document_uuid == "12345678-1234-1234-1234-123456789abc"
    assert page_uuid == "87654321-4321-4321-4321-cba987654321"


def test_extract_document_uuid_returns_uuid_for_valid_url():
    assert DocumentUrlParser.extract_document_uuid(DOCUMENT_URL) == "12345678-1234-1234-1234-123456789abc"


def test_extract_uuids_handles_url_without_document_uuid():
    assert DocumentUrlParser.extract_uuids("https://example.com/not-a-document") == (None, None)


def test_extract_document_uuid_raises_for_missing_uuid():
    with pytest.raises(ValueError, match="Could not extract document UUID"):
        DocumentUrlParser.extract_document_uuid("https://example.com/not-a-document")


def test_extract_uuids_handles_page_without_page_uuid():
    assert DocumentUrlParser.extract_uuids("https://example.com/view/uuid:11111111-1111-1111-1111-111111111111") == (
        "11111111-1111-1111-1111-111111111111",
        None,
    )
