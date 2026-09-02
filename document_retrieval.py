#!/usr/bin/env python3
"""
Document Retrieval Script

This script processes a file containing document URLs and retrieves
all pages for each document.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict

from src.library_models.base.base_library import BaseLibrary
from src.library_models.factories.library_factory import LibraryFactory

logger = logging.getLogger(__name__)


def preprocess_documents(
    documents_file_path: Path, output_dir: str = "output", page_uuids: list[str] = None
) -> Dict[str, BaseLibrary]:
    """Read a file containing document URLs and build library objects.

    This function reads a newline-separated file of document URLs (ignoring
    lines that start with '#'), determines the correct library implementation
    for each URL using LibraryFactory, preprocesses the document via the
    library-specific preprocessing hook, and collects libraries keyed by their
    string representation.

    Args:
        documents_file_path: Path to a text file containing one document URL per line.
        output_dir: Base output directory used when preprocessing documents.
        page_uuids: Optional list of page UUIDs to pass-through to preprocessing; if
            supplied, the preprocessing may attach only those pages.

    Returns:
        A dictionary mapping library string identifiers to BaseLibrary instances
        that contain the preprocessed documents.
    """
    libraries: Dict[str, BaseLibrary] = {}
    with documents_file_path.open("r", encoding="UTF-8") as f:
        document_urls = [line.strip() for line in f if not line.strip().startswith("#")]

    for document_url in document_urls:
        try:
            library = LibraryFactory.from_url(document_url)
            library.append_preprocessed_document(
                library.preprocess_document_from_url(
                    document_url, page_detail_url=library.page_detail_url, output_dir=output_dir, page_uuids=page_uuids
                )
            )
            libraries[str(library)] = library
        except ValueError as e:
            logger.exception("Failed to create library for URL %s: %s", document_url, e)

    return libraries


def process_library_documents(library: BaseLibrary, additional_args: dict[str, list], output_dir: str) -> bool:
    """Process every document attached to a library.

    Iterates over the preprocessed documents stored in the given BaseLibrary and
    invokes the library-specific process_document hook for each document. Any
    exceptions raised during processing are logged and the document is recorded
    as failed.

    Args:
        library: The BaseLibrary instance whose documents should be processed.
        additional_args: A dictionary of additional arguments to pass through to
            the processing hooks (for example, pages or dezoomify options).
        output_dir: Base output directory where processed artifacts should be
            written.

    Returns:
        True when all documents processed successfully; False if any document
        failed during processing.
    """
    failed_documents = []
    for library_document in library.documents:
        try:
            library.process_document(library_document, additional_args, output_dir)
        except Exception as e:
            logger.exception("Failed to process document %s: %s", library_document.source_url, e)
            failed_documents.append(library_document)

    return len(failed_documents) == 0


def main():
    """Main entry point: parse CLI args and process multiple documents.

    This script expects a path to a text file containing document URLs (one per
    line). It constructs library objects for each URL, optionally filters pages
    and dezoomify settings through command-line options, and processes each
    library's documents.

    Args:
        None (reads arguments from sys.argv via argparse).

    Returns:
        None. The function configures logging and exits with side-effects (files, logs).
    """
    parser = argparse.ArgumentParser(description="Retrieve multiple documents from a file")
    parser.add_argument("--documents_file", help="Path to text file containing document URLs (one per line)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose (debug) logging")

    # Parse known arguments to pass through to dezoomify_retrieval.py
    parser.add_argument("--pages", nargs="+", help="List of page UUIDs to download (overrides automatic discovery)")
    parser.add_argument("--output", default="output", help="Base output directory for downloaded images")
    parser.add_argument(
        "--dezoomify-path", default="dezoomify-rs", help="Path to dezoomify-rs executable (default: dezoomify-rs)"
    )
    parser.add_argument(
        "--dezoomify-args", nargs="+", action="extend", help="Additional arguments to pass to dezoomify-rs"
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.DEBUG if args.verbose else logging.INFO
    )

    # Build additional arguments to pass through
    additional_args = {}
    if args.pages:
        additional_args["--pages"] = args.pages
    if args.dezoomify_path != "dezoomify-rs":
        additional_args["dezoomify-path"] = args.dezoomify_path
    if args.dezoomify_args:
        additional_args["dezoomify-args"] = []
        for arg in args.dezoomify_args:
            additional_args["dezoomify-args"].append(arg)
    logger.debug("Additional args to pass: %s", additional_args)

    # Create base output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)

    success = True
    try:
        # Preprocess each document
        libraries: Dict[str, BaseLibrary] = preprocess_documents(
            Path(args.documents_file), output_dir=args.output, page_uuids=args.pages
        )
        # Start processing per library
        for library in libraries.values():
            success = process_library_documents(library, additional_args, args.output)
    except ValueError as e:
        print(e)

    # Collect and display results
    if success:
        logger.info("All documents processed successfully.")
    else:
        logger.warning("Some documents failed to process. Check logs for details.")


if __name__ == "__main__":
    main()
