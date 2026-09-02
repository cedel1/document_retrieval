"""Tests for DSMODocument."""

from pathlib import Path

from src.library_models.dsmo.dsmo_document import DSMODocument
from test.library_models.fixtures import DOCUMENT_URL


def test_extract_document_uuid_from_url_uses_document_parser():
    assert DSMODocument._extract_document_uuid_from_url(DOCUMENT_URL) == "11111111-1111-1111-1111-111111111111"


def test_dsmo_document_from_uuid_creates_pages_and_output_dir():
    document = DSMODocument().from_uuid(
        "doc-123",
        DOCUMENT_URL,
        output_dir="tmp",
        page_uuids=["22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"],
    )

    assert document.identifier == "doc-123"
    assert document.output_dir == Path("tmp/doc-123")
    assert [page.identifier for page in document.pages] == [
        "22222222-2222-2222-2222-222222222222",
        "33333333-3333-3333-3333-333333333333",
    ]


def test_dsmo_document_from_url_extracts_uuid_and_builds_pages():
    document = DSMODocument().from_url(DOCUMENT_URL, output_dir="tmp")

    assert document.identifier == "11111111-1111-1111-1111-111111111111"
    assert document.pages == []
