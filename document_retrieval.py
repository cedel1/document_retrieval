#!/usr/bin/env python3
"""
Document Retrieval Script

This script processes a file containing document URLs and retrieves
all pages for each document. Options can be given on the command line and/or in an optional TOML
config file (see src/settings/settings.py); command-line options always take precedence.
"""

import argparse
import logging
import sys
from multiprocessing.pool import Pool, AsyncResult
from pathlib import Path
from typing import Dict, Optional, Sequence

from pathvalidate.argparse import validate_filepath_arg
from src.library_models.base.base_library import BaseLibrary
from src.library_models.factories.library_factory import LibraryFactory
from src.settings.settings import ConfigError, Settings, find_config, is_positive_int, load_config, resolve_settings

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent


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
    documents_file_path: Path,
    output_dir: str = "output",
    page_uuids: list[str] = None,
    processes: int | None = None,
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
        processes: Number of concurrent processes to use for preprocessing.

    Returns:
        A dictionary mapping library string identifiers to BaseLibrary instances
        that contain the preprocessed documents.
    """
    libraries: Dict[str, BaseLibrary] = {}

    with Pool(processes=processes) as pool:  # default is None, which means use processor core number
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
                document, library_name = result.get()
                print(
                    f"Appending preprocessed document {document.title} ({document.identifier}) to "
                    f"library {library_name}."
                )
                libraries[library_name].append_preprocessed_document(document)
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


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Options that can also be set in the config file default to ``None`` so that "not given on the command line"
    can be told apart from an explicit value. The real defaults live in ``src/settings/settings.py``.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(description="Retrieve multiple documents from a file")
    parser.add_argument(
        "--config",
        help="Path to a TOML config file. If omitted, document_retrieval.toml next to this script is used when "
        "it exists. Command-line options override values from the config file.",
    )
    # This file should already exist on the filesystem, created by user:
    # so no need to validate - it either is or is not found
    parser.add_argument(
        "--documents_file",
        help="Path to text file containing document URLs (one per line); required here or in the config file",
    )
    parser.add_argument("--verbose", action="store_true", default=None, help="Enable verbose (debug) logging")
    parser.add_argument(
        "--processes",
        default=None,
        type=is_positive_int,
        help="Number of processes to use where parallel processing can occur. The default is to use the same number as "
        "processor cores.",
    )

    parser.add_argument("--pages", nargs="+", help="List of page UUIDs to download (overrides automatic discovery)")
    # this will be most likely created by this script, so validate it
    parser.add_argument(
        "--output", type=validate_filepath_arg, help="Base output directory for downloaded images (default: output)"
    )
    parser.add_argument(
        "--dezoomify-path",
        dest="dezoomify_path",
        help="Path to dezoomify-rs executable (default: dezoomify-rs)",
    )
    parser.add_argument(
        "--dezoomify-args",
        dest="dezoomify_args",
        nargs="+",
        action="extend",
        help="Additional arguments to pass to dezoomify-rs; overrides the config file, including library tables",
    )
    return parser


def build_additional_args(settings: Settings, library_name: str) -> dict:
    """Build the additional processing arguments passed to a library.

    Args:
        settings: The resolved settings.
        library_name: ``library_name`` of the library being processed; selects library-specific dezoomify args.

    Returns:
        A dictionary with the ``dezoomify-path`` and ``dezoomify-args`` entries (always present) and, when
        page UUIDs were set, a ``--pages`` entry.
    """
    additional_args: dict = {
        "dezoomify-path": settings.dezoomify_path,
        "dezoomify-args": settings.dezoomify_args_for(library_name),
    }
    if settings.pages:
        additional_args["--pages"] = settings.pages
    return additional_args


def main(argv: Optional[Sequence[str]] = None):
    """Main entry point: parse CLI args, merge the optional config file and process multiple documents.

    This script expects a path to a text file containing document URLs (one per
    line). It constructs library objects for each URL, optionally filters pages
    and dezoomify settings through command-line options or the config file, and
    processes each library's documents. Settings are resolved with the precedence
    command line > ``[library.<library_name>]`` config table > top-level config > defaults.

    Args:
        argv: Command-line arguments (without the program name); ``None`` reads ``sys.argv``.

    Returns:
        None. The function configures logging and exits with side-effects (files, logs).

    Raises:
        ConfigError: If the config file is missing (when given explicitly) or invalid.
        SystemExit: If no documents file is set on the command line or in the config file.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    known_libraries = [library_class.library_name for library_class in LibraryFactory.library_classes]
    config_path = find_config(args.config, SCRIPT_DIR)
    config = load_config(config_path, known_libraries) if config_path else None
    settings = resolve_settings(args, config)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG if settings.verbose else logging.INFO,
    )
    if config_path:
        logger.debug("Using config file %s", config_path)
    else:
        logger.debug("No config file found; using command-line options only")

    if not settings.documents_file:
        parser.error("documents_file must be set with --documents_file or in the config file")

    # Create base output directory
    Path(settings.output).mkdir(parents=True, exist_ok=True)

    library_results = []
    try:
        # Preprocess each document
        libraries: Dict[str, BaseLibrary] = preprocess_documents(
            Path(settings.documents_file),
            output_dir=settings.output,
            page_uuids=settings.pages,
            processes=settings.processes,
        )
        # Start processing per library
        for library in libraries.values():
            additional_args = build_additional_args(settings, library.library_name)
            logger.debug("Additional args to pass to %s: %s", library.library_name, additional_args)
            library_results.append(process_library_documents(library, additional_args, settings.output))

    except ValueError as e:
        logger.exception(e)
        raise e

    # Collect and display results
    if all(library_results) and any(library_results):
        logger.info("All documents processed successfully.")
    else:
        logger.warning("Some documents failed to process. Check logs for details.")


if __name__ == "__main__":
    try:
        main()
    except ConfigError as config_error:
        sys.exit(f"Configuration error: {config_error}")
