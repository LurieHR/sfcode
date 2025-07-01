#!/usr/bin/env python3
"""Analyze duplicate text in chunks to understand the duplication pattern."""

import json
from collections import Counter, defaultdict
import re

# Load chunks
print("Loading chunks...")
with open('sf_code_chunks_test.json', 'r') as f:
    chunks = json.load(f)

print(f"Total chunks: {len(chunks)}")

# Extract all text content
all_texts = [chunk['content'] for chunk in chunks]

# Find exact duplicate chunks
text_counter = Counter(all_texts)
duplicates = [(text, count) for text, count in text_counter.items() if count > 1]

print(f"\n=== EXACT DUPLICATE CHUNKS ===")
print(f"Number of chunks that appear more than once: {len(duplicates)}")
print(f"Total duplicate occurrences: {sum(count - 1 for _, count in duplicates)}")

# Show top duplicates
print("\nTop 10 most duplicated chunks:")
for text, count in sorted(duplicates, key=lambda x: x[1], reverse=True)[:10]:
    preview = text[:100] + "..." if len(text) > 100 else text
    print(f"\nAppears {count} times: '{preview}'")

# Analyze duplicate patterns within chunks (substring analysis)
print("\n\n=== DUPLICATE PATTERNS WITHIN CHUNKS ===")

# Look for repeated sentences within individual chunks
repeated_sentences = 0
chunks_with_repeats = 0

for i, chunk in enumerate(chunks):
    text = chunk['content']
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    
    # Check for duplicates within this chunk
    sentence_counts = Counter(sentences)
    duplicated = [(s, c) for s, c in sentence_counts.items() if c > 1]
    
    if duplicated:
        chunks_with_repeats += 1
        repeated_sentences += sum(c - 1 for _, c in duplicated)
        
        if chunks_with_repeats <= 3:  # Show first 3 examples
            print(f"\nChunk {i} has repeated sentences:")
            print(f"Chapter: {chunk.get('chapter', 'N/A')}")
            print(f"Section: {chunk.get('section', 'N/A')}")
            for sent, count in duplicated:
                print(f"  - Appears {count} times: '{sent[:80]}...'")

print(f"\n\nSummary:")
print(f"Chunks with internal repeated sentences: {chunks_with_repeats}")
print(f"Total repeated sentences: {repeated_sentences}")

# Analyze overlapping text between consecutive chunks
print("\n\n=== OVERLAPPING TEXT BETWEEN CONSECUTIVE CHUNKS ===")

overlaps = 0
total_overlap_chars = 0

for i in range(len(chunks) - 1):
    text1 = chunks[i]['content']
    text2 = chunks[i + 1]['content']
    
    # Check if end of text1 appears at start of text2
    min_overlap = 50  # Minimum characters to consider an overlap
    max_check = min(len(text1), len(text2), 500)
    
    for length in range(max_check, min_overlap - 1, -1):
        if text1[-length:] == text2[:length]:
            overlaps += 1
            total_overlap_chars += length
            if overlaps <= 3:  # Show first 3 examples
                print(f"\nChunks {i} and {i+1} overlap by {length} characters:")
                print(f"Overlapping text: '{text1[-length:][:100]}...'")
            break

print(f"\n\nTotal overlapping consecutive chunks: {overlaps}")
print(f"Total overlapping characters: {total_overlap_chars}")

# Check for parent-child duplication pattern
print("\n\n=== PARENT-CHILD DUPLICATION PATTERN ===")

# Group chunks by chapter/article to find nested duplicates
by_chapter = defaultdict(list)
for i, chunk in enumerate(chunks):
    chapter = chunk.get('chapter', 'Unknown')
    by_chapter[chapter].append((i, chunk))

parent_child_duplicates = 0
for chapter, chapter_chunks in by_chapter.items():
    if len(chapter_chunks) < 2:
        continue
        
    # Check if any chunk's text is contained in another chunk in same chapter
    for i in range(len(chapter_chunks)):
        for j in range(i + 1, len(chapter_chunks)):
            idx1, chunk1 = chapter_chunks[i]
            idx2, chunk2 = chapter_chunks[j]
            text1 = chunk1['content']
            text2 = chunk2['content']
            
            if len(text1) > 50 and len(text2) > 50:  # Skip very short texts
                if text1 in text2 or text2 in text1:
                    parent_child_duplicates += 1
                    if parent_child_duplicates <= 3:  # Show first 3
                        print(f"\nFound parent-child duplicate:")
                        print(f"Chapter: {chapter}")
                        print(f"Chunk {idx1} ({len(text1)} chars) is contained in Chunk {idx2} ({len(text2)} chars)")
                        contained = text1 if text1 in text2 else text2
                        print(f"Contained text: '{contained[:100]}...'")

print(f"\n\nTotal parent-child duplicates found: {parent_child_duplicates}")