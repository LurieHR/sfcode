#!/usr/bin/env python3
"""
Diff analyzer that compares SF code by article divisions.
"""

import json
import sys
import re
from pathlib import Path
from difflib import SequenceMatcher


def load_json_chunks(json_path):
    """Load the JSON chunks file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_article_divisions(text):
    """Find all article divisions in the text."""
    # Pattern to match ARTICLE headers
    # Looking for patterns like "ARTICLE I:", "ARTICLE II:", etc.
    # Allow for optional newline after colon
    article_pattern = r'ARTICLE\s+([IVXLCDM]+):\s*([^\n]+)?'
    
    articles = []
    for match in re.finditer(article_pattern, text):
        article_num = match.group(1)
        article_title = match.group(2).strip() if match.group(2) else ""
        start_pos = match.start()
        
        articles.append({
            'number': article_num,
            'title': article_title,
            'start': start_pos,
            'full_header': match.group(0)
        })
    
    # Add end positions
    for i in range(len(articles)):
        if i < len(articles) - 1:
            articles[i]['end'] = articles[i + 1]['start']
        else:
            articles[i]['end'] = len(text)
    
    return articles


def extract_article_text(text, article):
    """Extract text for a specific article."""
    return text[article['start']:article['end']]


def reconstruct_text_from_json(chunks):
    """Reconstruct the raw text from JSON chunks."""
    reconstructed_lines = []
    
    for chunk in chunks:
        # Add content if present (primary text field)
        if 'content' in chunk and chunk['content']:
            reconstructed_lines.append(chunk['content'])
        # Also check for 'text' field as fallback
        elif 'text' in chunk and chunk['text']:
            reconstructed_lines.append(chunk['text'])
    
    return '\n'.join(reconstructed_lines)


def should_ignore_diff(text):
    """Check if a difference should be ignored based on whitespace, underscores, or URLs."""
    # Check if it's just whitespace
    if text.strip() == '':
        return True
    
    # Check if it's just underscores vs spaces
    if text.replace('_', ' ').strip() == '':
        return True
    
    # Check if it's a URL
    url_patterns = [
        r'^https?://[^\s]+$',
        r'^ftp://[^\s]+$',
        r'^www\.[^\s]+$'
    ]
    
    for pattern in url_patterns:
        if re.match(pattern, text.strip()):
            return True
    
    return False


def normalize_whitespace(text):
    """Normalize whitespace for comparison."""
    # Replace all whitespace characters with single spaces
    # This includes \n, \r, \t, non-breaking spaces, etc.
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def get_surrounding_context(text, start, end, context_size=400):
    """Get surrounding context for a difference."""
    # Calculate context boundaries
    context_start = max(0, start - context_size)
    context_end = min(len(text), end + context_size)
    
    # Get the context
    before = text[context_start:start]
    diff_text = text[start:end]
    after = text[end:context_end]
    
    # Mark the difference with brackets
    return f"{before}[[[{diff_text}]]]{after}"


def find_and_print_differences_for_article(raw_text, reconstructed_text, article_num, min_diff_size=200):
    """Find and print differences for a specific article."""
    # Store original texts for display
    original_raw = raw_text
    original_reconstructed = reconstructed_text
    
    # Normalize whitespace for comparison
    normalized_raw = normalize_whitespace(raw_text)
    normalized_reconstructed = normalize_whitespace(reconstructed_text)
    
    # For very large articles, process in chunks
    MAX_CHUNK_SIZE = 1000000  # 1MB chunks
    
    if len(normalized_raw) > MAX_CHUNK_SIZE or len(normalized_reconstructed) > MAX_CHUNK_SIZE:
        print(f"  Article {article_num} is very large, processing in chunks...")
        # For now, just do a simple comparison
        if normalized_raw == normalized_reconstructed:
            print(f"  Article {article_num} content is IDENTICAL despite large size")
            return 0
        else:
            print(f"  Article {article_num} content DIFFERS - skipping detailed analysis due to size")
            print(f"  Size difference: {len(normalized_reconstructed) - len(normalized_raw)} chars")
            return 1
    
    # Use SequenceMatcher for efficient difference finding on normalized text
    matcher = SequenceMatcher(None, normalized_raw, normalized_reconstructed)
    
    diff_count = 0
    
    # Get all opcodes (differences)
    opcodes = list(matcher.get_opcodes())
    
    for idx, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if tag == 'equal':
            continue
        
        # Extract the different parts from normalized text
        norm_raw_part = normalized_raw[i1:i2]
        norm_reconstructed_part = normalized_reconstructed[j1:j2]
        
        # For display, we need to map back to original text positions
        # This is approximate but should be close enough for context
        raw_part = norm_raw_part  # We'll show the normalized diff
        reconstructed_part = norm_reconstructed_part
        
        # Check if we should ignore this difference
        if should_ignore_diff(raw_part) and should_ignore_diff(reconstructed_part):
            continue
        
        # Skip small differences if configured
        max_diff_len = max(len(raw_part), len(reconstructed_part))
        if max_diff_len < min_diff_size:
            continue
        
        diff_count += 1
        
        # Determine the type of difference
        if tag == 'delete':
            # Text present in raw, missing in reconstructed
            print("\n" + "-" * 80)
            print(f"Article {article_num} - Diff {diff_count}: {len(raw_part)} characters present in RAW, missing in RECONSTRUCTED")
            print(f"Missing text: {repr(raw_part)}")
            print(f"\nRAW text context:")
            print(get_surrounding_context(normalized_raw, i1, i2))
            print(f"\nRECONSTRUCTED text context (at position {j1}):")
            # For missing text in reconstructed, show where it should be with markers
            context_start = max(0, j1 - 400)
            context_end = min(len(normalized_reconstructed), j1 + 400)
            before = normalized_reconstructed[context_start:j1]
            after = normalized_reconstructed[j1:context_end]
            markers = '%-' * (len(raw_part) // 2) + '%' * (len(raw_part) % 2)
            print(f"{before}[[[{markers}]]]{after}")
            
        elif tag == 'insert':
            # Text present in reconstructed, missing in raw
            print("\n" + "+" * 80)
            print(f"Article {article_num} - Diff {diff_count}: {len(reconstructed_part)} characters present in RECONSTRUCTED, missing in RAW")
            print(f"Extra text: {repr(reconstructed_part)}")
            print(f"\nRAW text context (at position {i1}):")
            # For extra text in raw, show where it's missing with markers
            context_start = max(0, i1 - 400)
            context_end = min(len(normalized_raw), i1 + 400)
            before = normalized_raw[context_start:i1]
            after = normalized_raw[i1:context_end]
            markers = '%-' * (len(reconstructed_part) // 2) + '%' * (len(reconstructed_part) % 2)
            print(f"{before}[[[{markers}]]]{after}")
            print(f"\nRECONSTRUCTED text context:")
            print(get_surrounding_context(normalized_reconstructed, j1, j2))
            
        elif tag == 'replace':
            # Text different between raw and reconstructed
            print("\n" + "=" * 80)
            print(f"Article {article_num} - Diff {diff_count}: REPLACEMENT - {len(raw_part)} chars in RAW replaced by {len(reconstructed_part)} chars in RECONSTRUCTED")
            print(f"RAW text: {repr(raw_part)}")
            print(f"RECONSTRUCTED text: {repr(reconstructed_part)}")
            print(f"\nRAW text context:")
            print(get_surrounding_context(normalized_raw, i1, i2))
            print(f"\nRECONSTRUCTED text context:")
            print(get_surrounding_context(normalized_reconstructed, j1, j2))
    
    return diff_count


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python diff_analyzer.py <json_file> [min_diff_size]")
        print("  min_diff_size: minimum character difference to display (default: 200)")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    
    # Get minimum difference size from command line or use default
    MIN_DIFF_SIZE = 200
    if len(sys.argv) == 3:
        try:
            MIN_DIFF_SIZE = int(sys.argv[2])
        except ValueError:
            print(f"Error: min_diff_size must be an integer, got '{sys.argv[2]}'")
            sys.exit(1)
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)
    
    # Load JSON chunks
    print(f"Loading JSON from: {json_path}")
    chunks = load_json_chunks(json_path)
    
    # Reconstruct text
    print("Reconstructing text from JSON...")
    reconstructed_text = reconstruct_text_from_json(chunks)
    
    # Save reconstructed text
    reconstructed_path = Path("reconstructed_raw.txt")
    with open(reconstructed_path, 'w', encoding='utf-8') as f:
        f.write(reconstructed_text)
    print(f"Saved reconstructed text to: {reconstructed_path}")
    
    # Load raw source text
    raw_text_path = Path("rawcodes/san_francisco-ca-unstructuredtext.txt")
    if not raw_text_path.exists():
        print(f"Error: Raw text file not found: {raw_text_path}")
        sys.exit(1)
    
    print(f"Loading raw text from: {raw_text_path}")
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    raw_text = None
    
    for encoding in encodings:
        try:
            with open(raw_text_path, 'r', encoding=encoding) as f:
                raw_text = f.read()
            print(f"Successfully loaded with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    
    if raw_text is None:
        print("Error: Could not decode raw text file with any common encoding")
        sys.exit(1)
    
    print(f"\nRaw text size: {len(raw_text)} characters")
    print(f"Reconstructed text size: {len(reconstructed_text)} characters")
    
    # Find article divisions in both texts
    print("\nFinding article divisions in raw text...")
    raw_articles = find_article_divisions(raw_text)
    print(f"Found {len(raw_articles)} articles in raw text:")
    for art in raw_articles:
        print(f"  - ARTICLE {art['number']}: {art['title']} (chars {art['start']}-{art['end']})")
    
    print("\nFinding article divisions in reconstructed text...")
    reconstructed_articles = find_article_divisions(reconstructed_text)
    print(f"Found {len(reconstructed_articles)} articles in reconstructed text:")
    for art in reconstructed_articles:
        print(f"  - ARTICLE {art['number']}: {art['title']} (chars {art['start']}-{art['end']})")
    
    # Compare article structure
    print("\n" + "=" * 80)
    print("ARTICLE STRUCTURE COMPARISON")
    print("=" * 80)
    
    raw_article_nums = [art['number'] for art in raw_articles]
    recon_article_nums = [art['number'] for art in reconstructed_articles]
    
    # Find missing articles
    missing_in_recon = set(raw_article_nums) - set(recon_article_nums)
    extra_in_recon = set(recon_article_nums) - set(raw_article_nums)
    
    if missing_in_recon:
        print(f"\nArticles in RAW but missing in RECONSTRUCTED: {sorted(missing_in_recon)}")
    if extra_in_recon:
        print(f"\nArticles in RECONSTRUCTED but not in RAW: {sorted(extra_in_recon)}")
    
    # Create lookup dictionaries
    raw_dict = {art['number']: art for art in raw_articles}
    recon_dict = {art['number']: art for art in reconstructed_articles}
    
    # Compare articles that exist in both
    common_articles = set(raw_article_nums) & set(recon_article_nums)
    
    print("\n" + "=" * 80)
    print("DETAILED ARTICLE COMPARISON")
    print("=" * 80)
    
    total_diffs = 0
    
    for article_num in sorted(common_articles):
        raw_art = raw_dict[article_num]
        recon_art = recon_dict[article_num]
        
        raw_art_text = extract_article_text(raw_text, raw_art)
        recon_art_text = extract_article_text(reconstructed_text, recon_art)
        
        # Quick check if they're identical
        if raw_art_text == recon_art_text:
            # Don't print anything for identical articles
            pass
        else:
            # Analyze differences
            article_diffs = find_and_print_differences_for_article(raw_art_text, recon_art_text, article_num, MIN_DIFF_SIZE)
            total_diffs += article_diffs
            
            # Only print header if we found differences
            if article_diffs > 0:
                print(f"\nFound {article_diffs} differences >= {MIN_DIFF_SIZE} chars in Article {article_num}")
    
    print(f"\n{'=' * 80}")
    print(f"Analysis complete! Total differences >= {MIN_DIFF_SIZE} chars found: {total_diffs}")


if __name__ == "__main__":
    main()