# document_retrieval

Python tooling for retrieving high-resolution scans from Kramerius-based digital libraries, with the current implementation focused on the DSMO / Digitalni studovna archive. The project reads document URLs from a text file, resolves the right library backend, discovers page UUIDs, and downloads each page through `dezoomify-rs`.

## Features

- Batch processing of multiple documents from a single input file
- Multiprocessing support for parallel document preprocessing
- Library-based URL dispatch via `LibraryFactory`
- Automatic page discovery for Kramerius 5 repositories
- Per-library output layout under a shared base output directory
- Custom dezoomify-rs binary path and extra dezoomify arguments
- Comprehensive logging support with `--verbose`
- Selenium-based page discovery hooks for JavaScript-rendered content

## Installation

### Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### dezoomify-rs

Install the binary and ensure it is available on `PATH`:

```bash
brew install dezoomify-rs
```

Or download the executable from the project releases page:
https://github.com/lovasoa/dezoomify-rs/releases

If the binary is not in `PATH`, pass it explicitly with `--dezoomify-path`.

## Usage

The script expects a text file with one document URL per line. Blank lines and lines starting with `#` are ignored.

```bash
python document_retrieval.py --documents_file documents.txt
```

### Arguments

- `--documents_file` (required): Path to a file containing document URLs, one per line
- `--verbose`: Enable debug logging
- `--output`: Base output directory for downloaded files (default: `output`)
- `--dezoomify-path`: Path to the `dezoomify-rs` executable (default: `dezoomify-rs`)
- `--dezoomify-args`: Additional arguments to pass through to `dezoomify-rs`; pass them as separate CLI values
- `--pages`: Optional list of page UUIDs to download (overrides automatic page discovery)

## Example input file

`documents.txt`:

```text
# one URL per line
https://www.knihovna.cz/kod_knihovny/view/uuid:a6729f13-f527-4918-a92e-83c1f5fceaf2
```

## Examples

### Basic batch download

```bash
python document_retrieval.py --documents_file documents.txt
```

### Custom output directory

```bash
python document_retrieval.py --documents_file documents.txt --output my_images
```

### Custom dezoomify-rs path

```bash
python document_retrieval.py --documents_file documents.txt --dezoomify-path /usr/local/bin/dezoomify-rs
```

### Pass additional dezoomify-rs options

```bash
python document_retrieval.py --documents_file documents.txt --dezoomify-args --largest
```

### Full command with page filtering and custom options

```bash
python document_retrieval.py \
  --documents_file documents.txt \
  --output my_images \
  --dezoomify-path /usr/local/bin/dezoomify-rs \
  --dezoomify-args --largest
```

### Download specific pages only

```bash
python document_retrieval.py \
  --documents_file documents.txt \
  --pages uuid:11111111-1111-1111-1111-111111111111 uuid:22222222-2222-2222-2222-222222222222
```

## Project structure

```text
.
├── document_retrieval.py          # CLI entry point
├── documents.txt                  # example input file
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # project configuration
├── src/
│   ├── helper_services/           # DOM / API fetch helpers
│   ├── library_models/            # URL -> library model mapping
│   ├── servers/                   # server-specific page discovery logic
│   ├── services/                  # shared helpers such as URL parsing
│   └── helpers/                   # utility functions (e.g., singleton pattern)
├── test/                          # comprehensive test suite
│   ├── fixtures.py                # shared test fixtures
│   ├── conftest.py                # pytest configuration
│   ├── helper_services/           # tests for helper services
│   ├── library_models/            # tests for library models
│   ├── servers/                   # tests for server implementations
│   └── services/                  # tests for shared services
└── output/                        # default root directory for downloaded artifacts
```

## Supported sources

The current implementation includes a library model for the DSMO archive and Kramerius 5 server discovery metadata. The architecture is designed so additional repositories can be added by registering another library model in `src/library_models/factories/library_factory.py`.

## Testing

The project includes a comprehensive test suite using pytest. To run the tests:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest test/test_document_retrieval.py

# Run tests with coverage
pytest --cov=src --cov=test
```

### Test structure

- `test/fixtures.py` - Shared fixtures for document retrieval tests
- `test/helper_services/` - Tests for DOM/API fetch helpers
- `test/library_models/` - Tests for library model implementations
- `test/servers/` - Tests for server-specific discovery logic
- `test/services/` - Tests for shared services
- `test/test_document_retrieval.py` - Tests for the main CLI entry point

Tests should follow the naming convention `test_{method_under_test}should|should_not{what is the test testing}` for clarity and maintainability.

## Performance considerations

- **Multiprocessing**: Currently, document preprocessing uses multiprocessing with fixed a pool size of 2 processes for parallel processing
- **Memory usage**: Each document is pre-processed independently to minimize wait time for Selenium and page download
