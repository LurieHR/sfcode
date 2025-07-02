# San Francisco Municipal Code Parser

A Python parser for extracting text and metadata from San Francisco Municipal Code HTML documents.

## Overview

This project contains tools for parsing the complete San Francisco Municipal Code HTML export and comparing parsed output with the original raw text to ensure completeness.

## Main Components

### 1. `parse_sf_code.py` - HTML Parser
Extracts text content and metadata from the SF Municipal Code HTML file, creating structured JSON output with:
- Document hierarchy (Charter → Chapter → Article → Section)
- Links (internal, external, images)
- Amendment history
- Cross-references

**Usage:**
```bash
python parse_sf_code.py -i rawcodes/san_francisco-ca-complete.html -o sf_code_chunks.json
```

### 2. `diff_analyzer.py` - Text Comparison Tool
Compares the parsed/reconstructed text with the original raw text to identify missing or altered content.

**Features:**
- Normalizes whitespace before comparison
- Configurable minimum difference size filter
- Processes large files by article divisions
- Shows exact differences with context

**Usage:**
```bash
# Default: show differences >= 200 characters
python diff_analyzer.py sf_code_chunks.json

# Show all differences
python diff_analyzer.py sf_code_chunks.json 0

# Show only large differences >= 500 characters
python diff_analyzer.py sf_code_chunks.json 500
```

## Input Files

- `rawcodes/san_francisco-ca-complete.html` - Complete SF Municipal Code HTML (105MB)
- `rawcodes/san_francisco-ca-unstructuredtext.txt` - Raw text for validation (31MB)

## Output

- `sf_code_chunks.json` - Parsed content with metadata (200MB+)

## Requirements

- Python 3.6+
- BeautifulSoup4

## Data Source

HTML files exported from American Legal Publishing:
https://codelibrary.amlegal.com/codes/san_francisco/latest/overview