"""Tests for DSMOLibrary."""

from src.library_models.dsmo.dsmo_library import DSMOLibrary


def test_dsmo_library_uses_expected_server_metadata(monkeypatch):
    library = DSMOLibrary("https://www.digitalniknihovna.cz/dsmo/view/uuid:11111111-1111-1111-1111-111111111111")

    assert library.library_name == "Library_DSMO"
    assert library.server_urls[0].startswith("https://www.digitalniknihovna.cz/dsmo/")
    assert library.page_detail_url == "https://digitalnistudovna.army.cz/"


def test_dsmo_library_preprocess_document_from_url_passes_through_arguments(monkeypatch):
    captured = {}

    def fake_from_url(library, source_url, page_detail_url, output_dir, page_uuids=None):
        captured["library"] = library
        captured["source_url"] = source_url
        captured["page_detail_url"] = page_detail_url
        captured["output_dir"] = output_dir
        captured["page_uuids"] = page_uuids
        return {"source_url": source_url}

    monkeypatch.setattr("src.library_models.dsmo.dsmo_library.DSMODocumentFactory.from_url", fake_from_url)
    library = DSMOLibrary("https://www.digitalniknihovna.cz/dsmo/view/uuid:11111111-1111-1111-1111-111111111111")

    result = library.preprocess_document_from_url(
        "https://www.digitalniknihovna.cz/dsmo/view/uuid:11111111-1111-1111-1111-111111111111",
        page_detail_url="https://digitalnistudovna.army.cz/",
        output_dir="tmp",
        page_uuids=["page-1"],
    )

    assert result == {"source_url": "https://www.digitalniknihovna.cz/dsmo/view/uuid:11111111-1111-1111-1111-111111111111"}
    assert captured["output_dir"] == "tmp/Library_DSMO"
    assert captured["page_uuids"] == ["page-1"]
