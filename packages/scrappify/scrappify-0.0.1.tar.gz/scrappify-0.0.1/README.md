# Scrappify

Scrappify is a powerful yet simple website scraping and downloading tool. It allows you to easily **scrape links, download files, filter by file types, extract patterns (like emails or phone numbers), and perform deep crawling** — all from Python or the command line.

---

## Features

* Download entire websites
* Extract links, emails, phone numbers, or custom regex patterns
* Filter downloads by file type (images, documents, scripts, etc.)
* Fast downloads with configurable workers
* Cross-domain crawling support
* Command-line interface (CLI) and Python API

---

## Installation

```bash
pip install scrappify
```

---

## Python Usage

### Basic Usage

```python
from scrappify import url, scrap, download

# Download entire website
url_download = url("https://example.com")
downloaded_files = download(url_download, output_dir="my_site")
print(f"Downloaded {len(downloaded_files)} files")

# Get all links from a page
links = scrap(url_download)
print(f"Found {len(links)} links")
```

### File Type Filtering

```python
from scrappify import url, download
from scrappify.patterns import file_type

# Download only JavaScript files
js_files = download("https://example.com", file_type="js", output_dir="js_files")

# Download images using category
images = download("https://example.com", file_type=file_type['image'], output_dir="images")

# Download multiple specific file types
docs_and_images = download("https://example.com", file_type=["pdf", "jpg", "png"])
```

### Pattern Searching

```python
from scrappify import url, download
from scrappify.patterns import pattern

# Find emails in all downloaded files
email_results = download("https://example.com", pattern=pattern['email'])

# Find phone numbers in HTML files only
phone_results = download("https://example.com", file_type="html", pattern=pattern['phone'])

# Custom regex pattern
custom_pattern = r'\b\d{3}-\d{2}-\d{4}\b'  # SSN pattern
ssn_results = download("https://example.com", pattern=custom_pattern)

# Combine file type and pattern
results = download("https://example.com", file_type="js", pattern=pattern['url'])
```

### Advanced Scraping

```python
from scrappify import url, scrap, download

# Deep crawling (multiple levels)
deep_links = scrap("https://example.com", depth=3)
print(f"Found {len(deep_links)} links across 3 levels")

# Download with increased workers
fast_download = download("https://example.com", max_workers=20, output_dir="fast_download")

# Cross-domain downloading (disable same-domain restriction)
all_links = scrap("https://example.com", same_domain_only=False)
```

### Programmatic Pattern Extraction

```python
from scrappify.core.utils import search_pattern_in_file

# Search pattern in specific file
results = search_pattern_in_file("downloaded_file.html", r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
for result in results:
    print(f"Email found: {result['match']} at line {result['line']}")
```

---

## Command Line Usage

```bash
# Download entire website
scrappify https://example.com -o my_site

# Download only PDF files
scrappify https://example.com -t pdf -o documents

# Download images and search for emails
scrappify https://example.com -t image -p email -o images_with_emails

# Deep crawl (3 levels) and download everything
scrappify https://example.com -d 3 -o deep_site

# Use custom regex pattern
scrappify https://example.com -p '\b\d{3}-\d{2}-\d{4}\b' -o ssn_search

# List available patterns
scrappify --list-patterns

# List available file types
scrappify --list-types

# High-performance download with 20 workers
scrappify https://example.com -w 20 -o fast_download
```

### Complex Examples

```bash
# Download all JavaScript and CSS files, search for URLs
scrappify https://example.com -t javascript -t css -p url -o assets_with_urls

# Download documents and images, search for prices
scrappify https://example.com -t document -t image -p price -o priced_content

# Deep crawl with custom pattern
scrappify https://example.com -d 2 -p '#[a-zA-Z0-9_]+' -o hashtags
```

---

## Available Options

### File Types

* `image` → png, jpg, gif, svg, etc.
* `document` → pdf, docx, txt, etc.
* `javascript`, `css`, `html`
* Custom extensions supported (e.g., `zip`, `mp4`)

### Patterns

* `email` → find emails
* `phone` → detect phone numbers
* `url` → extract URLs
* `price` → detect price patterns
* Custom regex patterns supported

---


## License

MIT License © 2025 \[MrFidal]
