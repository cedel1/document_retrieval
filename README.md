# dezoomify_retrieval

A Python project for retrieving high-resolution images from digital library archives using dezoomify-rs.

## Installation

### Python Dependencies

```bash
pip install -r requirements.txt
```

### dezoomify-rs

Install dezoomify-rs using Homebrew:

```bash
brew install dezoomify-rs
```

Or download it from [GitHub releases](https://github.com/lovasoa/dezoomify-rs/releases).

## Usage

### Basic Usage

```bash
python document_retrieval.py <URL>
```

### Arguments

- `url` (required): URL of the document page
- `--pages`: List of page UUIDs to download (overrides automatic discovery)
- `--output`: Output directory for downloaded images (default: `output`)
- `--dezoomify-path`: Path to dezoomify-rs executable (default: `dezoomify-rs`)
- `--dezoomify-args`: Additional arguments to pass to dezoomify-rs

### Examples

#### Automatic Page Discovery

```bash
python document_retrieval.py "https://www.digitalniknihovna.cz/dsmo/view/uuid:a8839797-e14a-4992-9ba3-c9abcf631d88?page=uuid:12ee3ffa-254f-11eb-a67c-001b63bd97ba&fulltext=befestigung"
```

#### Manual Page Specification

```bash
python document_retrieval.py "https://www.digitalniknihovna.cz/dsmo/view/uuid:a8839797-e14a-4992-9ba3-c9abcf631d88?page=uuid:12ee3ffa-254f-11eb-a67c-001b63bd97ba&fulltext=befestigung" --pages 12ee3ffa-254f-11eb-a67c-001b63bd97ba
```

#### Custom Output Directory

```bash
python document_retrieval.py "https://..." --output my_images
```

#### Custom dezoomify-rs Path

```bash
python document_retrieval.py "https://..." --dezoomify-path /path/to/dezoomify-rs
```

#### Additional dezoomify-rs Arguments

```bash
python document_retrieval.py "https://..." --dezoomify-args "--largest" "--max-width" "4000"
```

#### Combined Options

```bash
python document_retrieval.py "https://..." --pages uuid1 uuid2 uuid3 --output my_images --dezoomify-path /usr/local/bin/dezoomify-rs --dezoomify-args "--largest"
```

## Features

- **Automatic Page Discovery**: Attempts to find all pages in a document via API or DOM parsing
- **Manual Page Specification**: Override automatic discovery with specific page UUIDs
- **Flexible Image Formats**: Supports JPEG, PNG, TIFF, and other formats based on dezoomify-rs output
- **Configurable Delays**: Random delays between downloads (1-10 seconds) to avoid rate limiting
- **Custom dezoomify-rs Arguments**: Pass additional options to dezoomify-rs for advanced control
- **JavaScript Rendering**: Optional Selenium support for pages that require JavaScript rendering

## Development

### Adding Selenium Support (Optional)

For pages that require JavaScript rendering, install Selenium:

```bash
pip install selenium
```

Ensure Chrome browser and ChromeDriver are installed on your system.
