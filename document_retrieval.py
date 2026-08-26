#!/usr/bin/env python3
"""
Document Retrieval Script

This script processes a file containing document URLs and retrieves
all pages for each document using the dezoomify_retrieval.py script.
"""

import argparse
import subprocess
import sys
from typing import List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_urls_from_file(file_path: str) -> List[str]:
    """
    Read URLs from a text file, one per line.

    Args:
        file_path: Path to the text file containing URLs

    Returns:
        List of URLs
    """
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    urls.append(line)
    except FileNotFoundError:
        logger.error("Error: File not found: %s", file_path)
        sys.exit(1)
    except Exception as e:
        logger.error("Error reading file: %s", e)
        sys.exit(1)

    return urls


def retrieve_document(url: str, additional_args: List[str], document_number: int, base_output_dir: str) -> bool:
    """
    Retrieve a single document using dezoomify_retrieval.py.

    Args:
        url: URL of the document
        additional_args: Additional arguments to pass to dezoomify_retrieval.py
        document_number: The document number for naming the output directory
        base_output_dir: Base output directory

    Returns:
        True if successful, False otherwise
    """
    # Create document-specific output directory
    document_output_dir = Path(base_output_dir) / f"document_{document_number:03d}"
    # keep the original behavior of failing if the directory already exists
    document_output_dir.mkdir(parents=True, exist_ok=False)

    # Update the output argument in additional_args
    output_args = []
    i = 0
    while i < len(additional_args):
        arg = additional_args[i]
        logger.debug("arg: %s", arg)
        if arg == "--output" and i + 1 < len(additional_args):
            # Skip the next argument as we'll override it
            i += 2
        elif arg.startswith("--output="):
            # Skip this argument as we'll override it
            i += 1
        else:
            output_args.append(arg)
            i += 1

    # Add our custom output directory
    output_args.extend(["--output", str(document_output_dir)])

    command = ["python", "dezoomify_retrieval.py", url] + output_args

    try:
        print("\nProcessing document %d: %s", document_number, url)
        logger.info("Output directory: %s", document_output_dir)
        logger.debug("Running command: %s", command)
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("dezoomify_retrieval failed for %s (returncode=%s)", url, result.returncode)
            logger.error("stdout: %s", result.stdout)
            logger.error("stderr: %s", result.stderr)
        return result.returncode == 0
    except Exception as e:
        logger.error("Error processing document %s: %s", url, e)
        return False


def main():
    """Main function to process multiple documents."""
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

    # Read URLs from file
    urls = read_urls_from_file(args.documents_file)

    if not urls:
        print("No URLs found in file")
        sys.exit(1)

    logger.info("Found %d documents to process", len(urls))

    # Build additional arguments to pass through
    additional_args = []
    if args.pages:
        additional_args.extend(["--pages"] + args.pages)
    if args.dezoomify_path != "dezoomify-rs":
        additional_args.extend(["--dezoomify-path", args.dezoomify_path])
    if args.dezoomify_args:
        additional_args.extend([f"--dezoomify-args={dezoomify_arg}" for dezoomify_arg in args.dezoomify_args])
    logger.debug("Additional args to pass: %s", additional_args)
    # Create base output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # Process each document
    successful = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        logger.info("\n%s", "=" * 60)
        logger.info("Document %d/%d", i, len(urls))
        logger.info("%s", "=" * 60)

        logger.debug("retrieve_document(%s, %s, %d, %s)", url, additional_args, i, args.output)
        if retrieve_document(url, additional_args, i, args.output):
            successful += 1
        else:
            failed += 1

    logger.info("\n%s", "=" * 60)
    logger.info("Processing complete: %d successful, %d failed", successful, failed)
    logger.info("%s", "=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
