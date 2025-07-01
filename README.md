# San Francisco Municipal Code Parser

A Python parser for converting San Francisco Municipal Code HTML documents into structured, searchable JSON chunks.

## Overview

This parser processes the complete San Francisco Municipal Code HTML export and breaks it down into manageable chunks while preserving the hierarchical structure and metadata.

## Features

- **Hierarchical Structure Recognition**: Automatically identifies and preserves the document hierarchy (Chapters → Articles → Divisions → Sections)
- **Smart Chunking**: Creates chunks at structural boundaries with configurable size limits (default 2000 characters)
- **Metadata Extraction**: 
  - Document structure (chapter, article, division, section information)
  - Internal and external links
  - Amendment history
  - CSS class information for semantic content types
- **Cross-Reference Support**: Parses and preserves internal document references

## Usage

### Basic Usage

```bash
python parse_sf_code.py
```

### Command Line Options

```bash
python parse_sf_code.py [-h] [-i INPUT] [-o OUTPUT] [-s CHUNK_SIZE] [-b]

Options:
  -h, --help            Show help message and exit
  -i INPUT, --input INPUT
                        Input HTML file (default: rawcodes/san_francisco-ca-small.html)
  -o OUTPUT, --output OUTPUT
                        Output JSON file (default: sf_code_chunks.json)
  -s CHUNK_SIZE, --chunk-size CHUNK_SIZE
                        Maximum chunk size (default: 2000)
  -b, --browse          Browse chunks interactively after parsing
```

### Example: Parse the Complete Code

```bash
python parse_sf_code.py -i rawcodes/san_francisco-ca-complete.html -o sfcode.json
```

## Output Format

The parser generates a JSON file containing an array of chunks. Each chunk includes:

```json
{
  "content": "The actual text content...",
  "doc_id": "sf_municipal_code_charter_article_i",
  "chunk_id": "sf_municipal_code_charter_article_i_1",
  "chunk_index": 1,
  "title": "Charter - Article I",
  "uuid": "deterministic-uuid-based-on-doc-id",
  "chapter": "Charter",
  "article": "ARTICLE I: EXISTENCE AND POWERS OF THE CITY AND COUNTY",
  "article_number": "I",
  "article_title": "EXISTENCE AND POWERS OF THE CITY AND COUNTY",
  "division": null,
  "section_id": "rid-0-0-0-123",
  "section_number": "1.100",
  "section_title": "NAME AND BOUNDARIES",
  "div_classes": ["Currency", "Table-Text"],
  "all_links": {
    "internal_links": [...],
    "external_links": [...],
    "intercode_links": [...]
  },
  "references": [
    {
      "hash": "#JD_2.100",
      "reference_string": "Section 2.100",
      "record_id": "0-0-0-123"
    }
  ],
  "history_data": {
    "added_by": ["123-45"],
    "amended_by": ["678-90", "234-56"],
    "see_also": []
  },
  "source_url": "https://codelibrary.amlegal.com/codes/san_francisco/latest/overview",
  "download_date": "2024-06-30",
  "city": "San Francisco",
  "processing_timestamp": "2024-11-07T12:34:56Z",
  "character_count": 1847
}
```

## Helper Scripts

### code_helpers.py

Provides utility functions for analyzing the parsed data:

- `count_chunks(json_file)` - Count total chunks
- `get_chunk_by_identifier(json_file, doc_id, section_id, uuid)` - Retrieve specific chunks
- `count_chapters_and_sections(json_file)` - Get statistics about the document structure
- `inspect_chunks(json_file, num_chunks, verbose)` - Examine chunk contents
- `get_referenced_chunks_from_chunk(json_file, source_chunk, reference_index)` - Follow cross-references

## Data Source

The HTML files are exported from the American Legal Publishing system that hosts the official San Francisco Municipal Code at:
https://codelibrary.amlegal.com/codes/san_francisco/latest/overview

## Requirements

- Python 3.6+
- BeautifulSoup4
- A helper function `generate_doc_uuid` from the congressionalrag project (for UUID generation)

## Statistics

When parsing the complete SF Municipal Code:
- Input: ~117,000 HTML elements
- Output: ~24,000 chunks
- Covers: 459 chapters across all municipal codes

## License

This parser is provided as-is for processing publicly available municipal code data.