# document_retrieval

Python tooling for retrieving high-resolution scans from Kramerius-based digital libraries, with the current
implementation focused on the DSMO / Digitalni studovna archive. The project reads document URLs from a text file,
resolves the right library backend, discovers page UUIDs, and downloads each page through `dezoomify-rs`.

## Features

- Batch processing of multiple documents from a single input file
- Multiprocessing support for parallel document preprocessing
- Library-based URL dispatch via `LibraryFactory`
- Automatic page discovery for Kramerius 5 repositories
- Per-library output layout under a shared base output directory
- Custom dezoomify-rs binary path and extra dezoomify arguments
- Optional TOML config file holding the command-line values, with library-dependent settings
- Website certificate validation on by default; opt out with `--allow-insecure` (globally or per library)
- Comprehensive logging support with `--verbose`
- Selenium-based page discovery hooks for JavaScript-rendered content

## Installation

### Python dependencies

```bash
uv sync
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
An input file without URLs produces a warning and exits successfully.

Missing document metadata is treated as empty. Unexpected non-string REST metadata is reported, and other retrieval
methods are tried where available.

Recognized certificate verification failures produce a warning for each failed request; `--verbose` also shows the
diagnostic details. Other retrieval methods are still tried. Certificate validation is never disabled automatically.
See [Known issues](#known-issues) for a limitation affecting `dezoomify-rs` on macOS and Windows.

The final summary lists failed documents and page download counts. A document fails if any requested page fails, or if
its properties file cannot be created. Existing document output directories are never overwritten. The command exits
with status 1 if any document fails, or 0 when all documents succeed (or there are no URLs).

Commands run through `uv run`, which uses the project's `.venv` without manual activation.

```bash
uv run python document_retrieval.py --documents_file documents.txt
```

### Arguments

- `--config`: Path to a TOML config file (see [Configuration file](#configuration-file)); a missing file is an error
- `--documents_file` (required on the command line or in the config file): Path to a file containing document URLs, one
  per line
- `--verbose` / `--no-verbose`: Enable or disable debug logging; `--no-verbose` overrides `verbose = true` from the
  config file
- `--processes`: Number of processes for parallel processing (default: number of processor cores)
- `--output`: Base output directory for downloaded files (default: `output`)
- `--allow-insecure` / `--no-allow-insecure`: Disable or (re-)enable website certificate validation (default:
  certificates are validated). An explicit value overrides the config file, including library tables. When validation
  is disabled, `--accept-invalid-certs` is also passed to `dezoomify-rs`. **Security note:** with validation disabled
  the connection can be intercepted or spoofed; use it only for sites you trust.
- `--images-subfolder`: Name of a subfolder inside each document folder into which the page images are downloaded;
  `properties.txt` stays in the document folder. It must be a single folder name valid on all platforms (no path
  separators, no reserved names like `CON` or `properties.txt`, no trailing dots or spaces, no characters like `:` or
  `?`). Without it, images are placed directly in the document folder. The download fails if the subfolder already
  exists. Also settable per library in the config file.
- `--dezoomify-path`: Path to the `dezoomify-rs` executable (default: `dezoomify-rs`)
- `--dezoomify-args`: Additional arguments to pass through to `dezoomify-rs`; pass them as separate CLI values
- `--pages`: Optional list of page UUIDs to download (overrides automatic page discovery)

## Configuration file

Every option can also be stored in an optional [TOML](https://toml.io) file. Without `--config`, the file
`document_retrieval.toml` in the same directory as `document_retrieval.py` is loaded if it exists (otherwise it is
silently ignored and only command-line options are used). `--config PATH` loads that file instead and fails if it
does not exist. Copy `document_retrieval.example.toml` to `document_retrieval.toml` as a starting point; the
latter is git-ignored.

```toml
documents_file = "documents.txt"
output = "output"
processes = 4
verbose = false
dezoomify_path = "dezoomify-rs"
dezoomify_args = ["--largest"]

# Library-dependent settings; the table name is the exact library_name of the library
[library.Library_DSMO]
dezoomify_args = ["--max-width", "4000"]
```

**Precedence** (highest first): command line > `[library.<library_name>]` table > top-level config keys > built-in
defaults. A list given on the command line (`--pages`, `--dezoomify-args`) *replaces* the config list; a
`--dezoomify-args` value also overrides library tables. To change a value for one run, give it on the command line;
there are no per-library command-line options. Boolean options come in pairs (`--verbose` / `--no-verbose`), so the
command line can switch a setting both on and off; when neither is given, the config value (or the default) applies.

**Keys**: top-level `documents_file`, `output`, `processes`, `verbose`, `pages`, `dezoomify_path`,
`dezoomify_args`, `allow_insecure`, `images_subfolder`; per-library tables accept `dezoomify_args`,
`allow_insecure` and `images_subfolder`.

**Validation** is strict: unknown keys, unknown library tables, unknown keys inside a library table and invalid
values or types (checked with the same rules as the command-line options) stop the program with an error.

**Paths** inside the config file (`documents_file`, `output`, and `dezoomify_path` when it contains a directory,
e.g. `./bin/dezoomify-rs`; a bare name such as `dezoomify-rs` is still looked up on `PATH`) are relative to the config
file's directory, while paths given on the command line are relative to the current directory. Document URLs always stay
in the `documents_file`, never in the config.

## Example input file

`documents.txt`:

```text
# one URL per line
https://www.knihovna.cz/kod_knihovny/view/uuid:a6729f13-f527-4918-a92e-83c1f5fceaf2
```

## Examples

### Basic batch download

```bash
uv run python document_retrieval.py --documents_file documents.txt
```

### Custom output directory

```bash
uv run python document_retrieval.py --documents_file documents.txt --output my_images
```

### Custom dezoomify-rs path

```bash
uv run python document_retrieval.py --documents_file documents.txt --dezoomify-path /usr/local/bin/dezoomify-rs
```

### Pass additional dezoomify-rs options

```bash
uv run python document_retrieval.py --documents_file documents.txt --dezoomify-args --largest
```

### Full command with page filtering and custom options

```bash
uv run python document_retrieval.py \
  --documents_file documents.txt \
  --output my_images \
  --dezoomify-path /usr/local/bin/dezoomify-rs \
  --dezoomify-args --largest
```

### Download specific pages only

```bash
uv run python document_retrieval.py \
  --documents_file documents.txt \
  --pages uuid:11111111-1111-1111-1111-111111111111 uuid:22222222-2222-2222-2222-222222222222
```

## Project structure

```text
.
├── document_retrieval.py          # CLI entry point
├── documents.txt                  # example input file
├── document_retrieval.example.toml # example config file
├── uv.lock                        # locked Python dependencies
├── pyproject.toml                 # project configuration
├── src/
│   ├── helper_services/           # DOM / API fetch helpers
│   ├── library_models/            # URL -> library model mapping
│   ├── servers/                   # server-specific page discovery logic
│   ├── services/                  # shared helpers such as URL parsing
│   ├── settings/                  # config file loading and settings resolution
│   └── helpers/                   # utility functions (e.g., singleton pattern)
├── test/                          # comprehensive test suite
│   ├── fixtures.py                # shared test fixtures
│   ├── conftest.py                # pytest configuration
│   ├── helper_services/           # tests for helper services
│   ├── library_models/            # tests for library models
│   ├── servers/                   # tests for server implementations
│   ├── services/                  # tests for shared services
│   └── settings/                  # tests for config file and settings
└── output/                        # default root directory for downloaded artifacts
```

## Supported sources

The current implementation includes a library model for the DSMO archive and Kramerius 5 server discovery metadata. The
architecture is designed so additional repositories can be added by registering another library model in
`src/library_models/factories/library_factory.py`.

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
- `test/settings/` - Tests for config file loading and settings resolution
- `test/test_document_retrieval.py` - Tests for the main CLI entry point

### Test naming convention

All test functions must follow this format:

```
test_{method_name}_{should|should_not}_{what_is_being_checked}
```

**Examples:**

- `test_output_base_should_truncate_filename_to_64_chars`
- `test_get_document_pages_should_retry_with_next_method_on_failure`
- `test_init_should_raise_type_error_when_instantiated_directly`

This convention applies to all new tests and ensures consistency across the test suite.

## Performance considerations

- **Multiprocessing**: Currently, document preprocessing uses multiprocessing with fixed a pool size of 2 processes for
  parallel processing
- **Memory usage**: Each document is pre-processed independently to minimize wait time for Selenium and page download

## Known issues

On macOS and Windows, certificate verification failures reported by `dezoomify-rs` may not be recognized. In that case,
the full error output is shown instead of a concise warning, and it may not suggest `--allow-insecure`. Certificate
validation remains enabled; contact the server owner to fix the certificate, or use `--allow-insecure` only if you trust
the server and accept the [security risk](#arguments).
