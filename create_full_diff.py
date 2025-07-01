#!/usr/bin/env python3
"""Create a simple ordered diff between raw text and parsed chunks."""

import json
import re
import difflib
import sys

def compare_image_urls(raw_text, chunks):
    """Compare image URLs between raw text and parsed chunks."""
    # Extract unique image URLs from raw text
    raw_image_urls = set()
    # First normalize the text by removing line breaks within URLs
    # Look for URLs that might have line breaks
    image_pattern = r'https://export\.amlegal\.com/media/[^/]+/IMAGES/[^\]]+\.(jpg|png)'
    
    # Find all potential image URLs, even with line breaks
    text_normalized = raw_text
    # Remove line breaks that appear within URLs
    url_with_break_pattern = r'(https://export\.amlegal\.com/media/[^/]+/IMAGES/[^\]]*)\s*\n\s*([^\]]+\.(jpg|png))'
    text_normalized = re.sub(url_with_break_pattern, r'\1\2', text_normalized, flags=re.MULTILINE)
    
    for match in re.finditer(image_pattern, text_normalized):
        raw_image_urls.add(match.group(0))

    # Extract unique image URLs from chunks
    chunk_image_urls = set()
    for chunk in chunks:
        if 'all_links' in chunk and 'image_links' in chunk['all_links']:
            for img in chunk['all_links']['image_links']:
                if 'src' in img:
                    chunk_image_urls.add(img['src'])

    print(f"\n=== IMAGE URL COMPARISON ===")
    print(f"Unique image URLs in raw text: {len(raw_image_urls)}")
    print(f"Unique image URLs in chunks: {len(chunk_image_urls)}")

    # Find missing URLs
    missing_from_chunks = raw_image_urls - chunk_image_urls
    if missing_from_chunks:
        print(f"\nMissing from chunks ({len(missing_from_chunks)} URLs):")
        for url in sorted(missing_from_chunks)[:10]:  # Show first 10
            print(f"  - {url}")
        if len(missing_from_chunks) > 10:
            print(f"  ... and {len(missing_from_chunks) - 10} more")

    # Find extra URLs in chunks
    extra_in_chunks = chunk_image_urls - raw_image_urls
    if extra_in_chunks:
        print(f"\nExtra in chunks ({len(extra_in_chunks)} URLs):")
        for url in sorted(extra_in_chunks)[:10]:  # Show first 10
            print(f"  - {url}")

def compare_text_content(raw_text, chunks):
    """Compare text content between raw and parsed chunks."""
    # Make a copy of raw text and remove ALL URLs (including those with spaces/newlines)
    raw_copy = raw_text
    
    # First, fix URLs that have line breaks in them
    url_with_break_pattern = r'(https://export\.amlegal\.com/media/[^/]+/IMAGES/[^\]]*)\s*\n\s*([^\]]+\.(jpg|png))'
    raw_copy = re.sub(url_with_break_pattern, '', raw_copy, flags=re.MULTILINE)
    
    # Then remove all remaining URLs
    url_pattern = r'https://export\.amlegal\.com/media/[^\s\]]+\.(jpg|png)'
    raw_copy = re.sub(url_pattern, '', raw_copy)
    
    # Also remove the square brackets that contained URLs
    raw_copy = re.sub(r'\[\]', '', raw_copy)
    
    # Combine chunks
    combined_chunks = " ".join(chunk['content'] for chunk in chunks)
    
    # Normalize whitespace (but don't remove all of it)
    raw_norm = re.sub(r'\s+', ' ', raw_copy).strip()
    chunks_norm = re.sub(r'\s+', ' ', combined_chunks).strip()

    print(f"\n=== TEXT COMPARISON (URLs removed from raw) ===")
    print(f"Raw (normalized): {len(raw_norm)} chars")
    print(f"Chunks (normalized): {len(chunks_norm)} chars")
    print(f"Difference: {abs(len(raw_norm) - len(chunks_norm))} chars ({abs(len(raw_norm) - len(chunks_norm)) / len(raw_norm) * 100:.2f}%)")

    # Optional: Show first few characters of each to verify
    if len(raw_norm) > 0 and len(chunks_norm) > 0:
        print(f"\nFirst 100 chars of raw (normalized): '{raw_norm[:100]}'...")
        print(f"First 100 chars of chunks (normalized): '{chunks_norm[:100]}'...")
    
    # Show detailed differences
    show_detailed_diff(raw_norm, chunks_norm)

def show_detailed_diff(raw_norm, chunks_norm):
    """Show detailed character-by-character differences between normalized texts."""
    print("\n=== DETAILED DIFFERENCES ===\n")
    
    diff_count = 0
    i = 0
    j = 0
    
    while i < len(raw_norm) and j < len(chunks_norm):
        if raw_norm[i] == chunks_norm[j]:
            i += 1
            j += 1
        else:
            diff_count += 1
            # Find extent of difference
            raw_start = i
            chunk_start = j
            
            # Find where they sync up again
            found_sync = False
            for window in range(1, 100):
                for offset in range(window):
                    if i + offset < len(raw_norm) and j + window - offset < len(chunks_norm):
                        if raw_norm[i + offset:i + offset + 10] == chunks_norm[j + window - offset:j + window - offset + 10]:
                            i += offset
                            j += window - offset
                            found_sync = True
                            break
                if found_sync:
                    break
            
            if not found_sync:
                i += 1
                j += 1
                
            print(f"Diff {diff_count} at raw:{raw_start} chunk:{chunk_start}")
            print(f"  Raw:    '{raw_norm[max(0,raw_start-20):i+20]}'")
            print(f"  Chunks: '{chunks_norm[max(0,chunk_start-20):j+20]}'")
            print()
            
    
    # Handle remaining text
    if i < len(raw_norm):
        print(f"\nRaw has {len(raw_norm) - i} extra characters at end")
        print(f"Extra: '{raw_norm[i:i+100]}'...")
        
    if j < len(chunks_norm):
        print(f"\nChunks have {len(chunks_norm) - j} extra characters at end")
        print(f"Extra: '{chunks_norm[j:j+100]}'...")

def main():
    # Get chunk file from command line or use default
    chunk_file = sys.argv[1] if len(sys.argv) > 1 else 'sf_code_chunks.json'
    print(f"Comparing against: {chunk_file}")

    # Load files
    with open('/Users/helen/Downloads/san_francisco-ca-unstructuredtext.txt', 'r', encoding='utf-8', errors='replace') as f:
        raw_text = f.read()

    with open(chunk_file, 'r') as f:
        chunks = json.load(f)

    # Run comparisons
    compare_image_urls(raw_text, chunks)
    compare_text_content(raw_text, chunks)

if __name__ == "__main__":
    main()