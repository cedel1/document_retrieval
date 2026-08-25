#!/usr/bin/env python3
"""
Document Retrieval Script

This script processes a file containing document URLs and retrieves
all pages for each document using the dezoomify_retrieval.py script.
"""

import argparse
from ntpath import exists
import os
import subprocess
import sys
from typing import List


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
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
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
    document_output_dir = os.path.join(base_output_dir, f"document_{document_number:03d}")
    os.makedirs(document_output_dir, exist_ok=False)

    # Update the output argument in additional_args
    output_args = []
    i = 0
    while i < len(additional_args):
        arg = additional_args[i]
        print(f"arg: {arg}")
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
    output_args.extend(["--output", document_output_dir])

    command = ["python", "dezoomify_retrieval.py", url] + output_args

    try:
        print(f"\nProcessing document {document_number}: {url}")
        print(f"Output directory: {document_output_dir}")
        print(command)
        result = subprocess.run(command, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error processing document {url}: {e}")
        return False


def main():
    """Main function to process multiple documents."""
    parser = argparse.ArgumentParser(description="Retrieve multiple documents from a file")
    parser.add_argument("--documents_file", help="Path to text file containing document URLs (one per line)")

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

    # Read URLs from file
    urls = read_urls_from_file(args.documents_file)

    if not urls:
        print("No URLs found in file")
        sys.exit(1)

    print(f"Found {len(urls)} documents to process")

    # Build additional arguments to pass through
    additional_args = []
    if args.pages:
        additional_args.extend(["--pages"] + args.pages)
    if args.dezoomify_path != "dezoomify-rs":
        additional_args.extend(["--dezoomify-path", args.dezoomify_path])
    if args.dezoomify_args:
        additional_args.extend([f"--dezoomify-args={dezoomify_arg}" for dezoomify_arg in args.dezoomify_args])
        # additional_args.extend(args.dezoomify_args)

    print(additional_args)
    # Create base output directory
    os.makedirs(args.output, exist_ok=True)

    # Process each document
    successful = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"Document {i}/{len(urls)}")
        print(f"{'='*60}")

        print(f"retrieve_document({url}, {additional_args}, {i}, {args.output})")
        if retrieve_document(url, additional_args, i, args.output):
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Processing complete: {successful} successful, {failed} failed")
    print(f"{'='*60}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
