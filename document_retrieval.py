#!/usr/bin/env python3
"""
Document Retrieval Script

This script processes a file containing document URLs and retrieves
all pages for each document.
"""

import argparse
import logging
from multiprocessing.pool import Pool, AsyncResult
from pathlib import Path
from typing import Dict

from pathvalidate.argparse import validate_filepath_arg

from src.library_models.base.base_library import BaseLibrary
from src.library_models.factories.library_factory import LibraryFactory

logger = logging.getLogger(__name__)


def get_document_urls(documents_file_path: Path):
    """Read document URLs from a file, ignoring comments.

    This function reads a file line by line and yields each line that does not
    start with '#' (treated as a comment). Lines are stripped of leading and
    trailing whitespace before being yielded.

    Args:
        documents_file_path: Path to a text file containing document URLs,
            one per line. Lines starting with '#' are treated as comments
            and ignored.

    Yields:
        str: Document URLs from the file, with whitespace stripped.
    """
    with open(documents_file_path, "r", encoding="UTF-8") as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                yield line.strip()


def get_library_document(document_url, output_dir, page_uuids, library_class):
    """Preprocess a single document from a URL using the provided library.

    The worker creates its own library instance. Library instances are not
    shared between processes; the parent process owns the final library state.

    Args:
        document_url: URL of the document to preprocess.
        output_dir: Base output directory where preprocessed document data should be written.
        page_uuids: Optional list of page UUIDs to pass-through to preprocessing; if
            supplied, the preprocessing may attach only those pages.
        library_class: The class of the BaseLibrary instance to use for preprocessing the document.

    Returns:
        tuple: A tuple containing (document, str(library)) where document is the preprocessed
            BaseDocument instance and library is the name of the BaseLibrary instance.

    Raises:
        ValueError: If the document preprocessing fails for the given URL.
    """
    try:
        library = library_class()
        document = library.preprocess_document_from_url(
            document_url,
            page_detail_url=library.page_detail_url,
            output_dir=output_dir,
            page_uuids=page_uuids,
        )
        return document, str(library)
    except ValueError as e:
        logger.exception("Failed to create document for URL %s: %s", document_url, e)
        raise e


def preprocess_documents(
    documents_file_path: Path, output_dir: str = "output", page_uuids: list[str] = None
) -> Dict[str, BaseLibrary]:
    """Read a file containing document URLs and build library objects.

    This function reads a newline-separated file of document URLs (ignoring
    lines that start with '#'), determines the correct library implementation
    for each URL using LibraryFactory, preprocesses the document via the
    library-specific preprocessing hook using multiprocessing, and collects
    libraries keyed by their string representation.

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

    with Pool(processes=2) as pool:
        results: list[AsyncResult] = []
        for document_url in get_document_urls(documents_file_path):
            try:
                print(f"Preprocessing {document_url}.")
                library = LibraryFactory.from_url(document_url)
                libraries[str(library)] = library
                results.append(
                    pool.apply_async(
                        get_library_document, args=(document_url, output_dir, page_uuids, library.__class__)
                    )
                )
            except ValueError as e:
                logger.exception("Failed to create library for URL %s: %s", document_url, e)

        for result in results:
            try:
                result, library_name = result.get()
                print(
                    f"Appending preprocessed document {result.title} ({result.identifier}) to library {library_name}."
                )
                libraries[library_name].append_preprocessed_document(result)
            except (TimeoutError, ValueError) as e:
                logger.exception("Failed to retrieve result: %s", e)

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
        # pylint: disable-next=broad-exception-caught
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
    # This file should already exist on the filesystem, created by user:
    # so no need to validate - it either is or is not found
    parser.add_argument("--documents_file", help="Path to text file containing document URLs (one per line)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose (debug) logging")

    # Parse known arguments to pass through to document_retrieval.py
    parser.add_argument("--pages", nargs="+", help="List of page UUIDs to download (overrides automatic discovery)")
    # this will be most likely created by this script, so validate it
    parser.add_argument(
        "--output", default="output", help="Base output directory for downloaded images", type=validate_filepath_arg
    )
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

    library_results = []
    try:
        # Preprocess each document
        libraries: Dict[str, BaseLibrary] = preprocess_documents(
            Path(args.documents_file), output_dir=args.output, page_uuids=args.pages
        )
        # Start processing per library
        for library in libraries.values():
            library_results.append(process_library_documents(library, additional_args, args.output))

    except ValueError as e:
        logger.exception(e)
        raise e

    # Collect and display results
    if all(library_results) and any(library_results):
        logger.info("All documents processed successfully.")
    else:
        logger.warning("Some documents failed to process. Check logs for details.")


if __name__ == "__main__":
    main()
